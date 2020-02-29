import os
import json
import requests

from flask import Flask, request
from blockchain.chain import Blockchain
from blockchain import chain_utils, block_utils
from blockchain.maintenance_record import MaintenanceRecord

app = Flask(__name__)

# Node's copy of blockchain
blockchain = Blockchain()

# Maintain peer addresses
peers = []

# ---------------------------------------------------[API Endpoints]----------------------------------------------------
# -------------------------------------------------------[Chain]--------------------------------------------------------


@app.route('/chain', methods=['GET'])
def get_chain():
    response = {
        'length': len(blockchain.chain),
        'chain': blockchain.chain,
        'peers': json.dumps(peers)
    }
    return json.dumps(response), 200


# -----------------------------------------------------[Add Records]----------------------------------------------------


@app.route('/record', methods=['POST'])
def add_record():
    # Generate record from request data
    record = generate_record(request.get_json())

    # Generate record returns None with invalid data
    if record is None or not block_utils.is_record_valid(record):
        return 'Invalid data provided to create maintenance record', 400

    # Add record to record pool
    blockchain.record_pool.add_record(record)

    # Broadcast record to peers
    broadcast_record(record)
    return 'Record added to pool', 200


@app.route('/sync/record', methods=['POST'])
def sync_record():
    # Generate record from request data
    record = generate_record(request.get_json())

    # Generate record returns None with invalid data
    if record is None:
        return 'Invalid data provided to create maintenance record', 400

    blockchain.record_pool.add_record(record)
    return' "Record added to pool"', 200


# ---------------------------------------------------[Register Nodes]---------------------------------------------------

@app.route('/register', methods=['POST'])
def register_node():
    # TODO: Should add some authentication to prevent anyone registering to the blockchain.
    if 'node_address' not in request.get_json():
        return 'Node address not provided', 400

    address = request.get_json()['node_address']

    # Get most update to date chain on the network
    chain_consensus()

    # Return the node a list of peers on the network and an updated version of the chain
    response = {
        'peers': peers,
        'chain': blockchain.chain
    }

    # Added the new node to the list of peers.
    peers.append(address)

    return json.dumps(response), 200


@app.route('/register', methods=['GET'])
def discover_peers():
    global peers
    global blockchain

    # Discovery nodes needs address to update list of addresses.
    if request.args.get('node_address') is None:
        return 'No address provided', 400
    else:
        address = request.args['node_address']

    # Generate data and headers for POST request
    data = {'node_address': address}
    headers = {'Content-Type': 'application/json'}

    # Send request to directory node for chain and peer list
    response = requests.post('http://127.0.0.1:5000/register', data=json.dumps(data), headers=headers)

    # If request successful, update chain and list of peers
    if response.status_code == 200:
        blockchain.chain = response.json()['chain']
        peers = response.json()['peers']
        print(f"Node '{address}' successfully joined the network")
        return 'OK', 200
    else:
        print(f"Node '{address}' failed to join the network, reason: {response.reason}")
        return response.reason


# -----------------------------------------------------[Mine Blocks]----------------------------------------------------


@app.route('/mine', methods=['GET'])
def mine_block():
    mined_block = blockchain.mine()
    # TODO - Error handling


# --------------------------------------------------[Broadcast Functions]-----------------------------------------------


def broadcast_record(record):
    # Send unverified record to all peers
    for peer in peers:
        headers = {'Content-Type': "application/json"}
        data = {
            'aircraft_reg_number': record.aircraft_reg_number,
            'date_of_record': record.date_of_record,
            'filename': record.filename,
            'file_path': record.file_path
        }
        requests.post(f"http://{peer}/sync/record", headers=headers, data=data)


def chain_consensus():
    updated_chain = False

    # Request chain from each node
    for peer in peers:
        headers = {'Content-Type': 'application/json'}
        response = requests.get(f"http://{peer}/chain", headers=headers)
        # If node's chain is longer and valid, update chain
        if response.json()['length'] > len(blockchain.chain) and \
                blockchain.is_chain_valid():
            blockchain.chain = response.json()['chain']
            updated_chain = True

    if updated_chain:
        if os.path.exists(chain_utils.path_to_stored_chain()):
            # Deleting old chain
            os.remove(chain_utils.path_to_stored_chain())

            # Storing updating chain
            blocks_json_file = open(chain_utils.path_to_stored_chain(), 'w')
            json.dump(blockchain.chain, blocks_json_file)
            blocks_json_file.close()


# ---------------------------------------------------[Utility Functions]------------------------------------------------


def generate_record(request_json):
    # Parameters needed for a valid record
    record_parameters = ['aircraft_reg_number', 'date_of_record', 'filename', 'file_path']

    # Bad request if request does not contain all correct
    if not all(param in request_json for param in record_parameters):
        return None

    return MaintenanceRecord(request_json['aircraft_reg_number'],
                             request_json['date_of_record'],
                             request_json['filename'],
                             request_json['file_path'])
