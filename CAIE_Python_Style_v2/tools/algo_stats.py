import sys, json, re, collections
sys.path.insert(0, sys.argv[2])
from style_stats import group_of
rows = [json.loads(l) for l in open(sys.argv[1], encoding='utf-8')]
rows = [b for b in rows if not b['duplicate_of'] and b['language'] in ('pseudocode', 'python') and group_of(b)]
c = collections.Counter(); ex = collections.defaultdict(list)
def hit(key, b):
    c[(b['language'], group_of(b).split('-')[0], key)] += 1
    if len(ex[key]) < 4: ex[key].append(b['id'])
for b in rows:
    t = b['text']
    # bubble sort detection: adjacent compare + temp swap
    if re.search(r'\[\s*\w+\s*\+\s*1\s*[\],]', t) and re.search(r'\b(Temp\w*|temp)\s*(←|=)', t) and re.search(r'>|<', t):
        if re.search(r'NoSwaps|Swap|Swapped|Flag|Sorted|DataSwapped', t):
            if re.search(r'^\s*REPEAT', t, re.M): hit('bubble: flag + REPEAT/UNTIL', b)
            elif re.search(r'^\s*WHILE|^\s*while', t, re.M): hit('bubble: flag + WHILE', b)
            else: hit('bubble: flag (other)', b)
        else:
            hit('bubble: nested FOR, no flag', b)
        if re.search(r'Boundary\s*(←|=)\s*Boundary\s*-\s*1|Last\s*(←|=)\s*Last\s*-\s*1|NumberItems\s*←\s*NumberItems - 1|Outer\s*(←|=)\s*Outer\s*-\s*1', t):
            hit('bubble: shrinking boundary', b)
    if re.search(r'\w+\[\w+\]\s*,\s*\w+\[\w+\s*\+\s*1\]\s*=\s*\w+\[\w+\s*\+\s*1\]\s*,', t):
        hit('python tuple swap', b)
    # insertion sort
    if re.search(r'(ItemToInsert|ValueToInsert|CurrentValue|Current2|Temp1|LastItem|Value)\s*(←|=)\s*\w+\[', t) and re.search(r'(WHILE|while).*(>|<)', t) and re.search(r'\[\s*\w+\s*\+\s*1\s*\]\s*(←|=)\s*\w+\[|\[\s*\w+\s*\]\s*(←|=)\s*\w+\[\s*\w+\s*-\s*1', t):
        hit('insertion sort', b)
    # binary search
    if re.search(r'(Mid|Middle|MidValue|Midpoint|MidPoint|CurrentItem)\s*(←|=)\s*.*(DIV\s*2|/\s*2|//\s*2|\\\s*2)', t):
        hit('binary search', b)
        if re.search(r'(Find|Search|BinarySearch)\w*\(.*(Mid|Middle)\s*[-+]\s*1', t): hit('binary search: recursive', b)
    # linear search forms
    if re.search(r'Found\w*\s*(←|=)\s*(FALSE|False)', t) or re.search(r'(Found|Flag)\s*(←|=)\s*(TRUE|True)', t):
        if re.search(r'^\s*(WHILE|while)\b.*(NOT\s+Found|Found\s*=\s*FALSE|Found\s*==\s*False|not\s+Found|not\(Found\))', t, re.M | re.I): hit('search: WHILE ... AND NOT Found', b)
        elif re.search(r'^\s*UNTIL\b.*Found', t, re.M): hit('search: REPEAT ... UNTIL Found OR end', b)
    if re.search(r'^\s*(FOR|for)\b[\s\S]*?^\s*(RETURN|return)\b', t, re.M) and re.search(r'(RETURN|return)\s+(-1|FALSE|False|–\s*1)', t):
        hit('search: FOR with early RETURN', b)
    if re.search(r'(←|=)\s*-1\b', t) and re.search(r'(RETURN|return)\s+\w+', t) and re.search(r'Index|Pos|RetVal|Location|Position', t):
        hit('not-found sentinel -1', b)
    # max / min initialisation
    m = re.search(r'\b(Max|Min|Highest|Lowest|Largest|Smallest|High|Low|Large|Small|MaxWeek|MinWeek|Larea|Sarea|LowestScore|Highest\w*)\s*(←|=)\s*([^\n]+)', t)
    if m:
        rhs = m.group(3).strip()
        if re.match(r'^[\w]+\s*\[\s*(0|1)\s*(,\s*\w+)?\]$', rhs) or re.match(r'^\w+\[\w+\]$', rhs) and 'Counter' not in rhs:
            hit('max/min init: first element', b)
        elif re.match(r'^-?\d+(\.\d+)?$', rhs.replace('−', '-').replace('–', '-')):
            hit('max/min init: literal sentinel', b)
        elif re.match(r'^[A-Za-z]\w*$', rhs):
            hit('max/min init: from variable (e.g. first input)', b)
    # totals / averages
    if re.search(r'\bTotal\w*\s*(←|=)\s*Total\w*\s*\+', t) or re.search(r'\bSum\s*(←|=)\s*Sum\s*\+', t):
        hit('running total', b)
    if re.search(r'\b(Count\w*|Counter)\s*(←|=)\s*(Count\w*|Counter)\s*\+\s*1', t):
        hit('counter +1', b)
    # string traversal with MID / index
    if re.search(r'MID\(\s*\w+\s*,\s*\w+\s*,\s*1\s*\)', t): hit('string: MID(S, i, 1) char loop', b)
    if re.search(r'\w+\[\w+\]\s*$|\w+\[\w+:\w+\s*\+\s*1\]', t) and b['language'] == 'python' and re.search(r'for\s+\w+\s+in\s+range\(.*len\(', t): hit('python string: index loop over len()', b)
    # file loops
    if re.search(r'WHILE NOT EOF', t): hit('file: WHILE NOT EOF(...)', b)
    if re.search(r'readline\(\)', t) and re.search(r'while\s+\w+\s*!=\s*""|while\s+len\(', t): hit('python file: readline until ""', b)
    if re.search(r'for\s+\w+\s+in\s+\w*[Ff]ile\w*\s*:', t): hit('python file: for Line in File', b)
    if re.search(r'\.read\(\)\.split', t): hit('python file: read().split', b)
    if re.search(r'except\s+IOError', t): hit('python: except IOError', b)
    if re.search(r'^\s*except\s*:', t, re.M): hit('python: bare except', b)
    # stacks/queues
    if re.search(r'(Top\w*|StackPointer|SP)\s*(←|=|\+=)\s*(Top\w*|StackPointer|SP)?\s*[+-]?\s*1', t) and re.search(r'Push|Pop|Stack', t): hit('stack with pointer', b)
    if re.search(r'(Head|Tail|Front|Rear)\w*\s*(←|=)', t) and re.search(r'Enqueue|Dequeue|Queue', t): hit('queue with head/tail pointers', b)
    if re.search(r'(Tail\w*|Rear\w*|Head\w*|Front\w*)\s*(←|=)\s*(0|1)\b', t) and re.search(r'(>|>=|=)\s*(MaxSize|\d+)', t) and re.search(r'Enqueue|Dequeue', t): hit('queue: circular wrap', b)
for k in sorted(c, key=lambda k: (k[2], k[0], k[1])):
    print(f'{k[2]:45s} {k[0]:10s} {k[1]:3s} {c[k]:4d}')
print()
for k, v in ex.items(): print(k, v)
