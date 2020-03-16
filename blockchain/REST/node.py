import json
import os

import requests
from flask import Flask, request

from blockchain import chain_utils, block_utils
from blockchain.chain import Blockchain
from blockchain.chord import chord_utils
from blockchain.chord.chord import Chord

app = Flask(__name__)

if __name__ == '__main__':
    app.run(host='0.0.0.0')

# Create logger
logger = chain_utils.init_logger("Node ")

# List of known peer addresses
peers = []

# Address of discovery node
discovery_node_address = '172.17.0.1:5000'

# Address of node
node_address = ''

# Node's blockchain instance
blockchain = Blockchain()

# Node's chord instance
chord = None


#                                                     /+=---------=+\
# --------------------------------------------------=+|  Discovery  |+=-------------------------------------------------
#                                                     \+=---------=+/

@app.route('/discovery/initialise', methods=['GET'])
def init_discover_node():
    global chord, node_address
    logger.info("Node was asked to initialise the chord ring")

    chord = Chord(discovery_node_address)
    node_address = discovery_node_address
    return 'Discovery Node Initialised', 200


@app.route('/discovery/peers', methods=['GET'])
def get_known_peers():
    logger.info("Node was asked to return its list of peers")
    return json.dumps({'peers': peers}), 200


#                                                  /+=---------------=+\
# -----------------------------------------------=+|  Node Management  |+=----------------------------------------------
#                                                  \+=---------------=+/

@app.route('/node/ping', methods=['GET'])
def ping():
    logger.info("Node was asked for a status update")
    return 'OK', 200


@app.route('/node', methods=['POST'])
def accept_peer():
    # Check address is provided
    if 'node_address' not in request.get_json():
        return 'Node address not provided', 400
    address = str(request.get_json()['node_address'])

    logger.info(f"Node was asked to add '{address}' to the network")

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
    global node_address, chord

    logger.info("Node was asked to register itself with discovery node")

    # Discovery nodes needs address to update list of addresses.
    if 'node_address' not in request.args:
        return 'No address provided', 400

    # Generate data and headers for POST request
    node_address = request.args['node_address']
    data = {'node_address': node_address}
    headers = {'Content-Type': 'application/json'}

    # Send request to directory node for chain and peer list
    response = requests.post(f'http://{discovery_node_address}/node', data=json.dumps(data), headers=headers)

    # If request successful, update chain and list of peers
    if response.status_code == 200:
        join_chord_network()
        blockchain.chain = chain_utils.get_chain_from_json(response.json()['chain'])
        for response_peer in response.json()['peers']:
            if response_peer not in peers and response_peer != node_address:
                peers.append(response_peer)
        return json.dumps(peers, sort_keys=True, indent=2), 200
    else:
        return response.content, 400


#                                                    /+=----------=+\
# -------------------------------------------------=+|  Blockchain  |+=-------------------------------------------------
#                                                    \+=----------=+/

@app.route('/chain', methods=['GET'])
def get_chain():
    logger.info("Node was asked to return its chain and peer list")
    response = {
        'length': len(blockchain.chain),
        'chain': chain_utils.get_chain_json(blockchain.chain),
        'peers': peers
    }
    return json.dumps(response, sort_keys=True, indent=2), 200


@app.route('/chain/record-pool', methods=['POST', 'GET'])
def manage_records():
    if request.method == 'POST':
        logger.info("Node was asked to add a record to its pool")

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
    else:
        logger.info("Node was asked to return its record pool")

        # Get unverified records in JSON serializable format
        response = []
        for record in blockchain.record_pool.unverified_records:
            response.append(record.__dict__)

        data = {
            'length': len(response),
            'records': response
        }

        return json.dumps(data, sort_keys=True, indent=2), 200


# ---------------------------------------------------[Mine/Add Blocks]--------------------------------------------------

@app.route('/chain/mine', methods=['GET'])
def mine_block():
    logger.info("Node was asked to mine a block")

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


@app.route('/chain/add-block', methods=['POST'])
def add_block():
    logger.info("Node was asked to add a block")

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


# ------------------------------------------------[Chain Synchronisation]-----------------------------------------------

@app.route('/chain/sync/record', methods=['POST'])
def sync_record():
    logger.info("Node was asked to sync its record pool")

    # Generate record object from request data
    record = generate_record_from_request(request.get_json())

    # Record is None with invalid request data
    if record is None:
        return 'Invalid data provided to create maintenance record', 400

    # Add new record to record pool
    blockchain.record_pool.add_record(record)
    return 'Record added to pool', 200


