#!/usr/bin/env python3
"""Render explicitly selected PDF pages; page numbers are one-based."""
import argparse
from pathlib import Path
import fitz

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('pdf', type=Path)
    ap.add_argument('--pages', required=True, help='1,3,10 or 1-3')
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--dpi', type=int, default=100)
    args = ap.parse_args()
    selected = set()
    for part in args.pages.split(','):
        ends = part.split('-')
        if len(ends) == 1:
            selected.add(int(part))
        elif len(ends) == 2:
            lo, hi = map(int, ends)
            if lo > hi: ap.error('Page range is reversed')
            selected.update(range(lo, hi + 1))
        else: ap.error('Invalid page list')
    with fitz.open(args.pdf) as doc:
        if not selected or min(selected) < 1 or max(selected) > len(doc):
            ap.error('Page number outside this PDF')
        if not 36 <= args.dpi <= 600: ap.error('Use 36–600 dpi')
        args.out.mkdir(parents=True, exist_ok=True)
        for page in sorted(selected):
            target = args.out / f'{args.pdf.stem}-p{page:02}.png'
            doc[page-1].get_pixmap(dpi=args.dpi, alpha=False).save(target)
            print(target)

if __name__ == '__main__': main()
