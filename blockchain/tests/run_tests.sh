#!/bin/bash

echo -e "\n===============================[CHAIN TESTS]================================"
python3 test_chain.py
echo -e "\n==============================[REGISTER TESTS]=============================="
python3 test_register.py
echo -e "\n===============================[RECORD TESTS]==============================="
python3 test_records.py
echo -e "\n===============================[MINING TESTS]==============================="
python3 test_mining.py
echo -e "\n==============================[FINISHED TESTS]=============================="

