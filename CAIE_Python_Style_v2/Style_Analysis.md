# How Cambridge mark schemes write code, and what that means for a Python project

Version 2.0 (re-analysis), 11 October 2026. Scope: every published mark scheme (MS) from
2016 to 2025 for Cambridge IGCSE Computer Science 0478 and AS & A Level Computer Science
9608 / 9618, 399 documents in total. A Chinese version is in `Style_Analysis_zh.md`.

## 1. Summary

1. **Identifiers are PascalCase almost everywhere** (`TotalWeight`, `NumberOfItems`,
   `ThisChar`). In the 2023–2025 IGCSE schemes and in 9618 AS/A Level schemes, 88–98 % of
   distinct identifiers are PascalCase; the remainder are conventional single letters
   (`i`, `X`, `Y`) and short capitalised abbreviations (`DD`, `MM`). Lower-case, camelCase and
   snake_case names occur mainly in the old IGCSE schemes (2016–2022) and in one
   transitional 2021 A Level scheme. The 0478 syllabus (2023 onwards) makes PascalCase
   mandatory and forbids underscores.
2. **Cambridge's own Python follows the same naming.** In the Python answers of 9618
   Paper 4 (2021–2025), 89 % of assigned names and 94 % of function names are PascalCase,
   attributes are `self.__PascalCase`, and methods are `GetX` / `SetX`.
3. **The style changed with the syllabus, so "inconsistencies" are mostly era differences.**
   Old IGCSE (2016–2022) allowed `PRINT`, `=` for assignment, `CASE x OF`, `WHILE … DO`,
   undeclared variables and, in 2019–2021, 0-based loops; IGCSE from 2023 uses `OUTPUT`, `DECLARE`, `ARRAY[1:n]` and
   `FOR … NEXT Count`. 9608 wrote `THEN` on its own line and ended loops with `ENDFOR`;
   9618 writes `IF … THEN` on one line and `NEXT Index`.
4. **Pseudocode arrays start at 1.** Of the `FOR` loops that start at 0 or 1, 89–98 % start
   at 1 in AS and 2023+ IGCSE answers, and the 9618 guide says "Generally, a lower bound of 1 will be used". Zero is
   used when the index means something (hours 0–23) and in Paper 4 practical contexts.
5. **Cambridge's Python arrays start at 0**, and loops are written `for X in range(0, N):`
   with an explicit start (83 of 131 `for` loops in 9618 Paper 4).
6. **Algorithms are written out step by step.** No mark-scheme Python answer uses
   `sorted`, `.sort`, `sum`, `min`, `max`, `map`, `filter`, `lambda`, `enumerate`, `zip`,
   f-strings, `.format` or `with open`. Searches, totals, extremes and sorts are explicit
   loops with counters, flags and temporary variables (the only shortcuts are `in` in three
   2016 answers and `random.sample` in one 2025 answer).
7. **Flags are usually compared explicitly.** AS pseudocode writes `WHILE Found = FALSE`
   about six times as often as `NOT Found` (99 against 16), and 9618 Paper 4 Python writes
   `while Valid == False:` 33 times and `not` twice. The 2023+ IGCSE answers are the exception:
   they prefer `UNTIL NOT Swap` / `IF NOT Booked` (12 against 1).
8. **Paper 4 Python leans on global state.** Arrays and pointers are module-level variables
   with `global` statements in every subprogram (148 `global` statements). Several results
   are returned as a tuple to imitate BYREF (`return (True, Queue, Head, Tail, NumItems)`).
9. **Declaration comments are a Cambridge habit.** AS Python answers begin subprograms with
   `# DECLARE Index : INTEGER` or `## Count As Integer` (137 such lines in 92 blocks), and
   9618 Paper 4 tags variables with trailing type comments (`Queue = [] #string 50 elements`).
10. **List comprehensions are used only to create arrays.** `[0 for I in range(100)]` and
    `[[0 for X in range(3)] for Y in range(20)]` appear alongside `append` loops; a
    comprehension is never used to filter or compute.
11. **The mark schemes are not model Python.** Many Python answers contain errors
    (`FALSE`, `Return`, `<>`, missing colons, Python 2 `print`), two answers build
    two-dimensional lists whose rows are one shared list (`[['*'] * 2] * 100`), and one
    repeats a single record object across each row. Copy the structure, not the mistakes.
12. **The previous analysis (v1.0) is unreliable in places.** Its extractor scrambled the 108
    documents with rotated pages and labelled Java, Pascal and VB as Python. It also
    over-stated how often 0-based arrays occur, and banned some idioms that Cambridge's own
    Python uses. Details: `Audit_of_v1.md`.

The rules derived from this evidence are in `AGENTS.md` (for an AI coding assistant) and
`AI_Coding_Prompt.txt` (a short version to paste into a chat).

## 2. Sources and method

### 2.1 Documents

| Level (this report) | Papers | Mark schemes |
|---|---|---:|
| IG | 0478 Papers 1 and 2 | 138 |
| AS | 9608 and 9618 Papers 1 and 2 | 132 |
| AL | 9608 and 9618 Papers 3 and 4 | 129 |

All 399 PDFs were downloaded again from the URLs recorded in the v1 manifest; every file
matched its recorded SHA-256 hash (`tools/ms_manifest.csv`, `tools/download_ms.py`).
Official references: the 0478 syllabus 2023–2025 (pseudocode section), the 9618 syllabus
2024–2025 and the 9618 Pseudocode Guide for Teachers (2026 edition), taken from the v1 zip.

### 2.2 Extraction

Mark schemes typeset code in a monospace font (Courier New, Courier, or embedded subset fonts
with uniform 0.6 em glyphs in 2016), so code can be separated from marking prose by font. The
extractor (`tools/extract_code.py`):

- reads every character with its font and position (PyMuPDF);
- transforms coordinates for the 108 documents that contain landscape pages stored with a
  page rotation (without this, columns interleave);
