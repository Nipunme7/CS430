#!/usr/bin/env python3
"""
Python Web server implementation

@authors:
@version:
"""

import argparse
import logging
from datetime import datetime
from pathlib import Path
from random import randint
from socket import AF_INET, SOCK_STREAM, socket
from time import sleep

SRVR_ADDR = "127.0.0.2"  # Local client is going to be 127.0.0.1
SRVR_PORT = 43080  # Open http://127.0.0.2:43080 in a browser
SRVR_NAME = "CS430/2024"


def parse_request(data: bytes) -> dict:
    """Parse the incoming request"""
    text = data.decode()
    lines = text.split("\r\n")

    first_line = lines[0].split(" ")
    method = first_line[0]
    url = first_line[1]
    version = first_line[2]

    request = {}
    request["method"] = method
    request["url"] = url
    request["version"] = version

    for line in lines[1:]:
        if line == "":
            break
        parts = line.split(": ", 1)
        key = parts[0]
        value = parts[1]
        request[key] = value

    return request


def format_response(
    http_version: str, status_code: int, header: dict = {}, data: str = ""
) -> bytes:
    """Format the response"""
    if status_code == 200:
        status_text = "OK"
    elif status_code == 404:
        status_text = "Not Found"
    elif status_code == 405:
        status_text = "Method Not Allowed"
    else:
        status_text = "Not Implemented"

    response = http_version + " " + str(status_code) + " " + status_text + "\r\n"
    response = response + "Date: " + str(datetime.now()) + "\r\n"
    response = response + "Server: " + SRVR_NAME + "\r\n"

    if header != None:
        for key in header:
            response = response + key + ": " + header[key] + "\r\n"

    if data != "":
        response = response + "Content-Length: " + str(len(data)) + "\r\n"

    response = response + "\r\n" + data
    return response.encode()
    


def server_loop(logfilename: Path):
    """Main server loop"""
    print("The server has started")
    with socket(AF_INET, SOCK_STREAM) as sock:
        sock.bind((SRVR_ADDR, SRVR_PORT))
        sock.listen(1)

        while True:
            conn, addr = sock.accept()
            data = conn.recv(4096)

            if data == b"":
                conn.close()
                continue

            request = parse_request(data)
            method = request["method"]
            url = request["url"]
            version = request["version"]

            if "User-Agent" in request:
                user_agent = request["User-Agent"]
            else:
                user_agent = ""

            log = open(logfilename, "a")
            log.write(str(datetime.now()) + " | " + url + " | " + addr[0] + " | " + user_agent + "\n")
            log.close()

            if method == "POST":
                body = "<html><head></head><body><h1>Use GET to retrieve resources from this server</h1></body></html>"
                response = format_response(version, 405, None, body)
            elif method != "GET":
                response = format_response(version, 501, None, "")
            else:
                filepath = Path("data/projects/webserver") / url[1:]
                if filepath.is_file() == False:
                    body = "<html><head></head><body><h1>File " + url + " not found on our server</h1></body></html>"
                    response = format_response(version, 404, None, body)
                else:
                    file = open(filepath)
                    file_data = file.read()
                    file.close()
                    last_modified = str(datetime.fromtimestamp(filepath.stat().st_mtime))
                    header = {}
                    header["Content-Type"] = "text/plain; charset=utf-8"
                    header["Last-Modified"] = last_modified
                    response = format_response(version, 200, header, file_data)

            conn.sendall(response)
            conn.close()


def main():
    """Set up arguments and start the main server loop"""
    arg_parser = argparse.ArgumentParser(description="Parse arguments")
    arg_parser.add_argument(
        "-l",
        "--logfile",
        type=str,
        help="Log file name",
        default="src/projects/webserver/webserver.log",
    )
    arg_parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable logging.DEBUG mode"
    )
    args = arg_parser.parse_args()

    logger = logging.getLogger("root")
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logger.level)

    try:
        server_loop(Path(args.logfile))
    except KeyboardInterrupt:
        print("\nThe server has stopped")


if __name__ == "__main__":
    main()
