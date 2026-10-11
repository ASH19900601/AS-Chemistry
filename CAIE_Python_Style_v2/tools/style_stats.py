"""Quantitative style statistics for CAIE mark-scheme pseudocode and Python.

Usage: python -I style_stats.py classified.jsonl OUT_DIR

Counts are made over unique (de-duplicated) code blocks. Groups:
  IG-0478-old   0478 Paper 2, 2016-2022 (pre-2023 syllabus)
  IG-0478-new   0478 Paper 2, 2023-2025 (2023 syllabus onwards)
  AS-9608       9608 Paper 2 (2016-2021)
  AS-9618       9618 Paper 2 (2021-2025)
  AL-9608       9608 Paper 4 (2016-2021)  [Paper 3 merged in]
  AL-9618       9618 Papers 3/4 (2021-2025)
"""
import sys, os, re, json, collections, csv

PSEUDO_KEYWORDS = set("""
IF THEN ELSE ENDIF END ENDWHILE WHILE DO FOR TO STEP NEXT ENDFOR REPEAT UNTIL CASE OF OTHERWISE ENDCASE
PROCEDURE ENDPROCEDURE FUNCTION ENDFUNCTION RETURNS RETURN CALL DECLARE CONSTANT ARRAY INTEGER REAL STRING CHAR
BOOLEAN DATE TRUE FALSE AND OR NOT MOD DIV INPUT OUTPUT PRINT OPENFILE READFILE WRITEFILE CLOSEFILE READ WRITE
APPEND RANDOM EOF BYREF BYVAL BYVALUE TYPE ENDTYPE CLASS ENDCLASS PUBLIC PRIVATE NEW INHERITS SUPER SEEK
GETRECORD PUTRECORD OPEN CLOSE NULL BREAK
""".split())
LIBRARY = ['LENGTH', 'LEN', 'MID', 'LEFT', 'RIGHT', 'SUBSTRING', 'UCASE', 'LCASE', 'TO_UPPER', 'TO_LOWER',
           'NUM_TO_STR', 'STR_TO_NUM', 'NUM_TO_STRING', 'STRING_TO_NUM', 'TONUM', 'INT', 'ROUND', 'RANDOM',
           'RAND', 'RND', 'MOD', 'DIV', 'ASC', 'CHR', 'EOF', 'IS_NUM', 'ISNUM', 'DAY', 'MONTH', 'YEAR',
           'DAYINDEX', 'SETDATE', 'TODAY', 'NOW', 'SQRT', 'CHARACTERCOUNT', 'ONECHAR']
LIB_SET = set(LIBRARY)
LINENO = re.compile(r'^\s*\d{1,3}\s{1,6}(?=\S)')


def group_of(b):
    syl, paper, year = b['syllabus'], b['paper'], b['year']
    if syl == '0478':
        if paper != 2:
            return None
        return 'IG-0478-old' if year < 2023 else 'IG-0478-new'
    if paper in (1,):
        return None
    if paper == 2:
        return 'AS-' + syl
    return 'AL-' + syl


def strip_strings_comments(line, comment='//'):
    line = re.sub(r'"[^"]*"', '""', line)
    line = re.sub(r"'[^']*'", "''", line)
    if comment in line:
        line = line.split(comment)[0]
    return line


def case_style(name):
    if len(name) == 1:
        return 'single-letter'
    if '_' in name.strip('_'):
        parts = [p for p in name.split('_') if p]
        if all(p.isupper() or p.isdigit() for p in parts):
            return 'UPPER_SNAKE'
        if all(p[:1].isupper() for p in parts):
            return 'Pascal_Snake'
        return 'snake_case'
    if name.isupper():
        return 'UPPERCASE'
    if name.islower():
        return 'lowercase'
    if name[0].isupper():
        if any(ch.isupper() or ch.isdigit() for ch in name[1:]):
            return 'PascalCase (multi-word)'
        return 'Capitalised (one word)'
    return 'camelCase'


