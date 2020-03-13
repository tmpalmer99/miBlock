import requests
import sys

from blockchain.chord import chord_utils


class FingerTable:
    table = None

    def __init__(self):
        table = []

    def add_entry(self, peer_id, peer_address):
        if len(self.table) == 2:
            return False

    def add_successor(self):
        # TODO: add entry to first table slot, if place taken need to move keys.
        return None



class ChordServer:
    server_address = None
    server_id = None
    finger_table = None
    peers = None
    successor = None

    def __init__(self, ip_address):
        self.server_address = ip_address
        self.server_id = chord_utils.get_hash(ip_address)
        self.finger_table = FingerTable()
        self.successor = self.get_successor()


    def get_successor(self):
        response = requests.get(f"http://{self.server_address}/sync/node")
        self.peers = response.json().copy()

        server_identifiers = []
        for peer in self.peers:
            peer_tuple = (chord_utils.get_hash(peer), peer)
            server_identifiers.append(peer_tuple)

        # If there are no other servers, make server it's own successor
        if len(server_identifiers) == 0:
            return self.server_id, self.server_address

        successor = sys.maxsize
        successor_address = ''
        for server_id in server_identifiers:
            if self.server_id < server_id[0] < successor:
                successor = server_id[0]
                successor_address = server_id[1]

        # Server has highest id, need to find the start server
        if successor == sys.maxsize:
            for server_id in server_identifiers:
                if server_id[0] < self.server_id and server_id[0] < successor:
                    successor = server_id[0]
                    successor_address = server_id[1]
        return successor, successor_address