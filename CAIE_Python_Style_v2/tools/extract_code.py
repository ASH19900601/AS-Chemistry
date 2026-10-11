"""Layout-aware extraction of code blocks from CAIE mark-scheme PDFs.

Code in the mark schemes is typeset in a monospace font (Courier New, Courier,
or an embedded subset font with uniform 0.6 em glyphs).  The assignment arrow
comes from the Symbol font.  This script

1. classifies every character as code / neutral (Symbol arrow etc.) / prose,
2. groups characters into visual lines and splits lines into column segments,
3. rebuilds indentation from x positions on a monospace grid,
4. joins consecutive code lines into blocks (also across page breaks),
5. records the nearest prose label above each block (e.g. "Python"),
6. writes blocks.jsonl.

Usage: python -I extract_code.py PDF_ROOT OUT_JSONL
"""
import sys, os, re, glob, json, collections
import pymupdf

SYMBOL_MAP = {'': '←', '←': '←', '−': '-', '': '-',
              '': '*', '×': '*', '': ' ', '': '→',
              '': '<=', '': '>=', '': '<>'}
# left arrows drawn with Wingdings fonts in 2016-2020 IGCSE mark schemes
WINGDINGS_ARROWS = {'\u00c5', '\x04', '\uf021'}
HEADER_FOOTER = re.compile(
    r'^(Question|Answer|Marks|Guidance|Page \d+( of \d+)?|© UCLES.*|©\s*Cambridge.*|'
    r'Cambridge (International|IGCSE|O Level|Assessment).*|Mark Scheme.*|PUBLISHED|'
    r'\d{4}/\d{2}|[A-Z][a-z]+/[A-Z][a-z]+ \d{4}|Syllabus|Paper|\[Turn over)$')


def font_is_code(font, mono_fonts):
    return 'Courier' in font or font in mono_fonts


def find_mono_fonts(doc):
    widths = collections.defaultdict(list)
    for page in doc:
        for b in page.get_text('rawdict')['blocks']:
            for l in b.get('lines', []):
                for s in l['spans']:
                    for ch in s['chars']:
                        if ch['c'].strip() and len(widths[s['font']]) < 400:
                            widths[s['font']].append(round((ch['bbox'][2] - ch['bbox'][0]) / s['size'], 2))
    mono = set()
    for f, w in widths.items():
        if len(w) >= 20:
            share = sum(1 for x in w if abs(x - 0.6) <= 0.011) / len(w)
            if share > 0.95:
                mono.add(f)
    return mono


def page_chars(page, mono_fonts):
    """Return list of (x0, x1, y_baseline, size, char, kind) in visual (rotated) page space."""
    out = []
    m = page.rotation_matrix
    lin = pymupdf.Matrix(m.a, m.b, m.c, m.d, 0, 0)
    for b in page.get_text('rawdict')['blocks']:
        for l in b.get('lines', []):
            d = pymupdf.Point(l.get('dir', (1, 0))) * lin
            if abs(d.y) > 0.1 or d.x < 0:      # skip text that is not horizontal on the visual page
                continue
            for s in l['spans']:
                f = s['font']
                code = font_is_code(f, mono_fonts)
                sym = 'Symbol' in f
                wing = 'Wingdings' in f
                for ch in s['chars']:
                    c = ch['c']
                    kind = 'code' if code else 'prose'
                    if wing and c in WINGDINGS_ARROWS:
                        c = '\u2190'
                        kind = 'neutral'
                    elif sym:
                        if c in SYMBOL_MAP:
                            c = SYMBOL_MAP[c]
                            kind = 'neutral'
                        elif c in '\u2022\uf0b7':
                            kind = 'prose'
                        else:
                            kind = 'neutral'
                    if c in ('\u201c', '\u201d') and code:
                        c = '"'
                    r = pymupdf.Rect(ch['bbox']) * m
                    o = pymupdf.Point(ch['origin']) * m
                    out.append((r.x0, r.x1, round(o.y, 1), s['size'], c, kind))
    return recover_drawn_underscores(page, out)


