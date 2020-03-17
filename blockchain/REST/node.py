import json
import os
import socket
import ssl
import hashlib

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

# Discovery node initialises the network
@app.route('/discovery/initialise', methods=['GET'])
def init_discover_node():
    global chord, node_address
    logger.info("Node was asked to initialise the chord ring")

    chord = Chord(discovery_node_address)
    node_address = discovery_node_address
    return 'Discovery Node Initialised', 200


# Ask a node to return its list of known peers
@app.route('/discovery/peers', methods=['GET'])
def get_known_peers():
    logger.info("Node was asked to return its list of peers")
    return json.dumps({'peers': peers}), 200


#                                                  /+=---------------=+\
# -----------------------------------------------=+|  Node Management  |+=----------------------------------------------
#                                                  \+=---------------=+/

# Ping a node to check its status
@app.route('/node/ping', methods=['GET'])
def ping():
    logger.info("Node was asked for a status update")
    return 'OK', 200


# Receive a record file from a peer in the network
@app.route('/node/record', methods=['POST'])
def receive_file():
    if 'file_name' not in request.get_json():
        return 'File name was not provided', 400
    filename = request.get_json()['file_name']

    # Create socket and ssl context
    context = ssl.create_default_context()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)

    # Bind and listen
    sock.bind(('172.17.0.1', 443))
    sock.listen()

    # Wrap socket with ssl context and accept incoming connection
    ssock = context.wrap_socket(sock, server_side=True)
    conn, addr = ssock.accept()
    logger.info(f"Made connection with address '{addr}', receiving file '{filename}'")

    # Create file in record storage directory
    storage_path = block_utils.path_to_record_storage()
    file_path = storage_path + "/" + filename

    # Write incoming data to new file
    with open(file_path, 'wb') as file:
        while True:
            data = ssock.read(1024)
            # no more data received
            if not data:
                break
            file.write(data)
        file.close()

    # Close connection and socket
    conn.close()
    ssock.close()
    sock.close()

    # Add the filename to a list of files stored on this node
    chord.stored_files.append(filename)


# ENDPOINT FOR DISCOVERY NODE - Accepts a new nodes registration request
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


# Send a request to discovery node to join the blockchain network
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
        blockchain.chain = chain_utils.get_chain_from_json(response.json()['chain'])
        for response_peer in response.json()['peers']:
            if response_peer not in peers and response_peer != node_address:
                peers.append(response_peer)

        # Join the Chord network
        join_chord_network()

        return json.dumps(peers, sort_keys=True, indent=2), 200
    else:
        return response.content, 400


#                                                    /+=----------=+\
# -------------------------------------------------=+|  Blockchain  |+=-------------------------------------------------
#                                                    \+=----------=+/

# Get chain and peer information from a peer
@app.route('/chain', methods=['GET'])
def get_chain():
    logger.info("Node was asked to return its chain and peer list")
    response = {
        'length': len(blockchain.chain),
        'chain': chain_utils.get_chain_json(blockchain.chain),
        'peers': peers
    }
    return json.dumps(response, sort_keys=True, indent=2), 200


# Get records from or add records to a node's record pool
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

        # Send record to its successor
        file_successor = chord_utils.find_successor(node_address, chord_utils.get_hash(record.filename))
        logger.info(f"Maintenance record's successor is '{file_successor}'")
        if str(file_successor) != str(node_address):
            # Send record file to successor
            send_file_to_peer(file_successor, record.filename)
        else:
            # We are the file successor, move file to record storage
            logger.debug(f"Moving file from unused records to record storage directory")
            block_utils.move_record_file(record.filename)
            chord.stored_files.append(record.filename)

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

# Make a node mind a block
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


# Solved blocks are sent to a peer via this endpoint, new block is added to the peer's chain
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

# Send a new unverified record to all peers
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


# Ask peers for their list of peers to get an up to date list of active peers
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

# Searches for the successor node of a key
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


# Gets the node's chord predecessor
@app.route('/chord/predecessor', methods=['GET'])
def get_predecessor():
    logger.info("Node was asked to return its chord predecessor")
    return json.dumps({'predecessor': chord.predecessor}), 200


# Gets the node's chord successor
@app.route('/chord/successor', methods=['GET'])
def get_successor():
    logger.info("Node was asked to return its chord predecessor")
    return json.dumps({'successor': chord.successor}), 200


# Notifies a chord node of a new potential predecessor
@app.route('/chord/notify', methods=['POST'])
def notify():
    if 'predecessor' in request.get_json():
        logger.info(f"Node '{request.get_json()['predecessor']}' may be our predecessor")
        potential_predecessor = request.get_json()['predecessor']
        potential_predecessor_hash = chord_utils.get_hash(potential_predecessor)
        if chord.predecessor is None:
            logger.info(f"Node has new predecessor '{potential_predecessor}'")
            chord.predecessor = potential_predecessor
        elif chord_utils.get_hash(chord.predecessor) < potential_predecessor_hash < chord.node_id or \
                chord.node_id < chord_utils.get_hash(chord.predecessor) < potential_predecessor_hash:
            logger.info(f"Node has new predecessor '{potential_predecessor}'")
            old_predecessor = chord.predecessor
            
            chord.predecessor = potential_predecessor

            chord_utils.stabalise_node(old_predecessor)
        return 'OK', 200
    else:
        logger.info("Notify request missing predecessor data")
        return 'Missing predecessor data', 400


