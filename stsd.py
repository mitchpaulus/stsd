import math
import heapq
from collections import defaultdict, Counter
from typing import Optional
import sys
import mputils
import datetime
import os

huffman_bytes_for_bytes = 2
version_size_bytes = 2
page_size_size_bytes = 2
init_year_size_bytes = 2
num_day_entries_pages_size_bytes = 4
num_trends_pages_size_bytes = 4
num_index_pages_size_bytes = 4
num_data_pages_size_bytes = 4

page_size = 4096

trend_name_size_bytes = 124  # Bytes
trend_id_size_bytes = 4  # Bytes


class DataIndex:
    def __init__(self, trend_id: int, page_index: int, start_day: int, end_day: int) -> None:
        self.trend_id = trend_id
        self.page_index = page_index
        self.start_day = start_day
        self.end_day = end_day


def init(filepath):
    # Fail if file already exists
    with open(filepath, 'xb') as file:
        # Write initial configuration
        # 1. 2 byte: version number (0 - 2)
        # 2. 2 byte: page size in bytes (2 - 4)
        # 3. 2 byte: Initial year (default 2000) (4 - 6)
        # 4. 4 byte: number of day entries pages (6 - 10)
        # 5. 4 byte: number of trends pages (10 - 14)
        # 6. 4 byte: number of Index pages (14 - 18)
        # 6. 4 byte: number of Data pages (18 - 22)
        version = 1
        initial_year = 2000
        num_day_entries_pages = 0
        num_trends_pages = 0
        num_index_pages = 0
        num_data_pages = 0

        to_write = [
            (version, version_size_bytes),
            (page_size, page_size_size_bytes),
            (initial_year, init_year_size_bytes),
            (num_day_entries_pages, num_day_entries_pages_size_bytes),
            (num_trends_pages, num_trends_pages_size_bytes),
            (num_index_pages, num_index_pages_size_bytes),
            (num_data_pages, num_data_pages_size_bytes),
        ]

        for value, num_bytes in to_write:
            file.write(value.to_bytes(num_bytes, 'big'))

        # Write null bytes to fill the rest of the page
        file.write(b'\x00' * (page_size - sum([x[1] for x in to_write])))


def write_int(filepath, value: int, pos: int, num_bytes: int):
    with open(filepath, 'rb+') as file:
        file.seek(pos)
        file.write(value.to_bytes(num_bytes, 'big'))


def update_num_trend_pages(filepath, num_trends: int):
    write_int(filepath, num_trends, 10, 4)


def update_num_index_pages(filepath, num_indexes: int):
    write_int(filepath, num_indexes, 14, 4)


def update_num_data_pages(filepath, num_data: int):
    write_int(filepath, num_data, 18, 4)


def insert_blank_pages(filepath, page_index: int, num_pages: int):
    # Write to temp file, then do os.rename
    temp_filepath = filepath + ".tmp"

    with open(temp_filepath, 'xb') as temp_file:
        with open(filepath, 'rb') as file:
            # Copy the first page_index pages
            temp_file.write(file.read(page_index * page_size))
            # Write the new pages
            temp_file.write(b'\x00' * (page_size * num_pages))
            # Copy the rest of the file
            temp_file.write(file.read())

    os.replace(temp_filepath, filepath)


def print_summary(filepath):
    with open(filepath, 'rb') as file:
        configurations = file.read(18)

    page_size = int.from_bytes(configurations[2:4], 'big')
    init_year = int.from_bytes(configurations[4:6], 'big')
    num_day_entries_pages = int.from_bytes(configurations[6:10], 'big')
    num_trends_pages = int.from_bytes(configurations[10:14], 'big')
    num_index_pages = int.from_bytes(configurations[14:18], 'big')
    num_data_pages = int.from_bytes(configurations[18:22], 'big')

    file_size = os.path.getsize(filepath)
    total_num_pages = file_size // page_size
    print(f"Page size: {page_size} bytes")
    print(f"Initial year: {init_year}")
    print(f"Number of day entries pages: {num_day_entries_pages}")
    print(f"Number of trends pages: {num_trends_pages}")
    print(f"Number of index pages: {num_index_pages}")
    print(f"Number of data pages: {num_data_pages}")
    print(f"Total number of pages: {total_num_pages}")
    print(f"Total size: {file_size} bytes")


