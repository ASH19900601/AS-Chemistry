# Python house style: read like Cambridge pseudocode

This project is written for a learner who knows Cambridge IGCSE 0478 and AS & A Level
9608/9618 pseudocode. Write Python that a pseudocode reader can trace line by line, in the
way Cambridge's own mark-scheme Python is written (9608 Paper 2 appendix, 9618 Paper 4).
The evidence for every rule is in `Style_Analysis.md`; section numbers refer to it.
Where a rule deliberately differs from the mark schemes, it says so.

## 1. Names (§4)

- Use **PascalCase** for every name you create: variables, constants, arrays, parameters,
  functions, procedures, classes, attributes and methods: `TotalWeight`, `NumberOfItems`,
  `CalculateAverage`, `StudentRecord`, `self.__CurrentSpeed`, `GetCurrentSpeed()`.
- No underscores in your own names (the 0478 syllabus forbids them), except Python's own
  `__init__` and the `__` prefix for private attributes.
- Names describe the data. Prefer the Cambridge vocabulary: `Index`, `Count`, `Total`,
  `Found`, `Valid`, `NoSwaps`, `Boundary`, `Temp`, `ThisChar`, `NextChar`, `ThisLine`,
  `FileData`, `Result`, `ReturnValue`, `HeadPointer`, `TailPointer`, `TopOfStack`,
  `FreeNode`, `RootPointer`. Use the prefixes `This…`, `Next…`, `New…`, `Num…` / `NumberOf…`
  and `Is…` the same way.
- Single letters only where conventional: `X`, `Y` for coordinates and short `for` loops over
  rows and columns; otherwise `Index`, `Row`, `Column`.
- Never use two names that differ only in letter case (`Count` and `count`); pseudocode
  identifiers are case-insensitive.
- Constants: assign once near the top of the module and mark them with `# CONSTANT`.
  Use PascalCase (`MaxSize = 50`); one-word symbols may be capitals as in the mark schemes
  (`COMMA = ","`).
- Use British spellings in names and messages, as the papers do (`Initialise`, `Colour`).
- Keep Python keywords, built-ins and library names exactly as Python spells them
  (`def`, `if`, `range`, `len`, `print`, `self`, `.append`, `random.randint`). Do not invent
  upper-case wrappers such as `OUTPUT()` or `MID()`.

## 2. Declarations and comments (§8)

- Start each subprogram with declaration comments for its local variables, in pseudocode
  form:

  ```python
  def FindHighestPosition(Scores, NumberOfScores):
      # DECLARE Highest, Position, Index : INTEGER
  ```

- Declare every array with its type and valid bounds:
  `# DECLARE Scores : ARRAY[0:29] OF INTEGER`. For a record or class attribute, a trailing
  comment is enough: `self.__Name = NameP  # STRING`.
- When Python differs from pseudocode, say so in a short comment next to the line:
  `ThisCode = ThisLine[4:7]  # MID(ThisLine, 5, 3)`,
  `Middle = (Low + High) // 2  # (Low + High) DIV 2`.
- Use `#` comments, one idea each. No docstring essays.

## 3. Statements (§5, §8)

| Pseudocode | Python to write |
|---|---|
| `Total ← Total + Value` | `Total = Total + Value` |
| `Count ← Count + 1` | `Count = Count + 1` (not `+=`; Cambridge used `+=` only from 2023) |
| `OUTPUT "Total is ", Total` | `print("Total is", Total)` |
| `OUTPUT "Total is " & NUM_TO_STR(Total)` | `print("Total is " + str(Total))` |
| `OUTPUT "Enter a mark"` then `INPUT Mark` | `Mark = int(input("Enter a mark: "))` (see §4 for validation) |
| `IF … THEN … ELSE … ENDIF` | `if …:` / `else:` |
| nested `IF … ELSE IF …` | `if` / `elif` / `else` |
| `CASE OF Choice` … `OTHERWISE` | `if Choice == 1:` / `elif Choice == 2:` / `else:` (not `match`) |
| `<>` | `!=` |
| `AND`, `OR`, `NOT` | `and`, `or`, `not`, with brackets when conditions are mixed |
| `WHILE Found = FALSE AND Index <= Max` | `while Found == False and Index < NumberOfItems:` |
| `X MOD Y`, `X DIV Y` | `X % Y`, `X // Y` (comment if values can be negative) |
| `CALL Display(Name)` | `Display(Name)` |

- Compare Boolean flags explicitly (`== True`, `== False`), as Cambridge's Python does;
  `not Found` is also acceptable in loop conditions.
- One statement per line. No conditional expressions (`A if C else B`), no walrus `:=`,
  no chained one-liners.
