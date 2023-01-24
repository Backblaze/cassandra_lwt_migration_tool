from typing import Dict


def read_cass_node_ip_file(path: str) -> Dict[str, str]:
    """
    Reads a simple file format with a node address, a space and a node IP.

    :param path: A str containing a path to read the file from
    :returns: A dict from hostname to node_ip
    """

    node_ips: Dict[str, str] = {}

    with open(path, "r") as fd:
        for line in fd.readlines():
            line = line.strip()
            # Skip blank lines
            if len(line) == 0:
                continue

            # Skip comments
            if line[0] == "#":
                continue

            try:
                hostname, ip_addr = line.split(" ")
                node_ips[hostname] = ip_addr
            except ValueError as e:
                raise ValueError(f"Malformed line in cassandra nodes file: {line}")

    return node_ips