def write_data(filepath, trend_name: str, values: list[tuple[datetime.datetime, str]]):
    # Read first 4096 bytes to get the configuration
    with open(filepath, 'rb+') as file:
        configurations = file.read(18)

        page_size = int.from_bytes(configurations[2:4], 'big')
        init_year = int.from_bytes(configurations[4:6], 'big')
        num_day_entries_pages = int.from_bytes(configurations[6:10], 'big')
        num_trends_pages = int.from_bytes(configurations[10:14], 'big')
        num_index_pages = int.from_bytes(configurations[14:18], 'big')

        total_size = page_size * (num_day_entries_pages + num_trends_pages + num_index_pages)

        init_nd_date = mputils.fixed_from_gregorian(init_year, 1, 1)

        file.seek(page_size)

        # Read all the index pages
        all_index_pages = file.read(total_size)
        curr_pos = 0

        trend_pages = []
        for _ in range(num_trends_pages):
            trend_pages.append(all_index_pages[curr_pos:curr_pos + page_size])
            curr_pos += page_size

        # Check if we need a new trend page
        trends: dict[str, int] = read_trend_pages(trend_pages)
        if trend_name in trends:
            trend_id = trends[trend_name]
        else:
            trend_id = max(trends.values(), default=0) + 1
            num_trends = len(trends)

            if (num_trends + 1) * (trend_name_size_bytes + trend_id_size_bytes) >= num_trends_pages * page_size:
                file.close()
                insert_blank_pages(filepath, 1 + num_trends_pages, 1)
                update_num_trend_pages(filepath, num_trends_pages + 1)
                # Recursively start over
                write_data(filepath, trend_name, values)
                return

        day_entry_pages = []
        for _ in range(num_day_entries_pages):
            day_entry_pages.append(all_index_pages[curr_pos:curr_pos + page_size])
            curr_pos += page_size

        index_page_start_pos = curr_pos
        index_pages_bytes: list[bytes] = []
        for _ in range(num_index_pages):
            index_pages_bytes.append(all_index_pages[curr_pos:curr_pos + page_size])
            curr_pos += page_size

        data_page_start_pos = curr_pos

        # A list of (id, 180 byte day entry)
        day_entries: list[tuple[int, list[int]]] = [(idx, day) for idx, day in
                                                    enumerate(read_day_entry_pages(day_entry_pages))]
        day_entries.sort(key=lambda x: x[1])

        indexes: list[DataIndex] = read_index_page(index_pages_bytes)

        indexes_for_trend: list[DataIndex] = [x for x in indexes if x.trend_id == trends[trend_name]]

        # Group data by day
        day_grouped: dict[datetime.date, list[tuple[datetime.datetime, str]]] = mputils.groupby(values,
                                                                                                lambda x: x[0].date())

        day_entries_to_add = []

        for day in day_grouped:
            # day is datetime.date
            # Get the day entry for the day
            day_type = to_day_entry([x[0] for x in day_grouped[day]])
            day_index: Optional[int] = match_day_entry(day_entries, day_type)

            if day_index is None:
                # Add a new day entry
                day_entries_to_add.append((len(day_entries) + len(day_entries_to_add), day_type))

            # toordinal, Jan 1, Year 1, is 1.
            day_id = day.toordinal() - init_nd_date + 1

            encoded_values = encode_day_values([x[1] for x in day_grouped[day]])

            if len(encoded_values) > page_size:
                raise ValueError("Encoded values too large")

            # Find the best index page to write to.
            index_pages = []
            latest_index: Optional[DataIndex] = None
            for index in indexes_for_trend:
                if day_id > index.end_day and (
                        latest_index is None or day_id - index.end_day < day_id - latest_index.end_day):
                    latest_index = index

                if index.start_day <= day.toordinal() - init_nd_date + 1 <= index.end_day:
                    index_pages.append(index)
                    break

            if not index_pages:
                # Try to see if it fits into latest existing page
                if latest_index is not None:
                    data_page_start = data_page_start_pos + latest_index.page_index * page_size
                    file.seek(data_page_start)
                    # Read first two bytes
                    bytes_taken = int.from_bytes(file.read(2), 'big')

                    if bytes_taken + len(encoded_values) < page_size:
                        # It fits
                        # First write the number of bytes taken
                        file.seek(data_page_start)
                        file.write((bytes_taken + len(encoded_values)).to_bytes(2, 'big'))
                        # Then move to end and write new data
                        file.seek(data_page_start + bytes_taken)
                        file.write(bytes(encoded_values))

                else:
                    # Write the new index page info
                    if len(indexes) * 12 + 12 >= num_index_pages * page_size:
                        file.close()
                        insert_blank_pages(filepath, 1 + num_trends_pages + num_day_entries_pages + num_index_pages, 1)
                        update_num_index_pages(filepath, num_index_pages + 1)
                        # Recursively start over
                        write_data(filepath, trend_name, values)
                        return

                    file.seek(index_page_start_pos + len(indexes) * 12)
                    file.write(trend_id.to_bytes(4, 'big'))
                    file.write(num_index_pages.to_bytes(4, 'big'))
                    file.write(day_id.to_bytes(2, 'big'))
                    file.write(day_id.to_bytes(2, 'big'))
                    indexes_for_trend.append(DataIndex(trend_id, num_index_pages, day_id, day_id))
                    indexes.append(DataIndex(trend_id, num_index_pages, day_id, day_id))

                    # Write the new data page
                    file.seek(data_page_start_pos + num_index_pages * page_size)
                    file.write(len(encoded_values).to_bytes(2, 'big'))
                    file.write(bytes(encoded_values))
            else:
                # We need to insert/overwrite the data in the existing page
                raise ValueError("Not implemented yet")


