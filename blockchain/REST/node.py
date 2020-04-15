import json
import os
import socket
import threading
import time

import requests
from flask import Flask, request

from blockchain import chain_utils, block_utils
from blockchain.chain import Blockchain
from blockchain.chord import chord_utils
from blockchain.chord.chord import Chord
from blockchain.maintenance_record import MaintenanceRecord

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

# Boolean to simulate a node failing or going offline
online = False


#                                                     /+=---------=+\
# --------------------------------------------------=+|  Discovery  |+=-------------------------------------------------
#                                                     \+=---------=+/

# ---------------------------------------\
# Discovery node initialises the network |
# ---------------------------------------/
@app.route('/discovery/initialise', methods=['GET'])
def init_discover_node():
    global chord, node_address, online
    # Initialising chord node on discovery node
    chord = Chord(discovery_node_address)

    # Setting node address to a global variable
    node_address = discovery_node_address

    online = True
    return 'Discovery Node Initialised', 200


# ---------------------------------------------\
# Ask a node to return its list of known peers |
# ---------------------------------------------/
@app.route('/discovery/peers', methods=['GET'])
def get_known_peers():
    return json.dumps({'peers': peers}), 200


#                                                  /+=---------------=+\
# -----------------------------------------------=+|  Node Management  |+=----------------------------------------------
#                                                  \+=---------------=+/

# ---------------------------------------\
#     Ping a node to check its status    |
# ---------------------------------------/
@app.route('/node/ping', methods=['GET'])
def ping():
    if online:
        return 'OK', 200
    else:
        return 'Node offline', 400


# -------------------------------------------------\
# Receive a record file from a peer in the network |
# -------------------------------------------------/
@app.route('/node/record', methods=['POST'])
def receive_file():
    # Filename and checksum are required in the request
    if 'filename' not in request.get_json() or 'checksum' not in request.get_json():
        return 'File name was not provided', 400

    # Store request data in variables
    filename = request.get_json()['filename']
    received_checksum = request.get_json()['checksum']

    logger.info(f"Setting up server connection")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)

    # Bind and listen
    sock.bind(('0.0.0.0', 443))
    logger.info(f"Listening for connections...")
    sock.listen()

    # Wrap socket with ssl context and accept incoming connection
    conn, addr = sock.accept()
    logger.info(f"Made connection with address '{addr[0]}:{addr[1]}', receiving file with filename '{filename}'")

    # Create file in record storage directory
    storage_path = block_utils.path_to_record_storage()
    file_path = storage_path + "/" + filename

    # Write incoming data to new file
    with open(file_path, 'wb') as file:
        while True:
            # Get 1024 bytes of data from peer
            data = conn.recv(1024)
            # Break loop if no more data sent
            if not data:
                file.close()
                break
            # Write received data to file
            file.write(data)

    # Close connection and socket
    conn.close()
    sock.close()

    # Check file exists in file storage
    if not os.path.exists(file_path):
        logger.info("File path does not exist")
        return "Record was not transferred correctly", 400

    # Validate file checksums to ensure file integrity is maintained
    if block_utils.get_checksum_of_file(file_path) != received_checksum:
        logger.info("Checksums didn't match")
        return "Checksums don't match", 400

    logger.info(f"New file has been stored, checksums match")

    # Add the filename to a list of files stored on this node
    chord.stored_files.append(filename)
    return 'OK', 200


@app.route("/node/file", methods=['GET'])
def node_has_file():
    if 'filename' not in request.args:
        return 'No filename given', 400
    file_path = str(block_utils.path_to_record_storage()) + f"/{request.args['filename']}"
    if os.path.exists(file_path):
        return 'OK', 200
    else:
        return 'File does not exist', 400