def pseudo_stats(blocks):
    c = collections.Counter()
    names = collections.defaultdict(set)       # style -> names
    subprog = collections.Counter()
    subprog_names = collections.defaultdict(set)
    loopvars = collections.Counter()
    assign_targets = collections.Counter()
    lib = collections.Counter()
    array_lb = collections.Counter()
    for_start = collections.Counter()
    seen_names = set()
    for b in blocks:
        text = b['text']
        lines = [LINENO.sub('', l) for l in text.split('\n')]
        c['blocks'] += 1
        c['lines'] += len(lines)
        if b['nlines'] >= 4:
            c['blocks_4plus'] += 1
        joined = '\n'.join(lines)
        for raw in lines:
            line = strip_strings_comments(raw)
            s = line.strip()
            if not s:
                continue
            if '//' in raw:
                c['comment_lines'] += 1
            # assignment operator
            if re.match(r'^[A-Za-z_][\w.\[\], ]*(\[[^\]]*\])?\s*←', s):
                c['assign_arrow'] += 1
                tgt = re.match(r'^([A-Za-z_]\w*)', s).group(1)
                assign_targets[tgt] += 1
            elif re.match(r'^[A-Za-z_]\w*(\[[^\]]*\])?\s*=\s*[^=]', s) and not re.match(r'^(IF|WHILE|UNTIL|CASE|FOR|ELSE|OUTPUT|PRINT|RETURN)\b', s):
                c['assign_equals'] += 1
            if re.match(r'^OUTPUT\b', s):
                c['OUTPUT'] += 1
                if '&' in s:
                    c['OUTPUT_with_&'] += 1
                if ',' in s:
                    c['OUTPUT_with_comma'] += 1
            if re.match(r'^PRINT\b', s, re.I):
                c['PRINT'] += 1
            if re.match(r'^INPUT\b', s):
                c['INPUT'] += 1
                if re.match(r'^INPUT\s+"', raw.strip()):
                    c['INPUT_with_prompt'] += 1
            if re.match(r'^IF\b', s):
                c['IF'] += 1
                if re.search(r'\bTHEN\b', s):
                    c['IF_THEN_same_line'] += 1
            if re.match(r'^THEN\b', s):
                c['THEN_own_line'] += 1
            if re.match(r'^ELSE\s*IF\b|^ELSEIF\b', s):
                c['ELSEIF'] += 1
            if re.match(r'^END\s?IF\b', s):
                c['ENDIF'] += 1
            m = re.match(r'^FOR\s+([A-Za-z_]\w*)\s*(←|=)\s*(.+?)\s+(TO|To|to)\s+(.+?)(\s+STEP\s+(.+))?$', s)
            if m:
                c['FOR'] += 1
                loopvars[m.group(1)] += 1
                start = m.group(3).strip()
                for_start[start if start in ('0', '1') else 'other'] += 1
                if m.group(6):
                    c['FOR_STEP'] += 1
                    if m.group(7).strip().startswith(('-', '–', '−')):
                        c['FOR_STEP_negative'] += 1
            if re.match(r'^NEXT\s+[A-Za-z_]\w*', s):
                c['NEXT_var'] += 1
            elif re.match(r'^NEXT\b', s, re.I):
                c['NEXT_bare'] += 1
            if re.match(r'^ENDFOR\b|^END FOR\b', s):
                c['ENDFOR'] += 1
            if re.match(r'^WHILE\b', s):
                c['WHILE'] += 1
                if re.search(r'\bDO\b', s):
                    c['WHILE_DO'] += 1
            if re.match(r'^END\s?WHILE\b', s):
                c['ENDWHILE'] += 1
            if re.match(r'^REPEAT\b', s):
                c['REPEAT'] += 1
            if re.match(r'^UNTIL\b', s):
                c['UNTIL'] += 1
            if re.match(r'^CASE\s+OF\b', s):
                c['CASE_OF_x'] += 1
            elif re.match(r'^CASE\b.+\bOF\b', s, re.I):
                c['CASE_x_OF'] += 1
            if re.match(r'^OTHERWISE\b', s):
                c['OTHERWISE'] += 1
            if re.match(r'^DECLARE\b', s):
                c['DECLARE'] += 1
                for nm in re.findall(r'DECLARE\s+([\w, ]+?)\s*:', s):
                    for n in nm.split(','):
                        n = n.strip()
                        if n and n not in PSEUDO_KEYWORDS:
                            assign_targets[n] += 0
                am = re.search(r'ARRAY\s*\[\s*([^\]:]+?)\s*:', s)
                if am:
                    array_lb[am.group(1).strip()] += 1
                    c['ARRAY_decl'] += 1
                    if re.search(r'ARRAY\s*\[[^\]]*,[^\]]*\]', s):
                        c['ARRAY_2D_decl'] += 1
            if re.match(r'^CONSTANT\b', s):
                c['CONSTANT'] += 1
            if re.search(r'\bBYREF\b', s, re.I):
                c['BYREF'] += 1
            if re.search(r'\bBYVAL(UE)?\b', s, re.I):
                c['BYVAL'] += 1
            if re.match(r'^CALL\b', s, re.I):
                c['CALL'] += 1
            if re.match(r'^RETURN\b', s):
                c['RETURN'] += 1
            if re.match(r'^TYPE\b', s):
                c['TYPE'] += 1
            if re.match(r'^CLASS\b', s):
                c['CLASS'] += 1
            if re.match(r'^BREAK\b', s, re.I):
                c['BREAK'] += 1
            if re.search(r'OPENFILE\b.*\bFOR\s+READ', s):
                c['OPENFILE_READ'] += 1
            if re.search(r'OPENFILE\b.*\bFOR\s+WRITE', s):
                c['OPENFILE_WRITE'] += 1
            if re.search(r'OPENFILE\b.*\bFOR\s+APPEND', s):
                c['OPENFILE_APPEND'] += 1
            if re.search(r'OPENFILE\b.*\bFOR\s+RANDOM', s):
                c['OPENFILE_RANDOM'] += 1
            if re.search(r'\bEOF\s*\(', s):
                c['EOF'] += 1
            if re.search(r'=\s*TRUE\b|=\s*FALSE\b|<>\s*TRUE\b|<>\s*FALSE\b', s, re.I) and re.match(r'^(IF|WHILE|UNTIL)\b', s):
                c['bool_compare_explicit'] += 1
            elif re.match(r'^(IF|WHILE|UNTIL)\b', s) and re.search(r'\bNOT\s+[A-Z]\w*\b(?!\s*\()', s):
                c['bool_NOT_bare'] += 1
            if re.search(r'\[[^\]]*\]', s):
                c['lines_with_square_index'] += 1
            if re.search(r'\b[A-Z]\w*\s?\(\s*[A-Za-z]\w*\s*\)\s*(←|=|$)', s) and not re.search(r'\b(' + '|'.join(LIBRARY) + r')\s*\(', s):
                c['lines_with_paren_index_guess'] += 1
            for f in re.findall(r'\b([A-Z_]{2,})\s*\(', s):
                if f in LIB_SET:
                    lib[f] += 1
            for f in re.findall(r'\b(MOD|DIV)\b', s):
                lib[f + '_operator_or_call'] += 1
            # subprogram headers
            m = re.match(r'^(PROCEDURE|FUNCTION)\s+([A-Za-z_][\w-]*)', s, re.I)
            if m:
                subprog[m.group(1).upper()] += 1
                st = case_style(m.group(2))
                subprog_names[st].add(m.group(2))
        # identifier collection: assignment targets, declared names, loop vars, params
        idents = set()
        for raw in lines:
            s = strip_strings_comments(raw).strip()
            m = re.match(r'^([A-Za-z_]\w*)\s*(\[[^\]]*\])?\s*←', s)
            if m:
                idents.add(m.group(1))
            for nm in re.findall(r'DECLARE\s+([\w, ]+?)\s*:', s):
                for n in nm.split(','):
                    if n.strip():
                        idents.add(n.strip())
            m = re.match(r'^FOR\s+([A-Za-z_]\w*)', s)
            if m:
                idents.add(m.group(1))
            m = re.match(r'^(?:PROCEDURE|FUNCTION)\s+[\w-]+\s*\((.*)\)', s, re.I)
            if m:
                for p in re.findall(r'([A-Za-z_]\w*)\s*(?::|,|$)', re.sub(r'\b(BYREF|BYVAL|BYVALUE)\b', '', m.group(1), flags=re.I)):
                    if p.upper() not in PSEUDO_KEYWORDS:
                        idents.add(p)
        for n in idents:
            if n.upper() in PSEUDO_KEYWORDS or n in LIB_SET:
                continue
            key = (b['file'], n)
            if key in seen_names:
                continue
            seen_names.add(key)
            names[case_style(n)].add(n)
            c['ident_occurrences'] += 1
    return {
        'counts': dict(c),
        'identifier_styles_unique_names': {k: len(v) for k, v in names.items()},
        'identifier_style_examples': {k: sorted(v)[:25] for k, v in names.items()},
        'subprogram_counts': dict(subprog),
        'subprogram_name_styles': {k: len(v) for k, v in subprog_names.items()},
        'subprogram_name_examples': {k: sorted(v)[:30] for k, v in subprog_names.items()},
        'loop_variables_top': loopvars.most_common(25),
        'assignment_targets_top': assign_targets.most_common(60),
        'library_routines': lib.most_common(),
        'array_lower_bounds': array_lb.most_common(10),
        'for_start_values': dict(for_start),
    }


