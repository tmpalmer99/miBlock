import hashlib
import requests
import json
import math


def get_hash(address):
    # Gets SHA1 hash value of a node address
    hash_hex = hashlib.sha1(str(address).encode()).hexdigest()

    hash_reduced_mag = float(float(int(hash_hex, 16) / math.pow(2, 160)) * math.pow(2, 10))
    return hash_reduced_mag


# -----------------------------------------------[Chord Request Handlers]-----------------------------------------------

def find_successor(node_address, key):
    # Send get request to a node asking to find the successor of a key
    response = requests.get(f"http://{node_address}/chord/lookup?key={key}")
    if response.status_code == 200:
        return response.json()['successor']
    else:
        return None


def get_predecessor(node_address):
    # Send get request to address asking for their predecessor
    response = requests.get(f"http://{node_address}/chord/predecessor")
    if response.status_code == 200:
        return response.json()['predecessor']
    else:
        return None


def notify_successor(successor_address, node_address):
    # Send a post request to a successor, notifying them of their new predecessor
    response = requests.post(f"http://{successor_address}/chord/notify",
                             data=json.dumps({'predecessor': node_address}),
                             headers={'Content-Type': "application/json"})
    return response.status_code == 200


def stabalise_node(node_address):
    response = requests.get(f"http://{node_address}/chord/stabalise")
    return response.status_code == 200