- maps the assignment arrow drawn in Symbol or Wingdings fonts (`←`, `U+F0AC`, `Å`, `\x04`)
  back to `←`;
- removes "fake bold" glyphs printed twice with a small offset (`AAlarmmState` →
  `AlarmState`);
- restores underscores that five 2023–2025 Paper 4 schemes draw as short lines instead of
  characters. These PDFs show a single underscore (`def _init_(self, …)`, `self._ID`) where
  the intended Python is `__init__` and `self.__ID`; the corpus keeps what the PDF shows;
- rebuilds indentation from x positions using the measured character width of each block;
- joins lines that the PDF wrapped inside a table cell, and blocks split by a page break;
- records the marking text directly above each block, including the language label
  ("Python", "VB.NET", "Java", "Pascal").

`tools/classify.py` assigns a language from the label and keyword evidence, then removes
duplicates (variants 1 and 3 of a session often share a paper). Scanned code images were
looked for: the images in the programming-paper schemes are flowcharts, tree diagrams and
screenshots of program output, not code listings.

### 2.3 Corpus

| Level | Language | Unique blocks | Lines | MS files |
|---|---|---:|---:|---:|
| IG | pseudocode | 294 | 3 734 | 66 |
| AS | pseudocode | 472 | 5 666 | 68 |
| AS | Python (9608 Paper 2 appendix) | 92 | 983 | 31 |
| AL | pseudocode | 155 | 1 756 | 56 |
| AL | Python (9608 / 9618 Paper 4) | 478 | 3 625 | 43 |
| AS + AL | Visual Basic, Java, Pascal | 1 170 | 13 164 | — |

Readable corpus files: `corpus/IG_pseudocode.txt`, `AS_pseudocode.txt`,
`AL_pseudocode.txt`, `AS_python.txt`, `AL_python.txt`. All 6 750 blocks (every language,
with page, coordinates, context and duplicate links) are in `corpus/blocks.jsonl`. Each
block header gives the source PDF and physical page.

### 2.4 Groups used for statistics

Statistics are counted per syllabus era over unique blocks from the programming papers:

| Group | Contents |
|---|---|
| IG-old | 0478 Paper 2, 2016–2022 |
| IG-new | 0478 Paper 2, 2023–2025 (new syllabus) |
| AS-9608 | 9608 Paper 2, 2016–2021 |
| AS-9618 | 9618 Paper 2, 2021–2025 |
| AL-9608 | 9608 Papers 3–4, 2016–2021 |
| AL-9618 | 9618 Papers 3–4, 2021–2025 |

Counts are descriptive. Variants of the same session are correlated, extraction can still
split or merge a few blocks, and regular-expression counts can misclassify a line. Full
tables: `stats/pseudocode_counts.csv`, `stats/python_counts.csv`,
`stats/*_identifier_styles.csv`, `stats/style_statistics.json`,
`stats/algorithm_patterns.txt`.

## 3. Official conventions and what the mark schemes actually do

| Topic | Official documents | Mark-scheme practice |
|---|---|---|
| Identifier case | 0478: "mixed case using Pascal case, e.g. FirstName … must start with a capital letter … the underscore should not be used". 9618: "mixed case … for example NumberOfPlayers" | PascalCase dominates (section 4). The schemes call this "Camel Case": "Sensible / meaningful variable names // use of Camel Case", "Capitalised keywords" (9618_s23_ms_22, 9608_w19_ms_22) |
| Case sensitivity | Both: identifiers are case-insensitive; `Countdown` and `CountDown` must not be two variables | Followed |
| Single letters | Both: allowed where conventional (`i`, `j` for indices, `X`, `Y` for coordinates) | `i`, `j`, `n` in 9608 loops; `X`, `Y` in 9618 Paper 4 Python |
| Keywords | Upper case | Upper case; IGCSE answers occasionally write `Print`, `For`, `Next`, `Repeat` |
| Indentation | 0478: four spaces, `THEN`/`ELSE` and `CASE` branches two. 9618: usually three spaces | IG: `IF … ` then `THEN` on the next line, indented two. 9618: `IF … THEN` on one line |
| Arrays | 9618: "Generally, a lower bound of 1 will be used". 0478: "The first index can be zero or one" | 1-based in most pseudocode; 0-based in Python |
| Parameters | 9618: by value unless `BYREF` is stated | `BYREF` appears in 13 AS headers |
| Declarations | 9618: good practice to declare | IG-new and AS answers declare; several schemes note "declarations are not required" (0478_s25_ms_22 p6, 0478_w25_ms_21) |

The 15-mark IGCSE question (2023 onwards) is marked with a levels grid whose top band
requires "Suitable identifiers with names meaningful to their purpose" and "All of the data
structures used have meaningful names" (e.g. 0478_s23_ms_21, 0478_m24_ms_22).

## 4. Identifiers

### 4.1 Case styles of variable, constant and parameter names

Distinct names that are assigned, declared, used as a loop variable or used as a parameter,
counted once per mark scheme:

| Style | IG-old | IG-new | AS-9608 | AS-9618 | AL-9608 | AL-9618 |
|---|---:|---:|---:|---:|---:|---:|
| PascalCase, several words (`TotalWeight`) | 86 | 95 | 246 | 210 | 121 | 76 |
| Capitalised single word (`Count`) | 44 | 85 | 102 | 88 | 55 | 45 |
| Pascal with underscore (`Ticket_Number`) | 12 | 0 | 0 | 1 | 0 | 0 |
| snake_case (`total_weight`) | 3 | 0 | 0 | 5 | 0 | 0 |
| camelCase (`foundProc`) | 8 | 0 | 0 | 0 | 7 | 0 |
| lowercase (`total`) | 7 | 0 | 1 | 6 | 6 | 0 |
| UPPERCASE (`MM`, `EOL`) | 1 | 0 | 2 | 16 | 1 | 0 |
| single letter (`i`, `X`) | 3 | 9 | 11 | 11 | 5 | 2 |
| **PascalCase share** | **79 %** | **95 %** | **96 %** | **88 %** | **90 %** | **98 %** |