def python_stats(blocks):
    c = collections.Counter()
    names = collections.defaultdict(set)
    defs = collections.defaultdict(set)
    seen = set()
    for b in blocks:
        lines = b['text'].split('\n')
        c['blocks'] += 1
        c['lines'] += len(lines)
        text = b['text']
        for raw in lines:
            s = raw.strip()
            code = strip_strings_comments(s, '#')
            if re.match(r'^#', s):
                c['comment_lines'] += 1
                if re.search(r'(:\s*|\bAs\s+|\bas\s+|DECLARE\s+.*:\s*)(INTEGER|STRING|REAL|BOOLEAN|CHAR|Integer|String|Real|Boolean|Char|integer|string|real|boolean|char|int|str|float|bool|File|file|Date|date|single|Single)', s):
                    c['declaration_comment'] += 1
                if re.match(r'^#\s*DECLARE\b', s):
                    c['declaration_comment_DECLARE_form'] += 1
            elif re.search(r'#\s*(integer|string|real|boolean|char|int|str|float|Integer|String|Real|Boolean|single|Single|INTEGER|STRING)\b', s):
                c['trailing_type_comment'] += 1
            if re.match(r'^global\b', code):
                c['global_stmt'] += 1
            if re.match(r'^def\s', code):
                c['def'] += 1
                m = re.match(r'^def\s+([A-Za-z_]\w*)\s*\((.*)\)', code)
                if m:
                    defs[case_style(m.group(1).strip('_'))].add(m.group(1))
                    if m.group(1).startswith('__') and not m.group(1).endswith('__'):
                        c['private_method'] += 1
            if re.match(r'^class\s', code):
                c['class'] += 1
            # self._X is how five 2023-2025 schemes print self.__X (drawn underscores)
            if re.search(r'self\._{1,2}[A-Za-z]', code):
                c['private_attr_use'] += 1
            elif re.search(r'self\.\s?[A-Za-z]', code):
                c['public_attr_use'] += 1
            if re.search(r'super\(\)\.\s*_{0,2}init', code):
                c['super_init'] += 1
            if re.search(r'\b[A-Z]\w*\.__init__\(self', code):
                c['parent_init_explicit'] += 1
            if re.search(r'\bdef\s+(Get|get)[A-Z]\w*\(self', code):
                c['getter'] += 1
            if re.search(r'\bdef\s+(Set|set)[A-Z]\w*\(self', code):
                c['setter'] += 1
            m = re.match(r'^for\s+(\w+)\s+in\s+(.+):', code)
            if m:
                c['for'] += 1
                it = m.group(2)
                if re.match(r'range\s*\(\s*0\s*,', it):
                    c['for_range_0_n'] += 1
                elif re.match(r'range\s*\(\s*1\s*,', it):
                    c['for_range_1_n'] += 1
                elif re.match(r'range\s*\(\s*[^,()]+\)\s*$', it):
                    c['for_range_n'] += 1
                elif re.match(r'range\s*\(', it):
                    c['for_range_other'] += 1
                else:
                    c['for_each_item'] += 1
                    if re.search(r'File|file|Line', it):
                        c['for_line_in_file'] += 1
            if re.match(r'^while\b', code):
                c['while'] += 1
                if re.match(r'^while\s*\(?\s*True\s*\)?\s*:', code) or re.match(r'^while\s*\(1\)', code):
                    c['while_True'] += 1
            if re.match(r'^break\b', code):
                c['break'] += 1
            if re.match(r'^(\w+)\s*=\s*\1\s*\+\s*1\b', code) or re.match(r'^([\w.]+)\s*=\s*\1\s*\+\s*1\b', code):
                c['incr_X_eq_X_plus_1'] += 1
            if re.search(r'\+=\s*1\b', code):
                c['incr_plus_equals'] += 1
            if re.search(r'==\s*(True|False|TRUE|FALSE|true|false)\b', code):
                c['compare_eq_bool'] += 1
            if re.search(r'\bnot\s*[(A-Za-z]', code):
                c['not_operator'] += 1
            if re.search(r'\[[^\]]*\bfor\b[^\]]*\bin\b[^\]]*\]', code):
                c['list_comprehension'] += 1
            if re.search(r'\[[^\]\[]*\]\s*\*\s*\w+', code):
                c['list_times_n'] += 1
            if re.search(r'\.append\(', code):
                c['append'] += 1
            if re.search(r'=\s*\[\s*\]', code):
                c['empty_list_init'] += 1
            if re.search(r'=\s*\[(\s*[-\w."\']+\s*,){3,}', code):
                c['literal_list_init'] += 1
            if re.search(r'\blambda\b', code):
                c['lambda'] += 1
            if re.search(r'\b(sorted|\.sort)\s*\(', code):
                c['sort_builtin'] += 1
            if re.search(r'\b(min|max|sum)\s*\(', code):
                c['min_max_sum'] += 1
            if re.search(r'\bin\s+[A-Za-z_]\w*\s*:', code) and not re.match(r'^for\b', code):
                c['in_membership'] += 1
            if re.search(r'\.index\(', code):
                c['index_method'] += 1
            if re.search(r'\bopen\s*\(', code):
                c['open'] += 1
            if re.search(r'\bwith\s+open\b', code):
                c['with_open'] += 1
            if re.search(r'\.readline\(\)', code):
                c['readline'] += 1
            if re.search(r'\.read\(\)', code):
                c['read_all'] += 1
            if re.search(r'\.close\b', code):
                c['close'] += 1
            if re.search(r'\.strip\(|\.rstrip\(', code):
                c['strip'] += 1
            if re.search(r'\.split\(', code):
                c['split'] += 1
            if re.match(r'^try\s*:', code):
                c['try'] += 1
            if re.match(r'^except\s*:', code):
                c['except_bare'] += 1
            elif re.match(r'^except\s+\w', code):
                c['except_named'] += 1
            if re.search(r'\bprint\s*\(', code):
                c['print'] += 1
                if re.search(r'\bprint\s*\(.*[^=!<>]".*",', s) or re.search(r'print\s*\([^)]*,\s*[A-Za-z]', s):
                    c['print_with_commas'] += 1
                if re.search(r'\+\s*str\(|str\([^)]*\)\s*\+', s):
                    c['print_str_concat'] += 1
            if re.search(r'\bf"|\bf\'', s):
                c['f_string'] += 1
            if re.search(r'"\s*%\s*\(|\.format\(', s):
                c['percent_or_format'] += 1
            if re.search(r'\binput\s*\(', code):
                c['input'] += 1
                if re.search(r'\bint\s*\(\s*input', code) or re.search(r'\bfloat\s*\(\s*input', code):
                    c['input_converted'] += 1
            if re.match(r'^return\b', code, re.I):
                c['return'] += 1
                if re.match(r'^return\s*\(?[^()]+,[^()]+\)?\s*$', code):
                    c['return_tuple'] += 1
            if re.match(r'^[\w\[\]]+\s*,\s*[\w\[\]]+(\s*,\s*[\w\[\]]+)*\s*=\s*\S', code):
                c['multiple_assignment'] += 1
            if re.search(r'(\w+\[[^\]]+\])\s*,\s*(\w+\[[^\]]+\])\s*=\s*\2\s*,\s*\1', code):
                c['tuple_swap'] += 1
            if re.match(r'^(Temp|temp|TempNumber|Temp\w*)\s*=\s*\w+\[', code):
                c['temp_swap_start'] += 1
            if re.match(r'^[A-Z][A-Z_]+\s*=\s*', code):
                c['UPPER_constant_assign'] += 1
            if re.search(r'\brandom\.|\brandint\(', code):
                c['random'] += 1
            # identifiers: assignment targets
            m = re.match(r'^([A-Za-z_]\w*)\s*(\[[^\]]*\])*\s*=\s*[^=]', code)
            if m and m.group(1) not in ('self',):
                key = (b['file'], m.group(1))
                if key not in seen:
                    seen.add(key)
                    names[case_style(m.group(1))].add(m.group(1))
            m = re.match(r'^self\._{1,2}([A-Za-z]\w*)\s*=', code)
            if m:
                key = (b['file'], 'self.__' + m.group(1))
                if key not in seen:
                    seen.add(key)
                    names['attr:' + case_style(m.group(1))].add(m.group(1))
    return {
        'counts': dict(c),
        'identifier_styles_unique_names': {k: len(v) for k, v in names.items()},
        'identifier_style_examples': {k: sorted(v)[:25] for k, v in names.items()},
        'def_name_styles': {k: len(v) for k, v in defs.items()},
        'def_name_examples': {k: sorted(v)[:30] for k, v in defs.items()},
    }


