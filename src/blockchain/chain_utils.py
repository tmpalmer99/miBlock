import src.blockchain.block_utils as b_utils
from pathlib import Path
import json
import os


# A utility function to traverse the chain and return the block with given index
def get_block_by_index(index):
    chain = load_chain_from_storage()
    if len(chain) != 0:
        chain.reverse()
        for block in chain:
            if block["index"] == index:
                return b_utils.get_block_object_from_dict(block)
    return None


# A utility function to traverse the chain and return the block that contains the given filename
def get_block_by_record(record_filename):
    chain = load_chain_from_storage()
    if len(chain) != 0:
        chain.reverse()
        for block in chain:
            for record in block["records"]:
                if record["record_filename"] == record_filename:
                    return b_utils.get_block_object_from_dict(block)
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
        print(chain)
        return chain


def get_app_root_directory():
    return Path(__file__).parent.parent.parent
