import sys

template = "sudo FROM_IP={} FROM_PORT={} FROM_IF={} TO_OWN=10.0.5.1 TO_IP=10.0.5.2 TO_PORT={} ./add.sh"

for port in range(1, int(sys.argv[3])):
    print(template.format(sys.argv[1], port, sys.argv[2], port))