# ------------------------------------------------------------------------\
# ENDPOINT FOR DISCOVERY NODE - Accepts a new node's registration request |
# ------------------------------------------------------------------------/
@app.route('/node', methods=['POST'])
def accept_peer():
    # Check address is provided
    if 'node_address' not in request.get_json():
        return 'Node address not provided', 400

    # Response with Bad Request if node already registered
    if request.get_json()['node_address'] in peers:
        return 'Address already registered', 400

    address = str(request.get_json()['node_address'])

    # Log the registration request
    logger.info(f"Node was asked to add '{address}' to the network")

    # Reach chain consensus with network
    peer_chain_consensus()

    # Return a list of peers on the network and an updated version of the chain
    response_peers = peers.copy()
    response_peers.append(discovery_node_address)
    response = {
        'peers': response_peers,
        'chain': chain_utils.get_chain_json(blockchain.chain)
    }

    # Added the new node to the list of peers.
    peers.append(address)

    return json.dumps(response, sort_keys=True, indent=2), 200


# ----------------------------------------------------------------\
# Send a request to discovery node to join the blockchain network |
# ----------------------------------------------------------------/
@app.route('/node/register', methods=['POST'])
def register_node():
    global node_address, chord

    logger.info("Node is registering itself on the network")

    # Discovery nodes needs address to update list of addresses.
    if 'node_address' not in request.args:
        return 'No address provided', 400

    node_address = request.args['node_address']

    # Generate data and headers for POST request
    data = {'node_address': node_address}
    headers = {'Content-Type': 'application/json'}

    # Send request to directory node for chain and peer list
    response = requests.post(f'http://{discovery_node_address}/node', data=json.dumps(data), headers=headers)

    # If request successful, update chain and list of peers
    if response.status_code != 200:
        return 'Discovery node failed', 400

    # Save received chain to node
    blockchain.chain = chain_utils.get_chain_from_json(response.json()['chain'])

    # Add received peers to global list of known peers
    for response_peer in response.json()['peers']:
        peers.append(response_peer)

    # Join the Chord network
    response = join_chord_network()
    if response != 0:
        return response, 400

    return 'Registration to network was successful', 200


# ---------------------------------------------------\
# Get the IP address of a node for socket connection |
# ---------------------------------------------------/
@app.route('/node/hostname', methods=['GET'])
def get_node_hostname():
    return json.dumps({'hostname': socket.gethostbyname(socket.gethostname())}), 200


@app.route('/node/leave', methods=['GET'])
def leave_network():
    global online
    broadcast_peer_sync(broadcast=True)

    moved_files, files_to_move = 0, 0
    if len(chord.stored_files) != 0:
        # Move our files to successor
        files_to_move = len(chord.stored_files)
        for file in chord.stored_files:
            if file_transfer_handler(chord.successor, file):
                moved_files += 1
        chord.stored_files = []

    response = requests.get(f"http://{chord.predecessor}/chord/stabalise")

    online = False
    broadcast_chord_update(peers)
    broadcast_peer_sync(broadcast=True)
    if response.status_code == 200:
        # Return success if all files transferred
        if moved_files == files_to_move:
            return 'OK', 200
        else:
            return 'Not all files transferred to successor', 400
    else:
        return response.reason, 400


#                                                    /+=----------=+\
# -------------------------------------------------=+|  Blockchain  |+=-------------------------------------------------
#                                                    \+=----------=+/

# -------------------------------------------\
# Get chain and peer information from a peer |
# -------------------------------------------/
@app.route('/chain', methods=['GET'])
def get_chain():
    logger.info("Node was asked to return its chain and peer list")
    response = {
        'length': len(blockchain.chain),
        'chain': chain_utils.get_chain_json(blockchain.chain),
        'peers': peers
    }
    return json.dumps(response, sort_keys=True, indent=2), 200


# --------------------------------------------------------\
# Get records from or add records to a node's record pool |
# --------------------------------------------------------/
@app.route('/chain/record-pool', methods=['POST', 'GET'])
def manage_records():
    if request.method == 'POST':
        logger.info("Node was asked to add a record to its record pool")

        # Generate record from request data
        record = generate_record_from_request(request.get_json())

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
            logger.info(f"Transferring file '{record.filename}' to '{file_successor}'")
            file_transfer_handler(file_successor, record.filename, stored=False)
        else:
            # We are the file successor, move file to record storage
            block_utils.move_record_file(record.filename)
            chord.stored_files.append(record.filename)

        response = requests.get(f"http://{file_successor}/node/file?filename={record.filename}")
        if response.status_code != 200:
            return response.content, 400
        else:
            logger.info(f"Maintenance record was successfully stored on file's successor node")
            return f"Record containing file with filename '{record.filename}' added to record pool'", 200
    else:
        logger.info("Node was asked to return its record pool")

        # Get unverified records in JSON serializable format
        response = []

        # Add all unverified records to return list
        for record in blockchain.record_pool.unverified_records:
            response.append(record.__dict__)

        # Generate response data
        data = {
            'length': len(response),
            'records': response
        }

        return json.dumps(data, sort_keys=True, indent=2), 200


