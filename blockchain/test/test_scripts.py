import os
import json
import datetime

from blockchain.maintenance_record import MaintenanceRecord


def create_test_records():
    records = []
    print("Creating psuedo-records")
    if not os.path.exists(f"{os.getcwd()}/test_data"):
        os.mkdir("test_data")
    record_file = open(f"{os.getcwd()}/test_data/records.txt", "w")

    record1 = MaintenanceRecord("1234", str(datetime.datetime.now()), "test_scripts.py", __file__)
    record1.file_hash = record1.get_file_hash()
    records.append(record1.__dict__)

    record2 = MaintenanceRecord("3456", str(datetime.datetime.now()), "test_scripts.py", __file__)
    record2.file_hash = record1.get_file_hash()
    records.append(record2.__dict__)

    record3 = MaintenanceRecord("789", str(datetime.datetime.now()), "test_scripts.py", __file__)
    record3.file_hash = record1.get_file_hash()
    records.append(record3.__dict__)

    record4 = MaintenanceRecord("3912", str(datetime.datetime.now()), "test_scripts.py", __file__)
    record4.file_hash = record1.get_file_hash()
    records.append(record4.__dict__)

    for record in records:
        json.dump(record, record_file)
        record_file.write("\n")
    record_file.close()
    print(records)


create_test_records()
