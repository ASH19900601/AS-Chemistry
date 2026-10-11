# AI SQ Grader (Python version)

A Python implementation of the group's Part 1 design for the **AI Structure Question Grader**.
It compares a student's answers to CAIE structured questions with the mark scheme and:

- reads a Cambridge mark scheme PDF, the question paper and photos or scans of handwritten
  answers with an AI service;
- gives point-by-point feedback in four categories (Clearly correct, Possibly correct,
  Incorrect, Outside the mark scheme);
- estimates the mark and diagnoses each lost mark;
- re-marks corrections, typed or photographed;
- keeps a mistake notebook and progress tracking;
- exports PDF reports, and backs up and restores the learning records as JSON.

The modules follow the structure chart. Where the chart would have stopped a feature from
working, the code goes beyond it; the differences are listed below. The code is written in
the style of Cambridge pseudocode (PascalCase names, `# DECLARE` comments, explicit loops, no
Python shortcuts; see `../CAIE_Python_Style_v2/AGENTS.md`). The browser version
([AI-SQ-Grader](https://github.com/ASH19900601/ai-sq-grader)) was used as a reference for the
AI request format, mark-scheme reading and the marking rules.

## Run it

Python 3.8 or later. Optional libraries:

```text
pip install pymupdf      # PDF text, and scanned PDF pages turned into pictures for the AI
pip install pypdf        # PDF text only (used if pymupdf is not installed)
```

Without them the program still runs with text files and photos.

```text
python AISQGrader.py
```

To try it with the sample files and the offline demo marker, choose **1. Mark a new paper**
and enter:

| Prompt | Type |
|---|---|
| Level / subject | 2 (AS Level), 2 (Chemistry) |
| Paper number, series, year | 22, 2 (May/June), 2023 |
| Answer files | `SampleData/Sample_Chemistry_Answers.txt`, then `SampleData/Sample_Answer_Q3.png`, then Enter |
| Mark scheme / question paper | `SampleData/Sample_Chemistry_MS.txt`, then Enter (no question paper) |
| Correction | Y, `2(b)`, 2, `SampleData/Sample_Corrected_2b.txt` |
| Mistake notebook | 5 (show all), then 6 (close) |
| Backup / import | Y, then N |

Main menu option 2 reopens the saved records, filters the mistake notebook, backs up, or
imports a backup (try `SampleData/Invalid_Backup.json`). Option 4 tests the AI connection.

## AI service

`Settings.txt` (or main menu option 3) chooses the AI service:

- `Provider=Offline` (default): a built-in **demo marker** that compares key words. It needs
  no internet or API key, so the program can be tested and demonstrated anywhere. It is far
  less accurate than an AI examiner. It cannot read Cambridge mark scheme PDFs, question papers
  or handwriting: such answers are flagged for review.
- `Provider=OpenAI` or `Provider=DeepSeek`, or the base URL of any OpenAI-compatible service
  (`https://.../v1`), with `ModelName=...`. To read photos and scanned pages, use a model that
  accepts images, for example `gpt-4o-mini`; `deepseek-chat` reads text only. The API key is
  **never saved**: set the environment variable `SQ_API_KEY`, or type it when asked (the
  typing is hidden).

With an AI service:

| Step | What the AI does | Safeguard |
|---|---|---|
| Mark scheme | Reads a Cambridge mark scheme PDF a few pages at a time (skipping the cover and general marking principles) and returns the marking points, marks and "depends on" rules | The result is saved as `ParsedMarkSchemes/<name>_SQ.txt` to be checked and corrected; if any part fails, marking stops |
| Question paper (optional) | Copies the question text for each question, so the examiner knows what was asked | Marking continues without it if it fails |
| Answers | Transcribes photos and scanned pages of handwriting and matches each answer to its question number | Low-confidence readings, unreadable images and unknown question numbers are flagged for review |
| Marking | Judges each marking point, seeing the question text and the original handwriting images | Every reply is checked; a failed or invalid reply gives "Not assessed" and a review flag, never "Incorrect" |
| Diagnosis | Gives the likely reason for each lost mark | Falls back to fixed rules |

## Modules and who wrote them

The split follows the group chat in Part 1 (Fox: paper selection and uploads; Kevin: document
processing and grading; Caroline: correction, regrading and learning records; Andy: PDF reports,
JSON backup and restore). The main module and the AI connection were added to Fox's part.

| Module | File | Member | Returns |
|---|---|---|---|
| AI SQ Grader (main) | `AISQGrader.py` | Fox | - |
| AI connection (requests to the AI service, with images) | `AIConnection.py` | Fox | AIResponse |
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

**SQ text format for mark schemes** (`SampleData/Sample_Chemistry_MS.txt`), read without AI:

```text
QUESTION 2(a) [3]
P1 [1] moles of NaOH = 0.0250 x 0.100 = 0.00250 mol
P2 [1] moles of HCl = 0.00250 mol because the reacting ratio is 1 : 1
P3 [1] concentration of HCl = 0.100 mol dm-3
RULE P3 DEPENDS ON P2
```

Alternatives in a marking point are separated by `/`. Any other mark scheme (for example a
Cambridge PDF) is read by the AI and saved in this format.

**Answers**: typed text or PDF text, where each answer starts with its question number
(`1(a) The nucleus contains ...`); or photos (`.png`, `.jpg`, `.webp`) and scanned PDF pages of
handwriting, which are read by the AI.

**Files the program creates**:
- `LearningRecords.json` holds the lists `Papers`, `Mistakes`, `Attempts` (every attempt with
  its full feedback) and `Errors`.
- `Reports/` holds the PDF reports.
- `Backups/` holds the JSON backups.
- `Downloads/` holds downloaded papers.
- `ParsedMarkSchemes/` holds mark schemes read by the AI.

## Differences from the Part 1 design

- **AI reading of documents.** The Document Processing Module also receives AISettings, so the
  AI can read mark scheme PDFs, the question paper and handwriting (Part 1 functionality 2).
  The chart gave this module no AISettings.
- **New AI connection module.** All AI requests go through `AIConnection.py`, a new shared
  module. Request AI Judgement is still in the Grading and Feedback Module, and calls it.
- **Optional question paper.** `DocumentSet.QuestionPaperFile` and `QuestionItem.QuestionText`
  are new fields; the question text is given to the AI examiner.
- **Marks on each point.** `PointFeedback.Marks` is a new field, so Calculate Estimated Mark can
  add up marks from the PointFeedbackSet.
- **"Not assessed" category.** Points that cannot be judged (a flagged question, a failed AI
  request) get the category "Not assessed"; they are never counted as Incorrect.
- **Records are classes.** Records are plain classes (one per pseudocode `TYPE`) rather than
  `@dataclass`, to stay close to the pseudocode.
- **Local database.** The database is a JSON file instead of a browser database.
- **Reviewing without marking.** Main menu option 2 opens the records and reports without
  marking a new paper (empty GradingResult and RegradeResult), and option 4 tests the AI
  connection.
- **Dashboard and report extras.** The dashboard shows the average score by subject. Each
  mistake-notebook entry shows what still needs improving. The PDF report shows the question
  text and writes chemistry and maths symbols (H₂O, Na⁺, Δ, ⇌) in a form the PDF font can print.

## Tests

```text
python -m unittest discover -s tests -v
```

89 tests, one file per member. They use temporary folders and a local test server that answers
like an OpenAI-compatible AI service, so no API key or internet connection is needed. They
cover reading mark scheme PDFs, scans and photos, and the error paths. The program has not yet
been run here against a real AI service.

## Part 2 submission drafts

`Submission_Drafts/` has a draft for each member, made from the school template:
`<Name>_Part2_Submission.docx` (cover, the member's code, and a test plan) and
`<Name>_Part2_Submission.md` (the same test plan, a rubric checklist and a plan for the
one-minute video). Every "Actual outcome" was produced by running the program. Rows marked
"test AI server" used the local test server instead of a real AI service. After changing any
code, run `python Tools/BuildSubmissionDrafts.py` to rebuild them, then read every row and put
it in your own words where you wish. The tables are long; keep the tests you want.

Notes for the group:

- The code requirements ask you to acknowledge any code written by someone other than you.
  Follow your teacher's rules on how to acknowledge the shared `SQRecords.py`, the other
  members' modules you call, and any help from AI tools.
- Each video must be under one minute and 30 MB, show input, integration with another member's
  module and output, and must not show your name or voice. Run the program from a folder whose
  path does not contain your name. Never show your API key on screen.
