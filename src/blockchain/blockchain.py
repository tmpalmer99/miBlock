import time
import os
import json
from src.blockchain.block import Block


class Blockchain:
    chain = []
    blocks_directory = None

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


blockchain = Blockchain()
