from typing import Dict


def read_cass_node_ip_file(path: str) -> Dict[str, str]:
    node_ips: Dict[str, str] = {}

    with open(path, 'r') as fd:
        for line in fd.readlines():
            line = line.strip()
            # Skip blank lines
            if len(line) == 0:
                continue

            # Skip comments
            if line[0] == '#':
                continue

            try:
                hostname, ip_addr = line.split(' ')
                node_ips[hostname] = ip_addr
            except ValueError as e:
                raise ValueError(f'Malformed line in cassandra nodes file: {line}')

    return node_ips

