"""Download the 399 CAIE mark-scheme PDFs listed in ms_manifest.csv and verify SHA-256.

Usage: python download_ms.py [OUT_DIR]        (default OUT_DIR: ../pdfs)

Files are saved as OUT_DIR/<level>/<filename>. A file is kept only when its
SHA-256 matches the manifest, so a changed or substituted download is rejected.
Already-verified files are skipped, so the script can be re-run after failures.
"""
import csv
import hashlib
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def Sha256OfFile(Path):
    Hasher = hashlib.sha256()
    with open(Path, 'rb') as File:
        Block = File.read(65536)
        while Block != b'':
            Hasher.update(Block)
            Block = File.read(65536)
    return Hasher.hexdigest()


def DownloadOne(Url, Target, ExpectedHash):
    for Attempt in range(1, 5):
        try:
            Request = urllib.request.Request(Url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(Request, timeout=120) as Response:
                Data = Response.read()
            if hashlib.sha256(Data).hexdigest() == ExpectedHash:
                with open(Target, 'wb') as File:
                    File.write(Data)
                return True
            print('  hash mismatch on attempt', Attempt)
        except OSError as Error:
            print('  attempt', Attempt, 'failed:', Error)
        time.sleep(2 ** Attempt)
    return False


def Main():
    OutDir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'pdfs')
    Rows = list(csv.DictReader(open(os.path.join(HERE, 'ms_manifest.csv'), encoding='utf-8')))
    Failed = []
    for Row in Rows:
        Folder = os.path.join(OutDir, Row['level'])
        os.makedirs(Folder, exist_ok=True)
        Target = os.path.join(Folder, Row['filename'])
        if os.path.exists(Target) and Sha256OfFile(Target) == Row['sha256']:
            continue
        print('Downloading', Row['filename'])
        if not DownloadOne(Row['url'], Target, Row['sha256']):
            Failed.append(Row['filename'])
    print('Done.', len(Rows) - len(Failed), 'verified,', len(Failed), 'failed')
    for Name in Failed:
        print('  FAILED:', Name)


if __name__ == '__main__':
    Main()
