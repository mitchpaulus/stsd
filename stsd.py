import math
import heapq
from collections import defaultdict, Counter
from typing import Optional
import sys

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
        # 1. 2 byte: version number
        # 2. 2 byte: page size in bytes
        # 3. 2 byte: Initial year (default 2000)
        # 4. 4 byte: number of day entries pages
        # 5. 4 byte: number of trends pages
        # 6. 4 byte: number of Index pages
        version = 1
        page_size = 4096
        initial_year = 2000
        num_day_entries_pages = 0
        num_trends_pages = 0
        num_index_pages = 0

        file.write(version.to_bytes(2, 'big'))
        file.write(page_size.to_bytes(2, 'big'))
        file.write(initial_year.to_bytes(2, 'big'))
        file.write(num_day_entries_pages.to_bytes(4, 'big'))
        file.write(num_trends_pages.to_bytes(4, 'big'))
        file.write(num_index_pages.to_bytes(4, 'big'))

        # Write null bytes to fill the rest of the page
        file.write(b'\x00' * (page_size - 18))



def write_data(filepath, trend_name: str, values: list[tuple[str, str]]):
    # Read first 4096 bytes to get the configuration
    with open(filepath, 'rb+') as file:
        configurations = file.read(18)

    page_size = int.from_bytes(configurations[2:4], 'big')

    num_day_entries_pages = int.from_bytes(configurations[6:10], 'big')
    num_trends_pages = int.from_bytes(configurations[10:14], 'big')
    num_index_pages = int.from_bytes(configurations[14:18], 'big')

    total_size = page_size * (num_day_entries_pages + num_trends_pages + num_index_pages)

    # Read all the index pages
    file.seek(page_size)

    all_index_pages = file.read(total_size)

    day_entry_pages = all_index_pages[0:page_size * num_day_entries_pages]
    trend_pages = all_index_pages[page_size * num_day_entries_pages:page_size * (num_day_entries_pages + num_trends_pages)]
    index_pages = all_index_pages[page_size * (num_day_entries_pages + num_trends_pages):]

    day_entries = read_day_entry_page(day_entry_pages)
    trends = read_trend_page(trend_pages)
    indexes = read_index_page(index_pages)
    pass


def read_day_entry_page(pages: list[bytes]) -> list[list[int]]:
    pass

def read_trend_page(pages: list[bytes]) -> dict[str, int]:
    # 1. For each trend:
    # - 4 byte: trend Id (Once set, should never change)
    # - 256 bytes: trend name, UTF-8 encoded, padded with null bytes
    # Zero filled after the last trend record
    trends = {}
    pos_in_page = 0
    for page in pages:
        while pos_in_page < len(page):
            trend_id = int.from_bytes(page[pos_in_page:pos_in_page+4], 'big')
            if trend_id == 0:
                break
            pos_in_page += 4
            trend_name = page[pos_in_page:pos_in_page+256].decode('utf-8').rstrip('\x00')
            pos_in_page += 256

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
            trend_id = int.from_bytes(page[pos_in_page:pos_in_page+4], 'big')
            if trend_id == 0:
                break
            pos_in_page += 4
            page_index = int.from_bytes(page[pos_in_page:pos_in_page+4], 'big')
            pos_in_page += 4
            start_day = int.from_bytes(page[pos_in_page:pos_in_page+2], 'big')
            pos_in_page += 2
            end_day = int.from_bytes(page[pos_in_page:pos_in_page+2], 'big')
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
        output_bytes.append(int(s[i:i+8], 2))
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
    symbol_counts = {}

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

        # Now RLE the each value
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
        # - 2 bytes: number of bytes of data
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
        encoded_text = ''.join(huffman_codes[char] for char in text)

        # Dump the total number of bits, in 3 bytes
        output_bytes.extend(len(encoded_text).to_bytes(3, 'big'))
        output_bytes.extend(str_to_bytes(encoded_text))

        # Encode the symbols
        return output_bytes


def decode_day_values(encoded_bytes: list[int]) -> list[str]:
    encoding_type = encoded_bytes[0]

    if encoding_type == 0:
        # Dictionary encoding, followed by a run-length encoding
        keys = []
        key_count = encoded_bytes[1]
        index = 2
        for _ in range(key_count):
            key_length = encoded_bytes[index]
            index += 1
            keys.append(bytes(encoded_bytes[index:index+key_length]).decode('utf-8'))
            index += key_length

        day_values = []
        while index < len(encoded_bytes):
            length = encoded_bytes[index]
            index += 1
            value = keys[encoded_bytes[index]]
            index += 1
            day_values.extend([value] * length)

        return day_values

    elif encoding_type == 1:
        # Huffman encoding
        symbol_count = encoded_bytes[1]
        index = 2

        symbols = []
        huffman_code_lengths = []

        for _ in range(symbol_count):
            length = encoded_bytes[index]
            index += 1
            symbols.append(bytes(encoded_bytes[index:index+length]).decode('utf-8'))
            index += length
            huffman_code_lengths.append(encoded_bytes[index])
            index+=1

        num_bytes_required_for_codes = math.ceil(sum(huffman_code_lengths) / 8)
        code_bytes = encoded_bytes[index:index+num_bytes_required_for_codes]
        index += num_bytes_required_for_codes

        code_bits: str = ''.join([f"{code:08b}" for code in code_bytes])
        symbol_dict = {}

        code_index = 0
        for i, symbol in enumerate(symbols):
            length = huffman_code_lengths[i]
            symbol_dict[code_bits[code_index:code_index+length]] = symbol
            code_index += length


        num_bits = int.from_bytes(encoded_bytes[index:index+3], 'big')
        index += 3

        data_bytes = encoded_bytes[index:]
        data_bits = ''.join([f"{byte:08b}" for byte in data_bytes])

        day_values_chars: list[str] = []
        code = ""
        for bit in data_bits[0:num_bits]:
            code += bit
            if code in symbol_dict:
                day_values_chars.append(symbol_dict[code])
                code = ""

        return "".join(day_values_chars).split("\x1E")

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

            arg_index += 2
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
