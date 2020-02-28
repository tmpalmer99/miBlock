import os
import datetime

from blockchain.maintenance_record import MaintenanceRecord


def create_test_records():
    records = []
    if not os.path.exists(f"{os.getcwd()}/test_data"):
        os.mkdir("test_data")
    record_file = open(f"{os.getcwd()}/test_data/records.txt", "r+")
    record1 = MaintenanceRecord("1234", datetime.datetime.now(), "test_scripts.py", __file__)
    records.append(record1)
    record2 = MaintenanceRecord("3456", datetime.datetime.now(), "test_scripts.py", __file__)
    records.append(record2)
    record3 = MaintenanceRecord("789", datetime.datetime.now(), "test_scripts.py", __file__)
    records.append(record3)
    record4 = MaintenanceRecord("3912", datetime.datetime.now(), "test_scripts.py", __file__)
    records.append(record4)

    print(records)

create_test_records()