def main():
    src, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    pseudo = collections.defaultdict(list)
    py = collections.defaultdict(list)
    for line in open(src, encoding='utf-8'):
        b = json.loads(line)
        if b['duplicate_of']:
            continue
        g = group_of(b)
        if g is None:
            continue
        if b['language'] == 'pseudocode':
            pseudo[g].append(b)
        elif b['language'] == 'python':
            py[g].append(b)
    result = {'pseudocode': {}, 'python': {}}
    for g in sorted(pseudo):
        result['pseudocode'][g] = pseudo_stats(pseudo[g])
    for g in sorted(py):
        result['python'][g] = python_stats(py[g])
    with open(os.path.join(outdir, 'style_statistics.json'), 'w', encoding='utf-8') as fh:
        json.dump(result, fh, indent=1, ensure_ascii=False)
    # flat CSV of counts
    for kind in ('pseudocode', 'python'):
        groups = sorted(result[kind])
        keys = sorted({k for g in groups for k in result[kind][g]['counts']})
        with open(os.path.join(outdir, f'{kind}_counts.csv'), 'w', newline='', encoding='utf-8') as fh:
            w = csv.writer(fh)
            w.writerow(['metric'] + groups)
            for k in keys:
                w.writerow([k] + [result[kind][g]['counts'].get(k, 0) for g in groups])
        keys = sorted({k for g in groups for k in result[kind][g]['identifier_styles_unique_names']})
        with open(os.path.join(outdir, f'{kind}_identifier_styles.csv'), 'w', newline='', encoding='utf-8') as fh:
            w = csv.writer(fh)
            w.writerow(['style'] + groups)
            for k in keys:
                w.writerow([k] + [result[kind][g]['identifier_styles_unique_names'].get(k, 0) for g in groups])


if __name__ == '__main__':
    main()