def recover_drawn_underscores(page, chars):
    """Some 2023-2025 schemes draw '_' as a short filled line over a space glyph.
    Turn those spaces back into '_'. Touching line segments are merged first, so an
    underline that also runs under non-space characters (mark-point emphasis) is ignored."""
    m = page.rotation_matrix
    lines = []
    for d in page.get_drawings():
        r = d['rect'] * m
        if r.height <= 1.5 and 2.5 <= r.width <= 60 and d.get('fill') is not None:
            lines.append(pymupdf.Rect(r))
    if not lines:
        return chars
    lines.sort(key=lambda r: (round(r.y0 * 2), r.x0))
    segments = []
    for r in lines:
        if segments and abs(segments[-1].y0 - r.y0) <= 0.5 and r.x0 - segments[-1].x1 < 1.0:
            segments[-1].x1 = max(segments[-1].x1, r.x1)
        else:
            segments.append(r)
    result = list(chars)
    changed = False
    for seg in segments:
        same_line = [i for i, c in enumerate(result)
                     if c[5] == 'code' and abs(c[2] - (seg.y0 - 2.5)) <= 1.6]
        hits = [i for i in same_line if seg.x0 - 0.5 <= (result[i][0] + result[i][1]) / 2 <= seg.x1 + 0.5]
        if not hits or any(result[i][4] != ' ' for i in hits):
            continue
        neighbour = any(result[i][4].strip() and i not in hits and
                        (abs(result[i][1] - seg.x0) <= 1.0 or abs(result[i][0] - seg.x1) <= 1.0)
                        for i in same_line)
        if not neighbour:
            continue
        for i in hits:
            x0, x1, y, size, c, kind = result[i]
            result[i] = (x0, x1, y, size, '_', kind)
        changed = True
    return result if changed else chars


def drop_overprint(chars):
    """Remove duplicate glyphs drawn twice with a small offset (fake bold)."""
    out = []
    recent = []
    for c in sorted(chars, key=lambda c: (c[2], c[0])):
        w = max(c[1] - c[0], 0.1)
        dup = False
        for r in recent:
            if r[4] == c[4] and abs(r[2] - c[2]) <= 1.5 and abs(r[0] - c[0]) < 0.5 * w and c[4].strip():
                dup = True
                break
        if not dup:
            out.append(c)
            recent.append(c)
            if len(recent) > 6:
                recent.pop(0)
    return out


def group_lines(chars):
    chars = drop_overprint(chars)
    chars = sorted(chars, key=lambda c: (c[2], c[0]))
    lines = []
    for c in chars:
        if lines and abs(c[2] - lines[-1][0]) <= 2.0:
            lines[-1][1].append(c)
        else:
            lines.append([c[2], [c]])
    result = []
    for y, cs in lines:
        cs.sort(key=lambda c: c[0])
        # split into segments on large horizontal gaps
        segs = [[cs[0]]]
        for prev, cur in zip(cs, cs[1:]):
            size = max(prev[3], cur[3])
            gap = cur[0] - prev[1]
            both_code = prev[5] != 'prose' and cur[5] != 'prose'
            limit = size * (3.0 if both_code else 1.6)
            if gap > limit:
                segs.append([cur])
            else:
                segs[-1].append(cur)
        for sg in segs:
            nonspace = [c for c in sg if c[4].strip()]
            if not nonspace:
                continue
            ncode = sum(1 for c in nonspace if c[5] == 'code')
            nprose = sum(1 for c in nonspace if c[5] == 'prose')
            is_code = ncode > 0 and ncode >= 0.6 * (ncode + nprose)
            result.append({'y': y, 'x0': min(c[0] for c in nonspace), 'x1': max(c[1] for c in nonspace),
                           'size': max(c[3] for c in nonspace), 'chars': sg, 'code': is_code,
                           'prose_text': ''.join(c[4] for c in sg).strip()})
    return result


