import requests
import math

from blockchain.chord import chord_utils


class Chord:
    node_address = None
    node_id = None
    finger_table = None
    successor = None
    predecessor = None
    identifier_length = 160

    def __init__(self, ip_address):
        self.node_address = ip_address
        self.node_id = chord_utils.get_hash(ip_address)

        # Discovery node creates Chord ring
        if self.node_address == '172.17.0.1:5000':
            self.finger_table = [self.node_id for i in range(self.identifier_length)]
            self.successor = '172.17.0.1:5000'
        else:
            # Ask discovery node to find node's successor
            response = requests.get(f"http://172.17.0.1:5000/chord/find_successor?key={self.node_id}")
            self.successor = response.json()['successor']
            self.finger_table = self.init_finger_table()

    def find_successor(self, key):
        # Key exists between current node and it's successor
        if self.node_id < key <= self.successor:
            # Return successor's address
            return self.successor
        else:
            # Find the closest preceding node to the key
            preceding_node_address = self.find_closest_preceding_node(key)

            # Ask closest preceding node to find successor
            response = requests.get(f"http://{preceding_node_address}/chord/find_successor?key={key}")
            return response.json()['successor']

    def find_closest_preceding_node(self, key):
        # Iterate backwards through finger table to find preceding node to key
        for i in range(self.identifier_length - 1, -1, -1):
            if self.node_id < self.finger_table[i] <= key:
                return self.finger_table[i]
        # If key is smaller than node's id, jump to farthest known peer to restart search.
        return self.finger_table[-1]

    def init_finger_table(self):
        finger_table = []
        # Find successor to (server_id + 2^i % 2^160), store for i-th entry in finger table
        for i in range(self.identifier_length):
            # chord_id = succ(n+2^i)
            chord_id = (self.node_id + int(math.pow(2, i))) % math.pow(2, self.identifier_length)
            # Finger table no complete, ask discovery node to find successor
            finger = requests.get(f"http://172.17.0.1:5000/chord/find_successor?key={chord_id}").json()['successor']
            finger_table.append(finger)
        return finger_table

    def stabalise(self):
        # Verifying node's successor
        response = requests.get(f"http://{self.successor}/chord/predecessor")
        successors_predecessor = response.json()['predecessor']
        if self.node_id < chord_utils.get_hash(successors_predecessor) < chord_utils.get_hash(self.successor):
            self.successor = successors_predecessor
        requests.post(f"http://{successors_predecessor}/chord/notify?predecessor={self.node_address}")

    def check_predecessor(self):
        response = requests.get(f"http://{self.predecessor}/chord/ping")
        if response.status_code != 200:
            self.predecessor = None
