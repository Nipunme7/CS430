"""
Client implementation

@author:
@version: 2026.10
"""

import argparse
import logging
import sys
from random import choice, randint
from socket import AF_INET, SOCK_DGRAM, socket

PORT = 53

DNS_TYPES = {"A": 1, "AAAA": 28, "CNAME": 5, "MX": 15, "NS": 2, "PTR": 12, "TXT": 16}

PUBLIC_DNS_SERVER = [
    "1.0.0.1",  # Cloudflare
    "1.1.1.1",  # Cloudflare
    "8.8.4.4",  # Google
    "8.8.8.8",  # Google
    "9.9.9.9",  # Quad9
    "64.6.64.6",  # Verisign
    "64.6.65.6",  # Verisign
    "208.67.220.220",  # OpenDNS
    "208.67.222.222",  # OpenDNS
]


def val_to_2_bytes(value: int) -> tuple[int, int]:
    """
    Split a value into 2 bytes
    Return the result as a tuple of 2 integers
    """
    # TODO: Implement this function
    byte1 = (value >> 8) & 255
    byte2 = value & 255
    return (byte1, byte2)
    


def val_to_n_bytes(value: int, n_bytes: int) -> tuple[int, ...]:
    """
    Split a value into n bytes
    Return the result as a tuple of n integers
    """
    # TODO: Implement this function

    result = []
    i = n_bytes - 1
    while i >= 0:
        result.append((value >> (8 * i)) & 255)
        i = i - 1
    return tuple(result)


def bytes_to_val(data: bytes | list[int]) -> int:
    """Merge n bytes into a value"""
    # TODO: Implement this function

    result = 0
    for b in data:
        result = (result << 8) + b
    return result


def get_2_bits(data: bytes | list[int]) -> int:
    """
    Extract first two bits of a two-byte sequence
    Return the result as a decimal value
    """
    # TODO: Implement this function

    value = bytes_to_val(data)
    return value >> 14


def get_domain_name_location(data: bytes | list[int]) -> int:
    """
    Extract size of the offset from a two-byte sequence
    Return the result as a decimal value
    """
    # TODO: Implement this function

    value = bytes_to_val(data)
    return value & 16383


def parse_cli_query(
    q_domain: str, q_type: str, q_server: str | None = None
) -> tuple[list, int, str]:
    """
    Parse command-line query
    Return a tuple of the domain (as a list of subdomains), numeric type, and the server
    If the server is not specified, pick a random one from `PUBLIC_DNS_SERVER`
    If type is not `A` or `AAAA`, raise `ValueError`
    """
    # TODO: Implement this function

    if q_type != "A" and q_type != "AAAA":
        raise ValueError(q_type + " is an unknown query type")
    domain_list = q_domain.split(".")
    q_num = DNS_TYPES[q_type]
    if q_server is None:
        server = choice(PUBLIC_DNS_SERVER)
    else:
        server = q_server
    return (domain_list, q_num, server)


def format_query(q_domain: list, q_type: int) -> bytearray:
    """
    Format DNS query
    Take the domain name (as a list) and the record type as parameters
    Return a properly formatted query
    Assumpions (defaults):
    - transaction id: random 0..65535
    - flags: recursive query set
    - questions: 1
    - class: Internet
    """
    # TODO: Implement this function

    query = bytearray()
    trans_id = randint(0, 65535)
    query.extend(val_to_2_bytes(trans_id))
    query.extend(val_to_2_bytes(256))
    query.extend(val_to_2_bytes(1))
    query.extend(val_to_2_bytes(0))
    query.extend(val_to_2_bytes(0))
    query.extend(val_to_2_bytes(0))
    for part in q_domain:
        query.append(len(part))
        for ch in part:
            query.append(ord(ch))
    query.append(0)
    query.extend(val_to_2_bytes(q_type))
    query.extend(val_to_2_bytes(1))
    return query


