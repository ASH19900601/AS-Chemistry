#!/bin/sh
# Rebuild the corpus and statistics from the original mark-scheme PDFs.
# Requires Python 3.10+ and PyMuPDF (pip install pymupdf).
# Run from this tools/ directory:  sh run_pipeline.sh
set -e
PDFS=../pdfs
python3 download_ms.py "$PDFS"
python3 -I extract_code.py "$PDFS" ../corpus/blocks_raw.jsonl
python3 -I classify.py ../corpus/blocks_raw.jsonl ../corpus/blocks.jsonl
rm ../corpus/blocks_raw.jsonl
python3 -I dump.py ../corpus/blocks.jsonl ../corpus
# dump.py also writes *_visual_basic.txt, *_java.txt, *_pascal.txt and *_other_or_unclassified.txt
python3 -I style_stats.py ../corpus/blocks.jsonl ../stats
python3 -I algo_stats.py ../corpus/blocks.jsonl . > ../stats/algorithm_patterns.txt
echo "Corpus in ../corpus, statistics in ../stats"
