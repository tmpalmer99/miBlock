import hashlib
import os

from blockchain import chain_utils
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
    nonce = block_dict["nonce"]
    block_hash = block_dict["hash"]
    timestamp = block_dict["timestamp"]
    previous_hash = block_dict["previous_hash"]

    records = []
    for record_dict in block_dict["records"]:
        record = get_record_object_from_dict(record_dict)
        records.append(record)

    block = Block(index, previous_hash, timestamp, records, nonce)
    if block.get_block_hash() == block_hash:
        block.hash = block_hash
        return block
    return None


def get_record_object_from_dict(record_dict):
    """
    Converts a record in dictionary format to object form
    :param record_dict: Record in dictionary format
    :return:            Record in MaintenanceRecord type
    """
    return MaintenanceRecord(record_dict['aircraft_reg_number'],
                             record_dict['date_of_record'],
                             record_dict['filename'])


def get_block_dict_from_object(block):
    """
    Changes the format of a block allowing it to be JSON serialised
    :param block:   Regular block from a node's chain
    :return:        Block in format suitable for JSON serialisation
    """
    formatted_records = []
    for record in block.records:
        record_data = {
            'aircraft_reg_number': record.aircraft_reg_number,
            'date_of_record': record.date_of_record,
            'filename': record.filename,
            'file_hash': record.file_hash
        }
        formatted_records.append(record_data)

    block_dict = {
        'index': block.index,
        'previous_hash': block.previous_hash,
        'timestamp': block.timestamp,
        'nonce': block.nonce,
        'records': formatted_records,
        'hash': block.hash
    }

    return block_dict


def is_record_valid(record):
    """
    Checks the validity of a record
    :param record:  Record in question
    :return:        True if record is valid, False otherwise
    """
    # TODO: Node might not have file, it will exist on a different machine.
    # if not os.path.exists(record.file_path):
    #     return False
    if not str(record.file_path).split("/")[-1] == record.filename:
        return False
    return True


def maintenance_record_exists(filename):
    file_path = str(chain_utils.get_app_root_directory()) + f"/data/records/unused/{filename}"
    return os.path.exists(file_path)


def path_to_unused_record(filename):
    if maintenance_record_exists(filename):
        return str(chain_utils.get_app_root_directory()) + f"/data/records/unused/{filename}"
    return None


def path_to_record_storage():
    path = str(chain_utils.get_app_root_directory()) + "/data/records/used"
    if os.path.exists(path):
        return path
    else:
        return None


def move_record_file(filename):
    write_file = open(path_to_record_storage() + "/" + filename, 'wb')
    with open(path_to_unused_record(filename), 'rb') as read_file:
        while True:
            data = read_file.read(1024)
            if not data:
                break
            write_file.write(data)


def get_checksum_of_file(file_path):
    # MD5 checksum
    md5_hash = hashlib.md5()

    # Open file as file
    with open(file_path, 'rb') as file:
        while True:
            # Read 1024 bytes
            data = file.read(1024)

            # Reached end of file, no more data to read
            if not data:
                break

            # Update hash with new data
            md5_hash.update(data)
        # Close file when finished
        file.close()

    return md5_hash.hexdigest()



