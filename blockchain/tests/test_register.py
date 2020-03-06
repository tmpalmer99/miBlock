import unittest
import requests


class BasicTests(unittest.TestCase):

    def test_chain_loads(self):
        """
        Testing that the chain loads properly
        :return:
        """
        print("\n--Load Chain Test", end=" ")
        with self.subTest():
            response = requests.get("http://127.0.0.1:5000/chain")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['length'], 1)

        with self.subTest():
            response = requests.get("http://127.0.0.1:5001/chain")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['length'], 1)

    def test_node_register(self):
        print("\n--Register Node Test", end=" ")
        register_response = requests.post("http://127.0.0.1:5001/node/register?node_address=172.17.0.1:5001")
        self.assertEqual(register_response.status_code, 200)

        node1_response = requests.get("http://127.0.0.1:5000/chain")
        node2_response = requests.get("http://127.0.0.1:5001/chain")
        self.assertEqual(node1_response.json()['peers'][0], '172.17.0.1:5001')
        self.assertEqual(node2_response.json()['peers'][0], '172.17.0.1:5000')

    def test_register_same_node_twice(self):
        print("\n--Register Node Twice Test", end=" ")
        register_response = requests.post("http://127.0.0.1:5001/node/register?node_address=172.17.0.1:5001")
        self.assertEqual(register_response.status_code, 400)


print("Running register tests...")
if __name__ == "__main__":
    unittest.main()
