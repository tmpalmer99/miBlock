import hashlib
import os


class MaintenanceRecord:
    aircraft_reg = None
    date_of_record = None
    record_filename = None
    record_hash = None

    def __init__(self, aircraft_registration_number, date_of_record, filename):
        self.aircraft_reg = aircraft_registration_number
        self.date_of_record = date_of_record
        self.record_filename = filename
        self.record_hash = self.get_file_hash()

    def get_file_hash(self):
        file_hash = hashlib.sha256()
        reading_file = True

        try:

            file = open(f"{os.getcwd()}/{self.record_filename}", "rb")
        except (OSError, IOError) as e:
            print(str(e))
            return

        with file:
            while reading_file:
                data = file.read(4096)
                if data == "":
                    reading_file = False
                else:
                    file_hash.update(data)
        return file_hash