- Output: `print` with comma-separated values, or `+` with `str()`. No f-strings,
  `.format()` or `%` formatting. If a number must be rounded, round it first with `round()`
  in its own statement.

## 4. Loops (§5, §9.1)

- Count-controlled `FOR` → `for Index in range(0, N):` with an explicit start value.
  Translate bounds deliberately: pseudocode `FOR Index ← 1 TO N` over a 1-based array becomes
  `for Index in range(0, N):` over a 0-based list. A loop that counts values (not positions)
  keeps its values: `FOR Count ← 1 TO 10` → `for Count in range(1, 11):`.
  `STEP -1` → `range(Start, End - 1, -1)`.
- Pre-condition `WHILE` → `while Condition:`. Put the bounds test before the array access:
  `while Index < NumberOfItems and Names[Index] != SearchName:`.
- Post-condition `REPEAT … UNTIL Condition` → set a flag so that the body runs at least once,
  then loop until the condition holds:

  ```python
  Valid = False
  while Valid == False:          # REPEAT ... UNTIL Valid
      ...
      if <condition>:
          Valid = True
  ```

  Priming the variable with an invalid value (`Score = -1` / `while Score < 0 or Score > 100:`)
  is also used in the mark schemes. Avoid `while True:` with `break`.
- Leaving a loop early: in a function, `return` from inside a `for` loop is fine (9618 does
  it). Otherwise use a flag in a `while` condition rather than `break`.
- Iterate over positions, not items: `for Index in range(0, len(Names)):` with
  `Names[Index]`. Exceptions: `for Line in File:` when reading a file.

## 5. Arrays (§6)

- Use Python lists as arrays, indexed from 0, and say so in the declaration comment.
  Do not allocate an unused element 0 unless the user asks for 1-based positions.
- Declare an array with its full size before it is used, in one of the Cambridge forms:

  ```python
  # DECLARE Scores : ARRAY[0:29] OF INTEGER
  Scores = [0 for Index in range(30)]

  # DECLARE Grid : ARRAY[0:9, 0:9] OF STRING
  Grid = [["" for Column in range(10)] for Row in range(10)]
  ```

  or an empty list followed by an `append` loop. These comprehensions are the only ones
  allowed. `[0] * 30` is fine for numbers and strings; never write `[[0] * C] * R` or repeat
  one object (`[Record()] * N`), because every row or element would be the same object.
- Keep the number of valid elements in its own variable (`NumberOfScores`, `NumberItems`,
  `TopOfStack`) or mark empty slots with a stated sentinel (`""`, `-1`). Loops run to the
  logical size, not to `len()` of a part-filled array.
- A two-dimensional table is a list of lists accessed as `Table[Row][Column]`.
- A sentinel of `-1` must be tested before it is used as an index: `Names[-1]` is the last
  element in Python, not an error.
- Copying: `CopyOfScores = Scores` does not copy. Copy element by element in a loop.

## 6. Subprograms and parameters (§7)

- `PROCEDURE` → a `def` that does not return a value. `FUNCTION` → a `def` that returns one
  value of one type on every path. Several `return` statements are fine.
- Parameters are passed by value in pseudocode unless `BYREF` is stated. Python cannot change
  a caller's number or string through a parameter. When pseudocode uses `BYREF` or needs two
  results:
  - return the values together and unpack at the call, as Paper 4 answers do:
    `FirstName, LastName = SplitName(FullName)`; or
  - return a small record object whose fields are named as in a pseudocode `TYPE`
    (`RetVal.Done`, `RetVal.Value`).

  Write a comment giving the pseudocode header with `BYREF`.
- A list passed as a parameter can be changed inside the subprogram (as with `BubbleSort`);
  state this in a comment when it happens.
- Global data: for a program built around one set of arrays and pointers (a stack, queue,
  linked list, tree or table), declare them at module level with declaration comments and
  write `global Name` at the top of every subprogram that assigns to them, exactly as
  Paper 4 answers do. Pass everything else as parameters. If the program grows beyond one
  structure, put each structure in a class (§7).
- End a script with a `# main` section that initialises the data and calls the subprograms
  in order.

## 7. Classes and records (§6.4)

- Pseudocode `TYPE … ENDTYPE` record → a class whose `__init__` sets every field to a starting
  value of the right type, with public PascalCase fields (`self.StudentID = ""`).
- Pseudocode `CLASS` → a class with private attributes `self.__Name`, a constructor whose
  parameters end in `P` (`NameP`, `MaxSpeedP`), a `GetX()` method for each attribute that is
  read and `SetX(NewX)` for each that is changed.
