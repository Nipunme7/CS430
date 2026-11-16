"""
traceroute using ICMP

@author:
@version: 2026.11
"""

import argparse
import logging
import os
import socket
import struct
import time

ECHO_REQUEST_TYPE = 8
ECHO_REQUEST_CODE = 0
ATTEMPTS = 3


def checksum(pkt_bytes: bytes) -> int:
    """Calculate checksum"""
    chksum = 0
    if len(pkt_bytes) % 2 == 1:
        pkt_bytes = pkt_bytes + b"\00"
    i = 0
    while i < len(pkt_bytes):
        word = (pkt_bytes[i] << 8) + pkt_bytes[i + 1]
        chksum = ((chksum + word) & 0xFFFF) + ((chksum + word) >> 16)
        i = i + 2
    return ~chksum & 0xFFFF


def bytes_to_str(pkt_bytes: bytes) -> str:
    """Convert packet bytes to a printable string"""
    result = []
    i = 0
    while i < len(pkt_bytes):
        result.append(f"{pkt_bytes[i]:02x}")
        if (i + 1) % 16 == 0:
            result.append("\n")
        elif (i + 1) % 8 == 0:
            result.append("  ")
        else:
            result.append(" ")
        i = i + 1
    result.append("\n")
    result.append("\n")
    return "".join(result)


def format_request(req_id: int, seq_num: int) -> bytes:
    """Format an Echo request"""
    data = b"VOTE!"
    header = struct.pack("!BBHHH", ECHO_REQUEST_TYPE, ECHO_REQUEST_CODE, 0, req_id, seq_num)
    chk = checksum(header + data)
    header = struct.pack("!BBHHH", ECHO_REQUEST_TYPE, ECHO_REQUEST_CODE, chk, req_id, seq_num)
    return header + data


def send_request(sock: socket.socket, pkt_bytes: bytes, addr_dst: str, ttl: int) -> float:
    """Send an Echo Request"""
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, struct.pack("I", ttl))
    sock.sendto(pkt_bytes, (addr_dst, 33434))
    return time.time()


def receive_reply(sock: socket.socket) -> tuple:
    """Receive an ICMP reply"""
    pkt_bytes, addr = sock.recvfrom(1024)
    return pkt_bytes, addr, time.time()


def parse_reply(pkt_bytes: bytes) -> None:
    """Parse an ICMP reply"""
    header = pkt_bytes[20:28]
    data = pkt_bytes[28:]
    repl_type, repl_code, repl_checksum, repl_id, sequence = struct.unpack("!BBHHH", header)

    expected = {0: [0], 3: [0, 1, 3], 8: [0], 11: [0]}

    if repl_type not in expected:
        types = ", ".join([str(t) for t in expected])
        raise ValueError("Incorrect type " + str(repl_type) + " received instead of " + types)

    if repl_code not in expected[repl_type]:
        raise ValueError("Incorrect code " + str(repl_code) + " received with type " + str(repl_type))

    if checksum(header + data) != 0:
        good = checksum(header + data)
        raise ValueError(
            "Incorrect checksum " + f"{repl_checksum:04x}" + " received instead of " + f"{good:04x}"
        )


def traceroute(hostname: str, max_hops: int = 30) -> None:
    """Trace the route to a domain"""
    dest_addr = socket.gethostbyname(hostname)
    print("\nTracing route to " + hostname + " [" + dest_addr + "]")
    print("over a maximum of " + str(max_hops) + " hops\n")

    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))
    sock.settimeout(1)

    ttl = 0
    done = False
    req_id = os.getpid() & 0xFFFF

    while ttl < max_hops and done == False:
        ttl = ttl + 1
        print(f"{ttl:>3d}   ", end="")
        comment = ""
        seq_id = 0

        for attempt in range(ATTEMPTS):
            pkt_out = format_request(req_id, seq_id)
            time_sent = send_request(sock, pkt_out, dest_addr, ttl)
            try:
                pkt_in, resp_addr, time_rcvd = receive_reply(sock)
                rtt = (time_rcvd - time_sent) * 1000
                parse_reply(pkt_in)

                if rtt > 1:
                    print(f"{rtt:>3.0f} ms   ", end="")
                else:
                    print(f"{'<1':>3s} ms   ", end="")

                if resp_addr[0] == dest_addr:
                    done = True

                if comment == "":
                    try:
                        name = socket.gethostbyaddr(resp_addr[0])[0]
                        comment = name + " [" + resp_addr[0] + "]"
                    except socket.herror:
                        comment = resp_addr[0]

            except (socket.timeout, TimeoutError) as to_err:
                print(f"{'*':>3s}      ", end="")
                if comment == "":
                    comment = "Request timed out: " + str(to_err)
                continue

            except ValueError as val_err:
                print(f"{'!':>3s}      ", end="")
                if comment == "":
                    comment = "Error while parsing the response: " + str(val_err)
                continue

            seq_id = seq_id + 1

        print(comment)

    sock.close()
    print("\nTrace complete.")


def main():
    """Main function"""
    arg_parser = argparse.ArgumentParser(description="Parse arguments")
    arg_parser.add_argument("host", type=str, help="Host to trace")
    arg_parser.add_argument("-d", "--debug", action="store_true", help="Enable logging.DEBUG mode")
    args = arg_parser.parse_args()

    logger = logging.getLogger("root")
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logger.level)

    traceroute(args.host)


if __name__ == "__main__":
    main()
