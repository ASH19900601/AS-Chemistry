# Audit of `CAIE_Python_Style_v1.0.0`

This lists what in the previous package (the zip you supplied) is inaccurate or unsupported,
checked against the re-extracted corpus and the official documents. Section numbers refer to
`Style_Analysis.md`. Items are ordered by how much they affect the conclusions.

## A. Extraction and corpus

| # | Problem in v1 | Evidence | Effect |
|---|---|---|---|
| A1 | Pages stored with a rotation were not handled. Text from the code column and the marking column of 108 documents (mostly 2020–2025 IGCSE and Paper 4) was interleaved. | v1 `IG_pseudocode.txt` has 66 lines with two statements side by side, e.g. `WHILE Correct = "N"   INPUT PassengerID[Index]   INPUT JourneyTime[Index]` for 0478_w21_ms_22 p5. | IGCSE 2020–2025 code was largely unreadable, so era differences were missed. |
| A2 | The "Python" corpus mixes in other languages and fragments. | Of the 1 362 blocks in v1 `AL_python.txt`, 398 are one-line fragments; about 311 have Java markers (`;`, `System.out`), 101 Pascal (`begin`, `:=`), 79 VB (`Dim`, `End Sub`). For example `Procedure SetPlayerID () … WriteLn (…)` and `Constructor Player.Create(…)` are labelled Python (9608_s19_ms_41 p6–p8). v1 `AS_python.txt` has 20 Pascal-like and 14 Java-like blocks out of 118. | Statistics such as "AL python: `File` (16), `ReadData` (16)" and the reported 1 362 Python blocks do not describe Python. The real figure is 478 unique Python blocks. |
| A3 | Assignment arrows drawn in Wingdings fonts (2016–2020 IGCSE) were lost. | v1 IG text shows `Donation    BillValue * 0.01` (0478_w16_ms_22) and `Count    0` / `Count    Count + 1` (0478_w17_ms_21). | Old IGCSE assignments look like gaps. |
| A4 | "Fake bold" text (each glyph printed twice) was dropped or corrupted. | The alarm algorithm of 9608_s16_ms_21 and the `Decrypt` function of 9608_s16_ms_23 are missing from v1; 9608_s18_ms_23 appears as `CASE OFF ThisMarrk`. | Some 2016–2018 AS answers are missing or garbled. |
| A5 | Underscores drawn as lines (five 2023–2025 Paper 4 schemes) were lost. | `def init (self, …)` and `self. ID` for `__init__` / `self.__ID` (9618_w23_ms_41 p16). | Private attributes in recent Python answers look public. |
| A6 | Blocks continued over a page break were not joined, and code split by marking prose was not separated. | v1 notes "跨页算法不自动合并". | Long answers (15-mark IGCSE questions, Paper 4 programs) appear as fragments. |
| A7 | Inline code words in marking text were kept as code candidates. | v1 summary: 828 IG "pseudocode candidate blocks"; many are single identifiers from marking points. | Counts of blocks and names are inflated. |

## B. Statements in `Style_Analysis_zh.md` and `Evidence_Catalog.md`

