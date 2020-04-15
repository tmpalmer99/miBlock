import getopt
import json
import os
import sys

import requests
from prettytable import PrettyTable

sys.path.insert(0, os.path.abspath('..'))

import blockchain.chain_utils as chain_utils
import blockchain.block_utils as block_utils
import blockchain.chord.chord_utils as chord_utils
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


def main(argv):
    global number_of_nodes, nodes_registered

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
                if requests.get(f"http://127.0.0.1:500{i}/node/ping").status_code == 200:
                    nodes_registered.append(f"127.0.0.1:500{i}")
                else:
                    nodes_not_registered.append(f"127.0.0.1:500{i}")
    while True:
        if main_menu() == 1:

            node_menu_exit_code = 2
            while node_menu_exit_code == 2:
                node_menu_exit_code = node_menu()
            if node_menu_exit_code == 0:
                sys.exit()

        else:
            sys.exit()


def print_logo():
    logo_path = str(chain_utils.get_app_root_directory()) + "/miBlock_ascii_logo"
    logo_file = open(logo_path, 'r+')
    logo = logo_file.read()
    print(logo)


def print_chord_heading():
    logo_path = str(chain_utils.get_app_root_directory()) + "/chord_heading"
    logo_file = open(logo_path, 'r+')
    logo = logo_file.read()
    print(logo)


# Method used to display user errors to the user in red text
def print_error(message):
    print(f"{colours.ERROR}{message}{colours.ENDCOLOUR}")


def print_success(message):
    print(f"{colours.SUCCESS}{message}{colours.ENDCOLOUR}")


def main_menu():
    global active_node, nodes_not_registered
    os.system('clear')
    print_logo()
    # Print list of available commands
    print("\n")
    print(f"Use the '{colours.COMMAND}login {colours.UNDERLINE}node_address{colours.ENDCOLOUR}{colours.ENDCOLOUR}'    "
          f"command to login to a specified node")
    print(f"Use the '{colours.COMMAND}register {colours.UNDERLINE}node_address{colours.ENDCOLOUR}{colours.ENDCOLOUR}' "
          f"command to register a node.")
    print(f"Use the '{colours.COMMAND}register_all{colours.ENDCOLOUR}'          command to register all nodes.")
    print(f"Use the '{colours.COMMAND}nodes{colours.ENDCOLOUR}'                 command to show registered and unregistered nodes.")
    print(f"Use the '{colours.COMMAND}quit{colours.ENDCOLOUR}'                  command to exit the program.")

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
                print_success(f"Registration was successful for node '{node}'")

        elif command == "register_all":
            print(nodes_not_registered)
            for node in nodes_not_registered:
                response = requests.post(f"http://{node}/node/register?node_address=172.17.0.1:{node.split(':')[1]}")
                if response.status_code != 200:
                    print_error(f"Registration was unsuccessful for node '{node}'")
                else:
                    nodes_registered.append(node)
                    print_success(f"Registration was successful for node '{node}'")
            nodes_not_registered = []
        elif command == "nodes":
            print("\nRegistered nodes:")
            print("-----------------")
            for node in nodes_registered:
                print(node)
            print("\nUnregistered nodes:")
            print("-------------------")
            for node in nodes_not_registered:
                print(node)
        elif command == "quit":
            return 0
        else:
            print_error("Invalid command given, please try again...")


