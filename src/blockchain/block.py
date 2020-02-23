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
        :param index: Unique identification number of the block
        :param previous_hash: Hash of the previous block in the chain
        :param timestamp: Time since Unix epoch
        :param records: A list of maintenance records verified in the block
        :param nonce: A number used whilst mining to change the block's hash
        """
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.nonce = nonce
        self.records = records

    # TODO: Convert following method into one that converts block.__dict__ to block object
    # def __str__(self):
    #     """
    #     Returns the block serialised in JSON without the block hash
    #     """
    #     record_list = []
    #     for record in self.records:
    #         data = {
    #             "aircraft_registration_number": record.aircraft_reg,
    #             "date_of_record": record.date_of_record,
    #             "record_filename": record.record_filename,
    #             "record_hash": record.record_hash
    #         }
    #         record_list.append(data)
    #
    #     block = {
    #         "index": self.index,
    #         "previous_hash": self.previous_hash,
    #         "timestamp": self.timestamp,
    #         "nonce": self.nonce,
    #         "records": record_list
    #     }
    #     return block

    def get_block_hash(self):
        """
        Returns the hash of the serialised block
        """
        json_block = json.dumps(self.__dict__, sort_keys=True, indent=2)
        return hashlib.sha256(json_block.encode()).hexdigest()

