import os
import time
import json
from src.blockchain.block import Block
import src.blockchain.block_utils as block_utils
import src.blockchain.chain_utils as chain_utils


class Blockchain:
    chain = []
    blocks_directory = None
    mining_difficulty = 4

    def __init__(self):
        """
        Blockchain class constructor
        """

        self.chain = chain_utils.load_chain_from_storage()
        if len(self.chain) == 0:
            self.init_chain()

    def init_chain(self):
        """
        Initialises the blockchain with genesis block and writes it to a JSON file
        """
        self.generate_genesis_block()
        app_root_dir = chain_utils.get_app_root_directory()
        os.chdir("../..")
        os.mkdir("data")
        blocks_json_file = open(str(app_root_dir) + "/data/blocks.json", "w")
        json.dump(self.chain, blocks_json_file)
        blocks_json_file.close()
        self.chain = chain_utils.load_chain_from_storage()

    def generate_genesis_block(self):
        """
         Generates the genesis block for the blockchain
        """
        print("[DEBUG] Generating new genesis block.")
        genesis_block = Block(0, "0", time.time(), [])
        genesis_block.hash = genesis_block.get_block_hash()
        self.chain.append(genesis_block.__dict__)

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
            if block_hash[0:self.mining_difficulty] is '0' * self.mining_difficulty:
                return block_hash
            else:
                block.nonce += 1

    def last_block_on_chain(self):
        """
        :return: Block at the end of the chain
        """
        return block_utils.get_block_object_from_dict(self.chain[-1])

    def add_block(self, block):
        """
        A method to verify the new block, if block passes verification it can be added to
        the chain.

        :param block:   Solved block to be added to the chain
        :return:        True if block added, False otherwise
        """
        previous_hash = self.last_block_on_chain().hash
        block_hash = block.get_block_hash()

        # Verify correct previous hash exists in block
        if block.previous_hash == previous_hash:
            # Verify the block hash and the proof of work
            if block_hash.startwith('0' * self.mining_difficulty) and block_hash == block.hash:
                self.chain.append(block.__dict__)
                return True
            else:
                return False
        else:
            return False

    def mine(self, records):
        """
        Method allowing a node to verify transactions
        :return: The index of the new block
        """
        last_block = self.last_block_on_chain()

        if records is None:
            return False

        # Initialise new block
        new_block = Block(index=last_block.index + 1,
                          previous_hash=last_block.hash,
                          timestamp=time.time(),
                          records=records)

        # Solve mathematical problem to obtain block hash
        new_block.hash = self.proof_of_work(new_block)

        # Attempt to add the block to the chain
        self.add_block(new_block)
        return new_block.index


blockchain = Blockchain()
