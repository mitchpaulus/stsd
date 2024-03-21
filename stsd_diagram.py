from diagram import Rectangle, Text, Circle, Drawing, compute

width_per_btye = 2
height_per_row = 2
font_size = 0.3

d = Drawing()

blocks = [
    ("Version", 2),
    ("Page Size", 2),
    ("Initial Year", 2),
    ("Num Day Pages", 4),
    ("Num Trend Pages", 4),
    ("Num Index Pages", 4),
]

curr_row = 3

def y_from_row(row):
    return row * height_per_row

def block_text(rect, text):
    return d.text().x(rect.center_x()).y(rect.center_y()).text(text).font_size(font_size).xAnchor("middle").yAnchor("middle")

prev_block = None
for b in blocks:
    x2_prev = 0 if prev_block is None else prev_block.x2()
    rect = d.rect(b[0]).x(x2_prev).y(y_from_row(curr_row)).width(b[1] * width_per_btye).height(1)
    block_text(rect, b[0])
    prev_block = rect

def block(name, num_bytes):
    return d.rect(name).x(0).y(y_from_row(curr_row)).width(num_bytes * width_per_btye).height(1)

def print_blocks(blocks, y):
    prev_block = None
    for b in blocks:
        x2_prev = 0 if prev_block is None else prev_block.x2()
        rect = d.rect(b[0] + str(y)).x(x2_prev).y(y).width(b[1] * width_per_btye).height(1)
        block_text(rect, b[0])
        prev_block = rect


curr_row -= 1
print_blocks([
    ("Trend Id", 4),
    ("124 byte UTF-8 encoded name", 22),
    ], y_from_row(curr_row))

curr_row -= 1

print_blocks([("Non zero", 1), ("180 byte minute bit string", 25), ], y_from_row(curr_row))

curr_row -= 1

print_blocks([
    ("Trend Id", 4),
    ("Page Index", 4),
    ("Start Day Id", 2),
    ("End Day Id (Inc.)", 2),
], y_from_row(curr_row))

curr_row -= 1

print_blocks([
    ("Current number of bytes", 2),
    ("Day Id", 2),
    ("Day Type Id", 2),
    ("Dict/RLE Id = 1", 1),
    ("# Keys", 1),
    ("Length of key n", 1),
    ("n bytes UTF-8 key", 4),
    ("Num Values", 1),
    ("Length of run", 1),
    ("Key n", 1),
    ], y_from_row(curr_row))

d.to_svg(-1, -4, 60, 4)
