# `stsd`: Simple Time Series Database

I've needed an extremely simple time series database for my own needs.
It is designed around these principles:

- I only need minute precision
- It's only a simple string lookup by name
- I'm only querying by days at a time
- Concurrent traffic is extremely low
- Can do some simple operations using common text processing utilities
- Compression has to just be "good" enough
- Data is normally appended

# Operations

## Insert Data

Given:
    - String trend name
    - Array of timestamp, value pairs

Pseudocode:
    - Pull trend definition pages
    - Lookup trend Id
    - If Id found:


## Get Data by Day Range

Given:
    - String trend name
    - Start date
    - End date

## Get Available Trends

Given:
    - None

## Database Format

Database is broken up into pages of 4 kB.
First page is configuration.
Next pages are day type pages.
Next pages are trend definition pages.
Next pages are Index pages.
Next pages are data pages.

I want to format of the data on disk to be as simple as possible.

### Configuration Page

1. 2 byte: version number
2. 2 byte: page size in bytes
3. 2 byte: Initial year (default 2000)
4. 4 byte: number of day entries pages
5. 4 byte: number of trends pages
6. 4 byte: number of Index pages

### Day Type Page

1. For each day entry:
    - 1 byte: non-zero byte to indicate following 180 bits are good
    - 180 bytes: day format. Bit string of 1440 bits, 1 for each minute of the day.

Zero-padded after last record to page boundary.

### Trend Definition Page

1. For each trend:
    - 4 byte: trend Id (Once set, should never change)
    - 256 bytes: trend name, UTF-8 encoded, padded with null bytes

One-padded (to allow id to act as zero-index) after last record to page boundary.

### Index Page

Each index record is:

1. 4 byte: trend Id
2. 4 byte: page index
3. 2 byte: start day Id
4. 2 byte: end day Id (inclusive)

Zero-padded after last record to page boundary.

### Data Page Format

List of encoded days.
Days can be compressed using either be a dictionary/run length encoding, or Huffman coding.

Begins with

- 2 bytes: total number of days in page

For each encoded day:

Begins with:
    - 2 byte day Id (Indexed from Jan 1, of start year, default 2000)
    - 2 byte day type Id (0 indexed)

Then followed with either a dictionary/run length encoding, or Huffman coding.

#### Dictionary/Run Length Encoding

- 1 byte: 0 to represent dictionary encoding
- 1 byte: number of keys in dictionary (implying < 256 keys)
- For each key:
    - 1 byte: length of key 1
    - n bytes: UTF-8 string key 1
- 1 byte: number of values
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
- 2 bytes: number of *bits* of data
- p bytes: data, padded to byte boundary
