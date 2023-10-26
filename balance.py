# flask --app balance run
from flask import Flask
import sys
import random
from flask_cors import CORS, cross_origin
import threading
import random
import socket
import select
import time
import datetime
import re

app = Flask(__name__)
cors = CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"


ip_address = False
if len(sys.argv) > 1:
    ip_address = sys.argv[1]
    print("ip address:", ip_address)
else:
    print("No arguments provided.")

dummy = False
if len(sys.argv) > 2:
    print(
        "there is a lot of arguments, we start dummy mode (no connection to the scale)"
    )
    dummy = True


class ScaleConnection:
    def __init__(self, ip_address, port=4305):
        if not ip_address:
            ip_address = "192.168.55.29"
        print("ip is ", ip_address)
        self.ip = ip_address
        self.port = port
        self.last_call = datetime.datetime.now()
        self.sock = False

    def _send_msg(self, command):
        if self.sock:
            self.interrupt()
        if command == "SRU":
            return self._send_sru()
        result = ""
        try:
            now = datetime.datetime.now()
            if (now - self.last_call).total_seconds() < 0.1:
                time.sleep(0.1)
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = (self.ip, self.port)
            self.sock.settimeout(2)
            self.sock.connect(server_address)
            message = command + "\n"
            self.sock.sendall(message.encode("utf-8"))
            data = self.sock.recv(1024)  # Receive up to 1024 bytes
            result = data.decode("utf-8")
        except Exception as e:
            print("Exception caught:", e)
        finally:
            if self.sock:
                self.sock.close()
                self.sock = False
            self.last_call = datetime.datetime.now()
        return result

    def _send_sru(self):
        try:
            now = datetime.datetime.now()
            if (now - self.last_call).total_seconds() < 0.1:
                time.sleep(0.1)
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = (self.ip, self.port)
            self.sock.settimeout(2)
            self.sock.connect(server_address)
            message = "SRU\n"
            self.sock.sendall(message.encode("utf-8"))
            while True:
                data = self.sock.recv(1024)  # Receive up to 1024 bytes
                data = data.decode("utf-8")
                if "S S" in data:
                    print("we received: ", data)
                    self.parse_weight(data)
        except Exception as e:
            print("Exception caught:", e)
        finally:
            if self.sock:
                self.sock.close()
                self.sock = False
            self.last_call = datetime.datetime.now()
        return ""

    def interrupt(self):
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
            except Exception as e:
                print("Exception caught:", e)
            finally:
                self.sock = False

    def launch_sru(self):
        return self._send_sru()

    def parse_weight(self, weight):
        match = re.search(r"(\d+\.\d+)\s+(\w+)", weight)
        if match:
            number = float(match.group(1))  # Convert to float
            unit = match.group(2)  # This is the unit
            print(f"number: {number}, unit: {unit}")
            return number
        else:
            print("No match found.")
            return False

    def reset_tare(self):
        tare = self._send_msg("TAC")
        print("result for reset is ", tare)
        return tare

    def tare(self):
        tare = self._send_msg("T")
        print("tare result is ", tare)
        return tare

    def weight(self):
        weight = self._send_msg("S")
        if weight:
            return self.parse_weight(weight)
        else:
            return ""


scale = ScaleConnection(ip_address)


@app.route("/get_weight", methods=["POST", "GET"])
@cross_origin()
def get_weight():
    res = scale.weight()
    return {"weight": res}


@app.route("/tare", methods=["POST", "GET"])
def tare():
    return {"ok": scale.tare()}


@app.route("/reset_tare", methods=["POST", "GET"])
def reset_tare():
    return {"ok": scale.reset_tare()}


@app.route("/get_continuous", methods=["POST", "GET"])
def get_continuous():
    if not scale.sock:
        print("bizzare")
    return {"new": False}


@app.route("/launch_continuous", methods=["POST", "GET"])
def launch_continuous():
    if not scale.sock:
        thread = threading.Thread(name="interval_query", target=scale.launch_sru)
        thread.setDaemon(True)
        thread.start()
    return {"ok": "STARTED"}


@app.route("/stop_continuous", methods=["POST", "GET"])
def stop_continuous():
    scale.interrupt()
    return {"ok": "INTERUPTED"}


@app.route("/")
def doc():
    return """
    <html>
    <ul>
    <li>
    <a href="/get_weight"> /get_weight: Avoir le poids actuel</a>
    </li><li>
    <a href="/tare">/tare: Tare</a>
    </li><li>
    <a href="/reset_tare">/reset_tare: Reset Tare</a>
    </li><li>
    <a href="/launch_continuous">/launch_continuous: Lancer sans arret</a>
    </li><li>
    <a href="/get_continuous">/get_continuous: verifie si nouvelle valeur</a>
    </li><li>
    <a href="/stop_continuous">/stop_continuous: STOP</a>
    </li>
    </ul>
    </html>
    """


if __name__ == "__main__":
    app.run()
