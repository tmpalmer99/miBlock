from blockchain import chain_utils


class RecordPool:

    def __init__(self):
        self.unverified_records = []

    def add_record(self, record):
        """
        :param record: Record to be added to the pool of unverified records
        """
        self.unverified_records.append(record)

    def get_unverified_records(self):
        """
        Return a list of at most three unverified records, or
        Return None if no records in record pool.
        """
        records = []

        # Return at most 3 records, unless no records exist in pool
        if self.get_num_unverified_records() >= 3:
            for i in range(3):
                records.append(self.unverified_records[i])
            return records
        elif self.get_num_unverified_records() > 0:
            for i in range(self.get_num_unverified_records()):
                records.append(self.unverified_records[i])
            return records
        else:
            return records

    def get_num_unverified_records(self):
        """
        Return the number of unverified records in record pool
        """
        return len(self.unverified_records)

    def remove_records(self, records):
        """
        Removes a record from record pool once it has been verified
        :param records: List of records to be removed from pool
        :return:       True if record removed, False otherwise
        """
        for record in records:
            if record in self.unverified_records:
                if chain_utils.is_record_verified(record.filename):
                    self.unverified_records.remove(record)