- Inheritance: `class Helicopter(Vehicle):` with `super().__init__(…)`. A subclass uses the
  parent's `GetX`/`SetX` methods, not its private attributes.

## 8. Algorithms must be visible (§9)

Write searches, totals, counts, maxima, minima, sorts and string scans as explicit loops.
Do not use `sum`, `min`, `max`, `sorted`, `.sort`, `in` (as a search), `.index`, `.count`,
`.find`, `any`, `all`, `map`, `filter`, `reduce`, `lambda`, `enumerate`, `zip`,
`collections`, `random.sample`, generator expressions, comprehensions that compute or filter,
tuple swaps or other unpacking tricks. Use these templates:

- **Total / average**: `Total = 0` before the loop, add inside, divide after the loop, and
  check for zero items first.
- **Largest / smallest**: start from the first element (`Highest = Scores[0]`, loop from 1),
  or from a stated value outside the possible range when the range is known; keep the
  position as well when it is needed.
- **Linear search**: `Index = 0`, `Found = False`,
  `while Index < NumberOfItems and Found == False:` … return the position or `-1`.
- **Bubble sort**: `NoSwaps`, a `Boundary` that decreases after each pass, and a swap through
  `Temp` (three lines). When rows of a table are sorted, swap every column.
- **Insertion sort**: save `CurrentValue`, move larger items one place to the right in a
  `while Position >= 0 and DataArray[Position] > CurrentValue:` loop, then insert.
- **Binary search**: `Low`, `High`, `Middle = (Low + High) // 2`; iterative or recursive with
  the base case `if Upper < Lower: return -1`.
- **Strings**: process one character at a time with an index; build results by
  concatenation. Map the library routines: `LENGTH` → `len`, `MID(S, P, L)` →
  `S[P - 1:P - 1 + L]`, `LEFT(S, N)` → `S[0:N]`, `RIGHT(S, N)` → `S[len(S) - N:]`,
  `UCASE`/`TO_UPPER` → `.upper()`, `LCASE`/`TO_LOWER` → `.lower()`, `NUM_TO_STR` → `str()`,
  `STR_TO_NUM` → `int()` / `float()`, `ASC` → `ord`, `CHR` → `chr`, `INT` → `int`,
  `IS_NUM` → a small function using `try` / `float()` / `except ValueError`. `.split(",")` and
  `.strip()` may be used when reading a file record. No regular expressions.
- **Random numbers**: `INT(RAND(6)) + 1` or `ROUND(RANDOM() * 5, 0) + 1` →
  `random.randint(1, 6)`.
- **Stacks, queues, linked lists, trees, hash tables**: a fixed-size array plus named
  pointers and counts, updated step by step: `TopOfStack`, `HeadPointer`, `TailPointer`,
  `NumberItems`, `FirstNode`, `FirstEmpty`, `RootPointer`, `FreeNode`, `-1` as the null
  pointer. Test full and empty before every change. Do not use `list.pop()`, `deque`,
  `dict` or `heapq` in place of a structure the task asks you to implement.

Standard-library tools are allowed for work that is not the algorithm being practised:
`datetime` for dates, `random`, `os.path` for file names. Explain each in one comment.

## 9. Files and errors (§9.9)

- Read and write text files with `open`, an explicit loop and `close`, inside
  `try` / `except IOError:` (Cambridge's form). Read either with
  `ThisLine = File.readline()` / `while ThisLine != "":` (end of file is `""`) or with
  `for Line in File:`. Remove only the line ending: `Line.rstrip("\n")`.
- Close every file you open, including on the error path. `with open(...)` is not used in
  the mark schemes; use it only if the user agrees, with a comment that it closes the file.
- Convert input with `int(input(...))` or `float(input(...))` inside `try` /
  `except ValueError:` and ask again on failure.
- Catch the specific error (`IOError`, `ValueError`). Never write a bare `except:`, although
  some mark schemes do.

## 10. Before you finish

Check the code once more for:

- names not in PascalCase, or two names differing only in case;
- missing declaration comments for arrays and local variables;
- off-by-one errors in translated bounds, and `-1` used as an index;
- arrays built with shared rows or repeated objects;
- `REPEAT` translations whose body might not run once;
- scalar parameters expected to behave as `BYREF`;
- files that are not closed, bare `except:`, unconverted `input()`;
- any library call or idiom from §8 that hides a requested algorithm;
- mark-scheme slips copied by mistake: `TRUE`/`FALSE`, `Return`, `<>`, missing colons.

If a requirement of the real program (a library API, a GUI callback name, a file format)
conflicts with these rules, follow the requirement and explain the exception in one comment.
