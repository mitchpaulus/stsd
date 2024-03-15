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

def block_text(rect, text):
    return d.text().x(rect.center_x()).y(rect.center_y()).text(text).font_size(font_size).xAnchor("middle").yAnchor("middle")

prev_block = None
for b in blocks:
    x2_prev = 0 if prev_block is None else prev_block.x2()
    rect = d.rect(b[0]).x(x2_prev).y(2).width(b[1] * width_per_btye).height(1)
    block_text(rect, b[0])
    prev_block = rect

def block(name, num_bytes):
    return d.rect(name).x(0).y(2).width(num_bytes * width_per_btye).height(1)

for x in range(0, 11):
    for y in range(0, 5):
        d.circle(f"circle_{x}_{y}").x(x).y(y).r(0.01)

d.rect().x(0).y(0).width(1 * width_per_btye).height(1).text("Non zero").font_size(font_size)
d.rect().x(1 * width_per_btye).y(0).width(25 * width_per_btye).height(1).text("180 byte minute bit string").font_size(font_size)

d.to_svg(-1, -4, 60, 4)

#  print(f'<svg preserveAspectRatio="xMidYMid"  viewBox="0 -4 10 4" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">\n', end='')

#  for i in items:
    #  print(i.to_svg(), end="")

#  print('</svg>')
