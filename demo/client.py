import getopt
import json
import os
import sys

import requests

sys.path.insert(0, os.path.abspath('..'))

import blockchain.chain_utils as chain_utils
import blockchain.block_utils as block_utils
import demo.client_utils as client_utils


class colours:
    COMMAND = '\033[94m'
    ENDCOLOUR = '\033[0m'
    SUCCESS = '\033[92m'
    ERROR = '\033[91m'
    UNDERLINE = '\033[4m'


# ---- Global Variables ----
number_of_nodes = 0
nodes_registered = []
nodes_not_registered = []
active_node = ''
nodes = []


def main(argv):
    global number_of_nodes, nodes_registered, nodes

    try:
        opts, args = getopt.getopt(argv, "hn:", ["nodes="])
    except getopt.GetoptError:
        print('client.py -n <numberNodes>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print('client.py -n <numberNodes>')
            sys.exit()
        elif opt == "-n":
            number_of_nodes = arg
            for i in range(int(arg)):
                if i == 0:
                    nodes_registered.append(f"127.0.0.1:500{i}")
                else:
                    nodes_not_registered.append(f"127.0.0.1:500{i}")
                nodes.append(f"127.0.0.1:500{i}")
    while True:
        os.system('clear')
        print_logo()
        if main_menu() == 1:
            os.system('clear')
            print_logo()
            if node_menu() != 1:
                sys.exit()
        else:
            sys.exit()


def print_logo():
    logo_path = str(chain_utils.get_app_root_directory()) + "/miBlock_ascii_logo"
    logo_file = open(logo_path, 'r+')
    logo = logo_file.read()
    print(logo)


# Method used to display user errors to the user in red text
def print_error(message):
    print(f"{colours.ERROR}{message}{colours.ENDCOLOUR}")


def print_success(message):
    print(f"{colours.SUCCESS}{message}{colours.ENDCOLOUR}")


def main_menu():
    global active_node
    # Print list of available commands
    print("\n")
    print(f"Use the '{colours.COMMAND}login {colours.UNDERLINE}node_address{colours.ENDCOLOUR}{colours.ENDCOLOUR}'    "
          f"command to login to a specified node")
    print(f"Use the '{colours.COMMAND}register {colours.UNDERLINE}node_address{colours.ENDCOLOUR}{colours.ENDCOLOUR}' "
          f"command to register a node.")
    print(f"Use the '{colours.COMMAND}nodes{colours.ENDCOLOUR}'                 "
          f"command to show registered and unregistered nodes.")
    print(f"Use the '{colours.COMMAND}quit{colours.ENDCOLOUR}'                  "
          f"command to exit the program.")

    # Continuously prompts user for commands until the application state changes
    while True:
        command = input("\n>>> ")
        if command.split(" ")[0] == "login":
            try:
                node = command.split(" ")[1]
            except IndexError:
                print_error("Please provide a node address")
                continue

            if node in nodes_registered:
                active_node = node
                return 1
            else:
                print_error("Please provide a node address")

        elif command.split(" ")[0] == "register":
            try:
                node = command.split(" ")[1]
                port = node.split(':')[1]
            except IndexError:
                print_error("Please provide a node address")
                continue

            if node in nodes_registered:
                print_error("Node already registered")
                continue

            response = requests.post(f"http://{node}/node/register?node_address=172.17.0.1:{port}")

            if response.status_code != 200:
                print_error(response.reason)
            else:
                nodes_registered.append(node)
                nodes_not_registered.remove(node)
                print(f"{colours.SUCCESS}Node registration was successful.{colours.ENDCOLOUR}")

        elif command == "nodes":
            print("Available nodes: ", nodes)
            print("Registered nodes: ", nodes_registered)
            print("Unregistered nodes: ", nodes_not_registered)
        elif command == "quit":
            return 0
        else:
            print_error("Invalid command given, please try again...")


def node_menu():
    print("\n")
    global active_node
    # Print list of available commands
    print(f"Use the '{colours.COMMAND}chain{colours.ENDCOLOUR}'  command return the node's chain.")
    print(f"Use the '{colours.COMMAND}mine{colours.ENDCOLOUR}'   command to mine a block of unverified records.")
    print(f"Use the '{colours.COMMAND}peers{colours.ENDCOLOUR}'  command return the node's known peers.")
    print(f"Use the '{colours.COMMAND}record{colours.ENDCOLOUR}' command manage a nodes record pool.")
    print(f"Use the '{colours.COMMAND}logout{colours.ENDCOLOUR}' command to logout the active node.")
    print(f"Use the '{colours.COMMAND}quit{colours.ENDCOLOUR}'   command to exit the program.")

    # Continuously prompts user for commands until the application state changes
    while True:
        command = input("\n>>> ")
        if command == "chain":
            get_chain()
        elif command == "mine":
            mine_block()
        elif command == "peers":
            get_peers()
        elif command == "record":
            manage_record_pool()
        elif command == "logout":
            active_node = ""
            return 1
        elif command == "quit":
            return 0
        else:
            print_error("Invalid command given, please try again...")


#                                                  /+=--------------=+\
# -----------------------------------------------=+| Request Handlers |+=-----------------------------------------------
#                                                  \+=--------------=+/

def get_chain():
    response = requests.get(f"http://{active_node}/chain")
    chain = chain_utils.get_chain_from_json(response.json()['chain'])
    print(chain)
    client_utils.print_chain(chain)


def get_peers():
    response = requests.get(f"http://{active_node}/discovery/peers")
    for peer in response.json()['peers']:
        print("--", peer)


def manage_record_pool():
    print("Type 'add' to add a new record, 'list' to list records or 'cancel' to return.")
    expecting_command = True
    while expecting_command:
        command = input(" > ")
        if command == "add":
            expecting_command = False
            add_record()
        elif command == "list":
            expecting_command = False
            list_record()
        elif command == "cancel":
            expecting_command = False
        else:
            print_error("Invalid command given, please try again...")


def add_record():
    aircraft_reg = input("\nAircraft Registration Number: ")
    date_of_record = input("Date of Record: ")
    filename = input("Filename: ")

    data = {
        'aircraft_reg_number': aircraft_reg,
        'date_of_record': date_of_record,
        'filename': filename
    }
    headers = {'Content-Type': "application/json"}
    response = requests.post(f"http://{active_node}/chain/record-pool", data=json.dumps(data), headers=headers)
    if response.status_code == 200:
        print_success("Record has been added to the record pool")
    else:
        print_error("Something went wrong, please try again")


def list_record():
    response = requests.get(f"http://{active_node}/chain/record-pool")

    if response.json()['length'] == 0:
        print_error("There are no records in this node's record pool")
    else:
        json_records = response.json()['records']
        records = []
        for json_record in json_records:
            record = block_utils.get_record_object_from_dict(json_record, stored=False)
            records.append(record)
        client_utils.print_records(records)


def mine_block():
    response = requests.get(f"http://{active_node}/chain/mine")
    if response.status_code == 200:
        print_success(f"Block {response.json()['index']} successfully mined")
    else:
        print_error("Something went wrong, please try again")


if __name__ == '__main__':
    main(sys.argv[1:])