| # | v1 statement | What the evidence shows |
|---|---|---|
| B1 | §6 "CAIE 数组不统一从 1 开始" (arrays are not uniformly 1-based), illustrated with one 0–23 array; "新 Python 项目默认从 0 开始". | True but misleading. The 9618 guide says "Generally, a lower bound of 1 will be used"; of the `FOR` loops that start at 0 or 1, 89–98 % start at 1 in AS and 2023+ IGCSE answers; `ARRAY[1:…]` outnumbers `ARRAY[0:…]` 51 to 6 outside 9608 Papers 3–4. Zero is the exception (the index is a value, or old IGCSE, or 9608 Paper 4). The Python advice (0-based lists) is right, because Cambridge's Python is 0-based; the report should say the translation changes the bounds (§6.1). |
| B2 | §4 "官方 9618 指南描述了 mixed case … 没有要求 … PascalCase". | The 0478 syllabus (2023–2025, 2026–2028) requires "mixed case using Pascal case, e.g. FirstName … must start with a capital letter … the underscore should not be used". The schemes themselves credit "use of Camel Case" for `NumberOfPlayers`-style names (9618_s23_ms_22). |
| B3 | §3 and §4 present IGCSE naming as mixed ("历史答案也出现小写下划线名称及 PRINT"), using 0478_s16_ms_22 as "重要的历史反例". | The mixed styles belong to 2016–2022. From 2023, 95 % of IGCSE names are PascalCase and the rest are conventional single letters; `PRINT` falls from 101 lines to 4 (§4.1, §5). v1 never separates the eras, so differences between 0478 old/new and 9608/9618 (`ENDFOR` vs `NEXT`, `THEN` placement, `DECLARE`) are not explained. |
| B4 | §5 "允许 `Found == False` … 也允许 `not Found` … 前者是项目可选的阅读偏好". | Explicit comparison is the dominant Cambridge habit, not an optional preference: AS pseudocode 99 against 16; 9618 Paper 4 Python `== True/False` 33 against `not` 2 (§5, §8). |
| B5 | §5 shows `while True:` + `break` as the REPEAT translation. | Cambridge's Python uses a flag (`Valid = False` / `while Valid == False:`) or a primed variable; `while True` appears in 6 lines across all the Python answers (§8, §9.1). |
| B6 | §7 "最大最小值 … 错误地以 0 初始化" (initialising with 0 is wrong). | Cambridge accepts and often uses a sentinel outside the data range (`Large ← 0`, `Small ← 1000`, `Min ← 100`, `LowestScore ← 100`, `MaxWeek ← -1000`); it is wrong only when the range is unknown. First-element initialisation is the other accepted form (§9.3). |
| B7 | §7 and §10 forbid tuple swaps and comprehensions in general. | Correct as a project choice, but Cambridge's own Python uses comprehensions to create arrays (`[0 for I in range (100)]`, nested 2D forms; 14 lines) and tuple swaps in four 2022–2025 answers. The rule should allow the array-creation form and say that tuple swaps are avoided by choice (§6.3, §9.5). |
| B8 | §8 recommends a result record for multiple outputs as "本包选择". | Supported, but v1 does not show that Cambridge does this in pseudocode (`RETURNS Result`, 9618_w24_ms_21; `RETURNS PopData`, 9618_w25_ms_23) nor that Paper 4 Python returns tuples (`return (True, Queue, Head, Tail, NumItems)`, 9618_s22_ms_41) (§7). |
| B9 | §11 cites 9618_s25_ms_42 p13 to say globals and bare `except` should not be generalised; AGENTS.md says "Avoid arbitrary global state". | Globals are the normal Paper 4 style (148 `global` statements in 9618 Paper 4), not an exception. Whether to imitate them is a project decision; v2 allows module-level structures with `global` for single-structure programs and recommends classes beyond that (`AGENTS.md` §6). |
| B10 | Nothing on Cambridge's Python conventions. | Missing: declaration comments (`# DECLARE …`, `## X As Integer`), trailing type comments, `GetX`/`SetX`, `self.__PascalCase` attributes, constructor parameters ending in `P`, `#main` sections, `range(0, N)` with an explicit start, `print` with commas, no f-strings or `with` (§6.4, §8). |
| B11 | Nothing on the library routines and their Python equivalents per syllabus. | IGCSE `ROUND`, `RANDOM`, `SUBSTRING`, `MOD()`, `DIV()`; 9608 `NUM_TO_STRING`, `STRING_TO_NUM`, `ONECHAR`; 9618 `NUM_TO_STR`, `STR_TO_NUM`, `TO_UPPER`, `IS_NUM`, dates (§9.8). |
| B12 | Mark-scheme quality is mentioned only for exception handling. | Many Python answers are not valid Python (`FALSE`, `Return`, `<>`, missing colons, Python 2 `print`), and two contain the shared-row bug that v1 warns about (`[['*'] * 2] * 100`, 9608_w18_ms_21) (§8, §6.3). |
| B13 | `Corpus_Statistics.md`: "IG subprogram names: `Balance` (1), `CheckDetails` (1) …", "AL python variables: `File` (16) …". | Based on the contaminated corpus (A2) and fragment counts (A7); not usable. See `stats/style_statistics.json`. |

The six visual checks in `Evidence_Catalog.md` are correct: the cited pages say what the
catalogue says.

## C. Rules in `AGENTS.md` and `AI_Coding_Prompt.txt`

| v1 rule | Status in v2 |
|---|---|
| PascalCase for all names; never distinguish names by case; keep Python keywords as they are | Kept; strengthened with the 0478 "no underscore" rule and Cambridge vocabulary. |
| "Do not use comprehensions … in the core teaching algorithms" | Changed: the array-creation forms Cambridge uses are allowed; computing or filtering comprehensions remain forbidden. |
| "Prefer `for Index in range(LowerBound, UpperBound + 1)`" for every inclusive FOR loop | Changed: positions in 0-based lists use `range(0, N)` (Cambridge's form); value loops keep their values. |
| "A transparent `while True` loop with a final `if Finished: break` is permitted" for REPEAT | Changed: use a flag or primed variable; avoid `while True`. |
| "Avoid arbitrary global state" | Changed: module-level structures with `global` are allowed for single-structure programs, as in Paper 4. |
| "If several outputs are required, use a small named result record" | Kept, and tuple return with unpacking added as the Paper 4 alternative. |
| "`with open(...)` is allowed after explaining" | Changed: Cambridge never uses it; prefer `open` / `close` in `try` / `except IOError`, `with` only if the user agrees. |
| "Catch specific expected errors; never use bare `except:`" | Kept, marked as a deliberate departure from some mark schemes. |
| "`[0] * Capacity` … allowed; build 2D rows individually" | Kept. |
| "Default new Python arrays to zero-based indexing" | Kept, with the reason (Cambridge's Python is 0-based) and the bound translation made explicit. |
| Not covered | Added: declaration comments, explicit flag comparisons, `Count = Count + 1`, print and input forms, string-routine mapping, class conventions, `#main` section, British spelling. |

## D. What v1 got right

- The download inventory (798 files, 399 QP/MS pairs) and SHA-256 records: every MS hash
  matched on re-download.
- The general direction: explicit, traceable procedural code; AS style by default with A Level
  structures when needed; no hidden library algorithms.
- The Python-semantics warnings (`-1` as an index, shared 2D rows, `readline()` and EOF,
  `round()` and `//` with negative numbers, copying lists).
- The page references in `Evidence_Catalog.md`.
