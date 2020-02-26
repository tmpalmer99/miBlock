from flask import Flask
from src.blockchain.chain import Blockchain
from src.blockchain.record_pool import RecordPool

app = Flask(__name__)

# Node's copy of blockchain
blockchain = Blockchain()

# Node's copy of the record pool
record_pool = RecordPool()
