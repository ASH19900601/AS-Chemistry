# AI SQ Grader (Python version)

A Python implementation of the group's Part 1 design for the **AI Structure Question Grader**:
it compares a student's answers to CAIE structured questions with the mark scheme, gives
point-by-point feedback in four categories (Clearly correct, Possibly correct, Incorrect,
Outside the mark scheme), estimates the mark, diagnoses lost marks, re-marks corrections,
keeps a mistake notebook with progress tracking, and exports PDF reports and JSON backups.

The code follows the structure chart module by module, passes the composite records from the
design between modules, and is written in the style of Cambridge pseudocode (PascalCase
names, `# DECLARE` comments, explicit loops, no Python shortcuts; see
`../CAIE_Python_Style_v2/AGENTS.md`). The earlier browser version
([AI-SQ-Grader](https://github.com/ASH19900601/ai-sq-grader)) was used as a reference for the
AI request format and the marking rules.

## Run it

Python 3.8 or later. Nothing has to be installed; `pip install pypdf` is optional and lets the
program read answers from PDF files that contain text.

```text
python AISQGrader.py
```

To try it with the sample files, choose **1. Mark a new paper** and enter:

| Prompt | Type |
|---|---|
| Level / subject | 2 (AS Level), 2 (Chemistry) |
| Paper number, series, year | 22, 2 (May/June), 2023 |
| Answer files | `SampleData/Sample_Chemistry_Answers.txt`, then `SampleData/Sample_Answer_Q3.png`, then Enter |
| Mark scheme | `SampleData/Sample_Chemistry_MS.txt` |
| Correction | Y, `2(b)`, 2, `SampleData/Sample_Corrected_2b.txt` |
| Mistake notebook | 5 (show all), then 6 (close) |
| Backup / import | Y, then N |

Choose **2** in the main menu to reopen the saved records, filter the mistake notebook, back up,
or import a backup (try `SampleData/Invalid_Backup.json`).

## AI service

`Settings.txt` chooses the AI service:

- `Provider=Offline` (default): a built-in **demo marker** that compares key words. It needs no
  internet or API key, so the program can be tested and demonstrated anywhere, but it is far
  less accurate than an AI examiner.
- `Provider=OpenAI` or `Provider=DeepSeek`, or the base URL of any OpenAI-compatible service
  (`https://.../v1`), with `ModelName=...`. The API key is **never saved**: set the environment
  variable `SQ_API_KEY`, or type it when asked (the typing is hidden). Main menu option 3
  changes the service while the program runs.

The AI is asked for JSON; every reply is checked, and a failed or invalid reply marks the
points "Not assessed" and flags the question for review instead of marking it wrong.

## Modules and who wrote them

The split follows the group chat in Part 1 (Fox: paper selection and uploads; Kevin: document
processing and grading; Caroline: correction, regrading and learning records; Andy: PDF reports,
JSON backup and restore). The main module was added to Fox's part.

| Structure chart module | File | Member | Returns |
|---|---|---|---|
| AI SQ Grader (main) | `AISQGrader.py` | Fox | - |
| Paper and Document Management Module | `PaperDocumentManagement.py` | Fox | DocumentSet |
| Document Processing Module | `DocumentProcessing.py` | Kevin | ProcessedPaper |
| Grading and Feedback Module, with Assess Marking Points, Compare With Marking Points, Build Assessment Prompt, Request AI Judgement, Parse Point Feedback, Flag For Review, Calculate Estimated Mark, Diagnose Errors | `GradingFeedback.py` | Kevin | GradingResult |
| Correction and Regrading Module | `CorrectionRegrading.py` | Caroline | RegradeResult |
| Learning Records and Progress Module | `LearningRecords.py` | Caroline | LearningData |
| Report Management Module | `ReportManagement.py` | Andy | ReportOutcome |
| Composite records (Part 1 notes) | `SQRecords.py` | whole group | - |

Every module can also be run on its own (`python GradingFeedback.py`, ...): its `# main`
section uses sample data, which shows the module working independently.

## File formats

**Mark scheme** (`SampleData/Sample_Chemistry_MS.txt`), one line per item:

```text
QUESTION 2(a) [3]
P1 [1] moles of NaOH = 0.0250 x 0.100 = 0.00250 mol
P2 [1] moles of HCl = 0.00250 mol because the reacting ratio is 1 : 1
P3 [1] concentration of HCl = 0.100 mol dm-3
RULE P3 DEPENDS ON P2
```

Alternatives in a marking point are separated by `/`. A Cambridge mark scheme PDF has to be
typed into this form first, because the program cannot read its table layout.

**Answers**: a text file (or a PDF with text) where each answer starts with its question number,
e.g. `1(a) The nucleus contains ...`. Answers in photos (`.png`, `.jpg`) are kept as image
references and the question is flagged for a teacher to review.

**Learning records**: `LearningRecords.json` (created when the program runs) with the lists
`Papers`, `Mistakes`, `Attempts` (every attempt with its full feedback) and `Errors`. Reports are
saved in `Reports/`, backups in `Backups/`, downloaded mark schemes in `Downloads/`.

## Differences from the Part 1 design

- `PointFeedback` has one extra field, `Marks`, so Calculate Estimated Mark can add up marks from
  the PointFeedbackSet it receives (the chart gives it no MarkingPoints). Update the records note.
- Points that cannot be judged (flagged question, failed AI request) get the category
  "Not assessed"; they are never counted as Incorrect.
- Records are plain classes (one per pseudocode `TYPE`) rather than `@dataclass`, to stay close to
  the pseudocode. The Part 1 note "each record is a dataclass" can say "each record is a class".
- Handwriting and diagrams in images are not recognised (no AI vision in this version): such
  answers are flagged for review, which meets the "uncertain matches are flagged" criterion.
- The local database is a JSON file instead of a browser database.
- Main menu option 2 opens the learning records and reports without marking a new paper (the
  Learning Records and Report modules receive an empty GradingResult and RegradeResult).
- Diagnose Errors uses Request AI Judgement to ask the AI; if that is not possible it applies
  fixed rules (no answer, missing number or unit, paraphrase, partial idea).

## Tests

```text
python -m unittest discover -s tests -v
```

68 tests, one file per member. They use temporary folders and a local test server that answers
like an AI service, so no API key or internet connection is needed.

## Part 2 submission drafts

`Submission_Drafts/` has a draft for each member, made from the school template:
`<Name>_Part2_Submission.docx` (cover, the member's code, and a test plan) and
`<Name>_Part2_Submission.md` (the same test plan, a rubric checklist and a plan for the
one-minute video). Every "Actual outcome" was produced by running the program. After changing
any code, run `python Tools/BuildSubmissionDrafts.py` to rebuild them, then read every row and
put it in your own words where you wish.

Notes for the group:

- The code requirements ask you to acknowledge any code written by someone other than you.
  Follow your teacher's rules on how to acknowledge the shared `SQRecords.py`, the other
  members' modules you call, and any help from AI tools.
- Each video must be under one minute and 30 MB, show input, integration with another member's
  module and output, and must not show your name or voice. Run the program from a folder whose
  path does not contain your name.
