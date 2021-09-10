template = "sudo FROM_IP=10.0.5.2 FROM_PORT={} FROM_IF=wg0 TO_OWN={} TO_IP={} TO_PORT={} ./add.sh"

for port in range(1, 1000):
    print(template.format(port, '10.0.0.44', '10.0.0.53', port))
