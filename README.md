# `stsd`: Simple Time Series Database

I've needed an extremely simple time series database for my own needs.
It is designed around these principles:

- I only need minute precision
- It's only a simple string lookup by name
- I'm only querying by days at a time
- Concurrent traffic is extremely low
- Can do some simple operations using common text processing utilities
- Compression has to just be "good" enough
- Data is ordered on disk
- Data is normally appended

## Database Format

I want to format of the data on disk to be as simple as possible.

1. 1 byte version number
2. 4 byte: number of day entries
3. For each day entry:
    - 180 bytes: day format
4.

### Day format

Can either be a dictionary/run length encoding, or Huffman coding.

#### Dictionary/Run Length Encoding

- 1 byte: 0 to represent dictionary encoding
- 1 byte: number of keys in dictionary (implying < 256 keys)
- For each key:
    - 1 byte: length of key 1
    - n bytes: UTF-8 string key 1
- For each value:
    - 1 byte: length of run of key n, (implies no run > 255, may need to repeat if run > 255)
    - 1 byte: key n, zero indexed

#### Huffman Coding

- 1 byte: 1 to represent Huffman encoding
- 1 byte: number of symbols
- For each symbol (n):
    - 1 byte: length of symbol
    - m bytes: UTF-8 string symbol
    - 1 byte: length of Huffman code (implies no code > 255 bits)
- o bytes: Huffman codes, padded to byte boundary
- 2 bytes: number of bytes of data
- p bytes: data, padded to byte boundary
