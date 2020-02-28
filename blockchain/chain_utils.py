import json
import os

from pathlib import Path
from blockchain import block_utils
from json.decoder import JSONDecodeError


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
    try:
        chain_file = open(path_to_stored_chain(), "r")
        chain = json.load(chain_file)
    except IOError:
        print("[INFO] JSON file containing blockchain was not found...")
        return []
    except JSONDecodeError:
        print("[INFO] JSON file containing blockchain was not found...")
        return []
    else:
        return chain


def get_app_root_directory():
    current_directory = Path(__file__).parent
    while str(current_directory).split("/")[-1] != 'miBlock':
        current_directory = current_directory.parent
    return current_directory


def generate_data_folder():
    while str(os.getcwd()).split("/")[-1] != 'miBlock':
        os.chdir("..")
    os.mkdir("data")


def path_to_stored_chain():
    return f"{get_app_root_directory()}/data/blocks.json"


def write_block_to_chain(block):
    print(f"[DEBUG]: Writing block with index {block.index}.")
    with open(path_to_stored_chain()) as chain_file:
        chain = json.load(chain_file)
    chain.append(block.__dict__)
    chain_file.close()
    with open(path_to_stored_chain(), "r+") as chain_file:
        json.dump(chain, chain_file)
