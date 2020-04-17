import os
import time
import json

from blockchain.block import Block
from blockchain.record_pool import RecordPool
from blockchain import chain_utils

# Create logger
logger = chain_utils.init_logger("Chain")


class Blockchain:
    chain = []
    mining_difficulty = 4

    def __init__(self):
        """
        Blockchain class constructor
        """
        logger.info("Initialising node's chain")
        self.record_pool = RecordPool()
        self.chain = chain_utils.load_chain_from_storage()
        if len(self.chain) == 0:
            self.init_chain()

    def init_chain(self):
        """
        Initialises the blockchain with genesis block and writes it to a JSON file
        """
        logger.info("Generating genesis block...")
        self.generate_genesis_block()

        app_root_dir = chain_utils.get_app_root_directory()
        if not os.path.exists(f"{app_root_dir}/data"):
            chain_utils.generate_data_folder()

        logger.info("Generating blocks.json...")
        blocks_json_file = open(f"{app_root_dir}/data/blocks.json", "w")
        chain_json = chain_utils.get_chain_json(self.chain)
        json.dump(chain_json, blocks_json_file, sort_keys=True, indent=2)
        blocks_json_file.close()
        self.chain = chain_utils.load_chain_from_storage()

    def generate_genesis_block(self):
        """
         Generates the genesis block for the blockchain
        """
        genesis_block = Block(0, "0", time.time(), [])
        genesis_block.hash = genesis_block.get_block_hash()
        self.chain.append(genesis_block)

    def proof_of_work(self, block):
        """
        Proof of work consensus algorithm, a mathematical problem that requires computational
        power to solve
        """
        logger.info(f"Starting proof of work for block with index '{block.index}'")
        block.nonce = 0
        solved = False

        # Increment nonce until valid hash is found
        while not solved:
            block_hash = block.get_block_hash()
            if block_hash[0:self.mining_difficulty] == '0' * self.mining_difficulty:
                logger.info(f"Block solved with a hash '{block_hash}'")
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
        logger.info(f"Adding block with index '{block.index}'")
        last_block = self.last_block_on_chain()
        previous_hash = last_block.hash

        # Verify correct previous hash exists in block
        if block.previous_hash == previous_hash:
            # Verify the block hash and the proof of work
            if self.is_block_hash_valid(block):
                chain_utils.write_block_to_chain(block)
                self.chain.append(block)
                logger.info(f"Added block")
                return self.is_chain_valid()
            else:
                logger.error(f"Block not added - block hash not valid")
                return False
        else:
            logger.error(f"Block not added - previous hash not valid")
            return False

    def mine(self):
        """
        Method allowing a node to verify transactions
        :return: The index of the new block
        """
        logger.info("Mining new block")
        for block in self.chain:
            self.record_pool.remove_records(block.records)

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
        """
        Checks the validity of a block's hash
        :param block:   The block in question
        :return:        True if block hash is valid, False otherwise
        """
        block_hash = block.get_block_hash()
        if block_hash.startswith('0' * self.mining_difficulty) and block_hash == block.hash:
            return True
        return False

    def is_chain_valid(self):
        """
        Checks the validity of a node's chain
        :return: True if node's chain is valid, False otherwise
        """
        previous_hash = ""
        # Check hashes are valid for each block in chain
        for block in self.chain:
            if block.index != 0:
                # Check previous block's data is unchanged
                if block.previous_hash != previous_hash:
                    return False
                # Check block's data is unchanged
                if not self.is_block_hash_valid(block):
                    return False
            previous_hash = block.get_block_hash()
        return True


    def is_record_valid(self, file_hash, filename):
        previous_hash = ""
        for block in self.chain:
            for record in block.records:
                if record.filename == filename and file_hash == record.file_hash:
                    if block.previous_hash == previous_hash and self.is_block_hash_valid(block):
                        return True
            previous_hash = block.get_block_hash()
        return False