def parse_response(resp_bytes: bytes) -> list[tuple]:
    """
    Parse server response
    Take response bytes as a parameter
    Return a list of tuples in the format of (name, address, ttl)
    """
    # TODO: Implement this function
    num_answers = bytes_to_val(resp_bytes[6:8])
    i = 12
    while True:
        if resp_bytes[i] == 0:
            i = i + 1
            break
        if get_2_bits(resp_bytes[i:i + 2]) == 3:
            i = i + 2
            break
        i = i + 1 + resp_bytes[i]
    i = i + 4
    return parse_answers(resp_bytes, i, num_answers)


def parse_answers(resp_bytes: bytes, answer_start: int, rr_ans: int) -> list[tuple]:
    """
    Parse DNS server answers
    Take response bytes, offset, and the number of answers as parameters
    Return a list of tuples in the format of (name, address, ttl)
    """
    # TODO: Implement this function

    answers = []
    i = answer_start
    n = 0
    while n < rr_ans:
        parts = []
        jumped = False
        saved = i
        while True:
            if resp_bytes[i] == 0:
                i = i + 1
                break
            if get_2_bits(resp_bytes[i:i + 2]) == 3:
                loc = get_domain_name_location(resp_bytes[i:i + 2])
                if jumped == False:
                    saved = i + 2
                    jumped = True
                i = loc
            else:
                length = resp_bytes[i]
                i = i + 1
                parts.append(resp_bytes[i:i + length].decode())
                i = i + length
        if jumped == True:
            i = saved
        name = ".".join(parts)
        rtype = bytes_to_val(resp_bytes[i:i + 2])
        i = i + 2
        i = i + 2
        ttl = bytes_to_val(resp_bytes[i:i + 4])
        i = i + 4
        rdlen = bytes_to_val(resp_bytes[i:i + 2])
        i = i + 2
        rdata = resp_bytes[i:i + rdlen]
        i = i + rdlen
        if rtype == 1:
            addr = parse_address_a(rdlen, rdata)
            answers.append((name, addr, ttl))
        elif rtype == 28:
            addr = parse_address_aaaa(rdlen, rdata)
            answers.append((name, addr, ttl))
        n = n + 1
    return answers


def parse_address_a(addr_len: int, addr_bytes: bytes) -> str:
    """
    Parse IPv4 address
    Convert bytes to human-readable dotted-decimal
    """
    # TODO: Implement this function
    parts = []
    j = 0
    while j < addr_len:
        parts.append(str(addr_bytes[j]))
        j = j + 1
    return ".".join(parts)


def parse_address_aaaa(addr_len: int, addr_bytes: bytes) -> str:
    """Extract IPv6 address"""
    # TODO: Implement this function

    parts = []
    j = 0
    while j < addr_len:
        val = bytes_to_val(addr_bytes[j:j + 2])
        parts.append(format(val, "x"))
        j = j + 2
    return ":".join(parts)

    


def resolve(query: tuple) -> None:
    """Resolve the query"""
    logger = logging.getLogger()

    try:
        q_domain, q_type, q_server = parse_cli_query(*query)
    except ValueError as ve:
        print(ve.args[0])
        sys.exit()
    logger.info(f"Resolving type {q_type} for {q_domain} using {q_server}")
    query_bytes = format_query(q_domain, q_type)
    with socket(AF_INET, SOCK_DGRAM) as sock:
        sock.sendto(query_bytes, (q_server, PORT))
        response_data, _ = sock.recvfrom(2048)
    answers = parse_response(response_data)
    print(f"DNS server used: {q_server}")
    for a in answers:
        print()
        print(f"{'Domain:':10s}{a[0]}")
        print(f"{'Address:':10s}{a[1]}")
        print(f"{'TTL:':10s}{a[2]}")


def main():
    """Main function"""
    arg_parser = argparse.ArgumentParser(description="Parse arguments")
    # TODO: Complete this function to accept domain name, record type, and the server address as command-line parameters

    arg_parser.add_argument("domain")
    arg_parser.add_argument("-t", "--type", default="A")
    arg_parser.add_argument("-s", "--server", default=None)

    arg_parser.add_argument("-d", "--debug", action="store_true", help="Enable logging.DEBUG mode")
    args = arg_parser.parse_args()

    logger = logging.getLogger("root")
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logger.level)

    resolve((args.domain, args.type, args.server))


if __name__ == "__main__":
    main()
