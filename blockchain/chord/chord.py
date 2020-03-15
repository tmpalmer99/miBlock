import math

from blockchain import chain_utils
from blockchain.chord import chord_utils

# Create logger
logger = chain_utils.init_logger("Chord")


class Chord:
    node_address = None
    node_id = None
    finger_table = []
    successor = None
    predecessor = None
    identifier_length = 10

    def __init__(self, ip_address):
        # Set node address and ID information
        self.node_address = ip_address
        self.node_id = chord_utils.get_hash(ip_address)

        logger.info(f"[{self.node_address}]: Initialising Chord node '{ip_address}'")

        # Discovery node creates Chord ring
        if self.node_address == '172.17.0.1:5000':
            for i in range(self.identifier_length):
                chord_id = (self.node_id + math.pow(2, i)) % math.pow(2, self.identifier_length)
                self.finger_table.append([chord_id, self.node_address])
            self.successor = self.node_address
        else:
            # Ask discovery node to find node's successor
            self.successor = chord_utils.find_successor('172.17.0.1:5000', self.node_id)
            logger.info(f"[{self.node_address}]: Found successor '{self.successor}'")
            logger.info(f"[{self.node_address}]: Notifying '{self.successor}' of our existence")

    def find_successor(self, key):
        key = float(key)
        # Key exists between current node and it's successor
        if self.node_id <= key <= chord_utils.get_hash(self.successor):
            # Return successor's address
            logger.info(f"[{self.node_address}]: Successor of 'key' is '{self.successor}'")
            return self.successor
        elif chord_utils.get_hash(self.successor) < self.node_id < key:
            logger.info(f"[{self.node_address}]: Successor of 'key' is '{self.successor}'")
            return self.successor
        else:
            # Find the closest preceding node to the key
            logger.info(f"[{self.node_address}]: Looking for closest preceding node")
            preceding_node_address = self.find_closest_preceding_node(key)

            if preceding_node_address == self.node_address:
                preceding_node_address = self.successor

            logger.info(f"[{self.node_address}]: Asking '{preceding_node_address}' to find key's successor")

            # Ask closest preceding node to find successor
            return chord_utils.find_successor(preceding_node_address, key)

    def find_closest_preceding_node(self, key):
        key = float(key)
        # Iterate backwards through finger table to find preceding node to key
        for i in range(self.identifier_length - 1, -1, -1):
            if self.node_id <= self.finger_table[i][0] <= key:
                return self.finger_table[i][1]

        # If key is smaller than node's id, jump to farthest known peer to restart search.
        for i in range(self.identifier_length - 1, -1, -1):
            if self.finger_table[i][1] != self.node_address:
                return self.finger_table[i][1]

        return self.successor

    def fix_fingers(self):
        logger.info(f"[{self.node_address}]: Fixing finger table for {self.node_address}")
        if len(self.finger_table) == 0:
            for index in range(self.identifier_length):
                # chord_id = succ(n+2^i)
                chord_id = (self.node_id + math.pow(2, index)) % math.pow(2, self.identifier_length)
                # Finger table no complete, ask discovery node to find successor
                successor = str(chord_utils.find_successor('172.17.0.1:5000', chord_id))
                logger.info(f"[{self.node_address}]: Fixing Table - succ({chord_id}): {successor}")
                self.finger_table.append([chord_id, successor])
        else:
            for index in range(len(self.finger_table)):
                chord_id = self.finger_table[index][0]
                self.finger_table[index][1] = str(self.find_successor(chord_id))

    def stabalise(self):
        logger.info(f"[{self.node_address}]: Stabilising...")

        # This if statement is true when second node is joining the chord network
        if self.node_address == self.successor:
            self.successor = self.predecessor
            successors_predecessor = self.predecessor
            logger.info(f"[{self.node_address}]: Found new successor '{self.successor}'")
        else:
            # Verify our successor's predecessor is correct
            successors_predecessor = chord_utils.get_predecessor(self.successor)
            if self.node_id <= chord_utils.get_hash(successors_predecessor) <= chord_utils.get_hash(self.successor):
                # Update our successor, it is incorrect
                self.successor = successors_predecessor
                logger.info(f"[{self.node_address}]: Found new successor '{self.successor}'")

            # Notify verified successor that we are their predecessor
            logger.info(f"[{self.node_address}]: Notifying '{successors_predecessor}' of our existence")

        chord_utils.notify_successor(successors_predecessor, self.node_address)

    def check_predecessor(self):
        # Check predecessor's status
        if not chord_utils.ping_address(self.predecessor):
            # Predecessor has failed, or no longer part of the system
            self.predecessor = None
