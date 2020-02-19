from MaintenanceRecord import MaintenanceRecord
import hashlib
import json


class Block:
    def __init__(self, index, previous_hash, timestamp, records, nonce=0):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.nonce = nonce
        self.records = records
        self.hash = self.get_block_hash()

    def get_block_hash(self):
        record_list = []
        for record in self.records:
            data = {
                "aircraft_registration_number": record.aircraft_reg,
                "date_of_record": record.date_of_record,
                "record_filename": record.record_filename,
                "record_hash": record.record_hash
            }
            record_list.append(data)

        block = {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "records": record_list
        }

        json_block = json.dumps(block, sort_keys=True)
        return hashlib.sha256(json_block.encode()).hexdigest()

