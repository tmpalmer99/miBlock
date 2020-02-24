import time
import os
import json
from src.blockchain.block import Block
from src.blockchain.block_utils import get_block_object_from_dict


class Blockchain:
    chain = []
    blocks_directory = None
    mining_difficulty = 4

    def __init__(self):
        """
        Blockchain class constructor
        """

        app_root_dir = os.path.abspath(os.curdir + "/../..")
        print("[DEBUG] Attempting to load blocks...")

        # Checks if the 'blocks' directory exists under the app's root directory
        if os.path.exists(f"{app_root_dir}/blocks"):
            self.blocks_directory = os.path.abspath(app_root_dir + "/blocks")
            # JSON file containing chain does not exists if 'load_chain()' returns false, so initialise one
            if not self.load_chain():
                self.init_chain()
        else:
            # If blocks directory does not exist, chain does not exist so initialise one.
            print("[DEBUG] Generating new blockchain, will need to be synced.")
            os.chdir("../..")
            os.mkdir("blocks")
            self.blocks_directory = app_root_dir + "/blocks"
            self.init_chain()

    def init_chain(self):
        """
        Initialises the blockchain with genesis block and writes it to a JSON file
        """
        self.generate_genesis_block()
        blocks_json_file = open(self.blocks_directory + "/blocks.json", "w")
        json.dump(self.chain, blocks_json_file)
        blocks_json_file.close()
        self.load_chain()

    def load_chain(self):
        """
        Loads a JSON file that stores that state of the blockchain

        :return: True if chain successfully loaded, False otherwise.
        """
        try:
            self.chain = json.load(open(self.blocks_directory + "/blocks.json", "r"))
        except IOError as e:
            return False
        else:
            print("[OK] Blocks were successfully loaded.")
            print(self.chain)
            return True

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

    def most_recent_block(self):
        """
        :return: Block at the end of the chain
        """
        return get_block_object_from_dict(self.chain[-1])

    def add_block(self, block):
        """
        A method to verify the new block, if block passes verification it can be added to
        the chain.

        :param block:   Solved block to be added to the chain
        :return:        True if block added, False otherwise
        """
        previous_hash = self.most_recent_block().hash
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
        last_block = self.most_recent_block()

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
