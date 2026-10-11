# CAIE pseudocode style for Python projects (v2)

A re-analysis of every Cambridge IGCSE 0478 and AS & A Level 9608/9618 Computer Science mark
scheme from 2016 to 2025 (399 documents), to find how Cambridge writes code, so that Python
written for a pseudocode learner looks familiar. It replaces `CAIE_Python_Style_v1.0.0`;
`Audit_of_v1.md` lists what was wrong in v1.

## Start here

| File | What it is |
|---|---|
| `Style_Analysis.md` | The analysis: naming, layout, arrays, subprograms, common algorithms, Cambridge's own Python, differences between IG, AS and AL, with counts and sources |
| `Style_Analysis_zh.md` | The same analysis in Chinese |
| `AGENTS.md` | Rules for an AI coding assistant. Copy it into the root of your Python project (or into the assistant's project instructions) |
| `AI_Coding_Prompt.txt` | A short version of the rules to paste at the start of a chat |
| `Audit_of_v1.md` | Errors and unsupported claims in the v1 package and how v2 changes them |
| `examples/` | Tested Python programs written in the recommended style, each naming the mark-scheme pattern it follows |

## Key findings

- Identifiers are PascalCase (`TotalWeight`) in 88–98 % of cases in current schemes, and
  Cambridge's Python uses the same names; the 2023 IGCSE syllabus forbids underscores.
- Pseudocode arrays start at 1; Cambridge's Python lists start at 0 and loops are written
  `for X in range(0, N):`.
- Algorithms are always written out with counters, flags and `Temp` swaps. No mark-scheme
  Python uses `sum`, `min`, `max`, `sorted`, `lambda`, f-strings or `with open`.
- Cambridge's Python compares flags explicitly (`while Valid == False:`), puts
  declaration and type comments on variables, and in Paper 4 keeps arrays and pointers in
  global variables.
- Many apparent inconsistencies are differences between syllabus eras: 0478 before and after
  2023, 9608 (2016–2021) and 9618 (2021 onwards).

## Corpus and statistics

| Path | Contents |
|---|---|
| `corpus/IG_pseudocode.txt`, `AS_pseudocode.txt`, `AL_pseudocode.txt` | Every distinct pseudocode block from the mark schemes, with source PDF, page and the marking text above it |
| `corpus/AS_python.txt`, `AL_python.txt` | Cambridge's Python answers (9608 Paper 2 appendix; 9608 and 9618 Paper 4) |
| `corpus/blocks.jsonl` | All 6 750 extracted blocks in every language (pseudocode, Python, VB, Java, Pascal, SQL, assembly), with coordinates, context, language basis and duplicate links |
| `stats/` | Counts per syllabus era: statements, identifier styles, library routines, Python idioms, algorithm patterns |
| `tools/` | The pipeline: `download_ms.py` (downloads the 399 PDFs listed in `ms_manifest.csv` and checks SHA-256), `extract_code.py`, `classify.py`, `dump.py`, `style_stats.py`, `algo_stats.py`, `run_pipeline.sh` |

Levels: IG = 0478 Papers 1–2; AS = 9608/9618 Papers 1–2; AL = 9608/9618 Papers 3–4.

## Reproduce

```sh
pip install pymupdf
cd tools
sh run_pipeline.sh        # downloads to ../pdfs, rebuilds corpus/ and stats/
```

The rebuild produces the committed `corpus/` and `stats/` files byte for byte, plus
per-language text files for VB, Java and Pascal. The PDFs themselves are not committed.

## Run the examples' tests

```sh
python -m unittest discover -s tests -v
```

## Notes

- The mark schemes are © Cambridge University Press & Assessment. The extracted text is kept
  for private study in this private repository; the PDF page is authoritative.
- Extraction is automatic. Typos in the code are Cambridge's own. A few blocks may be split
  or joined wrongly; the block header gives the page to check.
- `examples/` are original teaching programs, not official answers.
