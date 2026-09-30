"""
Server implementation

@author:
@version: 2026.9
"""

import argparse
import datetime
import logging
from pathlib import Path
from socket import AF_INET, SO_REUSEADDR, SOCK_STREAM, SOL_SOCKET, socket

SRVR_ADDR = "127.0.0.1"
SRVR_PORT = 4380  # Open http://127.0.0.1:4380 in a browser
SRVR_NAME = "CS430/2026"
# A request for the key should redirect to the mapped value
REDIRECT = {"alice.txt": "alice30.txt", "test.txt": "test26.txt"}


def parse_request(data: bytes) -> dict[str, str]:
    """Parse the incoming request

    :return: a dictionary of key-value mappings based on the request header
    """
    # TODO: Implement this function

    text = data.decode()
    if "\r\n\r\n" in text:
        header_text, body = text.split("\r\n\r\n", 1)
    else:
        header_text = text
        body = ""

    lines = header_text.split("\r\n")
    first_line = lines[0].split(" ")

    request = {}
    request["Method"] = first_line[0]
    request["Url"] = first_line[1]
    request["Version"] = first_line[2]

    for line in lines[1:]:
        if line == "":
            continue
        parts = line.split(": ", 1)
        request[parts[0]] = parts[1]

    if body != "":
        request["Body"] = body

    return request


def format_response(
    http_version: str, status_code: int, header: dict | None = None, data: str = ""
) -> bytes:
    """Format the response

    :return: encoded message that includes header and data
    """
    # TODO: Implement this function

    if data == None:
        data = ""

    if status_code == 200:
        status_text = "OK"
    elif status_code == 204:
        status_text = "No Content"
    elif status_code == 301:
        status_text = "Moved Permanently"
    elif status_code == 404:
        status_text = "Not Found"
    elif status_code == 405:
        status_text = "Method Not Allowed"
    elif status_code == 418:
        status_text = "I'm a teapot"
    elif status_code == 501:
        status_text = "Not Implemented"
    else:
        status_text = "HTTP Version Not Supported"

    response = http_version + " " + str(status_code) + " " + status_text + "\r\n"
    response = response + "Date: " + str(datetime.datetime.now()) + "\r\n"
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
    # TODO: Implement this function using TCP socket
    with socket(AF_INET, SOCK_STREAM) as sock:
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.bind((SRVR_ADDR, SRVR_PORT))
        sock.listen()
        print("The server has started")

        while True:
            conn, addr = sock.accept()
            data = conn.recv(4096)
            if data == b"":
                conn.close()
                continue
            request = parse_request(data)
            method = request["Method"]
            url = request["Url"]
            version = request["Version"]
            if "User-Agent" in request:
                user_agent = request["User-Agent"]
            else:
                user_agent = ""
            log = open(logfilename, "a")
            log.write(str(datetime.datetime.now()) + " | " + url + " | " + addr[0] + " | " + user_agent + "\n")
            log.close()
            filename = url[1:]
            if version != "HTTP/1.1":
                response = format_response(version, 505, None, None)
            elif method == "HEAD":
                body = "<html><head></head><body><h1>Use GET to retrieve resources from this server</h1></body></html>"
                response = format_response(version, 405, None, body)
            elif method == "POST":
                response = format_response(version, 418, None, None)
            elif method == "PUT":
                response = format_response(version, 501, None, None)
            elif method == "DELETE":
                response = format_response(version, 204, None, None)
            elif method == "GET":
                if filename in REDIRECT:
                    header = {}
                    header["Location"] = "/" + REDIRECT[filename]
                    response = format_response(version, 301, header, None)
                else:
                    filepath = Path("data/projects/webserver") / filename
                    if filepath.is_file() == False:
                        body = "<html><head></head><body><h1>File " + url + " not found on our server</h1></body></html>"
                        response = format_response(version, 404, None, body)
                    else:
                        file = open(filepath)
                        file_data = file.read()
                        file.close()
                        last_modified = str(datetime.datetime.fromtimestamp(filepath.stat().st_mtime))
                        header = {}
                        header["Content-Type"] = "text/plain; charset=utf-8"
                        header["Last-Modified"] = last_modified
                        response = format_response(version, 200, header, file_data)
            else:
                response = format_response(version, 501, None, None)
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
    arg_parser.add_argument("-d", "--debug", action="store_true", help="Enable logging.DEBUG mode")
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
