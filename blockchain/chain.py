import os
import time
import json

from blockchain.block import Block
from blockchain.record_pool import RecordPool
from blockchain import chain_utils, block_utils


class Blockchain:
    chain = []
    mining_difficulty = 4

    def __init__(self):
        """
        Blockchain class constructor
        """
        self.record_pool = RecordPool()
        self.chain = chain_utils.load_chain_from_storage()
        if len(self.chain) == 0:
            self.init_chain()

    def init_chain(self):
        """
        Initialises the blockchain with genesis block and writes it to a JSON file
        """
        self.generate_genesis_block()
        app_root_dir = chain_utils.get_app_root_directory()
        if not os.path.exists(f"{app_root_dir}/data"):
            chain_utils.generate_data_folder()
        blocks_json_file = open(f"{app_root_dir}/data/blocks.json", "w")
        chain_json = chain_utils.get_chain_json(self.chain)
        json.dump(chain_json, blocks_json_file, sort_keys=True, indent=2)
        blocks_json_file.close()
        self.chain = chain_utils.load_chain_from_storage()

    def generate_genesis_block(self):
        """
         Generates the genesis block for the blockchain
        """
        print("[DEBUG] Generating new genesis block.")
        genesis_block = Block(0, "0", time.time(), [])
        genesis_block.hash = genesis_block.get_block_hash()
        self.chain.append(genesis_block)

    def proof_of_work(self, block):
        """
        Proof of work consensus algorithm, a mathematical problem that requires computational
        power to solve
        """
        block.nonce = 0
        solved = False

        # Increment nonce until valid hash is found
        while not solved:
            block_hash = block.get_block_hash()
            if block_hash[0:self.mining_difficulty] == '0' * self.mining_difficulty:
                return block_hash
            else:
                block.nonce += 1

    def last_block_on_chain(self):
        """
        :return: Block at the end of the chain
        """
        return self.chain[-1]

    def add_block(self, block):
        """
        A method to verify the new block, if block passes verification it can be added to
        the chain.

        :param block:   Solved block to be added to the chain
        :return:        True if block added, False otherwise
        """
        last_block = self.last_block_on_chain()
        previous_hash = last_block.hash

        # Verify correct previous hash exists in block
        if block.previous_hash == previous_hash:
            # Verify the block hash and the proof of work
            if self.is_block_hash_valid(block):
                chain_utils.write_block_to_chain(block)
                self.chain.append(block)
                return self.is_chain_valid()
            else:
                return False
        else:
            return False

    def mine(self):
        """
        Method allowing a node to verify transactions
        :return: The index of the new block
        """
        records = self.record_pool.get_unverified_records()
        last_block = self.last_block_on_chain()

        if len(records) == 0:
            return None

        # Initialise new block
        new_block = Block(index=last_block.index + 1,
                          previous_hash=last_block.hash,
                          timestamp=time.time(),
                          records=records)

        # Solve mathematical problem to obtain block hash
        new_block.hash = self.proof_of_work(new_block)

        # Attempt to add the block to the chain
        if self.add_block(new_block):
            self.record_pool.remove_records(records)
            return new_block
        else:
            return None

    def is_block_hash_valid(self, block):
        block_hash = block.get_block_hash()
        if block_hash.startswith('0' * self.mining_difficulty) and block_hash == block.hash:
            return True
        return False

    # Checks all blocks in the chain are valid
    def is_chain_valid(self):
        previous_hash = ""
        for block in self.chain:
            if block.index != 0:
                if block.previous_hash != previous_hash:
                    return False
                if not self.is_block_hash_valid(block):
                    return False
            previous_hash = block.get_block_hash()
        return True