# Tells a chord node to stabalise
@app.route('/chord/stabalise', methods=['GET'])
def stabalise_chord_node():
    logger.info("Node was asked to stabalise its chord instance")
    chord.stabalise()
    return 'OK', 200


# Tells a chord node to update their finger table
@app.route('/chord/update', methods=['GET'])
def update_chord():
    logger.info("Node was asked to update its finger table")
    chord.fix_fingers()
    return 'OK', 200


# Requests a chord node's finger table
@app.route('/chord/finger-table', methods=['GET'])
def get_finger_table():
    logger.info("Node was asked to return its chord finger table")
    return json.dumps({'finger_table': json.dumps(chord.finger_table)}, sort_keys=True, indent=2), 200


#                                                 /+=-------------------=+\
# ----------------------------------------------=+|  Broadcast Functions  |+=-------------------------------------------
#                                                 \+=-------------------=+/

# Attempts to establish chain consensus amongst known peers
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


# Broadcasts a solved block to the network
def broadcast_block_to_peers(block):
    # Send solved block to all known peer's in the network
    data = block_utils.get_block_dict_from_object(block)
    headers = {'Content-Type': "application/json"}

    for peer in peers:
        requests.post(f"http://{peer}/chain/add-block", data=json.dumps(data), headers=headers)


# Tells known peers to update their finger tables
def broadcast_chord_update(nodes_to_update):
    # Get all peers known to discovery node
    for node in nodes_to_update:
        logger.info(f"Telling '{node}' to update their finger table")
        requests.get(f"http://{node}/chord/update")


# Broadcasts a new unverified record to the network
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


# Send a maintenance record to it's successor
def send_file_to_peer(successor_peer, filename):
    data = json.dumps({'file_name': filename})
    headers = {'Content-Type': "application/json"}

    # Tell peer to expect an incoming connection
    requests.post(f"http://{successor_peer}/node/record", data=data, headers=headers)

    # Create ssl context
    context = ssl.create_default_context()

    # Set up secure socket
    sock = socket.create_connection(('172.17.0.1', 443))

    # Wrap socket with ssl context
    ssock = context.wrap_socket(sock, server_hostname='172.17.0.1')

    # Get path to record file in directory of example records
    file_path = block_utils.path_to_unused_record(filename)

    # MD5 checksum
    md5_hash = hashlib.md5()

    # Open file and continiously send blocks of data to peer until file is fully read
    with open(file_path, 'rb') as file:
        while True:
            data = file.readline()
            md5_hash.update(data)
            # Reached end of file, no more data to read
            if not data:
                ssock.send(b"CHECKSUM\n")
                ssock.send(md5_hash.hexdigest())
                break
            ssock.send(data)
        file.close()

    # Close socket after use
    ssock.close()
    sock.close()


#                                                 /+=-------------------=+\
# ----------------------------------------------=+|   Utility Functions   |+=-------------------------------------------
#                                                 \+=-------------------=+/

# Creates a MaintenanceRecord object from a request
def generate_record_from_request(record_json):
    # Parameters needed for a valid record
    record_parameters = ['aircraft_reg_number', 'date_of_record', 'filename']

    # Bad request if request does not contain all correct
    if not all(param in record_json for param in record_parameters):
        return None

    if not block_utils.maintenance_record_exists(record_json['filename']):
        return None

    return block_utils.get_record_object_from_dict(record_json)


# Creates a Block object from a request
def generate_block_from_request(block_json):
    # Parameters needed for a valid block
    block_parameters = ['index', 'previous_hash', 'timestamp', 'nonce', 'records', 'hash']

    # Bad request if request does not contain all correct
    if not all(param in block_json for param in block_parameters):
        return None

    return block_utils.get_block_object_from_dict(block_json)


# Allows a node to join the chord network
def join_chord_network():
    global chord
    # Initialising chord node
    chord = Chord(node_address)

    # Notify node's successor of our existence
    logger.debug("Notifying our successor")
    chord_utils.notify_successor(chord.successor, chord.node_address)

    # Tell successor to stabalise
    logger.debug("Stabalising our successor")
    chord_utils.stabalise_node(chord.successor)

    # Predecessor and successor points are correct, fix finger tables of effected nodes
    logger.debug("Fixing our finger table")
    chord.fix_fingers()

    logger.debug("Telling peers to update their finger tables")
    broadcast_chord_update(peers)
