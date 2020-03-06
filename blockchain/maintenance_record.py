import hashlib


class MaintenanceRecord:
    aircraft_reg_number = None
    date_of_record = None
    filename = None
    file_hash = None
    file_path = None

    def __init__(self, aircraft_reg_number, date_of_record, filename, file_path):
        self.aircraft_reg_number = aircraft_reg_number
        self.date_of_record = date_of_record
        self.filename = filename
        self.file_path = file_path
        # TODO: Need to wait for chord implementation before hashes can be computed, Some computers wont store the file
        #       so can't get it's record, Need a get file hash from node with file method to check hashes
        # self.file_hash = self.get_file_hash()

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
