from flask import Flask
from blockchain.chain import Blockchain
from blockchain.record_pool import RecordPool

app = Flask(__name__)

# Node's copy of blockchain
blockchain = Blockchain()

# Node's copy of the record pool
record_pool = RecordPool()
