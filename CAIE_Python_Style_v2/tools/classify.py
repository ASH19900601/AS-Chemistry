"""Classify extracted code blocks by language and attach metadata.

Usage: python -I classify.py blocks.jsonl classified.jsonl
"""
import sys, re, json, hashlib, collections

LABEL_RE = [
    ('python', re.compile(r'\bPython\b')),
    ('visual_basic', re.compile(r'\b(VB\.?NET|Visual Basic|VB)\b')),
    ('java', re.compile(r'\bJava\b(?!Script)')),
    ('pascal', re.compile(r'\b(Pascal|Delphi)\b')),
    ('pseudocode', re.compile(r'\b[Pp]seudo-?code\b')),
]

FEATURES = {
    'pseudocode': [r'←', r'\bDECLARE\b', r'\bENDIF\b', r'\bENDWHILE\b', r'^\s*NEXT\b', r'\bENDPROCEDURE\b',
                   r'\bENDFUNCTION\b', r'\bRETURNS\b', r'\bTHEN\b', r'^\s*REPEAT\s*$', r'^\s*UNTIL\b', r'\bCASE OF\b',
                   r'\bOTHERWISE\b', r'\bENDCASE\b', r'\bOPENFILE\b', r'\bREADFILE\b', r'\bWRITEFILE\b',
                   r'\bCLOSEFILE\b', r'^\s*CALL\b', r'\bBYREF\b', r'\bBYVAL\b', r'^\s*OUTPUT\b', r'^\s*INPUT\b',
                   r'^\s*PROCEDURE\b', r'^\s*FUNCTION\b', r'\bENDTYPE\b', r'\bENDCLASS\b', r'\bARRAY\s*\[',
                   r'^\s*PRINT\b', r'\bENDFOR\b', r'^\s*FOR\b.*\bTo\b', r'\bEND ?IF\b', r'^\s*FOR\b.*\bTO\b', r'^\s*WHILE\b.*\bDO\b'],
    'python': [r'^\s*def \w+\(.*\)\s*:', r'^\s*(if|elif|while|for)\b.*:\s*(#.*)?$', r'^\s*else\s*:', r'\bprint\(',
               r'\binput\(', r'\brange\(', r'\bself\.', r'^\s*import \w+', r'^\s*from \w+ import', r'\bTrue\b',
               r'\bFalse\b', r'\bNone\b', r'^\s*#', r'\.append\(', r'^\s*global\b', r'^\s*class \w+.*:\s*$',
               r'^\s*try\s*:', r'^\s*except\b', r'\bopen\(', r'\blen\(', r'\bstr\(', r'\bint\('],
    'visual_basic': [r'^\s*Dim\b', r'\bAs (Integer|String|Boolean|Char|Double|Single|Date|New)\b', r'\bEnd (Sub|Function|If|While|Class|Select|Structure|Module)\b',
                     r'\bConsole\.', r'^\s*Next\b', r'^\s*(Public |Private )?(Sub|Function)\b', r'\bByVal\b', r'\bByRef\b',
                     r'^\s*Loop\b', r"^\s*'", r'\bThen\b', r'^\s*Do\b', r'\bElseIf\b', r'\bMod\b', r'\bAndAlso\b'],
    'java': [r'\bpublic\b', r'\bstatic\b', r'\bvoid\b', r'System\.out', r';\s*(//.*)?$', r'^\s*[{}]\s*$', r'\{\s*$',
             r'\b(int|String|boolean|double|char)\s+\w+\s*[=;,\)]', r'\+\+', r'\bfor\s*\(', r'\bnew \w+\(', r'\bScanner\b',
             r'\bthrows\b', r'\bcatch\s*\('],
    'pascal': [r'^\s*begin\b', r'^\s*end\s*;', r':=', r'^\s*var\b', r'\bwrite(ln)?\(', r'\bread(ln)?\(',
               r'^\s*(procedure|function)\b', r':\s*(integer|string|real|boolean|char)\s*;', r'\bthen\b', r'\bdo\b\s*$'],
    'sql': [r'^\W*(MP\d\s+)?SELECT', r'^\W*(MP\d\s+)?FROM', r'^\W*(MP\d\s+)?WHERE', r'^\W*ORDER ?BY', r'^\s*(CREATE|ALTER) TABLE\b', r'^\s*INSERT INTO\b',
            r'^\s*UPDATE\b', r'^\s*ORDER BY\b', r'\bPRIMARY KEY\b', r'^\s*GROUP BY\b', r'^\s*INNER JOIN\b'],
    'assembly': [r'^\s*(\w+:\s*)?(LDM|LDD|LDI|LDX|LDR|STO|ADD|SUB|INC|DEC|JMP|CMP|CMI|JPE|JPN|IN|OUT|END|AND|XOR|OR|LSL|LSR|MOV)\b\s*[#&B]?\w*\s*$'],
    'prolog': [r':-', r'^\s*\w+\(\w+(,\s*\w+)*\)\.\s*$'],
    'web': [r'<\w+>', r'</\w+>', r'\bdocument\.', r'\bvar \w+\s*=', r'<\?php', r'\$\w+'],
}
FEATURES = {k: [re.compile(p) for p in v] for k, v in FEATURES.items()}


