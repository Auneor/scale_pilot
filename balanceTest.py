import socket
import select
import time
import datetime
import re
from pyfzf.pyfzf import FzfPrompt
from collections import OrderedDict

"""
Configuration NETPLAN pour avoir accés à la balance:
simon@ ~ () $ cat /etc/netplan/01-network-manager-all.yaml
# Let NetworkManager manage all devices on this system
network:
  version: 2
  renderer: NetworkManager
  ethernets:
        eno2:
                addresses:
                        - 192.168.55.1/24
                nameservers:
                        addresses: [8.8.8.8]

puis netplan apply
"""
COMMANDS = [
    ("@", "Redémarrer la balance"),
    #    ("I0", "Envoyer la liste de toutes les instructions SICS disponibles"),
    #    ("I1", "Envoyer le niveau SICS et les versions SICS"),
    #   ("I2", "Envoyer les données de la balance"),
    #  ("I3", "Envoyer la version du logiciel de la balance"),
    # ("I4", "Envoyer le numéro de série"),
    ("S", "Envoyer la valeur de poids stable"),
    ("SI", "Envoyer immédiatement la valeur de poids"),
    #    ("SIR", "Envoyer immédiatement la valeur de poids et répéter"),
    ("Z", "Remettre à zéro"),
    ("ZI", "Remise à zéro immédiate"),
    #   ("D", "Décrire l'afficheur"),
    #  ("DW", "Affichage de poids"),
    # ("K", "Contrôle de clavier"),
    # ("SR", "Envoyer la valeur de poids stable et répéter"),
    ("T", "Tarage"),
    #    ("TA", "Valeur de tare"),
    ("TAC", "Effacer la tare"),
    ("TI", "Tarer immédiatement"),
    #    ("C2", "Calibrer avec un poids de calibrage externe"),
    #    ("C3", "Calibrer avec un poids de calibrage interne"),
    #    ("I31", "En-tête pour l'impression"),
    #   ("ICP", "Envoyer la configuration de l'impression"),
    #    ("LST", "Envoyer les réglages de menu"),
    #   ("M01", "Mode de pesée"),
    #    ("M02", "Réglage de stabilité"),
    #   ("M03", "Fonction autozéro"),
    #  ("M16", "Mode Sleep ou PowerOff"),
    # ("M19", "Envoyer le poids de calibrage"),
    # ("M21", "Envoyer/introduire l'unité de poids"),
    #    ("P100", "Impression sur imprimante de bandes"),
    #   ("P101", "Envoyer la valeur de poids stable à l'imprimante"),
    #  ("P102", "Envoyer la valeur de poids immédiatement à l'imprimante"),
    # ("PRN", "Impression sur n'importe quelle interface d'imprimante"),
    #    ("PWR", "MARCHE/ARRET"),
    ("RST", "Redémarrage"),
    ("SIH", "Envoyer immédiatement la valeur de poids en résolution élevée"),
    #   (
    #      "SIRU",
    #     "Envoyer immédiatement la valeur de poids dans l'unité actuelle et répéter",
    # ),
    ("SIU", "Envoyer immédiatement la valeur de poids dans l'unité actuelle"),
    ("SRU", "Envoyer la valeur de poids stable dans l'unité actuelle et répéter"),
    (
        "ST",
        "Envoyer la valeur de poids stable à l'actionnement de la touche de transfert",
    ),
    #   ("SU", "Envoyer la valeur de poids stable dans l'unité de poids actuelle"),
    #    ("SWU", "Commuter l'unité de poids"),
    #    ("SX", "Envoyer le jeu de données stable"),
    #   ("SXI", "Envoyer immédiatement le jeu de données"),
    #    ("SXIR", "Envoyer immédiatement le jeu de données et répéter"),
    #  ("TST2", "Lancer la fonction de test avec un poids externe"),
    # ("TST3", "Lancer la fonction de test avec un poids interne"),
    #    ("U", "Commuter l'unité de poids"),
]