What the minorities are:

- **IG-old** (2016–2022) mixes styles in the same answer: `num_sand_ordered`,
  `total_weight` (0478_s16_ms_22 p2–3), `Ticket_Number`, `Order_Complete` (0478_s18_ms_23,
  0478_w18_ms_21), `foundProc`, `posCount`, `count` (0478_s18_ms_21). None of these forms
  appear in IG-new.
- **AS-9618** upper-case names are short abbreviations (`DD`, `MM`, `HH`, `SS` in a clock
  procedure, `EOL`, `P1`, `F1`) and the lower-case names are `x1, y1, x2, y2` coordinates in
  9618_s24_ms_21. Underscore names are field or module names with a number
  (`Club_1`, `Limit_1`, `Stage_1`, `Report_1`).
- **AL-9608** camelCase comes from the June 2021 Paper 4 scheme (`binaryTree`, `topOfStack`,
  `searchValue`, `preOrder`, 9608_s21_ms_41). The 9618 Paper 4 scheme of the same session
  (9618_s21_ms_41) has camelCase Python (`linearSearch`, `bubbleSort`, `outputNodes`). Later
  schemes return to PascalCase.

### 4.2 Typical vocabulary

The most frequent assignment targets show how Cambridge names state:

| Role | Names seen most often |
|---|---|
| Loop index / position | `Index` (by far the most common in AS and 9618), `Count`, `Counter`, `Row`, `Column`, `Col`, `J` in bubble sorts, `i`, `j`, `n` (9608 only), `X`, `Y` (Paper 4 Python) |
| Totals and counts | `Total`, `Count`, `Sum`, `NumberOfItems`, `NumFound`, `CountA`, `TotalWeight` |
| Flags | `Found`, `Valid`, `NoSwaps`, `Swap`, `Swapped`, `Flag`, `Done`, `Finished`, `Continue`, `IsPal`, `EndOfGeoCode`, `Placed` |
| Current item | `ThisChar`, `NextChar`, `ThisLine`, `ThisNum`, `ThisValue`, `CurrentValue`, `CurrentNode`, `CurrentPointer` |
| Built-up results | `OutString`, `NewString`, `MyString`, `Result`, `RetVal`, `ReturnValue`, `ReturnFlag`, `DataToReturn` |
| Files | `FileData`, `FileLine`, `ThisLine`, `Line`, `FileName`, `File` (Python handle) |
| Temporaries | `Temp`, `TempString`, `TempInt`, `Temp1`, `Temp2` |
| Bounds and sizes | `Boundary`, `Lower`, `Upper`, `First`, `Last`, `Low`, `High`, `Mid`, `Middle`, `MaxSize`, `ArrayLength` |
| Pointers | `HeadPointer`, `TailPointer`, `TopOfStack`, `TopPointer`, `FreePointer`, `FreeNode`, `RootPointer`, `StartPointer`, `FirstNode`, `FirstEmpty`, `NullPointer` |

Prefixes used systematically: `This…` for the item being processed, `Next…` for the item
about to be read, `New…` for a value being built, `Num…` / `NumberOf…` for counts, `Is…`
for Boolean functions. Spelling is British (`Initialise`, `Colour`, `Centre`).

### 4.3 Constants

Pseudocode declares constants with `CONSTANT`. Both upper-case single words
(`CONSTANT COMMA = ','`, `HASH`, `SPACE`, `EMPTY`, `SPACECHAR`, `ASTERISK`) and PascalCase
(`CONSTANT MaxSize = 60`, `Capacity`, `TreeCount`, `Unused`, `Terminator`) occur; 9618 uses
`CONSTANT` 33 times in Paper 2. 9608 Python writes constants in capitals (`COMMA = ','`,
`TREECOUNT = 20`, `SAFELIMIT = 36`).

### 4.4 Procedures, functions and classes

| Group | Subprogram headers | PascalCase share | Examples |
|---|---:|---:|---|
| AS-9608 | 130 | 100 % | `CalculateCustomerID`, `ValidatePassword`, `BubbleSort`, `SearchFile`, `GetAverageScore` |
| AS-9618 | 141 | 95 % | `IsPalindrome`, `GetStart`, `FindPassword`, `CheckFile`, `AddError`, `Stage_1` |
| IG-new | 10 | 100 % | `CheckDetails`, `Balance`, `Deposit`, `Odds`, `Same`, `NewData` |
| AL (pseudocode) | 67 | 88 % | `InsertRecord`, `SearchHashTable`, `AddToList`, `FindValue`, `Enqueue`, `Pop` |

Names are verb + object (`AddNewScores`, `FindRepeats`, `OutputLowestScore`) or a single verb
for standard operations (`Push`, `Pop`, `Enqueue`, `Dequeue`, `Initialise`, `Search`,
`Sort`, `Hash`). Functions that answer a yes/no question start with `Is`, `Check` or
`Validate`. Classes are singular nouns in PascalCase (`Vehicle`, `Employee`, `Node`,
`TreeClass`, `Balloon`).

## 5. Statements and layout

Counts per group (lines in unique blocks):

