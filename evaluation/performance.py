import getopt
import json
import os
import sys
import time

import requests

sys.path.insert(0, os.path.abspath('..'))

import blockchain.chain_utils as chain_utils
import blockchain.chord.chord_utils as chord_utils

from os import listdir
from os.path import isfile, join


class colours:
    COMMAND = '\033[94m'
    ENDCOLOUR = '\033[0m'
    SUCCESS = '\033[92m'
    ERROR = '\033[91m'
    UNDERLINE = '\033[4m'


# ---- Global Variables ----
number_of_nodes = 0
number_of_records = 0
nodes_registered = []
nodes_not_registered = []
active_node = ''
all_records = []
records_on_network = []
timings = dict()


def print_logo():
    logo_path = str(chain_utils.get_app_root_directory()) + "/demo/images/miBlock_ascii_logo"
    logo_file = open(logo_path, 'r+')
    logo = logo_file.read()
    print(logo)


def register_nodes():
    print("\n>> Registering nodes")
    for node in nodes_not_registered:
        response = requests.post(f"http://{node}/node/register?node_address=172.17.0.1:{node.split(':')[1]}")
        if response.status_code != 200:
            print_error(f"Registration was unsuccessful for node '{node}'")
        else:
            nodes_registered.append(node)
            print_success(f"Registration was successful for node '{node}'")


def get_required_records():
    global all_records
    path = str(chain_utils.get_app_root_directory()) + "/data/records/unused"
    all_records = [f for f in listdir(path) if isfile(join(path, f))][0:300]


def add_records(records):
    i = 1
    print("\n>> Adding Records")
    for record in records:
        data = {
            'aircraft_reg_number': record,
            'date_of_record': i,
            'filename': record
        }
        headers = {'Content-Type': "application/json"}
        response = requests.post(f"http://127.0.0.1:500/chain/record-pool", data=json.dumps(data), headers=headers)
        if response.status_code == 200:
            successor = requests.get(f"http://127.0.0.1:500/chord/lookup?key={chord_utils.get_hash(record)}").json()['successor']
            # print_success(f"Record {i}:{record} has been added to the record pool @ {successor} - {chord_utils.get_hash(record)}")
            records_on_network.append(record)
            all_records.remove(record)
        i += 1
    # who_has_records()


def who_has_records():
    print("\n>> Finding Records")
    for node in nodes_registered:
        response = requests.get(f"http://{node}/chord/files")
        if response.status_code == 200:
            files = response.json()['files']
            print(f"{node}: {len(files)}")
        else:
            print_error("Something went wrong, please try again")


def print_nodes():
    response = requests.get(f"http://127.0.0.1:500/discovery/peers")
    print(f"Node - 172.17.0.1:500 @ '{chord_utils.get_hash('172.17.0.1:500')}'")
    for peer in response.json()['peers']:
        print(f"Node - {peer} @ '{chord_utils.get_hash(peer)}'")


def print_error(message):
    print(f"{colours.ERROR}{message}{colours.ENDCOLOUR}")


def print_success(message):
    print(f"{colours.SUCCESS}{message}{colours.ENDCOLOUR}")


def main(argv):
    global number_of_nodes, nodes_registered, number_of_records

    try:
        opts, args = getopt.getopt(argv, "hn:", ["nodes="])
    except getopt.GetoptError:
        print('performance.py -n <numberNodes>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print('performance.py -n <numberNodes>')
            sys.exit()
        elif opt == "-n":
            number_of_nodes = arg
            for i in range(int(arg)):
                if requests.get(f"http://127.0.0.1:50{i}/node/ping").status_code == 200:
                    nodes_registered.append(f"127.0.0.1:50{i}")
                else:
                    nodes_not_registered.append(f"127.0.0.1:50{i}")

    os.system('clear')
    print_logo()
    register_nodes()
    get_required_records()

    one_third = pow(2, 10) / 3
    two_third = one_third * 2
    three_third = pow(2, 10)

    response = requests.get(f"http://127.0.0.1:500/chord/lookup?key={one_third}")
    one_third_node = response.json()['successor']
    print("One third of chord ring:", one_third)
    print(f"Successor of One third: {one_third_node}")

    response = requests.get(f"http://127.0.0.1:500/chord/lookup?key={two_third}")
    two_third_node = response.json()['successor']
    print("\nTwo thirds of chord ring:", two_third)
    print(f"Successor of two thirds: {two_third_node}")

    response = requests.get(f"http://127.0.0.1:500/chord/lookup?key={three_third}")
    three_third_node = response.json()['successor']
    print("\nThree thirds of chord ring:", three_third)
    print(f"Successor of three thirds: {three_third_node}")

    print(f"\nNumber of nodes = {number_of_nodes}")
    while len(all_records) != 0:
        add_records(all_records[0:25])
        print(f">> Testing with {len(records_on_network)} records")

        random_key = int.from_bytes(os.urandom(2), byteorder='big', signed=False) % pow(2,10)
        print("     Random Key:", random_key)

        start_one = time.time()
        response = requests.get(f"http://{one_third_node}/chord/lookup?key={random_key}")
        end_one_s = time.time() - start_one
        print(f"     Successor: {response.json()['successor']}")

        start_two = time.time()
        response = requests.get(f"http://{two_third_node}/chord/lookup?key={random_key}")
        end_two_s = time.time() - start_two
        print(f"     Successor: {response.json()['successor']}")

        start_three = time.time()
        response = requests.get(f"http://{three_third_node}/chord/lookup?key={random_key}")
        end_three_s = time.time() - start_three
        print(f"     Successor: {response.json()['successor']}")

        print("\n     First Lookup:", end_one_s)
        print("     Second Lookup:", end_two_s)
        print("     Third Lookup:", end_three_s)
        average = (end_one_s + end_two_s + end_three_s) / 3.0
        print("     Average:", average)

        timings[len(records_on_network)] = average
    print(timings)


if __name__ == '__main__':
    main(sys.argv[1:])