IMPLEMENTED_COMMANDS = [
    ("@", "Redémarrer la balance"),
    ("I0", "Envoyer la liste de toutes les instructions SICS disponibles"),
    ("I1", "Envoyer le niveau SICS et les versions SICS"),
    ("I2", "Envoyer les données de la balance"),
    ("I3", "Envoyer la version du logiciel de la balance"),
    ("I4", "Envoyer le numéro de série"),
    ("S", "Envoyer la valeur de poids stable"),
    ("SI", "Envoyer immédiatement la valeur de poids"),
    ("SIR", "Envoyer immédiatement la valeur de poids et répéter"),
    ("Z", "Remettre à zéro"),
    ("ZI", "Remise à zéro immédiate"),
    ("D", "Décrire l'afficheur"),
    ("DW", "Affichage de poids"),
    ("K", "Contrôle de clavier"),
    ("SR", "Envoyer la valeur de poids stable et répéter"),
    ("T", "Tarage"),
    ("TA", "Valeur de tare"),
    ("TAC", "Effacer la tare"),
    ("TI", "Tarer immédiatement"),
    ("C2", "Calibrer avec un poids de calibrage externe"),
    ("C3", "Calibrer avec un poids de calibrage interne"),
    ("I31", "En-tête pour l'impression"),
    ("ICP", "Envoyer la configuration de l'impression"),
    ("LST", "Envoyer les réglages de menu"),
    ("M01", "Mode de pesée"),
    ("M02", "Réglage de stabilité"),
    ("M03", "Fonction autozéro"),
    ("M16", "Mode Sleep ou PowerOff"),
    ("M19", "Envoyer le poids de calibrage"),
    ("M21", "Envoyer/introduire l'unité de poids"),
    ("P100", "Impression sur imprimante de bandes"),
    ("P101", "Envoyer la valeur de poids stable à l'imprimante"),
    ("P102", "Envoyer la valeur de poids immédiatement à l'imprimante"),
    ("PRN", "Impression sur n'importe quelle interface d'imprimante"),
    ("PWR", "MARCHE/ARRET"),
    ("RST", "Redémarrage"),
    ("SIH", "Envoyer immédiatement la valeur de poids en résolution élevée"),
    (
        "SIRU",
        "Envoyer immédiatement la valeur de poids dans l'unité actuelle et répéter",
    ),
    ("SIU", "Envoyer immédiatement la valeur de poids dans l'unité actuelle"),
    ("SRU", "Envoyer la valeur de poids stable dans l'unité actuelle et répéter"),
    (
        "ST",
        "Envoyer la valeur de poids stable à l'actionnement de la touche de transfert",
    ),
    ("SU", "Envoyer la valeur de poids stable dans l'unité de poids actuelle"),
    ("SWU", "Commuter l'unité de poids"),
    ("SX", "Envoyer le jeu de données stable"),
    ("U", "Commuter l'unité de poids"),
]
"""
Commandes de la balance
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 @     Redémarrer la balance                                                        
 I0    Envoyer la liste de toutes les instructions SICS disponibles                 
 I1    Envoyer le niveau SICS et les versions SICS                                  
 I2    Envoyer les données de la balance                                            
 I3    Envoyer la version du logiciel de la balance                                 
 I4    Envoyer le numéro de série                                                   
 S     Envoyer la valeur de poids stable                                            
 SI    Envoyer immédiatement la valeur de poids                                     
 SIR   Envoyer immédiatement la valeur de poids et répéter                          
 Z     Remettre à zéro                                                              
 ZI    Remise à zéro immédiate                                                      
 D     Décrire l'afficheur                                                          
 DW    Affichage de poids                                                           
 K     Contrôle de clavier                                                          
 SR    Envoyer la valeur de poids stable et répéter                                 
 T     Tarage                                                                       
 TA    Valeur de tare                                                               
 TAC   Effacer la tare                                                               
 TI    Tarer immédiatement                                                          
 C2    Calibrer avec un poids de calibrage externe                                  
 C3    Calibrer avec un poids de calibrage interne                                  
 I     31En-tête pour l'impression                                                  
 ICP   Envoyer la configuration de l'impression                                     
 LST   Envoyer les réglages de menu                                                 
 M01   Mode de pesée                                                                
 M02   Réglage de stabilité                                                         
 M03   Fonction autozéro                                                            
 M16   Mode Sleep ou PowerOff                                                       
 M19   Envoyer le poids de calibrage                                                
 M21   Envoyer/introduire l'unité de poids                                          
 P100  Impression sur imprimante de bandes                                          
 P101  Envoyer la valeur de poids stable à l'imprimante                             
 P102  Envoyer la valeur de poids immédiatement à l'imprimante                      
 PRN   Impression sur n'importe quelle interface d'imprimante                       
 PWR   MARCHE/ARRET                                                                 
 RST   Redémarrage                                                                  
 SIH   Envoyer immédiatement la valeur de poids en résolution élevée                
 SIRU  Envoyer immédiatement la valeur de poids dans l'unité actuelle et répéter    
 SIU   Envoyer immédiatement la valeur de poids dans l'unité actuelle               
 SRU   Envoyer la valeur de poids stable dans l'unité actuelle et répéter           
 ST    Envoyer la valeur de poids stable à l'actionnement de la touche de transfert 
 SU    Envoyer la valeur de poids stable dans l'unité de poids actuelle             
 SWU   Commuter l'unité de poids                                                    
 SX    Envoyer le jeu de données stable                                             
 SXI   Envoyer immédiatement le jeu de données                                      
 SXIR  Envoyer immédiatement le jeu de données et répéter                           
 TST2  Lancer la fonction de test avec un poids externe                             
 TST3  Lancer la fonction de test avec un poids interne                             
 U     Commuter l'unité de poids                                                    
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""


class ScaleConnection:
    def __init__(self, ip="192.168.55.29", port=4305):
        self.ip = ip
        self.port = port
        self.last_call = datetime.datetime.now()

    def _send_msg(self, command):
        if command == "SRU":
            return self._send_sru()
        try:
            now = datetime.datetime.now()
            if (now - self.last_call).total_seconds() < 0.1:
                time.sleep(0.1)
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = (self.ip, self.port)
            self.sock.connect(server_address)
            message = command + "\n"
            self.sock.sendall(message.encode("utf-8"))
            data = self.sock.recv(1024)  # Receive up to 1024 bytes
        finally:
            self.sock.close()
            self.last_call = datetime.datetime.now()
        return data.decode("utf-8")

    def _send_sru(self):
        try:
            now = datetime.datetime.now()
            if (now - self.last_call).total_seconds() < 0.1:
                time.sleep(0.1)
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = (self.ip, self.port)
            self.sock.connect(server_address)
            message = "SRU\n"
            self.sock.sendall(message.encode("utf-8"))
            while True:
                data = self.sock.recv(1024)  # Receive up to 1024 bytes
                data = data.decode("utf-8")
                if "S S" in data:
                    print("we received: ", data)
                    self.parse_weight(data)
        finally:
            self.sock.close()
            self.last_call = datetime.datetime.now()
        return data.decode("utf-8")

    def interupt(self):
        self.sock.shutdown(socket.SHUT_RDWR)

    def parse_weight(self, weight):
        match = re.search(r"(\d+\.\d+)\s+(\w+)", weight)
        if match:
            number = float(match.group(1))  # Convert to float
            unit = match.group(2)  # This is the unit
            print(f"number: {number}, unit: {unit}")
        else:
            print("No match found.")

    def reset_tare(self):
        tare = self._send_msg("TAC")
        print("result for reset is ", tare)

    def tare(self):
        tare = self._send_msg("T")
        print("tare result is ", tare)

    def weight(self):
        weight = self._send_msg("S")
        self.parse_weight(weight)


scale = ScaleConnection()
# scale.weight()
# scale.tare()
# scale.weight()
# scale.reset_tare()
# scale.weight()
while True:
    prompts = ["{} -> {}".format(a[0], a[1]) for a in COMMANDS]
    fzf = FzfPrompt()

    partner = fzf.prompt((prompts))[0]
    code = partner.split("->")[0].strip()
    print(scale._send_msg(code))

    res = input("…")
    while res:
        print(scale._send_msg(res.upper()))
        res = input("…")