# ---------------------------------------------------[Mine/Add Blocks]--------------------------------------------------

# ---------------------------------------\
#         Make a node mind a block       |
# ---------------------------------------/
@app.route('/chain/mine', methods=['GET'])
def mine_block():
    logger.info("Node was asked to mine a block")

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

    return json.dumps(block_utils.get_block_dict_from_object(mined_block)), 200


# -------------------------------------------------------------------------------------------\
# Solved blocks are sent to a peer via this endpoint, new block is added to the peer's chain |
# -------------------------------------------------------------------------------------------/
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


# -----------------------------------------------------------\
# A method for verifying a record has not been tampered with |
# -----------------------------------------------------------/
@app.route('/chain/verify-record', methods=['GET'])
def verify_record():
    if "filename" not in request.args:
        return 'No filename specified', 401

    # Locate record file in network
    filename = request.args['filename']
    logger.info(f"Node was asked check the validity of record '{filename}'")
    file_successor = chord_utils.find_successor(node_address, chord_utils.get_hash(filename))
    response = requests.get(f"http://{file_successor}/chord/record?filename={filename}")

    if response.status_code == 200:
        file_hash = response.json()["file_hash"]
        logger.info(f"hash of '{filename}' is '{file_hash}'")
        if blockchain.is_record_valid(file_hash, filename):
            return "File is valid", 200
        else:
            return "file is not valid", 400
    else:
        return "File not found", 404

# ------------------------------------------------[Chain Synchronisation]-----------------------------------------------

# -----------------------------------------------\
#    Send a new unverified record to all peers   |
# -----------------------------------------------/
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


# ----------------------------------------------------------------------------\
# Ask peers for their list of peers to get an up to date list of active peers |
# ----------------------------------------------------------------------------/
@app.route('/chain/sync/peers', methods=['GET'])
def sync_peers():
    logger.info("Node was asked to sync its peer list")

    # Sync node's peer list by requesting other node's peer lists
    broadcast_peer_sync()
    return 'Synced peers', 200


# ----------------------------------------------------------------------------\
#        Ask peers for their chain to allows node to reach a consensus        |
# ----------------------------------------------------------------------------/
@app.route('/chain/sync/chain', methods=['GET'])
def chain_consensus():
    broadcast_peer_sync()
    peer_chain_consensus()
    return 'Chain consensus', 200


#                                                      /+=-------=+\
# ---------------------------------------------------=+|   Chord   |+=--------------------------------------------------
#                                                      \+=-------=+/

# -----------------------------------------\
# Searches for the successor node of a key |
# -----------------------------------------/
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


# ----------------------------------------------\
#        Gets the node's chord predecessor      |
# ----------------------------------------------/
@app.route('/chord/predecessor', methods=['GET'])
def get_predecessor():
    logger.info("Node was asked to return its chord predecessor")
    return json.dumps({'predecessor': chord.predecessor}), 200


# --------------------------------------------\
#        Gets the node's chord successor      |
# --------------------------------------------/
@app.route('/chord/successor', methods=['GET'])
def get_successor():
    logger.info("Node was asked to return its chord predecessor")
    return json.dumps({'successor': chord.successor}), 200


# -------------------------------------------------\
#        Gets the node's chord successor list      |
# -------------------------------------------------/
@app.route('/chord/successor-list', methods=['GET'])
def get_successor_list():
    logger.info("Node was asked to return its chord predecessor")
    return json.dumps({'successor-list': [chord.successor, chord.successors_successor]}), 200