@app.route('/chain/sync/peers', methods=['GET'])
def sync_peers():
    logger.info("Node was asked to sync its peer list")

    # Sync node's peer list by requesting other node's peer lists
    for peer in peers:
        response = requests.get(f"http://{peer}/discovery/peers")
        for response_peer in response.json()['peers']:
            if response_peer not in peers and response_peer != node_address:
                peers.append(response_peer)
    return 'Synced peers', 200


#                                                      /+=-------=+\
# ---------------------------------------------------=+|   Chord   |+=--------------------------------------------------
#                                                      \+=-------=+/

@app.route('/chord/lookup', methods=['GET'])
def find_successor():
    if 'key' not in request.args:
        return 'No key was given in request', 400

    key = request.args['key']

    if chord.node_address == chord.successor:
        successor = {'successor': chord.node_address}
    else:
        successor = {'successor': chord.find_successor(key)}

    return json.dumps(successor), 200


@app.route('/chord/predecessor', methods=['GET'])
def get_predecessor():
    logger.info("Node was asked to return its chord predecessor")
    return json.dumps({'predecessor': chord.predecessor}), 200


@app.route('/chord/successor', methods=['GET'])
def get_successor():
    logger.info("Node was asked to return its chord predecessor")
    return json.dumps({'successor': chord.successor}), 200


@app.route('/chord/notify', methods=['POST'])
def notify():
    if 'predecessor' in request.get_json():
        logger.info(f"Node '{request.get_json()['predecessor']}' may be our predecessor")
        potential_predecessor = request.get_json()['predecessor']
        potential_predecessor_hash = chord_utils.get_hash(potential_predecessor)
        if chord.predecessor is None:
            logger.info(f"Node has new predecessor '{potential_predecessor}'")
            chord.predecessor = potential_predecessor
        elif chord_utils.get_hash(chord.predecessor) <= potential_predecessor_hash <= chord.node_id or \
                chord.node_id <= chord_utils.get_hash(chord.predecessor) <= potential_predecessor_hash:
            logger.info(f"Node has new predecessor '{potential_predecessor}'")
            old_predecessor = chord.predecessor
            
            chord.predecessor = potential_predecessor

            chord_utils.stabalise_node(old_predecessor)
        return 'OK', 200
    else:
        logger.info("Notify request missing predecessor data")
        return 'Missing predecessor data', 400


@app.route('/chord/stabalise', methods=['GET'])
def stabalise_chord_node():
    logger.info("Node was asked to stabalise its chord instance")
    chord.stabalise()
    return 'OK', 200


@app.route('/chord/update', methods=['GET'])
def update_chord():
    logger.info("Node was asked to update its finger table")
    chord.fix_fingers()
    return 'OK', 200


@app.route('/chord/finger-table', methods=['GET'])
def get_finger_table():
    logger.info("Node was asked to return its chord finger table")
    return json.dumps({'finger_table': json.dumps(chord.finger_table)}, sort_keys=True, indent=2), 200


#                                                 /+=-------------------=+\
# ----------------------------------------------=+|  Broadcast Functions  |+=-------------------------------------------
#                                                 \+=-------------------=+/

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
        requests.post(f"http://{peer}/chain/add-block", data=json.dumps(data), headers=headers)


def broadcast_chord_update(nodes_to_update):
    # Get all peers known to discovery node
    for node in nodes_to_update:
        logger.info(f"Telling '{node}' to update their finger table")
        requests.get(f"http://{node}/chord/update")


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
        requests.post(f"http://{peer}/chain/sync/record", data=json.dumps(data), headers=headers)


#                                                 /+=-------------------=+\
# ----------------------------------------------=+|   Utility Functions   |+=-------------------------------------------
#                                                 \+=-------------------=+/

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


def join_chord_network():
    global chord
    # Initialising chord node
    chord = Chord(node_address)

    # Notify node's successor of our existence
    chord_utils.notify_successor(chord.successor, chord.node_address)

    # Tell successor to stabalise
    chord_utils.stabalise_node(chord.successor)

    # Predecessor and successor points are correct, fix finger tables of effected nodes
    chord.fix_fingers()

    nodes_to_update = []
    if chord.successor is not node_address:
        nodes_to_update.append(chord.successor)
    if chord.successor is not chord.predecessor:
        nodes_to_update.append(chord.predecessor)
    broadcast_chord_update(nodes_to_update)
