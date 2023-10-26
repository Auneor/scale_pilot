import re
import os
import subprocess


def match_ip(ip_address):
    pattern = r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$"

    match = re.match(pattern, ip_address)

    if match:
        octet1, octet2, octet3, octet4 = match.groups()
        return "{}.{}.{}".format(octet1, octet2, octet3)
    else:
        print("Invalid IP address!")
        return False


def install():
    ipget = """
    Bonjour nous allons installer le pilote de la balance.
    Quelle est l'adresse ip de la balance?
    (appuyer sur le bouton i de la balance deux fois pour qu'il soit affiché à l'écran)
    """
    print(ipget)
    res = input("? ")
    prefix = match_ip(res)
    if not prefix:
        return
    interface_file = """
auto eth0
iface eth0 inet static
    address {}.1
    netmask 255.255.255.0
    """.format(
        prefix
    )
    i_file = "/etc/network/interfaces.d/eth0"
    if not os.path.exists(i_file):
        try:
            with open(i_file, "w") as file:
                file.write(interface_file)
        except:
            print("error")
            print(
                "check that the content of {} match with {}".format(
                    i_file, interface_file
                )
            )
    else:
        print(
            "File {} already exists. check that the content match with {}".format(
                i_file, interface_file
            )
        )


def install_scale_program():
    directory = "/pilot"
    repository_url = "https://github.com/Auneor/scale_pilot.git"

    # Clone the repository if the directory doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)
        subprocess.run(["git", "clone", repository_url, directory])
        print("Repository cloned successfully.")
    else:
        print("Directory already exists.")

    # Create a systemd unit file
    unit_file_path = "/etc/systemd/system/pilot.service"
    unit_file_content = f"""\
    [Unit]
    Description=Scale Pilot Service
    After=network.target

    [Service]
    ExecStartPre=/usr/bin/git -C /pilot pull
    ExecStart=/usr/bin/python3 {directory}/balance.py

    [Install]
    WantedBy=multi-user.target
    """

    with open(unit_file_path, "w") as f:
        f.write(unit_file_content)

    subprocess.run(["systemctl", "enable", "pilot.service"])
    print("Systemd unit created and enabled.")


subprocess.run(["pip3", "install", "flask-cors", "--break-system-packages"])

install()
install_scale_program()
