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
                             record_dict['filename'],
                             record_dict['file_path'])


def get_block_dict_from_object(block):
    """
    Changes the format of a block allowing it to be JSON serialised
    :param block:   Regular block from a node's chain
    :return:        Block in format suitable for JSON serialisation
    """
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
