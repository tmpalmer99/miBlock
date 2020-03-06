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
            if block.index == index:
                return block
    return None


# A utility function to traverse the chain and return the block that contains the given filename
def is_record_verified(record_filename):
    chain = load_chain_from_storage()
    for block in chain:
        for record in block.records:
            if record.filename == record_filename:
                return True
    return False


def load_chain_from_storage():
    try:
        chain_file = open(path_to_stored_chain(), "r")
        chain_json = json.load(chain_file)
        chain = []
        for block in chain_json:
            chain.append(block_utils.get_block_object_from_dict(block))
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
    print(f"[DEBUG] - Writing block with index {block.index}.")
    with open(path_to_stored_chain()) as chain_file:
        block_dict = block_utils.get_block_dict_from_object(block)
        chain = json.load(chain_file)
        chain.append(block_dict)
        chain_file.close()
    with open(path_to_stored_chain(), "r+") as chain_file:
        json.dump(chain, chain_file, sort_keys=True, indent=2)
    print(f"[DEBUG] - Block Successfully Written...")


def get_chain_json(chain):
    chain_json = []
    for block in chain:
        block_json = block_utils.get_block_dict_from_object(block)
        chain_json.append(block_json)
    return chain_json


def get_chain_from_json(chain_json):
    chain = []
    for block in chain_json:
        block_obj = block_utils.get_block_object_from_dict(block)
        chain.append(block_obj)
    return chain
