import unittest
import requests

unittest.TestLoader.sortTestMethodsUsing = None


class BasicTests(unittest.TestCase):


    def test_add_five_records(self):
        print("--[TEST 1] Add and broadcast five new records")
        for i in range(1,6):
            print(f"   -- Adding record {i}")
            record_data = {
                'aircraft_reg_number': i,
                'date_of_record': '01/01/2020',
                'filename': 'blocks.json',
                'file_path': '/app/miBlock/data/blocks.json'
            }
            headers = {'Content-Type': 'application/json'}

            response = requests.post("http://127.0.0.1:5000/record", record_data, headers)
            self.assertEqual(response.status_code, 200)

            node1_response = requests.get("http://127.0.0.1:5000/record")
            node2_response = requests.get("http://127.0.0.1:5001/record")
            node3_response = requests.get("http://127.0.0.1:5002/record")
            print(f"      -- Checking that {i} record/s are present in pool")
            self.assertEqual(node1_response.json()['length'], i)
            self.assertEqual(node2_response.json()['length'], i)
            self.assertEqual(node3_response.json()['length'], i)
            self.assertEqual(node1_response.json()['records'][i-1]['aircraft_reg_number'], str(i))

    def test_remove_records(self):
        print("--[TEST 2] Testing records are removed from pool when verified")

        response = requests.get("http://127.0.0.1:5000/record")
        self.assertEqual(response.json()['length'], 5)

        requests.get("http://127.0.0.1:5000/mine")

        response = requests.get("http://127.0.0.1:5000/record")
        self.assertEqual(response.json()['length'], 2)

        requests.get("http://127.0.0.1:5000/mine")

        response = requests.get("http://127.0.0.1:5000/record")
        self.assertEqual(response.json()['length'], 0)

        # No records, so mining should result in bad request
        response = requests.get("http://127.0.0.1:5000/mine")
        self.assertEqual(response.status_code, 400)

    def test_sync_removed_records(self):
        print("--[TEST 3] Checking synchronisation of record pools")
        self.assertEqual(requests.get("http://127.0.0.1:5001/record").json()['length'], 0)
        self.assertEqual(requests.get("http://127.0.0.1:5002/record").json()['length'], 0)

        response = requests.get("http://127.0.0.1:5001/mine")
        self.assertEqual(response.status_code, 400)

        response = requests.get("http://127.0.0.1:5002/mine")
        self.assertEqual(response.status_code, 400)


print("Running record tests...")
if __name__ == "__main__":
    unittest.main()