# -----------------------------------------------------\
# Notifies a chord node of a new potential predecessor |
# -----------------------------------------------------/
@app.route('/chord/notify', methods=['POST'])
def notify():
    if 'predecessor' in request.get_json():
        logger.info(f"Node '{request.get_json()['predecessor']}' may be our predecessor")

        # Get predecessor address and find it's ID
        potential_predecessor = request.get_json()['predecessor']
        potential_predecessor_hash = chord_utils.get_hash(potential_predecessor)

        if chord.predecessor is None:
            # We have no predecessor, set our predecessor as the potential predecessor
            logger.info(f"Node has new predecessor '{potential_predecessor}'")
            chord.predecessor = potential_predecessor
        elif requests.get(f"http://{chord.predecessor}/node/ping").status_code == 400:
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


# --------------------------------------------\
#        Tells a chord node to stabalise      |
# --------------------------------------------/
@app.route('/chord/stabalise', methods=['GET'])
def stabalise_chord_node():
    chord.stabalise()
    return 'OK', 200


# ------------------------------------------------\
# Tells a chord node to update their finger table |
# ------------------------------------------------/
@app.route('/chord/update', methods=['GET'])
def update_chord():
    logger.info("Node was asked to update its finger table")
    chord.fix_fingers()
    return 'OK', 200


# -----------------------------------------------\
#       Requests a chord node's finger table     |
# -----------------------------------------------/
@app.route('/chord/finger-table', methods=['GET'])
def get_finger_table():
    logger.info("Node was asked to return its chord finger table")
    return json.dumps({'finger_table': json.dumps(chord.finger_table)}, sort_keys=True, indent=2), 200


# ----------------------------------------------------------------------------------\
# Tells a chord node to check if files under their jurisdiction have new successors |
# ----------------------------------------------------------------------------------/
@app.route('/chord/sync/files', methods=['GET'])
def check_file_successors():
    moved_files = 0
    files_to_move = len(chord.stored_files)
    for file in chord.stored_files:
        file_successor = chord.find_successor(chord_utils.get_hash(file))

        if file_successor != node_address:
            moved_files += 1
        else:
            if file_transfer_handler(file_successor, file):
                moved_files += 1

    return f"'{moved_files}' out of '{files_to_move}' file(s) transferred", 200


# ----------------------------------------\
#     Returns all files stored on node    |
# ----------------------------------------/
@app.route("/chord/files", methods=['GET'])
def get_stored_files():
    return json.dumps({'files': chord.stored_files}), 200


# -------------------------------------------------\
#       Ask chord node to retrieve file hash       |
# -------------------------------------------------/
@app.route('/chord/record', methods=['GET'])
def get_file_hash():
    logger.info("Node was asked to return a file's hash")
    if "filename" not in request.args:
        return 'No filename specified', 400
    filename = str(request.args["filename"])
    file_path = block_utils.path_to_stored_record(filename)
    record = MaintenanceRecord("temp", "temp", filename, file_path)
    return json.dumps({"file_hash":record.file_hash}), 200

#                                                 /+=-------------------=+\
# ----------------------------------------------=+|  Broadcast Functions  |+=-------------------------------------------
#                                                 \+=-------------------=+/

# Attempts to establish chain consensus amongst known peers
def peer_chain_consensus():
    updated_chain = False

    # Request chain from each peer
    for peer in peers:
        if requests.get(f"http://{peer}/node/ping").status_code == 400:
            peers.remove(peer)
        else:
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
        if requests.get(f"http://{peer}/node/ping").status_code == 400:
            peers.remove(peer)
        else:
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
        if requests.get(f"http://{peer}/node/ping").status_code == 400:
            peers.remove(peer)
        else:
            requests.post(f"http://{peer}/chain/sync/record", data=json.dumps(data), headers=headers)


# Send a maintenance record to it's successor
def send_file_to_peer(peer_hostname, file_path):
    # Set up secure socket
    logger.info(f"Setting up client socket, connecting to '{peer_hostname}:443'")

    # TODO: Create a try catch here, then spin for a TTL of 10. This will allow time for server setup to finish
    sock = socket.create_connection((peer_hostname, 443))

    # Open file and continuously send blocks of data to peer until file is fully read
    logger.info(f"Sending file bytes to server'")
    with open(file_path, "rb") as file:
        while True:
            # Read 1024 bytes from file
            data = file.read(1024)

            # Reached end of file, no more data to read
            if not data:
                break
            # Send data to peer
            sock.send(data)

    # Close socket after use
    file.close()
    sock.close()


