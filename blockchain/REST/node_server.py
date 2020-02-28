import os
import json
import requests

from flask import Flask, request
from blockchain import chain_utils
from blockchain.chain import Blockchain
from blockchain.record_pool import RecordPool
# import logging
#
# logging.basicConfig(filename='node.log',
#                     level=logging.DEBUG,
#                     format='%(asctime)s %(levelname)s: %(message)s')


app = Flask(__name__)

# Node's copy of blockchain
blockchain = Blockchain()

# Node's copy of the record pool
record_pool = RecordPool()

# Maintain peer addresses
peers = []


@app.route('/chain', methods=['GET'])
def get_chain():
    global blockchain

    response = {
        "length": len(blockchain.chain),
        "chain": blockchain.chain,
        "peers": json.dumps(peers)
    }
    return json.dumps(response), 200


@app.route('/register', methods=['POST'])
def register_node():
    global blockchain
    global peers

    # TODO: Should add some authentication to prevent anyone registering to the blockchain.
    address = request.get_json()["node_address"]

    # TODO: Reach consensus before sending chain
    # Return the node a list of peers on the network and an updated version of the chain
    response = {
        "peers": peers,
        "chain": blockchain.chain
    }

    # Added the new node to the list of peers.
    peers.append(address)

    return json.dumps(response), 200


@app.route('/register', methods=['GET'])
def discover_peers():
    global peers
    global blockchain

    # Discovery nodes needs address to update list of addresses.
    if request.args.get("node_address") is None:
        return "No address provided", 400
    else:
        address = request.args["node_address"]

    # Generate data and headers for POST request
    data = {"node_address": address}
    headers = {'Content-Type': "application/json"}

    # Send request to directory node for chain and peer list
    response = requests.post("http://127.0.0.1:5000/register", data=json.dumps(data), headers=headers)

    # If request successful, update chain and list of peers
    if response.status_code == 200:
        blockchain.chain = response.json()["chain"]
        peers = response.json()["peers"]
        print(f"Node '{address}' successfully joined the network")
        return "OK", 200
    else:
        print(f"Node '{address}' failed to join the network, reason: {response.reason}")
        return response.reason


@app.route('/mine', methods=['GET'])
def mine_block():
    mined_block = blockchain.mine(record_pool.get_unverified_records())


def chain_consensus():
    updated_chain = False

    for peer in peers:
        headers = {'Content-Type': "application/json"}
        response = requests.get(f"http://{peer}/chain", headers=headers)
        if response.json()["length"] > len(blockchain.chain) and \
                chain_utils.is_chain_valid(response.json()["chain"]):
            blockchain.chain = response.json()["chain"]
            updated_chain = True

    if updated_chain:
        app_root = chain_utils.get_app_root_directory()
        if os.path.exists(f"{app_root}/data/blocks.json"):
            os.remove(f"{app_root}/data/blocks.json")
            blocks_json_file = open(str(app_root) + "/data/blocks.json", "w")
            json.dump(blockchain.chain, blocks_json_file)
            blocks_json_file.close()
