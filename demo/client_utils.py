class colours:
    COMMAND = '\033[94m'
    ENDCOLOUR = '\033[0m'
    SUCCESS = '\033[92m'
    ERROR = '\033[91m'
    UNDERLINE = '\033[4m'


def print_chain(chain):
    for block in chain:
        print(f"--=[{colours.UNDERLINE}{colours.COMMAND}Block {block.index}{colours.ENDCOLOUR}]=--")
        print("  |-- Previous Hash:", block.previous_hash)
        print("  |-- Timestamp:", block.timestamp)
        print("  |-- Nonce:", block.nonce)
        print("  |-- Block Hash:", block.hash)
        print("  +-- Records")

        if len(block.records) == 0:
            print("      +-- This block has no records")
        else:
            record_count = 1
            for record in block.records:
                print("     +-- Record", record_count)
                print("         |-- Aircraft Registration Number:", record.aircraft_reg_number)
                print("         |-- Filename:", record.filename)
                print("         |-- Date of Record:", record.date_of_record)
                print("         +-- File hash:", record.file_hash)
                record_count += 1


def print_records(records):
    record_count = 1
    for record in records:
        print("-- Record", record_count)
        print("   |-- Aircraft Registration Number:", record.aircraft_reg_number)
        print("   |-- Filename:", record.filename)
        print("   |-- Date of Record:", record.date_of_record)
        print("   +-- File hash:", record.file_hash)
        record_count += 1
