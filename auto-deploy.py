from paramiko import SSHClient
import paramiko
import time

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--server_ip", help="Server端公网IP")
parser.add_argument("--server_user", help="Server端ssh用户名")
parser.add_argument("--server_pwd", help="Server端ssh密码")
parser.add_argument("--server_if", help="Server端拥有公网IP的网卡名称（例如eth0, ens160")
parser.add_argument("--client_ip", help="Client端内网IP")
parser.add_argument("--client_user", help="Client端ssh用户名")
parser.add_argument("--client_pwd", help="Client端ssh密码")
parser.add_argument("--host_ip", help="要被转发的机器的内网IP")
parser.add_argument("--max_port", help="最大进行转发的端口（转发端口的范围是1:<max_port>")
args = parser.parse_args()

SERVER_IP=args.server_ip
SERVER_USER=args.server_user
SERVER_PWD=args.server_pwd
CLIENT_IP=args.client_ip
CLIENT_USER=args.client_user
CLIENT_PWD=args.client_pwd
HOST_IP=args.host_ip
MAX_PORT=args.max_port
SERVER_IF=args.server_if

env_command = "SERVER_IP={}; CLIENT_IP={}; HOST_IP={}; MAX_PORT={}; SERVER_IF={};"
env_command = env_command.format(SERVER_IP, CLIENT_IP, HOST_IP, MAX_PORT, SERVER_IP)

def print_stdout(stdout, stderr):
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        print(stderr.readlines())
        raise Exception('Unknown Error happens!')
    for l in stdout.readlines():
        print(l, end='')

def change_ssh_port(host_ip, username, password):
    print("Changing SSH Port of Server to 52222")
    client = SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host_ip, 22, username, password)
    print("Server ssh connected..")
    
    stdin, stdout, stderr = client.exec_command("sed -i 's/#Port 22/Port 52222/g' /etc/ssh/sshd_config")
    stdin, stdout, stderr = client.exec_command("sudo service sshd restart")
    print_stdout(stdout, stderr)
    print("Port Changed.. Restarting SSH on Server")
    client.close()

    time.sleep(2)
    client = SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host_ip, 52222, username, password)
    stdin, stdout, stderr = client.exec_command("uname")
    print("test uname output: {}".format(stdout.readline()), end='')
    print("Done!")
    return client

def install_deps(client):
    # Install Git
    stdin, stdout, stderr = client.exec_command("sudo apt update && sudo apt install git python3 -y")
    print_stdout(stdout, stderr)

    # Clone Repo
    stdin, stdout, stderr = client.exec_command("git clone https://github.com/Entropy-xcy/yhjm2")
    print_stdout(stdout, stderr)

    # Install Dependencies
    stdin, stdout, stderr = client.exec_command("bash yhjm2/dep.sh")
    print_stdout(stdout, stderr)
    print("Dependency Installation Done!")

    time.sleep(1)

def configure_wg(server_ssh, client_ssh):
    # Server setup wireguard
    stdin, stdout, stderr = server_ssh.exec_command("bash yhjm2/wg-server.sh")
    exit_status = stdout.channel.recv_exit_status()
    server_pubkey = stdout.readlines()[0]
    server_pubkey = server_pubkey.replace('\n', '')
    print(server_pubkey)

    # Client setup wireguard
    stdin, stdout, stderr = client_ssh.exec_command("bash yhjm2/wg-client.sh")
    exit_status = stdout.channel.recv_exit_status()
    client_pubkey = stdout.readlines()[0]
    client_pubkey = client_pubkey.replace('\n', '')
    print(client_pubkey)

    # Server side add clinet
    stdin, stdout, stderr = server_ssh.exec_command("sudo wg set wg0 peer {} allowed-ips 10.0.5.0/24".format(client_pubkey))
    print_stdout(stdout, stderr)

    # Client side add server
    stdin, stdout, stderr = client_ssh.exec_command("sudo wg set wg0 peer {} allowed-ips 10.0.5.0/24 endpoint {}:52180 persistent-keepalive 1".format(server_pubkey, SERVER_IP))
    print_stdout(stdout, stderr)

    # Server ping client
    stdin, stdout, stderr = server_ssh.exec_command("ping 10.0.5.2 -c 3")
    print_stdout(stdout, stderr)

    # Client ping server
    stdin, stdout, stderr = client_ssh.exec_command("ping 10.0.5.1 -c 3")
    print_stdout(stdout, stderr)

def configure_iptables_client(client_ssh):
    stdin, stdout, stderr = client_ssh.exec_command("python3 yhjm2/add-client.py {} {} {} > yhjm2/add-client.sh".format(CLIENT_IP, HOST_IP, MAX_PORT))
    print_stdout(stdout, stderr)
    print("Starting Applying Iptables rules on Client, this might take a while...")

    stdin, stdout, stderr = client_ssh.exec_command("cd yhjm2; {} bash add-client.sh".format(env_command))
    print_stdout(stdout, stderr)
    print("Client Iptables configuration Done!")

def configure_iptables_server(server_ssh):
    stdin, stdout, stderr = server_ssh.exec_command("python3 yhjm2/add-server.py {} {} {} > yhjm2/add-server.sh".format(SERVER_IP, SERVER_IF, MAX_PORT))
    print_stdout(stdout, stderr)
    print("Starting Applying Iptables rules on Server, this might take a while...")

    stdin, stdout, stderr = server_ssh.exec_command("cd yhjm2; {} bash add-server.sh".format(env_command))
    print_stdout(stdout, stderr)
    print("Server Iptables configuration Done!")

if __name__ == "__main__":
    server_ssh = change_ssh_port(SERVER_IP, SERVER_USER, SERVER_PWD)
    client_ssh = SSHClient()
    client_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client_ssh.connect(CLIENT_IP, 22, CLIENT_USER, CLIENT_PWD)

    install_deps(server_ssh)
    install_deps(client_ssh)

    configure_wg(server_ssh, client_ssh)

    configure_iptables_client(client_ssh)
    configure_iptables_server(server_ssh)

    print("Everything is done! Please verify connectivity and performance using iperf.")
