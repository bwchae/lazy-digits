"""TTF -> Connect IQ bitmap font (AngelCode BMFont text .fnt + PNG atlas). The atlas holds the glyph coverage as grey
in RGB on opaque black: with antialias="true" only that gives grey edge pixels on the device (white text in the alpha
channel compiled to hard 1-bit edges, simulator 2026-10-27). Pass 'alpha' as the 5th argument for the old layout.
The line box is tight around the digits (cap height + pad above and below) so that drawText with VCENTER centres
the digits themselves, not an ascender/descender box.
Usage: make_bmfont.py <font.ttf> <cap px> <out base name> [chars | -] [alpha]"""
import sys
from PIL import Image, ImageDraw, ImageFont

ttf, cap, base = sys.argv[1], int(sys.argv[2]), sys.argv[3]
chars = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] != '-' else '0123456789.:-/%° '
RGB = not (len(sys.argv) > 5 and sys.argv[5] == 'alpha')
PAD = max(1, round(cap * 0.06))       # empty rows above the cap height and below the baseline

probe = ImageFont.truetype(ttf, 1000)
c8 = probe.getbbox('8', anchor='ls')
size = round(1000 * cap / (c8[3] - c8[1]))
f = ImageFont.truetype(ttf, size)
capH = -f.getbbox('8', anchor='ls')[1]   # actual cap height at this size
lineH = capH + 2 * PAD
basePx = capH + PAD                      # baseline, from the top of the line box

glyphs = []
for ch in chars:
    adv = round(f.getlength(ch))
    if ch == ' ':
        glyphs.append((ch, None, 0, 0, adv))
        continue
    l, t, r, b = f.getbbox(ch, anchor='ls')
    im = Image.new('L', (r - l + 2, b - t + 2), 0)
    ImageDraw.Draw(im).text((1 - l, 1 - t), ch, font=f, fill=255, anchor='ls')
    glyphs.append((ch, im, l - 1, basePx + t - 1, adv))

# Pack in one row-wrapped atlas.
W = 256
while True:
    x = y = rowH = 0
    pos = []
    for ch, im, *_ in glyphs:
        w, h = (im.size if im else (0, 0))
        if x + w > W:
            x, y, rowH = 0, y + rowH + 1, 0
        pos.append((x, y))
        x += w + 1
        rowH = max(rowH, h)
    if y + rowH <= W:
        break
    W *= 2
H = 1
while H < y + rowH:
    H *= 2
atlas = Image.new('RGBA', (W, H), (0, 0, 0, 255) if RGB else (255, 255, 255, 0))
name = base.split('/')[-1]
lines = [f'info face="{name}" size={size} bold=1 italic=0 charset="" unicode=1 stretchH=100 smooth=1 aa=1 '
         f'padding=0,0,0,0 spacing=1,1 outline=0',
         f'common lineHeight={lineH} base={basePx} scaleW={W} scaleH={H} pages=1 packed=0 alphaChnl=0 redChnl=4 '
         f'greenChnl=4 blueChnl=4',
         f'page id=0 file="{base.split("/")[-1]}.png"',
         f'chars count={len(glyphs)}']
for (ch, im, xo, yo, adv), (px, py) in zip(glyphs, pos):
    w, h = (im.size if im else (0, 0))
    if im:
        if RGB:
            atlas.paste(Image.merge('RGBA', (im, im, im, Image.new('L', im.size, 255))), (px, py))
        else:
            atlas.paste(Image.new('RGBA', im.size, (255, 255, 255, 255)), (px, py), im)
    lines.append(f'char id={ord(ch)} x={px} y={py} width={w} height={h} xoffset={xo} yoffset={yo} '
                 f'xadvance={adv} page=0 chnl=15')
atlas.save(base + '.png')
open(base + '.fnt', 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
print(f'{base}: cap {capH}px line {lineH}px atlas {W}x{H} glyphs {len(glyphs)}')
