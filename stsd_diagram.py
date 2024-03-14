from diagram import Rectangle, Text

width_per_btye = 1

version   = Rectangle("version").x(0).y(0).width(2).height(1)
page_size = Rectangle("page_size").x(version.x2()).y(0).width(4).height(1)

version_text = Text("version_text").x(version.center_x()).y(version.center_y()).text("version").font_size(0.5).xAnchor("middle").yAnchor("middle")


items = [
    version,
    page_size,
    version_text,
]

print(f'<svg viewBox="0 -2 10 2" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">\n', end='')

for i in items:
    print(i.to_svg(), end="")

print('</svg>')
