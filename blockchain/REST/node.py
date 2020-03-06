import os
import json
import requests

from flask import Flask, request
from blockchain.chain import Blockchain
from blockchain.block import Block
from blockchain import chain_utils, block_utils
from blockchain.maintenance_record import MaintenanceRecord

app = Flask(__name__)

if __name__ == '__main__':
    app.run(host='0.0.0.0')

# Node's copy of blockchain
blockchain = Blockchain()

# Maintain peer addresses
peers = []

# Discovery node address
discov_address = '172.17.0.1:5000'


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
    record = generate_record(request.form)

    app.logger.info(f"Adding Record with filename '{record.filename}'")

    # Generate record returns None with invalid data
    if record is None or not block_utils.is_record_valid(record):
        return 'Invalid data provided to create maintenance record', 400

    # Add record to record pool
    blockchain.record_pool.add_record(record)
    app.logger.info('Record added to pool')

    # Broadcast record to peers
    app.logger.info('Broadcasting record to network')
    broadcast_record(record)
    return 'Record added to pool', 200


@app.route('/sync/record', methods=['POST'])
def sync_record():
    # Generate record object from request data
    app.logger.info(f'Record received from network: {request.get_json()}')
    record = generate_record(request.get_json())

    # Generate record returns None with invalid data
    if record is None:
        return 'Invalid data provided to create maintenance record', 400

    blockchain.record_pool.add_record(record)
    app.logger.info(f'Record added to pool')
    return 'Record added to pool', 200


@app.route('/record', methods=['GET'])
def get_unverified_records():
    response = []
    for record in blockchain.record_pool.unverified_records:
        response.append(record.__dict__)

    data = {
        'length': len(response),
        'records': response
    }
    
    return json.dumps(data, sort_keys=True, indent=2), 200


# ---------------------------------------------------[Register Nodes]---------------------------------------------------

@app.route('/node', methods=['POST'])
def accept_node():
    # TODO: Should add some authentication to prevent anyone registering to the blockchain.

    if 'node_address' not in request.get_json():
        return 'Node address not provided', 400

    address = str(request.get_json()['node_address'])
    print("[DEBUG] - Address: ", address)

    if address in peers:
        return 'Address already registered', 400

    # Get most update to date chain on the network
    chain_consensus()

    # Return the node a list of peers on the network and an updated version of the chain
    response_peers = peers.copy()
    response_peers.append(discov_address)
    response = {
        'peers': response_peers,
        'chain': chain_utils.get_chain_json(blockchain.chain)
    }

    # Added the new node to the list of peers.
    peers.append(address)

    return json.dumps(response, sort_keys=True, indent=2), 200


@app.route('/node/register', methods=['POST'])
def register_node():
    app.logger.info('Requesting to join network...')

    # Discovery nodes needs address to update list of addresses.
    if 'node_address' not in request.args:
        return 'No address provided', 400
    else:
        address = request.args['node_address']

    # Generate data and headers for POST request
    data = {'node_address': address}
    headers = {'Content-Type': 'application/json'}

    # Send request to directory node for chain and peer list
    response = requests.post(f'http://{discov_address}/node', data=json.dumps(data), headers=headers)

    # If request successful, update chain and list of peers
    if response.status_code == 200:
        blockchain.chain = chain_utils.get_chain_from_json(response.json()['chain'])
        for peer in response.json()['peers']:
            peers.append(peer)
        app.logger.info(f"Node '{address}' successfully joined the network")
        return json.dumps(peers, sort_keys=True, indent=2), 200
    else:
        app.logger.error(f"Node '{address}' failed to join the network, reason: {response.content}")
        return response.content, 400


# -----------------------------------------------------[Mine Blocks]----------------------------------------------------

@app.route('/mine', methods=['GET'])
def mine_block():
    # Mine a block
    print("[INFO] - Mining...")
    mined_block = blockchain.mine()

    # Check block was successfully mined
    if mined_block is None:
        return "No records to verify", 400

    # Store length of chain before reaching consensus with peers
    length_of_chain = len(blockchain.chain)

    # Reach consensus with peers
    chain_consensus()

    # If node's chain is most up to date, broadcast it to peer's to synchronise chain
    if length_of_chain == len(blockchain.chain):
        broadcast_block(mined_block)
    
    return f'Block added to chain with index {mined_block.index}', 200


@app.route('/add_block', methods=['POST'])
def add_block():
    # Reach consensus with peers
    chain_consensus()

    block = generate_block(request.get_json())

    if block is None:
        return "There was an error when adding block", 400

    if blockchain.add_block(block):
        blockchain.record_pool.remove_records(block.records)
        return "Block was added to node's chain", 201
    else:
        return "There was an error when added block", 400


# --------------------------------------------------[Broadcast Functions]-----------------------------------------------


def chain_consensus():
    updated_chain = False

    # Request chain from each node
    for peer in peers:
        headers = {'Content-Type': "application/json"}
        response = requests.get(f"http://{peer}/chain", headers=headers)
        # If node's chain is longer and valid, update chain
        print(f"[DEBUG] - Response: {response.json()}")
        if response.json()['length'] > len(blockchain.chain) and \
                blockchain.is_chain_valid():
            blockchain.chain = chain_utils.get_chain_from_json(response.json()['chain'])
            updated_chain = True

    if updated_chain:
        if os.path.exists(chain_utils.path_to_stored_chain()):
            # Deleting old chain
            os.remove(chain_utils.path_to_stored_chain())

            # Storing updating chain
            blocks_json_file = open(chain_utils.path_to_stored_chain(), 'w')
            json.dump(chain_utils.get_chain_json(blockchain.chain), blocks_json_file, sort_keys=True, indent=2)
            blocks_json_file.close()


def broadcast_block(block):
    data = block_utils.get_block_dict_from_object(block)

    headers = {'Content-Type': "application/json"}

    for peer in peers:
        requests.post(f"http://{peer}/add_block", data=json.dumps(data), headers=headers)


def broadcast_record(record):
    app.logger.info(f'Broadcasting record with filename: {record.filename}')

    data = {
        'aircraft_reg_number': record.aircraft_reg_number,
        'date_of_record': record.date_of_record,
        'filename': record.filename,
        'file_path': record.file_path
    }
    headers = {'Content-Type': "application/json"}

    # Send unverified record to all peers
    for peer in peers:
        response = requests.post(f"http://{peer}/sync/record", data=json.dumps(data), headers=headers)
        app.logger.info(f"Outcome of broadcasting record to peer '{peer}': {response.content}")

# ---------------------------------------------------[Utility Functions]------------------------------------------------


def generate_record(record_json):
    # Parameters needed for a valid record
    record_parameters = ['aircraft_reg_number', 'date_of_record', 'filename', 'file_path']

    # Bad request if request does not contain all correct
    if not all(param in record_json for param in record_parameters):
        return None

    print("[DEBUG] - ALL PARAMS PRESENT")

    return block_utils.get_record_object_from_dict(record_json)


def generate_block(block_json):
    # Parameters needed for a valid block
    block_parameters = ['index', 'previous_hash', 'timestamp', 'nonce', 'records', 'hash']

    # Bad request if request does not contain all correct
    if not all(param in block_json for param in block_parameters):
        return None

    app.logger.info(f"Records 2: {block_json['records']}")

    return block_utils.get_block_object_from_dict(block_json)