def to_day_entry(datetime_values: list[datetime.datetime]) -> list[int]:
    # Convert the datetime values to a list of 1s and 0s
    day_values = [0] * (1440 // 8)

    for dt in datetime_values:
        minute = dt.hour * 60 + dt.minute
        day_values[minute // 8] |= 1 << (minute % 8)

    return day_values


def day_compare(day1: list[int], day2: list[int]) -> int:
    # Return 0 if the days are equal, -1 if day1 < day2, 1 if day1 > day2
    index = 0

    while index < len(day1) and index < len(day2):
        if day1[index] < day2[index]:
            return -1
        elif day1[index] > day2[index]:
            return 1
        index += 1

    if len(day1) < len(day2):
        return -1
    elif len(day1) > len(day2):
        return 1
    else:
        return 0


def match_day_entry(day_entries: list[tuple[int, list[int]]], day_times: list[int]) -> Optional[int]:
    # list[int] represents the byte array where each bit is a minute of the day
    # day_times is a list of datetime objects
    L = 0
    R = len(day_entries) - 1

    while L <= R:
        m = math.floor((L + R) / 2)
        test_entry = day_entries[m][1]

        if day_compare(test_entry, day_times) < 0:
            L = m + 1
        elif day_compare(test_entry, day_times) > 0:
            R = m - 1
        else:
            return test_entry[0]

    return None


def read_day_entry_pages(pages: list[bytes]) -> list[list[int]]:
    # 1. For each day entry:
    # - 1 byte: non-zero byte to indicate following 180 bits are good
    # - 180 bytes: day format. Bit string of 1440 bits, 1 for each minute of the day.
    # - Null filled after the last day entry
    day_entries = []
    for page in pages:
        pos_in_page = 0
        while pos_in_page < len(page):
            if page[pos_in_page] == 0:
                break
            pos_in_page += 1
            day_type = page[pos_in_page:pos_in_page + 180]
            pos_in_page += 180
            day_entries.append(list(day_type))
    return day_entries


def read_trend_pages(pages: list[bytes]) -> dict[str, int]:
    """
    For each trend:
     - 4 byte: trend Id (Once set, should never change). Starts at 1.
     - 124 bytes: trend name, UTF-8 encoded, padded with null bytes
    Zero filled after the last trend record
    Returns: dictionary from trend name to integer trend id
    """
    trends = {}
    pos_in_page = 0
    for page in pages:
        while pos_in_page < len(page):
            trend_id = int.from_bytes(page[pos_in_page:pos_in_page + 4], 'big')
            if trend_id == 0:
                break
            pos_in_page += 4
            trend_name = page[pos_in_page:pos_in_page + trend_name_size].decode('utf-8').rstrip('\x00')
            pos_in_page += trend_name_size

            trends[trend_name] = trend_id

    return trends


def read_index_page(pages: list[bytes]) -> list[DataIndex]:
    # Each index record is:
    # 1. 4 byte: trend Id
    # 2. 4 byte: page index
    # 3. 2 byte: start day Id
    # 4. 2 byte: end day Id (inclusive)
    # Null filled after the last index record
    indexes = []

    pos_in_page = 0
    for page in pages:
        while pos_in_page < len(page):
            trend_id = int.from_bytes(page[pos_in_page:pos_in_page + 4], 'big')
            if trend_id == 0:
                break
            pos_in_page += 4
            page_index = int.from_bytes(page[pos_in_page:pos_in_page + 4], 'big')
            pos_in_page += 4
            start_day = int.from_bytes(page[pos_in_page:pos_in_page + 2], 'big')
            pos_in_page += 2
            end_day = int.from_bytes(page[pos_in_page:pos_in_page + 2], 'big')
            pos_in_page += 2

            indexes.append(DataIndex(trend_id, page_index, start_day, end_day))

    return indexes


class Node:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left: Optional[Node] = None
        self.right: Optional[Node] = None

    # For priority queue, to compare nodes based on frequency
    def __lt__(self, other):
        return self.freq < other.freq


def build_huffman_tree_from_dict(frequency_dict: dict[str, int]):
    # Create a priority queue to hold nodes of the Huffman tree
    priority_queue = [Node(char, freq) for char, freq in frequency_dict.items()]
    heapq.heapify(priority_queue)

    # Combine nodes until there is only one tree
    while len(priority_queue) > 1:
        left = heapq.heappop(priority_queue)
        right = heapq.heappop(priority_queue)

        merged: Node = Node(None, left.freq + right.freq)
        merged.left = left
        merged.right = right

        heapq.heappush(priority_queue, merged)

    # The remaining element is the root of the Huffman tree
    return priority_queue[0]


def build_huffman_tree(text):
    # Count frequency of appearance of each character
    frequency = Counter(text)
    build_huffman_tree_from_dict(frequency)


def generate_codes(node, prefix="", code=None):
    if code is None:
        code = {}
    if node is not None:
        if node.char is not None:
            code[node.char] = prefix
        generate_codes(node.left, prefix + "0", code)
        generate_codes(node.right, prefix + "1", code)
    return code


def huffman_encoding(text):
    # Build Huffman Tree
    root = build_huffman_tree(text)

    # Generate Huffman Codes
    huffman_codes = generate_codes(root)

    # Encode Text
    encoded_text = ''.join(huffman_codes[char] for char in text)

    return encoded_text, huffman_codes


def str_to_bytes(s: str) -> list[int]:
    """Converts a string of 1s and 0s to a list of bytes"""
    # Input is list of 1s and 0s
    output_bytes = []
    # Zero pad to right multiple of 8
    s += '0' * ((8 - len(s) % 8) % 8)
    for i in range(0, len(s), 8):
        output_bytes.append(int(s[i:i + 8], 2))
    return output_bytes


bit_strings = {
    0: '000',
    1: '001',
    2: '010',
    3: '011',
    4: '100',
    5: '101',
    6: '110',
    7: '111'
}


def encode_day_values(day_values: list[str]) -> list[int]:
    key_counts = {}
    runs = []
    prev_value = None
    run_length = 0
    symbol_counts: dict[str, int] = {}

    for value in day_values:
        if value != prev_value:
            if prev_value is not None:
                runs.append((prev_value, run_length))
            run_length = 1
            prev_value = value
        else:
            run_length += 1

        key_counts[value] = key_counts.get(value, 0) + 1

        for c in value:
            symbol_counts[c] = symbol_counts.get(c, 0) + 1

    runs.append((prev_value, run_length))

    percent_unique = len(key_counts) / len(day_values)

    if percent_unique < 0.2:
        # Do a dictionary encoding, followed by a run-length encoding
        keys = list(key_counts.keys())

        # First byte is 0 to signal dictionary/RL encoding
        # Second byte is the number of keys
        output_bytes: list[int] = [0, len(keys)]

        # Next followed by 1 byte length of following UTF-8 encoded string for each unique value. Means max 256 length strings.
        for key in keys:
            output_bytes.append(len(key))
            output_bytes.extend(list(key.encode('utf-8')))

        output_bytes.append(len(runs))

        # Now RLE each value
        for value, length in runs:
            value_index = keys.index(value)
            # Handle case where run length is greater than 255
            while length > 255:
                output_bytes.append(255)
                output_bytes.append(value_index)
                length -= 255

            output_bytes.append(length)
            output_bytes.append(value_index)

        return output_bytes

    else:
        # Do a Huffman encoding. Input is the data values, assumed separated by 'Record Separator' character, 1E
        # - 1 byte: 1 to represent Huffman encoding
        # - 1 byte: number of symbols
        # - For each symbol (n):
        #     - 1 byte: length of symbol
        #     - m bytes: UTF-8 string symbol
        #     - 1 byte: length of Huffman code (implies no code > 255 bits)
        # - o bytes: Huffman codes, padded to byte boundary
        # - 2 bytes: number of *bits* of data
        # - p bytes: data, padded to byte boundary

        # First byte is 1 to signal Huffman encoding
        output_bytes = [1]

        # Need to add fake 'Record Separator' character to the symbol counts
        symbol_counts[chr(0x1E)] = len(day_values) - 1

        # Encode the number of keys
        output_bytes.append(len(symbol_counts))

        root = build_huffman_tree_from_dict(symbol_counts)
        huffman_codes = generate_codes(root)

        code_items = list(huffman_codes.items())

        # Encode the symbols
        all_codes = []
        for symbol, code in code_items:
            output_bytes.append(len(symbol))
            output_bytes.extend(list(symbol.encode('utf-8')))
            output_bytes.append(len(code))
            all_codes.append(code)

        # Dump all the huffman codes concatenated
        output_bytes.extend(str_to_bytes(''.join(all_codes)))

        # Encode the data
        text = "\x1E".join(day_values)
        # Literal string of 1s and 0s
        encoded_text = ''.join(huffman_codes[char] for char in text)

        if len(encoded_text) > 65535:
            raise ValueError("Encoded text too large")

        # Dump the total number of bytes, in huffman_bytes_for_bytes bytes
        num_bits = len(encoded_text)

        output_bytes.extend(num_bits.to_bytes(huffman_bytes_for_bytes, 'big'))
        output_bytes.extend(str_to_bytes(encoded_text))

        # Encode the symbols
        return output_bytes


def decode_data_page(encoded_bytes: list[int]) -> list[tuple[datetime.datetime, str]]:
    # List of encoded days.
    # Days can be compressed using either be a dictionary/run length encoding, or Huffman coding.
    #
    # Begins with
    #
    # - 2 bytes: total number of days in page
    #
    # For each encoded day:
    #
    # Begins with:
    #     - 2 byte day Id (Indexed from Jan 1, of start year, default 2000)
    #     - 2 byte day type Id (0 indexed)
    #
    # Then followed with either a dictionary/run length encoding, or Huffman coding.

    day_count = int.from_bytes(encoded_bytes[0:2], 'big')
    index = 2

    day_entries = []
    day_index = 0
    while day_index < day_count:
        day_id = int.from_bytes(encoded_bytes[index:index + 2], 'big')
        index += 2
        day_type_id = int.from_bytes(encoded_bytes[index:index + 2], 'big')
        index += 2

        day_values = decode_day_values(encoded_bytes[index:])


def decode_day_values(encoded_bytes: list[int], start_index=0) -> tuple[list[str], int]:
    """Decodes the day values from the encoded bytes
    Returns a list of strings, and the index of the next byte after the decoded values

    """
    encoding_type = encoded_bytes[start_index]

    if encoding_type == 0:
        # Dictionary encoding, followed by a run-length encoding

        # - 1 byte: 0 to represent dictionary encoding
        # - 1 byte: number of keys in dictionary (implying < 256 keys)
        # - For each key:
        #     - 1 byte: length of key 1
        #     - n bytes: UTF-8 string key 1
        # - 1 byte: number of values
        # - For each value:
        #     - 1 byte: length of run of key n, (implies no run > 255, may need to repeat if run > 255)
        #     - 1 byte: key n, zero indexed

        keys = []
        key_count = encoded_bytes[start_index + 1]
        index = start_index + 2
        for _ in range(key_count):
            key_length = encoded_bytes[index]
            index += 1
            keys.append(bytes(encoded_bytes[index:index + key_length]).decode('utf-8'))
            index += key_length

        num_values = encoded_bytes[index]

        index += 1
        day_values = []
        while len(day_values) < num_values:
            length = encoded_bytes[index]
            index += 1
            value = keys[encoded_bytes[index]]
            index += 1

            day_values.extend([value] * length)

        return day_values, index

    elif encoding_type == 1:
        # Huffman encoding
        symbol_count = encoded_bytes[start_index + 1]
        index = start_index + 2

        symbols = []
        huffman_code_lengths = []

        for _ in range(symbol_count):
            length = encoded_bytes[index]
            index += 1
            symbols.append(bytes(encoded_bytes[index:index + length]).decode('utf-8'))
            index += length
            huffman_code_lengths.append(encoded_bytes[index])
            index += 1

        num_bytes_required_for_codes = math.ceil(sum(huffman_code_lengths) / 8)
        code_bytes = encoded_bytes[index:index + num_bytes_required_for_codes]
        index += num_bytes_required_for_codes

        code_bits: str = ''.join([f"{code:08b}" for code in code_bytes])
        symbol_dict = {}

        code_index = 0
        for i, symbol in enumerate(symbols):
            length = huffman_code_lengths[i]
            symbol_dict[code_bits[code_index:code_index + length]] = symbol
            code_index += length

        num_bits = int.from_bytes(encoded_bytes[index:index + huffman_bytes_for_bytes], 'big')
        index += huffman_bytes_for_bytes

        num_bytes = num_bits // 8 + (1 if num_bits % 8 != 0 else 0)

        data_bytes = encoded_bytes[index:index + num_bytes]
        data_bits = ''.join([f"{byte:08b}" for byte in data_bytes])

        day_values_chars: list[str] = []
        code = ""
        for bit in data_bits[0:num_bits]:
            code += bit
            if code in symbol_dict:
                day_values_chars.append(symbol_dict[code])
                code = ""

        return "".join(day_values_chars).split("\x1E"), index + num_bytes

    else:
        raise ValueError("Unknown encoding type")


if __name__ == "__main__":
    arg_index = 1
    command = None

    while arg_index < len(sys.argv):
        if sys.argv[arg_index] == "init":
            command = "init"

            if arg_index + 1 >= len(sys.argv):
                print("Error: init requires a file path")
                sys.exit(1)

            init(sys.argv[arg_index + 1])
            sys.exit(0)
        elif sys.argv[arg_index] == "summary":
            command = "summary"

            if arg_index + 1 >= len(sys.argv):
                print("Error: summary requires a file path")
                sys.exit(1)

            print_summary(sys.argv[arg_index + 1])

            sys.exit(0)
        else:
            arg_index += 1

    test_strings = [
        "hello",
        "hello",
        "world",
        "world",
        "world",
        "hello",
        "world",
        "world",
        "world",
        "world",
        "hello",
    ]

    test_string = "\t".join(test_strings)

    print(encode_day_values(test_strings))
    # Compare to the output of plain UTF-8 encoding, tab separated
    ints = list(test_string.encode('utf-8'))
    print(ints)

    compression_ratio = len(encode_day_values(test_strings)) / len(ints)
    print(compression_ratio)

    # Example usage
    encoded_text, codes = huffman_encoding(test_string)
    print("Encoded text:", encoded_text)
    print(str_to_bytes(encoded_text))
    print("Huffman Codes:", codes)

    compression_ratio = len(str_to_bytes(encoded_text)) / len(ints)
    print(compression_ratio)

    with open('data.csv', 'r') as f:
        data = f.read()

    encoded_text, codes2 = huffman_encoding(data)
    print("Huffman Codes:", codes2)

    compression_ratio = len(str_to_bytes(encoded_text)) / len(data.encode('utf-8'))
    print(compression_ratio)