def render_code_line(seg, base_x, charw):
    chars = sorted((c for c in seg['chars']), key=lambda c: c[0])
    chars = [c for c in chars if c[4] != '']
    # drop leading spaces; indentation comes from x position
    while chars and not chars[0][4].strip():
        chars.pop(0)
    if not chars:
        return ''
    out = [' ' * max(0, int(round((chars[0][0] - base_x) / charw)))]
    prev = None
    for c in chars:
        if prev is not None:
            gap = c[0] - prev[1]
            if gap > 0.45 * charw:
                n = int(round(gap / charw))
                if n > 0 and not out[-1].endswith(' ') and c[4] != ' ':
                    out.append(' ' * n)
        out.append(c[4])
        prev = c
    return ''.join(out).rstrip()


def block_charw(segs, default):
    widths = []
    for s in segs:
        cs = sorted((c for c in s['chars'] if c[5] == 'code'), key=lambda c: c[0])
        for a, b in zip(cs, cs[1:]):
            adv = b[0] - a[0]
            if 0.3 * default < adv < 1.6 * default:
                widths.append(adv)
    if len(widths) < 5:
        return default
    widths.sort()
    return widths[len(widths) // 2]


def extract(pdf_path):
    doc = pymupdf.open(pdf_path)
    mono = find_mono_fonts(doc)
    name = os.path.basename(pdf_path)
    blocks = []
    for pno, page in enumerate(doc, start=1):
        segs = group_lines(page_chars(page, mono))
        code = [s for s in segs if s['code']]
        prose = [s for s in segs if not s['code'] and not HEADER_FOOTER.match(s['prose_text'])]
        code.sort(key=lambda s: (s['y'], s['x0']))
        cur = None
        for s in code:
            lh = s['size'] * 1.25
            if cur is not None:
                overlap = s['x0'] < cur['x1'] + 5 and s['x1'] > cur['x0'] - 60
                close = s['y'] - cur['y1'] <= 2.6 * lh
                same_line = abs(s['y'] - cur['y1']) <= 2.0
                # a prose line between them inside the code column breaks the block
                interrupt = any(cur['y1'] + 1 < p['y'] < s['y'] - 1 and p['x0'] < cur['x1'] and p['x1'] > cur['x0']
                                for p in prose)
                if (close and overlap and not interrupt) or (same_line and overlap):
                    cur['segs'].append(s)
                    cur['y1'] = s['y']
                    cur['x0'] = min(cur['x0'], s['x0'])
                    cur['x1'] = max(cur['x1'], s['x1'])
                    continue
                blocks.append(cur)
            cur = {'file': name, 'page': pno, 'y0': s['y'], 'y1': s['y'], 'x0': s['x0'], 'x1': s['x1'],
                   'segs': [s], 'page_h': page.rect.height}
        if cur is not None:
            blocks.append(cur)
        # attach labels / context from prose above each block on this page
        for b in blocks:
            if b['page'] != pno or 'label' in b:
                continue
            above = [p for p in prose if p['y'] < b['y0'] - 0.5 and p['y'] > b['y0'] - 120
                     and p['x0'] < b['x1'] and p['x1'] > b['x0'] - 40]
            above.sort(key=lambda p: p['y'])
            b['context'] = [p['prose_text'] for p in above[-4:]]
            b['label'] = above[-1]['prose_text'] if above else ''
            inner = [p['prose_text'] for p in prose if b['y0'] < p['y'] < b['y1'] and not (p['x0'] < b['x1'] and p['x1'] > b['x0'])]
            b['prose_after'] = any(p['y'] > b['y1'] + 1 and p['x0'] < b['x1'] and p['x1'] > b['x0'] for p in prose)
            b['prose_before'] = any(p['y'] < b['y0'] - 1 and p['x0'] < b['x1'] and p['x1'] > b['x0'] for p in prose)
    # render
    out = []
    for b in blocks:
        size = collections.Counter(round(s['size'], 1) for s in b['segs']).most_common(1)[0][0]
        charw = block_charw(b['segs'], 0.6 * size)
        base = min(s['x0'] for s in b['segs'])
        lines = []
        last_y = None
        for s in b['segs']:
            txt = render_code_line(s, base, charw)
            if last_y is not None and abs(s['y'] - last_y) <= 2.0 and lines:
                # same visual line, separate segment: append with spacing by column
                col = int(round((s['x0'] - base) / charw))
                prev = lines[-1]
                if col > len(prev):
                    lines[-1] = prev + ' ' * (col - len(prev)) + txt.lstrip()
                else:
                    lines[-1] = prev + ' ' + txt.lstrip()
            else:
                lines.append(txt)
            last_y = s['y']
        out.append({'file': b['file'], 'page': b['page'], 'y0': round(b['y0'], 1), 'y1': round(b['y1'], 1),
                    'x0': round(b['x0'], 1), 'x1': round(b['x1'], 1), 'label': b.get('label', ''),
                    'context': b.get('context', []), 'prose_before': b.get('prose_before', True),
                    'prose_after': b.get('prose_after', True), 'page_h': b['page_h'],
                    'nlines': len(lines), 'text': '\n'.join(lines)})
    # merge across page breaks
    merged = []
    for b in out:
        if merged:
            p = merged[-1]
            if (b['page'] == p['page'] + 1 and not p['prose_after'] and not b['prose_before']
                    and p['y1'] > p['page_h'] * 0.6 and b['y0'] < b['page_h'] * 0.4
                    and abs(b['x0'] - p['x0']) < 80 and p['nlines'] >= 2):
                p['text'] = p['text'] + '\n' + b['text']
                p['nlines'] += b['nlines']
                p['pages'] = p.get('pages', [p['page']]) + [b['page']]
                p['prose_after'] = b['prose_after']
                p['y1'] = b['y1']
                continue
        merged.append(b)
    return merged


def indent_of(line):
    return len(line) - len(line.lstrip(' '))


QNUM = re.compile(r'^\s*\d{1,2}\s?(\([a-z]\)|[a-z])?(\([ivx]+\))*\s+(?=[A-Z])')
CONT_END = re.compile(r'(,|&|\+|-|\*|/|\(|\bAND|\bOR|\bNOT|:|_|\bRETURNS|=|\u2190|\band|\bor|\\)\s*$')
CONT_START = re.compile(r'^\s*(RETURNS\b|&|\+|-(?!\d)|\*|/|\)|AND\b|OR\b|and\b|or\b|INTEGER\b|STRING\b|REAL\b|BOOLEAN\b|CHAR\b|[a-z]+\s*$)')


def normalise(text):
    lines = text.split('\n')
    if lines and QNUM.match(lines[0]):
        lines[0] = QNUM.sub('', lines[0])
        rest = [indent_of(l) for l in lines[1:] if l.strip()]
        if rest:
            opener = re.match(r'\s*(PROCEDURE|FUNCTION|def|class|IF|WHILE|FOR|REPEAT|CASE|TYPE|CLASS)\b', lines[0])
            shift = max(0, min(rest) - (3 if opener else 0))
            lines = [lines[0]] + [l[shift:] if l[:shift].strip() == '' else l.lstrip() for l in lines[1:]]
    lines = [re.sub(r'\s*\u2190\s*', ' \u2190 ', l).rstrip() if '\u2190' in l else l for l in lines]
    lines = [re.sub(r'^ \u2190 ', '\u2190 ', l) for l in lines]
    out = []
    for l in lines:
        if out and l.strip() and out[-1].strip():
            prev = out[-1]
            if indent_of(l) >= indent_of(prev) + 6 and (CONT_END.search(prev) or CONT_START.match(l)):
                out[-1] = prev.rstrip() + ' ' + l.strip()
                continue
        out.append(l)
    return '\n'.join(out)


def main():
    root, out_path = sys.argv[1], sys.argv[2]
    with open(out_path, 'w', encoding='utf-8') as fh:
        for path in sorted(glob.glob(os.path.join(root, '*', '*.pdf'))):
            level = os.path.basename(os.path.dirname(path))
            for i, b in enumerate(extract(path)):
                b['level'] = level
                b['raw_text'] = b['text']
                b['text'] = normalise(b['text'])
                b['id'] = f"{b['file'][:-4]}_p{b['page']}_b{i + 1}"
                fh.write(json.dumps(b, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
