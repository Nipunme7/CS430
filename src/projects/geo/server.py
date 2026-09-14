#!/usr/bin/env python3
"""
`geo server` implementation

@authors:
@version: 2022.9
"""
import argparse
import logging
import socket
from csv import DictReader

HOST = "127.0.0.1"
PORT = 4300


def read_file(filename: str) -> tuple[dict[str, str], int]:
    """Read the world countries and their capitals from the file
    Make sure not to count United States of America and USA as two different countries

    :param filename: file to read
    :return: the tuple of (dictionary, count) where
            `dictionary` is a map {country:capital} and
            `count` is the number of countries in the world
    """
    # TODO: Implement this function
    world = {}
    count = 0
    with open(filename) as f:
        reader = DictReader(f, delimiter=";")
        for row in reader:
            count += 1
            capital = row["Capital"]
            for country in row["Country"].split(","):
                world[country.strip()] = capital
    return world, count


def find_capital(world: dict, country: str) -> str:
    """Find the capital of an existing country
    Return *No such country* otherwise

    :param world: dictionary representing the world
    :param country: country to look up
    :return: capital of the specified country
    """
    # TODO: Implement this function

    if country in world:
        return world[country]
    else:
        return "No such country."


def format_message(message: str) -> bytes:
    """Convert the message to bytes

    :param message: message to send
    :return: message converted to bytes
    """
    # TODO: Implement this function

    return message.encode()


def parse_data(data: bytes) -> str:
    """Convert bytes to a string

    :param data: data to decode
    :return: decoded data
    """
    # TODO: Implement this function

    return data.decode()


def server_loop(world: dict):
    """Main server loop"""
    print("The server has started")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        # TODO: Implement this function
        sock.bind((HOST, PORT))
        while True:
            data, addr = sock.recvfrom(1024)
            country = parse_data(data)
            if country == "BYE":
                break
            capital = find_capital(world, country)
            sock.sendto(format_message(capital), addr)
    
    print("The server has finished")


def main():
    """Main function"""
    arg_parser = argparse.ArgumentParser(description="Enable debugging")
    arg_parser.add_argument("file", type=str, help="File name")
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
    world, _ = read_file(args.file)
    server_loop(world)


if __name__ == "__main__":
    main()
