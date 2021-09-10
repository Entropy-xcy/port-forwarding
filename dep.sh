sudo apt update 
sudo apt install wireguard -y

# Enable IP v4 forwarding
sysctl -w net.ipv4.ip_forward=1

# Delete All existing IP tables settings
sudo iptables -P INPUT ACCEPT
sudo iptables -P FORWARD ACCEPT
sudo iptables -P OUTPUT ACCEPT
sudo iptables -t nat -F
sudo iptables -t mangle -F
sudo iptables -F
sudo iptables -X
