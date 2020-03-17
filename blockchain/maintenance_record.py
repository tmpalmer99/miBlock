import hashlib


from blockchain import block_utils


class MaintenanceRecord:
    aircraft_reg_number = None
    date_of_record = None
    filename = None
    file_hash = None
    file_path = None

    def __init__(self, aircraft_reg_number, date_of_record, filename):
        self.aircraft_reg_number = aircraft_reg_number
        self.date_of_record = date_of_record
        self.filename = filename
        self.file_path = block_utils.path_to_unused_record(self.filename)
        self.file_hash = self.get_file_hash()

    def get_file_hash(self):
        """
        Generates a fingerprint of a maintenance record document
        """
        sha256 = hashlib.sha256()

        with open(self.file_path, 'rb') as f:
            while True:
                data = f.read(65536)
                if not data:
                    break
                sha256.update(data)

        return sha256.hexdigest()