| Feature | IG-old | IG-new | AS-9608 | AS-9618 | AL-9608 | AL-9618 |
|---|---:|---:|---:|---:|---:|---:|
| Assignment with `←` / with `=` | 433 / 14 | 463 / 4 | 784 / 13 | 767 / 3 | 257 / 4 | 156 / 0 |
| `OUTPUT` / `PRINT` lines | 188 / 101 | 243 / 4 | 106 / 0 | 113 / 0 | 16 / 0 | 32 / 0 |
| `IF` with `THEN` on the same line / all `IF`s | 36 / 155 | 0 / 99 | 14 / 189 | 187 / 205 | 2 / 86 | 47 / 51 |
| `NEXT Var` / bare `NEXT` / `ENDFOR` | 23 / 14 / 0 | 84 / 6 / 0 | 0 / 1 / 88 | 84 / 1 / 1 | 2 / 0 / 18 | 6 / 0 / 0 |
| `WHILE … DO` / all `WHILE`s | 28 / 41 | 24 / 35 | 0 / 66 | 0 / 58 | 0 / 19 | 0 / 11 |
| `REPEAT` loops | 59 | 46 | 23 | 28 | 10 | 2 |
| `CASE OF x` / `CASE x OF` | 5 / 17 | 6 / 0 | 9 / 0 | 9 / 0 | 0 / 0 | 0 / 0 |
| `DECLARE` lines | 0 | 103 | 363 | 289 | 91 | 104 |
| `CONSTANT` lines | 0 | 7 | 25 | 33 | 2 | 5 |
| `// comment` lines | 29 | 61 | 116 | 106 | 39 | 12 |
| Flag tested with `= TRUE/FALSE` / with bare `NOT` | 17 / 9 | 1 / 12 | 49 / 7 | 50 / 9 | 8 / 2 | 7 / 3 |
| `RETURN` statements | 0 | 4 | 73 | 105 | 54 | 22 |
| `CALL` statements | 0 | 1 | 10 | 19 | 6 | 2 |

Notes:

- **Output.** Values are listed with commas (`OUTPUT "Total is ", Total`). 9608 also
  concatenated with `&`, converting numbers with `NUM_TO_STRING` (23 `OUTPUT … &` lines);
  9618 prefers commas (30 against 4). A prompt is a separate `OUTPUT` line before `INPUT`.
- **IF layout.** IGCSE and 9608 put `THEN` on the next line, indented two spaces; 9618 writes
  `IF Count > Max THEN`. `ELSE IF` chains are written as nested `IF`s with `ENDIF`s.
- **Loops.** `FOR` is used whenever the number of repetitions is known; `WHILE` for searches
  and file reading; `REPEAT … UNTIL` for input validation and "at least once" processing. A
  `FOR` loop is sometimes left early: by setting the counter past the end (old IGCSE,
  `Count ← 10`), by `RETURN` inside the loop (about ten AS answers, mostly 9618), and by
  `BREAK` in four November 2025 9618 answers (9618_w25_ms_21, 9618_w25_ms_23), although
  `BREAK` is not in the guide.
- **Line continuation.** Long conditions are split with a trailing `__` or `_`
  (9608_s20_ms_21, 9618_w21_ms_22).
- **Several statements on one line.** Old IGCSE answers join assignments with `;`
  (`CountA ← 0; CountB ← 0`), which later schemes do not do.

## 6. Arrays, records and objects

### 6.1 Declaring arrays

`DECLARE StudentNames : ARRAY[1:30] OF STRING` and
`DECLARE Contacts : ARRAY[1:100, 1:2] OF STRING` are the standard forms (old IGCSE did not
declare arrays, and sometimes indexed with round brackets: `HoursHired(BoatNumber)`).

| Lower bound in `ARRAY[...]` | IG-new | AS-9608 | AS-9618 | AL-9608 | AL-9618 |
|---|---:|---:|---:|---:|---:|
| 1 | 20 | 15 | 8 | 3 | 8 |
| 0 | 0 | 2 | 3 | 10 | 1 |

| First value of `FOR` loops | IG-old | IG-new | AS-9608 | AS-9618 | AL-9608 |
|---|---:|---:|---:|---:|---:|
| 1 | 27 | 82 | 81 | 67 | 9 |
| 0 | 7 | 2 | 9 | 8 | 8 |

So pseudocode is 1-based by default. Zero-based arrays appear when the index is a value
(`HoursArray[0 : 23]` for hours, 9618_s25_ms_22 p13; `CheckTotal : ARRAY[0:35]` for totals
0–35, 9618_w25_ms_22), in old IGCSE answers (`FOR Count ← 0 TO 29`), and in 9608 Paper 4,
where answers had to match program code (`ARRAY[0:9] OF Node`).

### 6.2 Using arrays

- Arrays are initialised element by element in a loop:
  `FOR Index ← 1 TO 100` / `ResultArray[Index] ← "NO DATA"` / `NEXT Index`.
- The number of valid elements is kept in a separate variable (`NumElements`, `CurrentSize`,
  `NumberRecords`), or an empty element is marked with a sentinel (`""`, `-1`, `99999`,
  `"****"`, `"Empty"`).
- Parallel arrays (`Names[]` and `Heights[]`) and two-dimensional tables
  (`Results[InLoop, 4]`, `Contacts[Count, 1]`) are common in IGCSE answers. Records
  (`TYPE … ENDTYPE`) and arrays of records (`Loan[Index].StudentID`) appear in AS and A Level.
- When a row of a 2D array moves in a sort, every column is swapped with its own temporary
  variable (`Temp1`, `Temp2`, `TempString`).

### 6.3 Arrays in Cambridge's Python

| Form | AS-9608 | AL-9608 | AL-9618 | Example |
|---|---:|---:|---:|---|
| Empty list, then `append` in a loop | 4 | 4 | 57 | `QueueData = []` / `for x in range(0, 20):` / `QueueData.append("")` (9618_s24_ms_41) |
| List comprehension used as a declaration | 4 | 3 | 7 | `DataArray = [0 for I in range (100)]` (9618_w22_ms_41) |
| Nested comprehension for 2D | 1 | 3 | 2 | `ArrayNodes=[[0 for X in range(3)] for Y in range(20)]` (9618_w21_ms_41) |
| `[value] * n` | 5 | 3 | 4 | `ArrayData= [[0]*10 for i in range(10)]` (9618_s22_ms_42) |
| Literal list | 2 | 2 | 9 | `StackData = [0,0,0,0,0,0,0,0,0,0]` (9618_s22_ms_42) |

