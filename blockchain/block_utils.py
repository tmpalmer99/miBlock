import os

from blockchain.block import Block


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
    # Todo Records may need to be converted from dict representation
    records = block_dict["records"]
    block_hash = block_dict["hash"]

    block = Block(index, previous_hash, timestamp, records, nonce)
    block.hash = block_hash
    return block


def is_record_valid(record):
    if not os.path.exists(record.file_path):
        return False
    if not str(record.file_path).split("/")[-1] != record.filename:
        return False
    return True


