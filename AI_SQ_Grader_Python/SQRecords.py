# SQRecords.py
# AI SQ Grader - shared record types and constants.
#
# Written by the whole group from the Part 1 design ("Composite Return Records").
# Every module imports this file, so all modules pass the same records between them.
# Each class is a pseudocode record:  TYPE <Name> ... ENDTYPE
# __init__ gives every field a starting value of the right type; the calling module then
# assigns the fields, for example:  Paper = PaperDetails()  /  Paper.Level = "AS Level"
#
# Changes from the Part 1 notes (made so that the program works fully):
# - PointFeedback.Marks: copied from the marking point, so CalculateEstimatedMark can add up
#   marks from the PointFeedbackSet.
# - QuestionItem.QuestionText: the question from the question paper, so the AI knows what
#   was asked.
# - DocumentSet.QuestionPaperFile: the optional question paper.

# CONSTANT
CategoryClearlyCorrect = "Clearly correct"
CategoryPossiblyCorrect = "Possibly correct"
CategoryIncorrect = "Incorrect"
CategoryNotAssessed = "Not assessed"           # used when a question is flagged or the AI fails

# CONSTANT  ARRAY[0:5] OF STRING - reasons for lost marks (Part 1, functionality 4)
ErrorTypes = ["Conceptual error", "Calculation mistake", "Missing information",
              "Incomplete explanation", "Inaccurate terminology", "Incorrect units"]

# CONSTANT  correction status of a mistake-notebook entry
StatusNotCorrected = "Not corrected"
StatusPartlyCorrected = "Partly corrected"
StatusCorrected = "Corrected"
StatusNeedsReview = "Needs review"

# CONSTANT
OfflineProvider = "Offline"                    # built-in demo marker, no internet needed
DatabaseFileName = "LearningRecords.json"      # local database of the Learning Records Module


# ---------------------------------------------------------------- parameter records

class AISettings:                              # TYPE AISettings
    def __init__(self):
        self.Provider = OfflineProvider        # STRING  Offline, OpenAI, DeepSeek or a base URL
        self.ModelName = ""                    # STRING
        self.APIKey = ""                       # STRING  never saved to a file
                                               # ENDTYPE


class DownloadSettings:                        # TYPE DownloadSettings
    def __init__(self):
        self.ServiceURL = ""                   # STRING
        self.Enabled = False                   # BOOLEAN
                                               # ENDTYPE


# ---------------------------------------------------------------- nested records

class PaperDetails:                            # TYPE PaperDetails
    def __init__(self):
        self.Level = ""                        # STRING  e.g. "AS Level"
        self.Subject = ""                      # STRING  e.g. "Chemistry (9701)"
        self.PaperCode = ""                    # STRING  e.g. "9701/22/M/J/23"
        self.Session = ""                      # STRING  e.g. "May/June 2023"
                                               # ENDTYPE


class MarkingPoint:                            # TYPE MarkingPoint
    def __init__(self):
        self.PointID = ""                      # STRING  e.g. "P1"
        self.Requirement = ""                  # STRING  what the answer must contain
        self.Marks = 0                         # INTEGER
                                               # ENDTYPE


class MarkRules:                               # TYPE MarkRules
    def __init__(self):
        self.MaxMark = 0                       # INTEGER
        self.RuleNotes = ""                    # STRING  e.g. "P3 DEPENDS ON P2"
                                               # ENDTYPE


class QuestionItem:                            # TYPE QuestionItem
    def __init__(self):
        self.QuestionID = ""                   # STRING  e.g. "1(a)(ii)"
        self.QuestionText = ""                 # STRING  from the question paper (optional)
        self.AnswerText = ""                   # STRING
        self.MarkingPoints = []                # ARRAY OF MarkingPoint
        self.MarkingRules = MarkRules()        # MarkRules
        self.SourceImageRef = ""               # STRING  image file(s) or PDF page(s) holding the answer,
                                               #         e.g. "Page3.jpg; Answers.pdf#2"
                                               # ENDTYPE


class PointFeedback:                           # TYPE PointFeedback
    def __init__(self):
        self.PointID = ""                      # STRING
        self.Category = CategoryNotAssessed    # STRING  Clearly correct / Possibly correct / Incorrect
        self.Marks = 0                         # INTEGER (added, see note at the top)
        self.Explanation = ""                  # STRING
        self.Evidence = ""                     # STRING  words taken from the student's answer
                                               # ENDTYPE