The declaration is followed by a comment that states the pseudocode type and size:
`Queue = [] #integer 50 elements`, `HighScores = [] #String, 7 x 3`.
Two answers build 2D lists whose rows are one shared list, which is a bug in Python:
`ResultArray = [['*'] * 2] * 100` (9608_w18_ms_21 p12, an "alternative" answer) and
`// Board =[["E"]*9]*9` (9608_s16_ms_41 p12). A third,
`[[Record(-1,"")]*10 for i in range(100)]` (9618_w25_ms_41), repeats one record object
across each row.

### 6.4 Records and classes

Pseudocode records:

```
TYPE Student
   DECLARE StudentID : STRING
   DECLARE Email : STRING
   DECLARE Club_1 : INTEGER
ENDTYPE
DECLARE Membership : ARRAY [1:3000] OF Student
```
(9618_w21_ms_22 p5)

Pseudocode classes (A Level): `CLASS Car` / `PRIVATE Make : STRING` /
`PUBLIC PROCEDURE NEW (CarMake : STRING, …)` / `ENDCLASS` (9618_w22_ms_31).

Python classes in Paper 4 answers:

- attributes are private and PascalCase: `self.__CurrentSpeed = 0` (226 lines use private
  attributes and 54 public ones; the public ones are mainly simple record-like classes from
  2023–2025, such as `self.Key`, `self.Name`, `self.QueueArray`);
- every attribute gets `GetX()` and, when needed, `SetX(NewValue)` (58 getters and 18
  setters in 9618);
- constructor parameters are marked with `P`: `IDP`, `MaxSpeedP`, `DescriptionP`, `pName`,
  `PColour`, `Numberp`;
- a type comment follows the attribute: `self.__Name = pName #String`;
- inheritance uses `super().__init__(…)` (5) or `Vehicle.__init__(self, …)` (1 in 9618,
  3 in 9608); a child class reaches the parent's private data through its getters
  (`Vehicle.GetCurrentSpeed(self)`, 9618_s23_ms_41).

## 7. Subprograms and parameters

- Headers declare every parameter type and the return type:
  `FUNCTION ChangeSupp(Code1, Code2 : STRING) RETURNS INTEGER`. Procedures are called with
  `CALL` in 9618 (`CALL Reset(Port)`); IGCSE often calls without `CALL`.
- Local variables are declared at the top of the subprogram.
- A function may contain several `RETURN` statements. 9618 answers return from inside a
  `FOR` loop (`IF Try = ThisValue THEN RETURN Num`, 9618_w22_ms_22) and often give a
  second, single-exit version with a flag.
- Parameters are by value unless `BYREF` is written:
  `PROCEDURE UnPack(BYVAL TLine : STRING, BYREF SID, SDesc, SCost : STRING)`
  (9618_w22_ms_23).
- When a function has two results, 9618 pseudocode returns a record:
  `FUNCTION Evaluate(NumStr1, NumStr2 : STRING) RETURNS Result`, setting `RetVal.Done` and
  `RetVal.Value` (9618_w24_ms_21 p8); and `FUNCTION Pop() RETURNS PopData`
  (9618_w25_ms_23).
- Python answers imitate BYREF in two ways: by returning all changed values as a tuple and
  reassigning them at the call
  (`ReturnValue, QueueArray, QueueHeadPointer, QueueTailPointer, NumberOfItems = Enqueue(…)`,
  9618_s22_ms_41; `TheQueue, ReturnValue = Enqueue(TheQueue, DataInput)`, 9618_w24_ms_42),
  or by making the data global (next section).

## 8. Python as Cambridge writes it

9618 Paper 4 answers (381 unique blocks, 2 920 lines), with 9608 Paper 2 answers (92 blocks)
for comparison:

| Feature | 9608 P2 | 9618 P4 | Example |
|---|---:|---:|---|
| `global` statements | 0 | 148 | `def Push(DataToPush):` / `global StackData` / `global StackPointer` |
| Declaration comment lines (`# Index : INTEGER`, `#DECLARE …`) | 137 | 15 | `## Index, Count : Integer` (9608_s21_ms_22) |
| Trailing type comments (`#integer`) | 2 | 82 | `QueueHeadPointer = 0 #integer` |
| `for X in range(0, N)` / `range(N)` / `range(1, N…)` / `for Item in …` | 7 / 7 / 16 / 2 | 83 / 21 / 5 / 21 | `for X in range(0, NumberRecords):` |
| `while` loops / `while True` | 41 / 3 | 56 / 1 | `while Valid == False:` |
| `X = X + 1` / `X += 1` | 34 / 5 | 31 / 23 | both appear; `+=` only from 2023 |
| `== True` or `== False` / `not` | 15 / 14 | 33 / 2 | `if ReturnValue == True:` |
| `print` with comma-separated values / with `+ str(...)` | 14 / 6 | 53 / 4 | `print("The number", DataToFind, "is found", NumberTimes, "times")` |
| `int(input(...))` or `float(input(...))` / all `input` | 11 / 29 | 30 / 55 | `Score = int(input("Enter score"))` |
| `open` / `readline` / `for Line in File` / `.read()` | 20 / 28 / 1 / 0 | 29 / 23 / 13 / 5 | see file reading below |
| `try` / `except IOError` / bare `except:` | 0 / 0 / 0 | 24 / 11 / 13 | `except IOError:` / `print("Could not find file")` |
| `.strip()` / `.split()` | 7 / 1 | 29 / 9 | `Line.strip()`, `Line.split(",")` |
| Tuple returned / tuple swap / swap through `Temp` | 0 / 0 / 4 | 10 / 4 / 6 | `return (True, Queue, Head, Tail, NumItems)` |
| f-strings, `.format`, `with open`, `lambda`, `map`, `filter`, `sorted`, `.sort`, `sum`, `min`, `max` | 0 | 0 | (`"%s" % (...)` appears twice, in 2018 9608 Paper 4) |

Further observations:

- Upper-case constants (`COMMA = ','`) appear in 9608 Python; 9618 Python mostly writes
  literal values.
