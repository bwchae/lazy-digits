# Lazy Digits

A condensed, bold digit font for small screens that are read at a glance: bike computers, sports watches, dashboards.
Digits and a few symbols only, free under the SIL Open Font License.

[한국어 설명](README.ko.md)

![Lazy Digits specimen](docs/specimen.png)

## Why

Lazy Digits was made for [Lazy Dashboard](https://apps.garmin.com/apps/6b6fd786-e6ac-4419-9f56-75a55b97b7a3), a
Garmin Edge data field that puts a whole ride on one screen. Two things called for a font of its own:

- **Bigger numbers in the same cell.** At 0.60 of its height a digit is narrower than in most UI fonts, so a
  three-digit power value fills a cell about 10 % taller than Garmin's Roboto does.
- **The same digits in every language.** On Edge units set to Korean (and other Asian languages) the system number
  fonts are much smaller bitmaps; an app font looks the same whatever the device language.

## Design

- Squircle (rounded-square) bowls, one stroke weight, horizontal strokes slightly thinner than vertical ones.
- Shapes that stay apart when small or blurred: flat-top 3, open 4, straight-bar tails on 6 and 9, round 0, steep 7,
  1 with a short shallow flag.
- **Tabular**: every digit has the same width, so a live value (timer, speed, power) doesn't shift as it changes.
- Colon centred on the digits for clock and timer readouts.

## Characters

`0 1 2 3 4 5 6 7 8 9` `.` `:` `-` (also U+2212 minus) `/` `%` `°` and space.

## Use

**Desktop:** install `fonts/ttf/LazyDigits-Bold.ttf`.

**Garmin Connect IQ:** apps can't load TTF fonts, only bitmap fonts in BMFont format. `tools/make_bmfont.py` makes
one per size:

```sh
python tools/make_bmfont.py fonts/ttf/LazyDigits-Bold.ttf 48 resources/fonts/lazy48
```

```xml
<fonts>
    <font id="Lazy48" filename="lazy48.fnt" antialias="true"/>
</fonts>
```

The atlas stores each glyph as grey on opaque black; with `antialias="true"` that is the layout that gives smooth
edges (glyphs in the alpha channel compiled to hard 1-bit edges in our tests). The line box is cut tight around the
digits, so `Graphics.TEXT_JUSTIFY_VCENTER` centres the digits themselves. A 17-glyph anti-aliased font at 48 px cost
about 3 KB of app memory on an Edge 530 and almost nothing on an Edge 1040.

## Build from source

The outlines are generated: `sources/build_font.py` builds every glyph from rounded rectangles, bars and diagonals,
unites them with [skia-pathops](https://github.com/fonttools/skia-pathops) and writes the TTF with
[fontTools](https://github.com/fonttools/fonttools). Design choices (3 shape, width, stroke weight, ...) are
parameters at the top of the file.

```sh
pip install -r requirements.txt
python sources/build_font.py fonts/ttf
python tools/specimen.py
```

## License

Copyright 2026 Lazy Farmer. Licensed under the [SIL Open Font License 1.1](OFL.txt): free to use, embed, modify and
redistribute, including in commercial work; the font itself may not be sold on its own.