def initialise_receiving_peer(successor_node, filename):
    # Get path to record file in directory of example records
    file_path = block_utils.path_to_unused_record(filename)

    # Generate data and headers
    data = json.dumps({
        'filename': filename,
        'checksum': block_utils.get_checksum_of_file(file_path)
    })
    headers = {'Content-Type': "application/json"}

    logger.info(f"Telling successor '{successor_node}' to expect an incoming file transfer")

    # Tell peer to expect an incoming connection
    response = requests.post(f"http://{successor_node}/node/record", data=data, headers=headers)
    return response.content, response.status_code


def file_transfer_handler(file_successor, filename, stored=True):
    if file_successor != node_address:
        if stored:
            # Record already verified
            block_utils.stored_maintenance_record_exists(filename)
            file_path = block_utils.path_to_stored_record(filename)
        elif not stored:
            # Record not verified
            block_utils.unused_maintenance_record_exists(filename)
            file_path = block_utils.path_to_unused_record(filename)
        else:
            return "File doesn't exist", 400

        # Get hostname of file successor to set up a socket connection
        logger.debug("Requesting file successors hostname")
        successor_hostname = requests.get(f"http://{file_successor}/node/hostname").json()['hostname']
        logger.info(f"Received file successors hostname '{successor_hostname}'")

        # Creating threads to setup server peer and client peer
        t1 = threading.Thread(target=initialise_receiving_peer, args=(file_successor, filename))
        t2 = threading.Thread(target=send_file_to_peer, args=(successor_hostname, file_path))

        # Start threads
        logger.info(f"Asking file successor to set up server connection at '{file_successor}'")
        t1.start()
        # Allow time for server setup
        time.sleep(1)
        t2.start()

        # Join threads
        t1.join()
        t2.join()

    response = requests.get(f"http://{file_successor}/node/file?filename={filename}")
    return response.status_code == 200


def broadcast_peer_sync(broadcast=False):
    # Sync node's peer list by requesting other node's peer lists
    for peer in peers:
        if requests.get(f"http://{peer}/node/ping").status_code == 400:
            peers.remove(peer)
        else:
            response = requests.get(f"http://{peer}/discovery/peers")
            for response_peer in response.json()['peers']:
                if response_peer not in peers and response_peer != node_address:
                    peers.append(response_peer)

    if broadcast:
        for peer in peers:
            requests.get(f"http://{peer}/chain/sync/peers")


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

    if block_utils.stored_maintenance_record_exists(record_json['filename']):
        return block_utils.get_record_object_from_dict(record_json, stored=True)
    else:
        return block_utils.get_record_object_from_dict(record_json, stored=False)


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
    global chord, online
    # Initialising chord node
    chord = Chord(node_address)
    online = True

    # Notify node's successor of our existence
    logger.info("Notifying our successor")
    chord_utils.notify_successor(chord.successor, chord.node_address)

    # Tell successor to stabalise
    logger.info("Stabalising our successor")
    chord_utils.stabalise_node(chord.successor)

    # Predecessor and successor points are correct, fix finger tables of effected nodes
    logger.info("Fixing our finger table")
    chord.fix_fingers()

    # Tell nodes of the chord network to update their finger tables for the new changes
    logger.info("Telling peers to update their finger tables")
    broadcast_chord_update(peers)

    # Successor may have files in our jurisdiction, make sure they are sent to us
    logger.info("Telling successor to update their file store")
    response = requests.get(f"http://{chord.successor}/chord/sync/files")
    if response.status_code != 200:
        return response.reason
    return 0


def reset_node():
    global peers, node_address, blockchain, chord
    # List of known peer addresses
    peers = []

    # Address of node
    node_address = ''

    # Node's blockchain instance
    blockchain = Blockchain()

    # Node's chord instance
    chord = None