- Interactive validation is written by priming the variable with an invalid value so that
  the `while` loop runs at least once: `Score = -1` / `while Score < 0 or Score > 100000:`
  (9618_s22_ms_41), or with a `Valid` flag; `while True` with `break` is rare.
- A program usually ends with a `#main` section that sets the global variables and calls the
  subprograms in order.
- String processing uses indexing and slicing with comments (`FileData[:5]  #First 5
  characters`, 9608_s17_ms_21), `.upper()`, `.lower()`, `len()`, `str()`, `int()`; never
  regular expressions.
- Mark-scheme Python is not always valid. Examples: `Found = FALSE` and `Return Found`
  (9608_w20_ms_23), `while Index <= 1000 and Error <> TRUE:` (9608_s21_ms_21),
  `def BubbleSort()` without a colon and `End Sub` (9608_s20_ms_22), Python 2
  `print "No file found"` (9608_s20_ms_42), `FileHandle.close` without brackets
  (9608_s18_ms_21). Examiners mark the logic, so these were accepted; a real program must
  not copy them.

## 9. How the common algorithms are written

Each pattern gives the Cambridge pseudocode form, how Cambridge writes it in Python, and
the recommended Python. Approximate counts come from `stats/algorithm_patterns.txt`.

### 9.1 Input validation

Pseudocode (0478_s22_ms_21 p11):

```
REPEAT
  IF Score < 0 OR Score > 100
    THEN
      OUTPUT "Your entry must be between 0 and 100, inclusive, please try again "
      INPUT Score
  ENDIF
UNTIL Score >= 0 AND Score <= 100
```

or a `WHILE` re-input loop (`WHILE Score < 0 OR Score > 100 DO … INPUT Score … ENDWHILE`).
Paper 4 Python primes the variable or uses a flag:

```python
Valid = False
while Valid == False:
    Height = int(input("Enter the height in cm"))
    if Height >= 70 and Height <= 180:
        Valid = True
```
(9618_w24_ms_41)

Recommended: the flag form, adding `try` / `except ValueError` around `int(input(...))`
(as in 9608_s17_ms_42 `StartDig`, which used a bare `except`).

### 9.2 Totalling, counting, averages

```
Total ← 0
FOR Count ← 1 TO 50
    Total ← Total + Number[Count]
NEXT Count
Average ← Total / 50
OUTPUT "The average is ", Average
```
(0478_m23_ms_22 p5; `Total ← 0` is given just above the code). The total and the counter
are initialised before the loop, and the
average is calculated and output after it. Python: `Total = Total + DataArray[X]` inside
`for X in range(0, len(DataArray)):`, never `sum()`.

### 9.3 Largest and smallest

Two forms are accepted. Initialise from the first element:
`Max ← List[1]` / `FOR Counter ← 2 TO 1000` (0478_s24_ms_22 p8),
`Highest ← Mark[1]` (9608_s18_ms_21). Or initialise with a value outside the possible range:
`Min ← 100` for temperatures (0478_w23_ms_22), `LowestScore ← 100` for scores of 50–99
(9608_s18_ms_22), `MaxWeek ← -1000` (0478_w23_ms_23). The sentinel form is the more common
(about 16 answers against 3–5 for the first-element form); it is only correct when the range
of the data is known.
The position of the extreme is usually stored too (`Position ← i`, `LowestIndex ← StudentCounter`).

### 9.4 Linear search

Three forms, all with an explicit index:

```
Index ← 1
Found ← FALSE
WHILE Index <= 10000 AND Found = FALSE
   IF TagString[Index] = HashTag
      THEN
         Found ← TRUE
      ELSE
         Index ← Index + 1
   ENDIF
ENDWHILE
IF Found = FALSE
   THEN
      Index ← -1
ENDIF
RETURN Index
```
(9608_w20_ms_21 `GetIndex`; about 25 pseudocode and Python answers use a `WHILE` loop
with a `Found` flag)

- `REPEAT … UNTIL Found = TRUE OR Index > 10` (9618_s21_ms_22 `IgnoreWord`);
- `FOR Index ← 1 TO LENGTH(ThisString)` with `RETURN TRUE` inside and `RETURN FALSE` after
  the loop (9618_s22_ms_22 `Exists`).

"Not found" is reported as `-1`, `FALSE`, `""` or a message. Python answers keep the same
structure (`while Index < 500 and not Found:`, 9608_w19_ms_22). Python's `in` appears only
in 2016: once as a search with `.index` (9608_w16_ms_22, followed by two explicit-loop
alternatives) and twice to check a character against a list of valid characters
(9608_w16_ms_41, 9608_w16_ms_42).

### 9.5 Bubble sort

The AS form is standard across 2017–2025:

```
PROCEDURE BubbleSort()
  DECLARE Temp : STRING
  DECLARE NoSwaps : BOOLEAN
  DECLARE Boundary, J : INTEGER
  Boundary ← 999
  REPEAT
     NoSwaps ← TRUE
     FOR J ← 1 TO Boundary
        IF Contact[J] > Contact[J+1]
           THEN
              Temp ← Contact[J]
              Contact[J] ← Contact[J+1]
              Contact[J+1] ← Temp
              NoSwaps ← FALSE
        ENDIF
     ENDFOR
     Boundary ← Boundary - 1
  UNTIL NoSwaps = TRUE
ENDPROCEDURE
```
(9608_s20_ms_22; the same in 9608_w17_ms_21, 9618_w22_ms_22, 9618_s25_ms_21)

IGCSE uses `Swap` / `Flag` with `REPEAT … UNTIL NOT Swap` and a shrinking `Last`
(0478_m24_ms_22) or `WHILE Flag DO` (0478_s24_ms_23). Paper 4 Python answers often use two nested `for` loops
without a flag (`for X in range(0, ArrayLength-1):` / `for Y in range(0, ArrayLength-X-1):`,
9618_s23_ms_42). Recent ones swap with a tuple (`DataArray[J], DataArray[J+1] =
DataArray[J+1], DataArray[J]`, 9618_w22_ms_41, 9618_w24_ms_41, 9618_w25_ms_42); others swap
through `Temp`.

