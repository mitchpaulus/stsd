import stsd
import datetime

values1 = [
    "905.428",
    "909.64599999999996",
    "906.27200000000005",
    "913.86500000000001",
    "902.89700000000005",
    "900.36599999999999",
    "895.30499999999995",
    "904.58500000000004",
    "913.86500000000001",
    "878.43200000000002",
    "903.74099999999999",
    "895.30499999999995",
    "914.70799999999997",
    "905.428",
]

values2 = [
    "On",
    "Off",
    "On",
    "On",
    "On",
    "On",
    "On",
    "On",
    "On",
    "On",
    "On",
    "On",
    "On",
    "On",
]


def test1():
    # Round trip test
    encoded = stsd.encode_day_values(values1)
    decoded, bytes_consumed = stsd.decode_day_values(encoded)

    assert len(values1) == len(decoded), f"Expected {len(values1)} but got {len(decoded)}"
    for i in range(len(values1)):
        assert values1[i] == decoded[i]


def test2():
    # Round trip test
    encoded = stsd.encode_day_values(values2)
    decoded, bytes_consumed = stsd.decode_day_values(encoded)

    assert len(values2) == len(decoded), f"Expected {len(values2)} but got {len(decoded)}"
    for i in range(len(values2)):
        assert values2[i] == decoded[i]


def test3():
    start_datetime = datetime.datetime(2024, 3, 5, 0, 0)
    # Add 96 datetimes, spaced 15 minutes apart
    datetimes = [start_datetime + datetime.timedelta(minutes=15 * i) for i in range(96)]
    day_time_values = stsd.to_day_entry(datetimes)

    print(day_time_values)

    assert len(day_time_values) == 180, f"Expected 180 but got {len(day_time_values)}"


def init_test():
    stsd.init(f"{datetime.datetime.now().isoformat()}.db")


def write_test():
    # Write to file YYYY-mm-dd HHmm.db
    date = datetime.datetime.now()
    file = f'{date.strftime("%Y-%m-%d %H%M")}.db'
    stsd.init(file)

    values = []
    for i in range(24):
        values.append(((2024, 3, 21, i, 0), i))

    values = [(datetime.datetime(*v[0]), str(v[1])) for v in values]
    stsd.write_data(file, "Trend 1", values)

if __name__ == "__main__":
    write_test()

    #  test1()
    #  test2()
    #  test3()