def node_menu():
    os.system('clear')
    print_logo()
    print("\n")
    global active_node
    # Print list of available commands
    print(f"Use the '{colours.COMMAND}chain{colours.ENDCOLOUR}'     command return the node's chain.")
    print(f"Use the '{colours.COMMAND}mine{colours.ENDCOLOUR}'      command to mine a block of unverified records.")
    print(f"Use the '{colours.COMMAND}peers{colours.ENDCOLOUR}'     command return the node's known peers.")
    print(f"Use the '{colours.COMMAND}record{colours.ENDCOLOUR}'    command to manage a nodes record pool.")
    print(f"Use the '{colours.COMMAND}chord{colours.ENDCOLOUR}'     command to manage a nodes chord instance.")
    print(f"Use the '{colours.COMMAND}sync{colours.ENDCOLOUR}'      command to sync a node's peers.")
    print(f"Use the '{colours.COMMAND}consensus{colours.ENDCOLOUR}' command to achieve chain consensus for a node.")
    print(f"Use the '{colours.COMMAND}verify{colours.ENDCOLOUR}'    command to verify a record has not been tampered with.")
    print(f"Use the '{colours.COMMAND}clear{colours.ENDCOLOUR}'     command to clear the console.")
    print(f"Use the '{colours.COMMAND}leave{colours.ENDCOLOUR}'     command for node to leave the network.")
    print(f"Use the '{colours.COMMAND}logout{colours.ENDCOLOUR}'    command to logout the active node.")
    print(f"Use the '{colours.COMMAND}quit{colours.ENDCOLOUR}'      command to exit the program.")

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
        elif command == "chord":
            manage_chord_requests()
            return 2
        elif command == "sync":
            sync_peers()
        elif command == "consensus":
            chain_consensus()
        elif command == "verify":
            verify_record()
        elif command == "clear":
            return 2
        elif command == "leave":
            leave_status = leave_network()
            if leave_status == 200:
                active_node = ""
                return 1
            else:
                print_error(" Something went wrong, please try again")
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
    client_utils.print_chain(chain)


def get_peers():
    response = requests.get(f"http://{active_node}/discovery/peers")
    if len(response.json()['peers']) == 0:
        print_error("This node has no known peers")
    else:
        for peer in response.json()['peers']:
            print(f"-- {peer}")


def manage_record_pool():
    print(f"Use the '{colours.COMMAND}add{colours.ENDCOLOUR}'    command to add a record to the record pool.")
    print(f"Use the '{colours.COMMAND}list{colours.ENDCOLOUR}'   command to list a node's record pool.")
    print(f"Use the '{colours.COMMAND}return{colours.ENDCOLOUR}' command to return to node menu.")
    while True:
        command = input(" \n>> ")
        if command == "add":
            add_record()
        elif command == "list":
            list_record()
        elif command == "return":
            return
        else:
            print_error(" Invalid command given, please try again...")


def add_record():
    aircraft_reg = input(" Aircraft Registration Number: ")
    date_of_record = input(" Date of Record: ")
    filename = input(" Filename: ")

    data = {
        'aircraft_reg_number': aircraft_reg,
        'date_of_record': date_of_record,
        'filename': filename
    }
    headers = {'Content-Type': "application/json"}
    response = requests.post(f"http://{active_node}/chain/record-pool", data=json.dumps(data), headers=headers)
    if response.status_code == 200:
        print_success(" Record has been added to the record pool")
    else:
        print_error(" Something went wrong, please try again")


def list_record():
    response = requests.get(f"http://{active_node}/chain/record-pool")

    if response.json()['length'] == 0:
        print_error(" There are no records in this node's record pool")
    else:
        json_records = response.json()['records']
        records = []
        for json_record in json_records:
            record = block_utils.get_record_object_from_dict(json_record, stored=False)
            records.append(record)
        client_utils.print_records(records)


def mine_block():
    chain_consensus()
    response = requests.get(f"http://{active_node}/chain/mine")
    if response.status_code == 200:
        print_success(f"Block {response.json()['index']} successfully mined")
    else:
        print_error("Something went wrong, please try again")


def verify_record():
    filename = input(" Filename: ")
    response = requests.get(f"http://{active_node}/chain/verify-record?filename={filename}")
    if response.status_code == 200:
        print_success("This file is successfully verified and can be submitted as evidence in a court of law")
    elif response.status_code == 404:
        print_error("File does not exists")
    else:
        print_error("This file has been tampered with")