Recommended Python: the AS form with `NoSwaps`, `Boundary` and a `Temp` swap.

### 9.6 Insertion sort

```
FOR Index ← 2 to 1000
   Value ← DataArray[Index]
   Position ← Index – 1
   IF DataArray[Position] > Value THEN
      WHILE Position >= 1 AND DataArray[Position] > Value
         DataArray[Position + 1] ← DataArray[Position]
         Position ← Position – 1
      ENDWHILE
      DataArray[Position + 1] ← Value
   ENDIF
NEXT Index
```
(9618_s25_ms_33; Python version in 9618_s25_ms_43 `InsertionSort`). The bounds test comes
before the array access, which matters in Python because `DataArray[-1]` is valid.

### 9.7 Binary search

Iterative (`Mid ← (Start + End) DIV 2`, `End ← Mid – 1`, `Start ← Mid + 1`,
9618_s25_ms_22) and recursive (9618_w25_ms_42 `RecursiveBinarySearch`, 9618_s24_ms_42) forms
both appear. Python answers compute the midpoint with `//`, `int(.../2)` or
`Lower + (Upper - Lower) // 2`.

### 9.8 Strings

The string is processed one character at a time with `MID(Text, Index, 1)` (about 45 AS
answers), building a result with `&`:

```
FOR Index ← 1 TO LENGTH(OldString)
   ThisChar ← MID(OldString, Index, 1)
   IF ThisChar = Char1 THEN
      ThisChar ← Char2
   ENDIF
   NewString ← NewString & ThisChar
NEXT Index
```
(9618_s23_ms_21 `Replace`)

Library routines used (counts of calls):

| Routine | IG-new | AS-9608 | AS-9618 | Python equivalent |
|---|---:|---:|---:|---|
| `LENGTH(S)` | 10 | 45 | 54 | `len(S)` |
| `MID(S, P, L)` | — | 46 | 42 | `S[P - 1 : P - 1 + L]` |
| `SUBSTRING(S, P, L)` (IGCSE) | 6 | — | — | `S[P - 1 : P - 1 + L]` |
| `LEFT(S, N)` / `RIGHT(S, N)` | — | 40 / 27 | 35 / 22 | `S[0:N]` / `S[len(S) - N:]` |
| `UCASE` / `LCASE` | 4 / 2 | 3 / 2 | 3 / 5 | `.upper()` / `.lower()` |
| `TO_UPPER` / `TO_LOWER` | — | 2 / 0 | 7 / 4 | `.upper()` / `.lower()` |
| `NUM_TO_STRING` / `NUM_TO_STR` | — | 28 / 0 | 0 / 16 | `str(N)` |
| `STRING_TO_NUM` / `STR_TO_NUM` | — | 11 / 2 | 0 / 31 | `int(S)` or `float(S)` |
| `INT(X)` | — | 24 | 27 | `int(X)` (truncates towards zero) |
| `ROUND(X, D)` | 25 | — | — | `round(X, D)` (rounds halves to even) |
| `ASC` / `CHR` | — | 5 / 5 | 0 / 7 | `ord` / `chr` |
| `IS_NUM` | — | 2 | 6 | `try: float(S)` / `except ValueError:` |
| `RAND(X)` / `RND()` | — | 5 / 5 | 14 / 0 | `random.random() * X` |
| `RANDOM()` (0 to 1) | 6 | — | — | `random.random()` |
| `MOD` / `DIV` | 9 / 5 | 2 / 0 | 13 / 6 | `%` / `//` (for negative operands Python rounds down) |
| `EOF(F)` | — | 26 | 20 | `readline()` returns `""` |
| `DAY`, `MONTH`, `YEAR`, `SETDATE`, `DAYINDEX`, `TODAY` | — | — | 20 together | `datetime.date` |

IGCSE writes `MOD(X, 2)` and `DIV(Total, 60)` as functions; 9618 writes `Count MOD 2` and
`(Percent DIV 10)` as operators. Random integers are written `INT(RAND(6)) + 1` (9618) and
`ROUND(RANDOM() * 5, 0) + 1` (IGCSE); Python answers use `random.randint(1, 6)`.

Paper 4 Python answers index strings directly (`Value[0]`, `Data[0:6]`) and, from 2024,
use `Line.split(",")`. One 2025 answer fills an array with `random.sample(range(0,101),20)`
(9618_w25_ms_42), the only library shortcut of its kind.

### 9.9 Text files

Pseudocode (about 40 AS answers):

```
OPENFILE "ScoreDetails.txt" FOR READ
WHILE NOT EOF("ScoreDetails.txt")
   READFILE "ScoreDetails.txt", FileData
   …
ENDWHILE
CLOSEFILE "ScoreDetails.txt"
```

Modes are `READ`, `WRITE` and `APPEND` (plus `RANDOM` with `SEEK`, `GETRECORD`, `PUTRECORD` at
A Level). A file is processed by copying lines to a new file (`OPENFILE … FOR READ` and
`OPENFILE … FOR WRITE` together). IGCSE introduced file handling with the 2023 syllabus
(`OPENFILE "Quotations.txt" FOR WRITE`, 0478_s23_ms_23).

Python: 9608 Paper 2 answers read with `FileData = File.readline()` /
`while FileData != "":`; 9618 Paper 4 answers use

```python
try:
    DataFile = open("Data.txt", 'r')
    for Line in DataFile:
        DataArray.append(int(Line))
    DataFile.close()
except IOError:
    print("Could not find file")
```
(9618_s23_ms_41). `with open` is never used.

### 9.10 Stacks, queues, linked lists, trees, hash tables

These appear in AL pseudocode and in nearly every 9618 Paper 4 scheme:

- **Stack**: a fixed array plus `TopOfStack` (or `StackPointer`), initialised to `-1` or `0`;
  `Push` tests for full and returns `TRUE` / `FALSE`, `Pop` tests for empty and returns a
  sentinel (`-1`, `""`, `"No data"`, `-999`). Python answers use the same global array and
  pointer (9618_s22_ms_42, 9618_s25_ms_42, 9618_w25_ms_41).