class ErrorDiagnosis:                          # TYPE ErrorDiagnosis
    def __init__(self):
        self.ErrorType = ""                    # STRING  one of ErrorTypes
        self.PointID = ""                      # STRING
        self.Evidence = ""                     # STRING
        self.Explanation = ""                  # STRING
                                               # ENDTYPE


class QuestionResult:                          # TYPE QuestionResult
    def __init__(self):
        self.Question = QuestionItem()         # QuestionItem
        self.Feedback = PointFeedbackSet()     # PointFeedbackSet
        self.EstimatedMark = 0                 # INTEGER
        self.Diagnoses = []                    # ARRAY OF ErrorDiagnosis
                                               # ENDTYPE


class AttemptRecord:                           # TYPE AttemptRecord
    def __init__(self):
        self.QuestionID = ""                   # STRING
        self.AttemptNo = 0                     # INTEGER  1 = original answer
        self.AnswerText = ""                   # STRING
        self.Feedback = PointFeedbackSet()     # PointFeedbackSet
        self.EstimatedMark = 0                 # INTEGER
                                               # ENDTYPE


class MistakeEntry:                            # TYPE MistakeEntry
    def __init__(self):
        self.PaperCode = ""                    # STRING
        self.QuestionID = ""                   # STRING
        self.TopicTags = []                    # ARRAY OF STRING
        self.Status = StatusNotCorrected       # STRING
                                               # ENDTYPE


class ProgressSummary:                         # TYPE ProgressSummary
    def __init__(self):
        self.PaperScores = []                  # ARRAY OF INTEGER  percentage for each paper
        self.CommonErrorTypes = []             # ARRAY OF STRING   most frequent first
        self.CorrectedCount = 0                # INTEGER
                                               # ENDTYPE


# ---------------------------------------------------------------- composite return records

class DocumentSet:                             # TYPE DocumentSet
    def __init__(self):
        self.Paper = PaperDetails()            # PaperDetails
        self.AnswerFiles = []                  # ARRAY OF STRING
        self.MarkSchemeFile = ""               # STRING
        self.QuestionPaperFile = ""            # STRING  optional
        self.IsComplete = False                # BOOLEAN
                                               # ENDTYPE


class ProcessedPaper:                          # TYPE ProcessedPaper
    def __init__(self):
        self.Paper = PaperDetails()            # PaperDetails
        self.Questions = []                    # ARRAY OF QuestionItem
        self.UncertainMatches = []             # ARRAY OF STRING  question numbers to review
                                               # ENDTYPE


class PointFeedbackSet:                        # TYPE PointFeedbackSet
    def __init__(self):
        self.Points = []                       # ARRAY OF PointFeedback
        self.OutsideMSContent = []             # ARRAY OF STRING
        self.NeedsReview = False               # BOOLEAN
                                               # ENDTYPE


class AIResponse:                              # TYPE AIResponse
    def __init__(self):
        self.Success = False                   # BOOLEAN
        self.ReplyText = ""                    # STRING
        self.ErrorMessage = ""                 # STRING
                                               # ENDTYPE


class GradingResult:                           # TYPE GradingResult
    def __init__(self):
        self.Paper = PaperDetails()            # PaperDetails
        self.QuestionResults = []              # ARRAY OF QuestionResult
        self.TotalMark = 0                     # INTEGER
        self.MaxTotal = 0                      # INTEGER
                                               # ENDTYPE


class RegradeResult:                           # TYPE RegradeResult
    def __init__(self):
        self.HasCorrection = False             # BOOLEAN
        self.QuestionID = ""                   # STRING
        self.Attempts = []                     # ARRAY OF AttemptRecord
        self.MarkChange = 0                    # INTEGER
        self.FeedbackChanges = []              # ARRAY OF STRING
                                               # ENDTYPE


class LearningData:                            # TYPE LearningData
    def __init__(self):
        self.MistakeEntries = []               # ARRAY OF MistakeEntry
        self.AttemptHistories = []             # ARRAY OF AttemptRecord
        self.Progress = ProgressSummary()      # ProgressSummary
        self.SaveSuccess = False               # BOOLEAN
                                               # ENDTYPE


class ReportOutcome:                           # TYPE ReportOutcome
    def __init__(self):
        self.ReportFile = ""                   # STRING
        self.BackupFile = ""                   # STRING
        self.ImportValid = False               # BOOLEAN
        self.Message = ""                      # STRING
                                               # ENDTYPE
