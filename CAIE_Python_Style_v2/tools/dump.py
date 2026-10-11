"""Write readable per-level, per-language corpus files from classified blocks.

Usage: python -I dump.py blocks.jsonl OUT_DIR
"""
import sys, json, os, collections

HEADER = """# CAIE mark-scheme code corpus: {level} / {lang}
# Source: Cambridge International mark schemes (MS) 2016-2025, re-extracted from the PDFs
#         listed in tools/ms_manifest.csv (SHA-256 verified). Cambridge retains copyright;
#         this file is for private study.
# Levels: IG = IGCSE 0478 Papers 1-2; AS = 9608/9618 Papers 1-2; AL = 9608/9618 Papers 3-4.
# Each block header: block id | source PDF and physical page(s) | language (basis) | MS prose
#         just above the block (truncated). Identical blocks repeated in other variants are
#         listed once; corpus/blocks.jsonl records every block and its duplicate_of link.
# Extraction is automatic (monospace-font detection, indentation rebuilt from x positions).
# Typos in the code are Cambridge's own and are kept; wrapped lines may be re-joined.
# The PDF page is authoritative.

"""
src, outdir = sys.argv[1], sys.argv[2]
groups = collections.defaultdict(list)
for line in open(src, encoding='utf-8'):
    b = json.loads(line)
    lang = b['language']
    if lang not in ('pseudocode', 'python', 'visual_basic', 'java', 'pascal'):
        lang = 'other_or_unclassified'
    groups[(b['level'], lang)].append(b)
for (level, lang), blocks in groups.items():
    blocks.sort(key=lambda b: (b['year'], b['session'], b['syllabus'], b['paper'], b['variant'], b['page'], b['y0']))
    with open(os.path.join(outdir, f'{level}_{lang}.txt'), 'w', encoding='utf-8') as fh:
        fh.write(HEADER.format(level=level, lang=lang))
        for b in blocks:
            if b['duplicate_of']:
                continue
            pages = b.get('pages') or [b['page']]
            ctx = ' / '.join(c for c in b['context'][-2:])[:150]
            fh.write(f"=== {b['id']} | {b['file']} p{','.join(map(str, pages))} | {b['language']} ({b['language_basis']}) | context: {ctx}\n")
            fh.write(b['text'] + '\n\n')
