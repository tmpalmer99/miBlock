import json

from pathlib import Path
from blockchain import block_utils
from blockchain.chain import Blockchain


# A utility function to traverse the chain and return the block with given index
def get_block_by_index(index):
    chain = load_chain_from_storage()
    if len(chain) != 0:
        chain.reverse()
        for block in chain:
            if block["index"] == index:
                return block.utils.get_block_object_from_dict(block)
    return None


# A utility function to traverse the chain and return the block that contains the given filename
def get_block_by_record(record_filename):
    chain = load_chain_from_storage()
    if len(chain) != 0:
        chain.reverse()
        for block in chain:
            for record in block["records"]:
                if record["record_filename"] == record_filename:
                    return block_utils.get_block_object_from_dict(block)
    return None


def load_chain_from_storage():
    app_root_dir = get_app_root_directory()
    try:
        chain = json.load(open(str(app_root_dir) + "/data/blocks.json", "r"))
    except IOError as e:
        print("[INFO] JSON file containing blockchain was not found...")
        return []
    else:
        print("[OK] Blocks were successfully loaded.")
        return chain


# Checks all blocks in the chain are valid
def is_chain_valid(chain):
    previous_hash = ""
    for block in chain:
        block.hash = block.get_block_hash()
        if block.index != 0:
            if block.previous_hash != previous_hash:
                return False
            if not is_block_hash_valid(block_utils.get_block_object_from_dict(block)):
                return False
        previous_hash = block.get_block_hash()
    return True


def is_block_hash_valid(block):
    block_hash = block.get_block_hash()
    if block_hash.startwith('0' * Blockchain.mining_difficulty) and block_hash == block.hash:
        return True
    return False


def get_app_root_directory():
    return Path(__file__).parent.parent
