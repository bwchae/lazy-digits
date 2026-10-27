"""Specimen image for the README: every glyph, sample readouts at three sizes, day and night.
Usage: python tools/specimen.py [font.ttf] [out.png]"""
import sys

from PIL import Image, ImageDraw, ImageFont

FONT = sys.argv[1] if len(sys.argv) > 1 else 'fonts/ttf/LazyDigits-Bold.ttf'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'docs/specimen.png'


def sized(cap):
    """Font whose digit height is cap pixels."""
    probe = ImageFont.truetype(FONT, 1000)
    c = probe.getbbox('8', anchor='ls')
    return ImageFont.truetype(FONT, round(1000 * cap / (c[3] - c[1])))


img = Image.new('RGB', (1600, 1000), (250, 250, 250))
d = ImageDraw.Draw(img)
grey = (130, 130, 130)
label = ImageFont.load_default(size=20)
d.text((24, 18), 'Lazy Digits Bold', font=label, fill=grey)
d.text((24, 220), '0123456789', font=sized(150), fill=(0, 0, 0), anchor='ls')
d.text((24, 400), '. : - / % °', font=sized(150), fill=(0, 0, 0), anchor='ls')
y = 470
for cap, text in ((64, '188  34.7  7:38  1:05:32'), (44, '235  12°  98%  46/17  -5%  2.82'),
                  (30, '0123456789  20:34  8.45  132  -12  100%')):
    d.text((24, y + cap - 22), f'{cap}px', font=label, fill=grey)
    d.text((110, y + cap), text, font=sized(cap), fill=(0, 0, 0), anchor='ls')
    y += cap + 36
d.rectangle([0, y + 10, 1600, 1000], fill=(0, 0, 0))
d.text((110, y + 110), '188  34.7  7:38  12°  98%', font=sized(64), fill=(255, 255, 255), anchor='ls')
d.text((110, y + 190), '46/17  -5%  20:34  8.45', font=sized(44), fill=(80, 200, 120), anchor='ls')
img.save(OUT)
print(OUT)
