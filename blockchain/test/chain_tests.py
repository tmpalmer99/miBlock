import os
import json

from blockchain.chain import Blockchain
from blockchain.record_pool import RecordPool
from blockchain import chain_utils, block_utils


def block_hash_test_1():
    print("[TEST] - Checking if chain becomes invalid if block hashes are changed")
    for block in blockchain.chain:
        if block["index"] == 4:
            block["hash"] = 1

    print(blockchain.chain)
    if not blockchain.is_chain_valid():
        print("[TEST] - Success, invalid chain")
        for block in blockchain.chain:
            if block["index"] == 4:
                block["hash"] = block_utils.get_block_object_from_dict(block).get_block_hash()
    if blockchain.is_chain_valid():
        print("[TEST] - Success, valid chain")


def block_hash_test_2():
    print("[TEST] - Checking if chain becomes invalid if block hashes are changed")
    for block in blockchain.chain:
        if block["index"] == 3:
            for record in block["records"]:
                record["record_filename"] = "newfilename.txt"

    print(blockchain.chain)
    if not blockchain.is_chain_valid():
        print("[TEST] - Success, invalid chain")
        for block in blockchain.chain:
            if block["index"] == 3:
                for record in block["records"]:
                    record["record_filename"] = "test_scripts.py"
    if blockchain.is_chain_valid():
        print("[TEST] - Success, valid chain")


def create_block_from_record_pool():
    records = []
    record_file = open(f"{chain_utils.get_app_root_directory()}/blockchain/test/test_data/records.txt", "r+")
    for line in record_file:
        blockchain.add_record_to_pool(json.loads(line))
    print("[TEST]: Loaded records - ", records)

    blockchain.mine()
    if blockchain.is_chain_valid():
        print("[TEST] - Success")
    else:
        print("[TEST] - Fail, chain not valid")

    if len(blockchain.record_pool.unverified_records) == 1:
        print("[TEST] - Success")
    else:
        print("[TEST] - Fail, records not removed")


def create_two_blocks_from_record_pool():
    records = []
    record_file = open(f"{chain_utils.get_app_root_directory()}/blockchain/test/test_data/records.txt", "r+")
    for line in record_file:
        blockchain.add_record_to_pool(json.loads(line))
    print("[TEST]: Loaded records - ", records)

    blockchain.mine()
    blockchain.mine()

    if blockchain.is_chain_valid():
        print("[TEST] - Success")
    else:
        print("[TEST] - Fail, chain not valid")

    if len(blockchain.record_pool.unverified_records) == 0:
        print("[TEST] - Success")
    else:
        print("[TEST] - Fail, records not removed")


blockchain = Blockchain()
block_hash_test_1()
block_hash_test_2()
# create_block_from_record_pool()
# create_two_blocks_from_record_pool()
