import sys

template = "sudo FROM_IP=10.0.5.2 FROM_PORT={} FROM_IF=wg0 TO_OWN={} TO_IP={} TO_PORT={} ./add.sh"

for port in range(1, int(sys.argv[3])):
    print(template.format(port, sys.argv[1], sys.argv[2], port))
