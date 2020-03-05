import os

from blockchain.block import Block
from blockchain.maintenance_record import MaintenanceRecord


def get_block_object_from_dict(block_dict):
    """
    Blocks are sometimes represented in their dictionary form to allow JSON serialisation
    of block. 'get_object_from_dict' returns a block to a Block object.

    :param block_dict:  A dictionary representing a block object
    :return:            A Block object
    """
    index = block_dict["index"]
    previous_hash = block_dict["previous_hash"]
    timestamp = block_dict["timestamp"]
    nonce = block_dict["nonce"]
    block_hash = block_dict["hash"]

    records = []
    for record in block_dict["records"]:
        records.append(get_record_object_from_dict(record))

    block = Block(index, previous_hash, timestamp, records, nonce)
    if block.get_block_hash() == block_hash:
        block.hash = block_hash
        return block
    else:
        return None


def get_block_dict_from_object(block):
    formatted_records = []
    for record in block.records:
        formatted_records.append(record.__dict__)

    block_dict = {
        'index': block.index,
        'previous_hash': block.previous_hash,
        'timestamp': block.timestamp,
        'nonce': block.nonce,
        'records': formatted_records,
        'hash': block.hash
    }

    return block_dict


def get_record_object_from_dict(record):
    return MaintenanceRecord(record['aircraft_reg_number'],
                             record['date_of_record'],
                             record['filename'],
                             record['file_path'])


def is_record_valid(record):
    print(f"[DEBUG] - Checking record validity: {record}")
    if not os.path.exists(record.file_path):
        print(1)
        return False
    if not str(record.file_path).split("/")[-1] != record.filename:
        print(2)
        return False
    return True


