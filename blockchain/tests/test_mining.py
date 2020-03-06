import unittest
import requests

unittest.TestLoader.sortTestMethodsUsing = None


class BasicTests(unittest.TestCase):

    def test_mine_one_block(self):
        print("--[TEST 1] Mining one block")
        self.assertEqual(requests.get("http://127.0.0.1:5000/chain").json()['length'], 3)
        self.assertEqual(requests.get("http://127.0.0.1:5001/chain").json()['length'], 3)
        self.assertEqual(requests.get("http://127.0.0.1:5002/chain").json()['length'], 3)

        print("   -- Adding record '1234'")
        record_data = {
            'aircraft_reg_number': '1234',
            'date_of_record': '01/01/2020',
            'filename': 'blocks.json',
            'file_path': '/app/miBlock/data/blocks.json'
        }
        headers = {'Content-Type': 'application/json'}

        response = requests.post("http://127.0.0.1:5001/record", record_data, headers)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(requests.get("http://127.0.0.1:5000/record").json()['length'], 1)
        self.assertEqual(requests.get("http://127.0.0.1:5001/record").json()['length'], 1)
        self.assertEqual(requests.get("http://127.0.0.1:5002/record").json()['length'], 1)

        response = requests.get("http://127.0.0.1:5001/mine")
        self.assertEqual(response.status_code, 200)

        self.assertEqual(requests.get("http://127.0.0.1:5000/chain").json()['length'], 4)
        self.assertEqual(requests.get("http://127.0.0.1:5001/chain").json()['length'], 4)
        self.assertEqual(requests.get("http://127.0.0.1:5002/chain").json()['length'], 4)

        self.assertEqual(requests.get("http://127.0.0.1:5001/record").json()['length'], 0)

    def test_mine_block_with_empty_record_pool(self):
        print("--[TEST 2] Attempting to mine block with empty record pool")
        self.assertEqual(requests.get("http://127.0.0.1:5000/mine").status_code, 400)
        self.assertEqual(requests.get("http://127.0.0.1:5001/mine").status_code, 400)
        self.assertEqual(requests.get("http://127.0.0.1:5002/mine").status_code, 400)



print("Running mining tests...")
if __name__ == "__main__":
    unittest.main()