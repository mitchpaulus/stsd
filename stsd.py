import math
import heapq
from collections import defaultdict, Counter
from typing import Optional

class Node:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left: Optional[Node] = None
        self.right: Optional[Node] = None

    # For priority queue, to compare nodes based on frequency
    def __lt__(self, other):
        return self.freq < other.freq

def build_huffman_tree(text):
    # Count frequency of appearance of each character
    frequency = Counter(text)

    # Create a priority queue to hold nodes of the Huffman tree
    priority_queue = [Node(char, freq) for char, freq in frequency.items()]
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
    # Input is list of 1s and 0s"
    output_bytes = []
    # Zero pad to right multiple of 8
    s += '0' * (8 - len(s) % 8)
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

def encode_day_values(day_values: list[str]) -> list[bytes]:
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

    percent_unique = len(key_counts) / len(day_values)

    if percent_unique < 0.2:
        # Do a dictionary encoding, followed by a run-length encoding
        num_bits_required = math.ceil(math.log(len(key_counts), 2))
        keys = list(key_counts.keys())

        output_bytes = []

        # First byte is 0 to signal dictionary/RL encoding
        output_bytes.append(0)

        # First byte is the number of keys
        output_bytes.append(len(keys))

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
        # Do a Huffman encoding

        # First byte is 1 to signal Huffman encoding
        output_bytes = [1]

        # Encode the number of keys

        return []


if __name__ == "__main__":
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
