import json
import os
import logging

from pathlib import Path
from blockchain import block_utils
from json.decoder import JSONDecodeError


def init_logger(name):
    """
    Utility function to initialise a logger, prevents duplicate code in multiple files
    :param name: Name of logger
    :return:     Logger
    """
    # Create logger and set logging level
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Create log file
    logfile = str(get_app_root_directory()) + "/blockchain/logs/node.log"
    handler = logging.FileHandler(logfile)

    # Create logging format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # Add logger handler
    logger.addHandler(handler)

    return logger


def is_record_verified(record_filename):
    """
    A utility function to traverse the chain and return the block that contains the given filename
    :param record_filename: Name of file to lookup
    :return:                True if record has been verified on chain, False otherwise
    """
    chain = load_chain_from_storage()
    for block in chain:
        for record in block.records:
            if record.filename == record_filename:
                return True
    return False


def load_chain_from_storage():
    """
    A utility function to load the chain from storage
    :return: Node's chain from storage
    """
    try:
        # Open file containing node's chain
        chain_file = open(path_to_stored_chain(), "r")

        # Load chain in JSON format
        chain_json = json.load(chain_file)

        # Convert chain to object format
        chain = []
        for block in chain_json:
            chain.append(block_utils.get_block_object_from_dict(block))
    except IOError:
        return []
    except JSONDecodeError:
        return []
    else:
        return chain


def get_app_root_directory():
    """
    Utility function to get the path of the root directory for the application
    :return: Application's root directory
    """
    # Get the directory of this file
    current_directory = Path(__file__).parent

    # Change directory from current directory to app root
    while str(current_directory).split("/")[-1] != 'miBlock':
        current_directory = current_directory.parent
    return current_directory


def generate_data_folder():
    """
    Generates the data folder if accidentally removed
    """
    while str(os.getcwd()).split("/")[-1] != 'miBlock':
        os.chdir("..")
    os.mkdir("data")


def path_to_stored_chain():
    """
    Gets the path to the file that stores a node's chain
    """
    return f"{get_app_root_directory()}/data/blocks.json"


def write_block_to_chain(block):
    """
    Utility function to append block to the stored chain
    :param block: Block to be written to stored chain
    """
    with open(path_to_stored_chain()) as chain_file:
        # Get block in JSON serializable format
        block_dict = block_utils.get_block_dict_from_object(block)

        # Load chain from storage
        chain = json.load(chain_file)

        # Add new block to the chain
        chain.append(block_dict)

        # Close file
        chain_file.close()

        # Write updated chain to storage
        write_chain(get_chain_from_json(chain))


def write_chain(chain):
    """
    Utility function to write chain to storage
    :param chain: Chain to be written
    """
    # Open file and clear it's contents
    chain_file = open(path_to_stored_chain(), "r+")
    chain_file.read().split("\n")
    chain_file.seek(0)
    chain_file.truncate()

    # Write updated chain to storage
    json.dump(get_chain_json(chain), chain_file, sort_keys=True, indent=2)


def get_chain_json(chain):
    """
    Utility function to get a node's chain in JSON format
    :param chain:   Chain in object form
    :return:        Chain in JSON format
    """
    chain_json = []
    # For each block in the chain, append it to a new chain in JSON format
    for block in chain:
        block_json = block_utils.get_block_dict_from_object(block)
        chain_json.append(block_json)
    return chain_json


def get_chain_from_json(chain_json):
    """
    Utility function to get a node's chain in object format
    :param chain_json:  Chain in JSON format
    :return:            Chain in object form
    """
    chain = []
    # For each block in the chain, append it to a new chain in object form
    for block in chain_json:
        block_obj = block_utils.get_block_object_from_dict(block)
        chain.append(block_obj)
    return chain
