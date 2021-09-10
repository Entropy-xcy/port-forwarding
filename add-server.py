template = "sudo FROM_IP={} FROM_PORT={} FROM_IF={} TO_OWN=10.0.5.1 TO_IP=10.0.5.2 TO_PORT={} ./add.sh"

for port in range(1, 1000):
    print(template.format('66.181.45.7', port, 'ens18', port))
