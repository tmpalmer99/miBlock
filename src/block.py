import hashlib
import json


class Block:
    index = None
    previous_hash = None
    timestamp = None
    nonce = None
    hash = None
    records = []

    def __init__(self, index, previous_hash, timestamp, records, nonce=0):
        """
        Block class constructor
        :param index:           Unique identification number of the block
        :param previous_hash:   Hash of the previous block in the chain
        :param timestamp:       Time since Unix epoch
        :param records:         A list of maintenance records verified in the block
        :param nonce:           A number used whilst mining to change the block's hash
        """
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.nonce = nonce
        self.records = records

    def get_block_hash(self):
        """
        Returns the hash of a block
        """
        record_list = []
        # Get a JSON representation for each record in the block
        for record in self.records:
            record_list.append(record.__dict__)

        # Representation of block without it's hash
        block = {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "records": record_list
        }

        json_block = json.dumps(block)
        return hashlib.sha256(json_block.encode()).hexdigest()


