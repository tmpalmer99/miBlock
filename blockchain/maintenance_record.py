import hashlib


class MaintenanceRecord:
    aircraft_reg = None
    date_of_record = None
    record_filename = None
    file_hash = None
    path_to_file = None

    def __init__(self, aircraft_registration_number, date_of_record, filename, file_path):
        self.aircraft_reg = aircraft_registration_number
        self.date_of_record = date_of_record
        self.record_filename = filename
        self.path_to_file = file_path

    def get_file_hash(self):
        """
        Generates a fingerprint of a maintenance record document
        """
        sha256 = hashlib.sha256()

        with open(self.path_to_file, 'rb') as f:
            while True:
                data = f.read(65536)
                if not data:
                    break
                sha256.update(data)

        return sha256.hexdigest()
