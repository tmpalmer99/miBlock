import unittest
import requests


class BasicTests(unittest.TestCase):

    def test_chain_loads(self):
        with self.subTest():
            response = requests.get("http://127.0.0.1:5000/chain")
            self.assertEqual(response.status_code, 200)

        with self.subTest():
            response = requests.get("http://127.0.0.1:5001/chain")
            self.assertEqual(response.status_code, 200)


print("Running chain tests...")
if __name__ == "__main__":
    unittest.main()