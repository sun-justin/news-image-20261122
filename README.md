# news-image-20261122

![Python](https://img.shields.io/badge/python-3.13-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Size](https://img.shields.io/badge/image-1024x1024-lightgrey)

A program that draws a newspaper front page summing up the world news
of Sunday 22 November 2026, as a 1024x1024 PNG.

## What it draws

**THE WORLD TODAY — Sunday 22 November 2026**, a front page with:

- Lead: COP31 climate talks in Antalya stall in a second day of
  overtime; the latest draft deal makes no mention of fossil fuels.
- Iran strikes a civilian plant in Bahrain; two tankers are hit in
  the Strait of Hormuz.
- Mexico captures cartel boss "El Chapo Isidro" in Sinaloa; 11 killed.
- Trump, Xi and Putin meet in Shenzhen and agree nuclear-risk talks.
- An AI sell-off pushes US stocks into correction (S&P 500 -3.70%,
  Nasdaq -5.3%).
- Briefs: EU-Indonesia trade deal signed after 10 years; Russia hits
  Kryvyi Rih; 3 dead and 36 missing in an Indonesia factory fire;
  GTA 6 sets a $3.79bn launch record; UN states agree
  autonomous-weapons rules; Denmark expels a Russian attache.
- A markets strip: S&P 500 6,910, FTSE 100 10,346, Brent $89.95.

## How it works

`main.py` is pure Python 3 standard library. It draws every pixel
itself — a small 5x7 bitmap font, a hand-written PNG encoder
(`zlib` + `struct`) — with no network, no clock and no randomness,
so two runs write byte-identical output.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

The image is written to `out/entry.png` (1024x1024, under 1 MiB).
