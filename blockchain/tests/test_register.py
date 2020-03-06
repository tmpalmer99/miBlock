import unittest
import requests
import time

unittest.TestLoader.sortTestMethodsUsing = None


class BasicTests(unittest.TestCase):

    def test_chain_loads(self):
        """
        Testing that the chain loads properly
        :return:
        """
        # time.sleep(600)
        print("--[TEST 1] Load Chain Test")
        with self.subTest():
            response = requests.get("http://127.0.0.1:5000/chain")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['length'], 1)

        with self.subTest():
            response = requests.get("http://127.0.0.1:5001/chain")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['length'], 1)

    def test_node_register(self):
        print("--[TEST 2] Register Node Test")
        register_response = requests.post("http://127.0.0.1:5001/node/register?node_address=172.17.0.1:5001")
        self.assertEqual(register_response.status_code, 200)

        node1_response = requests.get("http://127.0.0.1:5000/chain")
        node2_response = requests.get("http://127.0.0.1:5001/chain")
        self.assertEqual(node1_response.json()['peers'], ['172.17.0.1:5001'])
        self.assertEqual(node2_response.json()['peers'], ['172.17.0.1:5000'])

    def test_register_same_node_twice(self):
        print("--[TEST 3] Register Node Twice Test")
        register_response = requests.post("http://127.0.0.1:5001/node/register?node_address=172.17.0.1:5001")
        self.assertEqual(register_response.status_code, 400)

    def test_register_multiple_nodes(self):
        print("--[TEST 4] Register Multiple Nodes")
        register_response = requests.post("http://127.0.0.1:5002/node/register?node_address=172.17.0.1:5002")
        node1_response = requests.get("http://127.0.0.1:5000/chain")
        node2_response = requests.get("http://127.0.0.1:5001/chain")
        node3_response = requests.get("http://127.0.0.1:5002/chain")
        self.assertEqual(register_response.status_code, 200)
        self.assertEqual(node1_response.json()['peers'], ['172.17.0.1:5001', '172.17.0.1:5002'])
        self.assertEqual(node2_response.json()['peers'], ['172.17.0.1:5000'])
        self.assertEqual(node3_response.json()['peers'], ['172.17.0.1:5001', '172.17.0.1:5000'])

    def test_sync_nodes(self):
        print("--[TEST 5] Sync Nodes Test")
        node_response = requests.get("http://127.0.0.1:5001/chain")
        self.assertEqual(node_response.json()['peers'], ['172.17.0.1:5000'])

        requests.get("http://127.0.0.1:5001/node")

        node_response = requests.get("http://127.0.0.1:5001/chain")
        self.assertEqual(node_response.json()['peers'], ['172.17.0.1:5000', '172.17.0.1:5002'])


print("Running register tests...")
if __name__ == "__main__":
    unittest.main()