- **Queue**: `HeadPointer`, `TailPointer` and `NumberItems`; the circular version wraps the
  pointer to 0 when it reaches the end (9618_s25_ms_41, 9618_s23_ms_42).
- **Linked list**: an array of nodes `[Data, Next]` with `FirstNode`/`StartPointer` and a
  free list `FirstEmpty`/`FreeListPointer`; `-1` is the null pointer (9618_w24_ms_41).
  From 2025 a node-object version with `None` appears (9618_s25_ms_43).
- **Binary tree**: an array of `[LeftPointer, Data, RightPointer]` with `RootPointer` and
  `FreeNode` (9618_w21_ms_41, 9618_w25_ms_42), or `Node` objects with `GetLeft` / `SetLeft`
  (9618_s25_ms_41); traversals are recursive.
- **Hash table**: `Hash ← Key MOD Size` with linear probing and wrap-round
  (9608_s17_ms_41, 9608_s20_ms_41), or with a separate overflow array (9618_s25_ms_42).

### 9.11 Recursion

Recursive answers test for the base case with an `IF` (`IF Number = 0 THEN RETURN 0`,
9618_w23_ms_42; binary search `IF Upper < Lower THEN RETURN -1`), and Paper 4 often asks
for both a recursive and an
iterative version of the same function (9618_w21_ms_41 `Unknown` / `IterativeUnknown`,
9618_w23_ms_42).

## 10. Differences between IG, AS and AL

| Aspect | IG (0478) | AS (9608 / 9618 Paper 2) | AL (Papers 3 / 4) |
|---|---|---|---|
| Typical answer | Whole program for a scenario: input, validation, arrays, totals, output; 15-mark question from 2023 | Self-contained procedures and functions with parameters, string handling, files | Data structures, records, classes, recursion; Paper 4 in Python/VB/Java |
| Declarations | None before 2023; `DECLARE` from 2023 | Always | Always in pseudocode; comments in Python |
| Arrays | Parallel 1D and 2D arrays, 1-based from 2023 | 1-based 1D/2D, arrays of records | 0-based in Paper 4 |
| Selection | `IF` / `THEN` on next line; `CASE OF` | 9608 as IGCSE; 9618 `IF … THEN` | as AS |
| Loops | `FOR … NEXT`, `REPEAT … UNTIL`, `WHILE … DO … ENDWHILE` | `FOR … ENDFOR` (9608) / `NEXT` (9618), `WHILE`, `REPEAT` | as AS |
| Library | `ROUND`, `RANDOM`, `LENGTH`, `SUBSTRING`, `UCASE`, `LCASE`, `MOD()`, `DIV()` | `MID`, `LEFT`, `RIGHT`, `LENGTH`, `NUM_TO_STR`, `STR_TO_NUM`, `INT`, `RAND`, dates | as AS |
| Subprograms | Few; `PROCEDURE`/`FUNCTION` with typed parameters from 2023 | Central; `BYREF`, `RETURNS`, `CALL` | plus methods, constructors, inheritance |

## 11. What this means for your Python project

1. Use PascalCase for every name you create: variables, constants, arrays, parameters,
   functions, classes, attributes and methods. Keep Python keywords and library names as
   they are (`def`, `print`, `range`, `self`, `__init__`, `.append`).
2. Write each algorithm out: initialise, loop, compare, count, swap with `Temp`, and return.
   Do not hide it in `sum`, `max`, `sorted`, `in`, `.index`, comprehensions or `lambda`.
3. Use lists indexed from 0 and write `range(0, N)` with an explicit start. When you translate
   a 1-based pseudocode loop `FOR Index ← 1 TO N`, either change it to `range(0, N)` and use
   `Index` as a 0-based position, or keep 1-based positions with an unused element 0. State
   the choice in a comment.
4. Declare variables in comments at the top of each subprogram (`# DECLARE Total : INTEGER`)
   and give each array its pseudocode type and bounds
   (`# DECLARE Scores : ARRAY[0:29] OF INTEGER`).
5. Translate `REPEAT … UNTIL` with a flag (`Valid = False` / `while Valid == False:`).
6. Compare flags explicitly (`while Found == False and Index < NumberOfItems:`); count with
   `Count = Count + 1`.
7. Print with commas (`print("Total is", Total)`) or `+ str(...)`; read numbers with
   `int(input("…"))` inside `try` / `except ValueError`.
8. Read files with `open`, a `readline()` or `for Line in File` loop, and `close()`, inside
   `try` / `except IOError`.
9. For data structures, keep the fixed array and the pointers visible. Module-level arrays
   with `global` statements reproduce the Paper 4 style for small programs; for a larger
   project put the array and its pointers in a class with private attributes and
   `Get`/`Set` methods.
10. When a subprogram must give back several values (pseudocode `BYREF`), return them together
    and unpack at the call, or return a small record object, and say so in a comment.
11. Copy Cambridge's structure, not its slips: no `[[x] * n] * m`, no bare `except:`, no
    `TRUE`/`FALSE`, and close every file you open.

`AGENTS.md` turns these points into rules with examples; `examples/` contains tested
programs written this way.

## 12. Limitations

- The statistics count lines matched by regular expressions over automatically extracted
  text; a small number of blocks are split, merged or mislabelled. Ratios are reliable,
  single counts can be off by a few.
- Variants within a session share questions, so the observations are not independent.
- 0478 Paper 2 schemes before 2023 often describe the expected program in marking points
  and give one example answer; there is less code per scheme than in AS.
- The Visual Basic, Java and Pascal answers are extracted (`corpus/blocks.jsonl`) but not
  analysed here.
- The official documents used are the 0478 2023–2025 syllabus and the 9618 2026 guide.
  Older 9608 guidance was not re-checked; the 9608 practice above comes from its mark
  schemes.