def manage_chord_requests():
    os.system('clear')
    print_chord_heading()
    print(f"Use the '{colours.COMMAND}successor{colours.ENDCOLOUR}'      command to print node's successor.")
    print(f"Use the '{colours.COMMAND}successor-list{colours.ENDCOLOUR}' command to print node's successor list.")
    print(f"Use the '{colours.COMMAND}predecessor{colours.ENDCOLOUR}'    command to print node's predecessor.")
    print(f"Use the '{colours.COMMAND}lookup{colours.ENDCOLOUR}'         command to lookup a key's successor.")
    print(f"Use the '{colours.COMMAND}file{colours.ENDCOLOUR}'           command to see if a node owns a file.")
    print(f"Use the '{colours.COMMAND}table{colours.ENDCOLOUR}'          command to print node's finger table.")
    print(f"Use the '{colours.COMMAND}files{colours.ENDCOLOUR}'          command to print node's stored files.")
    print(f"Use the '{colours.COMMAND}nodes{colours.ENDCOLOUR}'          command to print all node id's.")
    print(f"Use the '{colours.COMMAND}return{colours.ENDCOLOUR}'         command to return to the node menu.")

    while True:
        command = input("\n>>> ")
        if command == "successor":
            chord_successor()
        elif command == "successor-list":
            chord_successor_list()
        elif command == "predecessor":
            chord_predecessor()
        elif command == "lookup":
            chord_lookup()
        elif command == "file":
            node_has_file()
        elif command == "table":
            chord_table()
        elif command == "files":
            print_stored_files()
        elif command == "nodes":
            chord_nodes()
        elif command == "return":
            return None
        else:
            print_error("Invalid command given, please try again...")


def chord_predecessor():
    response = requests.get(f"http://{active_node}/chord/predecessor")
    if response.status_code == 200:
        print(f"Predecessor: {response.json()['predecessor']}")
    else:
        print_error("Something went wrong, please try again")


def chord_successor():
    response = requests.get(f"http://{active_node}/chord/successor")
    if response.status_code == 200:
        print(f"Successor: {response.json()['successor']}")
    else:
        print_error("Something went wrong, please try again")


def chord_successor_list():
    response = requests.get(f"http://{active_node}/chord/successor-list")
    if response.status_code == 200:
        print(f"Successor: {response.json()['successor-list']}")
    else:
        print_error("Something went wrong, please try again")


def chord_lookup():
    file = input("Filename: ")
    response = requests.get(f"http://{active_node}/chord/lookup?key={chord_utils.get_hash(file)}")
    if response.status_code == 200:
        print(f"{response.json()['successor']}")
    else:
        print_error("Something went wrong, please try again")


def node_has_file():
    file = input("Filename: ")
    response = requests.get(f"http://{active_node}/node/file?filename={file}")
    if response.status_code == 200:
        print_success("True")
    else:
        print_error("False")


def chord_table():
    response = requests.get(f"http://{active_node}/chord/finger-table")
    if response.status_code == 200:
        index = 1
        finger_table = PrettyTable()
        finger_table.field_names = ["Index", "Node_id + 2^i-1 mod 2^m", "Successor"]
        for finger in json.loads(response.json()['finger_table']):
            finger_table.add_row([index, finger[0], finger[1]])
            index += 1
        print(finger_table)
    else:
        print_error("Something went wrong, please try again")


def print_stored_files():
    response = requests.get(f"http://{active_node}/chord/files")
    if response.status_code == 200:
        files = response.json()['files']
        if len(files) == 0:
            print_error("This node has no files stored")
        else:
            for file in files:
                print(file)
    else:
        print_error("Something went wrong, please try again")


def chord_nodes():
    response = requests.get(f"http://127.0.0.1:5000/discovery/peers")
    print(f"Node - 172.17.0.1:5000 @ '{chord_utils.get_hash('172.17.0.1:5000')}'")
    for peer in response.json()['peers']:
        print(f"Node - {peer} @ '{chord_utils.get_hash(peer)}'")


def sync_peers():
    response = requests.get(f"http://{active_node}/chain/sync/peers")
    if response.status_code == 200:
        print_success("Peers successfully synced")
    else:
        print_error("Something went wrong, please try again")


def chain_consensus():
    response = requests.get(f"http://{active_node}/chain/sync/chain")
    if response.status_code == 200:
        print_success("Chain consensus achieved")
    else:
        print_error("Something went wrong, please try again")

def leave_network():
    response = requests.get(f"http://{active_node}/node/leave")
    nodes_not_registered.append(active_node)
    nodes_registered.remove(active_node)
    return response.status_code


if __name__ == '__main__':
    main(sys.argv[1:])