import os
import json
import requests

from flask import Flask, request
from blockchain.chain import Blockchain
from blockchain import chain_utils, block_utils

app = Flask(__name__)

if __name__ == '__main__':
    app.run(host='0.0.0.0')

# Node's copy of blockchain
blockchain = Blockchain()

# Maintain peer addresses
peers = []

# Discovery node address
discovery_node_address = '172.17.0.1:5000'

# Address of node
node_address = ''


# ---------------------------------------------------[API Endpoints]----------------------------------------------------
# -------------------------------------------------------[Chain]--------------------------------------------------------


@app.route('/chain', methods=['GET'])
def get_chain():
    response = {
        'length': len(blockchain.chain),
        'chain': chain_utils.get_chain_json(blockchain.chain),
        'peers': peers
    }
    return json.dumps(response, sort_keys=True, indent=2), 200


# -------------------------------------------------------[Records]-----------------------------------------------------


@app.route('/record', methods=['POST'])
def add_record():
    # Generate record from request data
    record = generate_record_from_request(request.form)

    # Generate record returns None with invalid data
    if record is None or not block_utils.is_record_valid(record):
        return 'Invalid data provided to create maintenance record', 400

    # Add record to record pool
    blockchain.record_pool.add_record(record)

    # Broadcast record to peers
    broadcast_record_to_peers(record)

    return 'Record added to pool', 200


@app.route('/record', methods=['GET'])
def get_unverified_records():
    # Get unverified records in JSON serializable format
    response = []
    for record in blockchain.record_pool.unverified_records:
        response.append(record.__dict__)

    data = {
        'length': len(response),
        'records': response
    }

    return json.dumps(data, sort_keys=True, indent=2), 200


@app.route('/sync/record', methods=['POST'])
def sync_record():
    # Generate record object from request data
    record = generate_record_from_request(request.get_json())

    # Record is None with invalid request data
    if record is None:
        return 'Invalid data provided to create maintenance record', 400

    # Add new record to record pool
    blockchain.record_pool.add_record(record)
    return 'Record added to pool', 200


# ---------------------------------------------------[Register Nodes]---------------------------------------------------


@app.route('/node', methods=['POST'])
def accept_peer():
    # TODO: Should add some authentication to prevent anyone registering to the blockchain.

    # Check address is provided
    if 'node_address' not in request.get_json():
        return 'Node address not provided', 400
    address = str(request.get_json()['node_address'])

    # Response with Bad Request if node already registered
    if address in peers:
        return 'Address already registered', 400

    # Get most update to date chain on the network
    peer_chain_consensus()

    # Return the node a list of peers on the network and an updated version of the chain
    response_peers = peers.copy()
    response_peers.append(discovery_node_address)
    response = {
        'peers': response_peers,
        'chain': chain_utils.get_chain_json(blockchain.chain)
    }

    # Added the new node to the list of peers.
    peers.append(address)

    return json.dumps(response, sort_keys=True, indent=2), 200


@app.route('/node/register', methods=['POST'])
def register_node():
    global node_address

    # Discovery nodes needs address to update list of addresses.
    if 'node_address' not in request.args:
        return 'No address provided', 400

    # Generate data and headers for POST request
    node_address = request.args['node_address']
    data = {'node_address': request.args['node_address']}
    headers = {'Content-Type': 'application/json'}

    # Send request to directory node for chain and peer list
    response = requests.post(f'http://{discovery_node_address}/node', data=json.dumps(data), headers=headers)

    # If request successful, update chain and list of peers
    if response.status_code == 200:
        blockchain.chain = chain_utils.get_chain_from_json(response.json()['chain'])
        for peer in response.json()['peers']:
            peers.append(peer)
        return json.dumps(peers, sort_keys=True, indent=2), 200
    else:
        return response.content, 400


@app.route('/node', methods=['GET'])
def sync_peers():
    # Sync node's peer list by requesting other node's peer lists
    for peer in peers:
        response = requests.get(f"http://{peer}/sync/node")
        for response_peer in response.json()['peers']:
            if response_peer not in peers and response_peer != node_address:
                peers.append(response_peer)
    return 'Synced peers', 200


@app.route('/sync/node', methods=['GET'])
def get_peers():
    # Respond with list of peers
    data = {'peers': peers}
    return json.dumps(data)


# -----------------------------------------------------[Mine Blocks]----------------------------------------------------

@app.route('/mine', methods=['GET'])
def mine_block():
    # Mine a block
    mined_block = blockchain.mine()

    # Check block was successfully mined
    if mined_block is None:
        return "No records to verify", 400

    # Store length of chain before reaching consensus with peers
    length_of_chain = len(blockchain.chain)

    # Reach consensus with peers
    peer_chain_consensus()

    # If node's chain is most up to date, broadcast it to peer's to synchronise chain
    if length_of_chain == len(blockchain.chain):
        broadcast_block_to_peers(mined_block)
    
    return f'Block added to chain with index {mined_block.index}', 200


@app.route('/add_block', methods=['POST'])
def add_block():
    # Generate block object from request
    block = generate_block_from_request(request.get_json())

    # Block is none with bad request data
    if block is None:
        return "There was an error when adding block", 400

    # Add new block to node's chain
    if blockchain.add_block(block):
        # If block contains verified records in node's record pool, remove records.
        blockchain.record_pool.remove_records(block.records)
        return "Block was added to node's chain", 201
    else:
        return "There was an error when adding block", 400


# --------------------------------------------------[Broadcast Functions]-----------------------------------------------


def peer_chain_consensus():
    updated_chain = False

    # Request chain from each peer
    for peer in peers:
        headers = {'Content-Type': "application/json"}
        response = requests.get(f"http://{peer}/chain", headers=headers)
        # If peer's chain is longer and valid, update chain
        if response.json()['length'] > len(blockchain.chain) and \
                blockchain.is_chain_valid():
            blockchain.chain = chain_utils.get_chain_from_json(response.json()['chain'])
            updated_chain = True

    if updated_chain:
        if os.path.exists(chain_utils.path_to_stored_chain()):
            chain_utils.write_chain(blockchain.chain)


def broadcast_block_to_peers(block):
    # Send solved block to all known peer's in the network
    data = block_utils.get_block_dict_from_object(block)
    headers = {'Content-Type': "application/json"}

    for peer in peers:
        requests.post(f"http://{peer}/add_block", data=json.dumps(data), headers=headers)


def broadcast_record_to_peers(record):
    data = {
        'aircraft_reg_number': record.aircraft_reg_number,
        'date_of_record': record.date_of_record,
        'filename': record.filename,
        'file_path': record.file_path
    }
    headers = {'Content-Type': "application/json"}

    # Send unverified record to all known peer's in the network
    for peer in peers:
        requests.post(f"http://{peer}/sync/record", data=json.dumps(data), headers=headers)


# ---------------------------------------------------[Utility Functions]------------------------------------------------


def generate_record_from_request(record_json):
    # Parameters needed for a valid record
    record_parameters = ['aircraft_reg_number', 'date_of_record', 'filename', 'file_path']

    # Bad request if request does not contain all correct
    if not all(param in record_json for param in record_parameters):
        return None

    return block_utils.get_record_object_from_dict(record_json)


def generate_block_from_request(block_json):
    # Parameters needed for a valid block
    block_parameters = ['index', 'previous_hash', 'timestamp', 'nonce', 'records', 'hash']

    # Bad request if request does not contain all correct
    if not all(param in block_json for param in block_parameters):
        return None

    return block_utils.get_block_object_from_dict(block_json)