LINENO = re.compile(r'^\s*\d{1,3}\s{1,6}(?=\S)')


def label_language(context):
    for text in reversed(context[-3:]):
        for lang, rx in LABEL_RE:
            if rx.search(text) and len(text) < 60:
                return lang
    return None


def score(text):
    sc = collections.Counter()
    for line in text.split('\n'):
        line = LINENO.sub('', line)
        for lang, pats in FEATURES.items():
            for p in pats:
                if p.search(line):
                    sc[lang] += 1
    return sc


def classify(block):
    text = block['text']
    sc = score(text)
    lab = label_language(block.get('context', []))
    if lab and lab != 'pseudocode':
        # a label applies when the code does not look strongly like something else
        best = sc.most_common(1)[0] if sc else (lab, 0)
        if sc[lab] > 0 or best[1] <= 1:
            return lab, 'label'
    if not sc:
        return 'unclassified', 'none'
    if sc['sql'] >= 2:
        return 'sql', 'keywords'
    lang, n = sc.most_common(1)[0]
    if n < 2 and lang != 'pseudocode':
        return 'unclassified', 'weak'
    if lang == 'pseudocode' and n < 2 and '\u2190' not in text:
        return 'unclassified', 'weak'
    # pseudocode vs VB 'Then'/'Next' collisions: uppercase keywords favour pseudocode
    if lang == 'visual_basic' and sc['pseudocode'] >= n:
        lang = 'pseudocode'
    if n < 1:
        return 'unclassified', 'none'
    return lang, 'keywords'


def norm_hash(text):
    t = re.sub(r'\s+', ' ', text).strip().lower()
    return hashlib.sha1(t.encode()).hexdigest()[:16]


def meta_from_name(fname):
    m = re.match(r'(\d{4})_([msw])(\d{2})_ms_(\d)(\d)', fname)
    syl, sess, yy, paper, variant = m.groups()
    return {'syllabus': syl, 'session': sess, 'year': 2000 + int(yy), 'paper': int(paper), 'variant': int(variant)}


def main():
    src, dst = sys.argv[1], sys.argv[2]
    seen = {}
    with open(dst, 'w', encoding='utf-8') as out:
        for line in open(src, encoding='utf-8'):
            b = json.loads(line)
            b.update(meta_from_name(b['file']))
            b['language'], b['language_basis'] = classify(b)
            h = norm_hash(b['text'])
            b['text_hash'] = h
            b['duplicate_of'] = seen.get(h)
            if h not in seen:
                seen[h] = b['id']
            out.write(json.dumps(b, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
