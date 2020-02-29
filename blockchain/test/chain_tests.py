import os
import json

from blockchain.chain import Blockchain
from blockchain import chain_utils, block_utils


class TerminalColours:
    PASS = '\033[92m'
    FAIL = '\033[91m'
    END = '\033[0m'


def block_hash_test_1():
    print("----------------------------[TEST]---------------------------")
    print("Checking if chain becomes invalid if block hashes are changed")
    print("-------------------------------------------------------------")
    if os.path.exists(chain_utils.path_to_stored_chain()):
        os.remove(chain_utils.path_to_stored_chain())

    blockchain = Blockchain()

    record_file = open(f"{chain_utils.get_app_root_directory()}/blockchain/test/test_data/records.txt", "r+")
    for line in record_file:
        blockchain.record_pool.add_record(json.loads(line))

    blockchain.mine()
    blockchain.mine()

    for block in blockchain.chain:
        if block["index"] == 1:
            block["hash"] = 1

    if not blockchain.is_chain_valid():
        print(f"{TerminalColours.PASS}[PASS] - Invalid chain{TerminalColours.END}")
        for block in blockchain.chain:
            if block["index"] == 1:
                block["hash"] = block_utils.get_block_object_from_dict(block).get_block_hash()
    else:
        print(f"{TerminalColours.FAIL}[FAIL] - Valid chain, should be invalid{TerminalColours.END}")

    if blockchain.is_chain_valid():
        print(f"{TerminalColours.PASS}[PASS] - Valid chain{TerminalColours.END}")
    else:
        print(f"{TerminalColours.FAIL}[FAIL] - Invalid chain, should be valid{TerminalColours.END}")
    print("-------------------------------------------------------------\n")


def block_hash_test_2():
    print("----------------------------[TEST]---------------------------")
    print("Checking if chain becomes invalid if block hashes are changed")
    print("-------------------------------------------------------------")
    if os.path.exists(chain_utils.path_to_stored_chain()):
        os.remove(chain_utils.path_to_stored_chain())

    blockchain = Blockchain()

    record_file = open(f"{chain_utils.get_app_root_directory()}/blockchain/test/test_data/records.txt", "r+")
    for line in record_file:
        blockchain.record_pool.add_record(json.loads(line))

    blockchain.mine()
    blockchain.mine()

    for block in blockchain.chain:
        if block["index"] == 2:
            for record in block["records"]:
                record["record_filename"] = "newfilename.txt"

    if not blockchain.is_chain_valid():
        print(f"{TerminalColours.PASS}[PASS] - Invalid chain{TerminalColours.END}")
        for block in blockchain.chain:
            if block["index"] == 2:
                for record in block["records"]:
                    record["record_filename"] = "test_scripts.py"
    else:
        print(f"{TerminalColours.FAIL}[FAIL] - Valid chain, should be invalid{TerminalColours.END}")

    if blockchain.is_chain_valid():
        print(f"{TerminalColours.PASS}[PASS] - Valid chain{TerminalColours.END}")
    else:
        print(f"{TerminalColours.FAIL}[FAIL] - Invalid chain, should be valid")
    print("-------------------------------------------------------------\n")


def create_block_from_record_pool():
    print("------------------------------[TEST]-----------------------------")
    print("Using record pool to mine blocks and checking records are removed")
    print("-----------------------------------------------------------------")
    if os.path.exists(chain_utils.path_to_stored_chain()):
        os.remove(chain_utils.path_to_stored_chain())

    blockchain = Blockchain()

    record_file = open(f"{chain_utils.get_app_root_directory()}/blockchain/test/test_data/records.txt", "r+")
    for line in record_file:
        blockchain.record_pool.add_record(json.loads(line))

    blockchain.mine()

    if blockchain.is_chain_valid():
        print(f"{TerminalColours.PASS}[PASS] - Valid chain{TerminalColours.END}")
    else:
        print(f"{TerminalColours.FAIL}[FAIL] - Chain not valid{TerminalColours.END}")

    if len(blockchain.record_pool.unverified_records) == 1:
        print(f"{TerminalColours.PASS}[PASS] - Records removed from record pool{TerminalColours.END}")
    else:
        print(f"{TerminalColours.FAIL}[FAIL] - Records not removed from record pool{TerminalColours.END}")
    print("-----------------------------------------------------------------\n")


def create_two_blocks_from_record_pool():
    print("------------------------------[TEST]-----------------------------")
    print("Using record pool to mine blocks and checking records are removed")
    print("-----------------------------------------------------------------")
    if os.path.exists(chain_utils.path_to_stored_chain()):
        os.remove(chain_utils.path_to_stored_chain())

    blockchain = Blockchain()

    record_file = open(f"{chain_utils.get_app_root_directory()}/blockchain/test/test_data/records.txt", "r+")
    for line in record_file:
        blockchain.record_pool.add_record(json.loads(line))

    print("[TEST]: Loaded records - ", blockchain.record_pool.unverified_records)
    blockchain.mine()
    print("[TEST]: Loaded records - ", blockchain.record_pool.unverified_records)
    blockchain.mine()

    if blockchain.is_chain_valid():
        print(f"{TerminalColours.PASS}[PASS] - Valid chain{TerminalColours.END}")
    else:
        print(f"{TerminalColours.FAIL}[FAIL] - Chain not valid{TerminalColours.END}")

    if len(blockchain.record_pool.unverified_records) == 0:
        print(f"{TerminalColours.PASS}[PASS] - Records removed from record pool{TerminalColours.END}")
    else:
        print(f"{TerminalColours.FAIL}[FAIL] - Records not removed from record pool{TerminalColours.END}")
    print("-----------------------------------------------------------------\n")


block_hash_test_1()
block_hash_test_2()
create_block_from_record_pool()
create_two_blocks_from_record_pool()
