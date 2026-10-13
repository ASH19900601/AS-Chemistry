# LearningRecords.py
# AI SQ Grader - Learning Records and Progress Module            (Caroline)
#
# Receives the GradingResult and RegradeResult and stores the results, answers, feedback
# and attempt histories in a local database file (LearningRecords.json), so they are still
# there when the application is closed and reopened. Keeps the mistake notebook, which
# can be filtered by subject, topic, paper and correction status, and calculates the
# progress summary. Returns one LearningData record.
# Original paper scores and later correction attempts are kept separately.
#
# Acknowledgement: the record types in SQRecords.py were agreed by the whole group.

import datetime            # date and time when a paper result is saved
import json                # converts the database to and from JSON text
import os                  # os.path finds the database file; os.replace swaps in the new file

import SQRecords

# CONSTANT
ProgramFolder = os.path.dirname(os.path.abspath(__file__))
DatabasePath = os.path.join(ProgramFolder, SQRecords.DatabaseFileName)
DatabaseVersion = 1

# CONSTANT  parallel arrays: a question gets topic TopicNames[i] if a marking point contains
# one of the words in TopicWords[i]
# DECLARE TopicNames : ARRAY[0:13] OF STRING
# DECLARE TopicWords : ARRAY[0:13] OF ARRAY OF STRING
TopicNames = ["Atomic structure", "Chemical bonding", "Moles and stoichiometry", "Reaction kinetics",
              "Energetics", "Equilibrium", "Acids and bases", "Redox and electrochemistry",
              "Organic chemistry", "Forces and motion", "Electricity", "Waves",
              "Cells and biomolecules", "Algorithms and programming"]
TopicWords = [["proton", "neutron", "electron", "nucleus", "isotope", "shell", "orbital", "nucleon"],
              ["covalent", "ionic", "metallic", "bond", "lattice", "electronegativity", "intermolecular"],
              ["mole", "mol", "concentration", "titration", "stoichiometry", "ratio", "yield"],
              ["rate", "activation", "collision", "catalyst", "boltzmann"],
              ["enthalpy", "exothermic", "endothermic", "hess"],
              ["equilibrium", "chatelier", "reversible"],
              ["acid", "base", "alkali", "ph", "neutralisation", "buffer"],
              ["oxidation", "reduction", "redox", "electrode", "electrolysis"],
              ["alkane", "alkene", "alcohol", "ester", "isomer", "polymer"],
              ["force", "acceleration", "velocity", "momentum", "newton"],
              ["current", "voltage", "resistance", "circuit", "potential"],
              ["wave", "frequency", "wavelength", "amplitude", "diffraction"],
              ["cell", "enzyme", "membrane", "protein", "dna"],
              ["algorithm", "array", "loop", "variable", "procedure"]]
FilterTypes = ["Subject", "Topic", "Paper", "Correction status", "Show all entries", "Close the notebook"]


# ---------------------------------------------------------------- records used only in this module

class PaperScoreRecord:                        # TYPE PaperScoreRecord - one original paper result
    def __init__(self):
        self.PaperCode = ""                    # STRING
        self.Subject = ""                      # STRING
        self.Session = ""                      # STRING
        self.TotalMark = 0                     # INTEGER
        self.MaxTotal = 0                      # INTEGER
        self.DateSaved = ""                    # STRING
                                               # ENDTYPE


class StoredAttempt:                           # TYPE StoredAttempt - an attempt and its paper
    def __init__(self):
        self.PaperCode = ""                    # STRING
        self.Attempt = SQRecords.AttemptRecord()   # AttemptRecord
                                               # ENDTYPE


class ErrorRecord:                             # TYPE ErrorRecord - one diagnosed lost mark
    def __init__(self):
        self.PaperCode = ""                    # STRING
        self.QuestionID = ""                   # STRING
        self.ErrorType = ""                    # STRING
                                               # ENDTYPE


class LearningDatabase:                        # TYPE LearningDatabase - everything in the file
    def __init__(self):
        self.Papers = []                       # ARRAY OF PaperScoreRecord
        self.Mistakes = []                     # ARRAY OF MistakeEntry
        self.Attempts = []                     # ARRAY OF StoredAttempt
        self.Errors = []                       # ARRAY OF ErrorRecord
                                               # ENDTYPE


# ---------------------------------------------------------------- converting to and from JSON

def FeedbackToDictionary(Feedback):
    # Converts a PointFeedbackSet into dictionaries and lists that json.dumps can write.
    # DECLARE PointList : ARRAY OF dictionary
    # DECLARE Index : INTEGER
    PointList = []
    for Index in range(0, len(Feedback.Points)):
        PointList.append({"PointID": Feedback.Points[Index].PointID,
                          "Category": Feedback.Points[Index].Category,
                          "Marks": Feedback.Points[Index].Marks,
                          "Explanation": Feedback.Points[Index].Explanation,
                          "Evidence": Feedback.Points[Index].Evidence})
    return {"Points": PointList, "OutsideMSContent": Feedback.OutsideMSContent,
            "NeedsReview": Feedback.NeedsReview}


def DictionaryToFeedback(Data):
    # Converts saved data back into a PointFeedbackSet. Missing values get starting values.
    # DECLARE Feedback : PointFeedbackSet
    # DECLARE ThisPoint : PointFeedback
    # DECLARE Index : INTEGER
    Feedback = SQRecords.PointFeedbackSet()
    if type(Data) != dict:
        return Feedback
    if type(Data.get("Points")) == list:
        for Index in range(0, len(Data["Points"])):
            if type(Data["Points"][Index]) == dict:
                ThisPoint = SQRecords.PointFeedback()
                ThisPoint.PointID = str(Data["Points"][Index].get("PointID", ""))
                ThisPoint.Category = str(Data["Points"][Index].get("Category", SQRecords.CategoryNotAssessed))
                ThisPoint.Marks = int(Data["Points"][Index].get("Marks", 0))
                ThisPoint.Explanation = str(Data["Points"][Index].get("Explanation", ""))
                ThisPoint.Evidence = str(Data["Points"][Index].get("Evidence", ""))
                Feedback.Points.append(ThisPoint)
    if type(Data.get("OutsideMSContent")) == list:
        for Index in range(0, len(Data["OutsideMSContent"])):
            Feedback.OutsideMSContent.append(str(Data["OutsideMSContent"][Index]))
    Feedback.NeedsReview = Data.get("NeedsReview", False) == True
    return Feedback


def DatabaseToDictionary(Database):
    # Converts the whole database into dictionaries and lists for json.dumps.
    # DECLARE Data : dictionary
    # DECLARE Index : INTEGER
    # DECLARE ThisAttempt : AttemptRecord
    Data = {"Version": DatabaseVersion, "Papers": [], "Mistakes": [], "Attempts": [], "Errors": []}
    for Index in range(0, len(Database.Papers)):
        Data["Papers"].append({"PaperCode": Database.Papers[Index].PaperCode,
                               "Subject": Database.Papers[Index].Subject,
                               "Session": Database.Papers[Index].Session,
                               "TotalMark": Database.Papers[Index].TotalMark,
                               "MaxTotal": Database.Papers[Index].MaxTotal,
                               "DateSaved": Database.Papers[Index].DateSaved})
    for Index in range(0, len(Database.Mistakes)):
        Data["Mistakes"].append({"PaperCode": Database.Mistakes[Index].PaperCode,
                                 "QuestionID": Database.Mistakes[Index].QuestionID,
                                 "TopicTags": Database.Mistakes[Index].TopicTags,
                                 "Status": Database.Mistakes[Index].Status})
    for Index in range(0, len(Database.Attempts)):
        ThisAttempt = Database.Attempts[Index].Attempt
        Data["Attempts"].append({"PaperCode": Database.Attempts[Index].PaperCode,
                                 "QuestionID": ThisAttempt.QuestionID,
                                 "AttemptNo": ThisAttempt.AttemptNo,
                                 "AnswerText": ThisAttempt.AnswerText,
                                 "EstimatedMark": ThisAttempt.EstimatedMark,
                                 "Feedback": FeedbackToDictionary(ThisAttempt.Feedback)})
    for Index in range(0, len(Database.Errors)):
        Data["Errors"].append({"PaperCode": Database.Errors[Index].PaperCode,
                               "QuestionID": Database.Errors[Index].QuestionID,
                               "ErrorType": Database.Errors[Index].ErrorType})
    return Data


def GetList(Data, Key):
    # Returns Data[Key] if it is a list, otherwise an empty list.
    if type(Data) == dict and type(Data.get(Key)) == list:
        return Data[Key]
    return []


def DictionaryToDatabase(Data):
    # Converts the data read from the file back into records. Entries that are not
    # dictionaries are skipped.
    # DECLARE Database : LearningDatabase
    # DECLARE Rows : ARRAY
    # DECLARE Index, TagIndex : INTEGER
    Database = LearningDatabase()
    Rows = GetList(Data, "Papers")
    for Index in range(0, len(Rows)):
        if type(Rows[Index]) == dict:
            Paper = PaperScoreRecord()
            Paper.PaperCode = str(Rows[Index].get("PaperCode", ""))
            Paper.Subject = str(Rows[Index].get("Subject", ""))
            Paper.Session = str(Rows[Index].get("Session", ""))
            Paper.TotalMark = int(Rows[Index].get("TotalMark", 0))
            Paper.MaxTotal = int(Rows[Index].get("MaxTotal", 0))
            Paper.DateSaved = str(Rows[Index].get("DateSaved", ""))
            Database.Papers.append(Paper)
    Rows = GetList(Data, "Mistakes")
    for Index in range(0, len(Rows)):
        if type(Rows[Index]) == dict:
            Entry = SQRecords.MistakeEntry()
            Entry.PaperCode = str(Rows[Index].get("PaperCode", ""))
            Entry.QuestionID = str(Rows[Index].get("QuestionID", ""))
            Entry.Status = str(Rows[Index].get("Status", SQRecords.StatusNotCorrected))
            for TagIndex in range(0, len(GetList(Rows[Index], "TopicTags"))):
                Entry.TopicTags.append(str(Rows[Index]["TopicTags"][TagIndex]))
            Database.Mistakes.append(Entry)
    Rows = GetList(Data, "Attempts")
    for Index in range(0, len(Rows)):
        if type(Rows[Index]) == dict:
            Stored = StoredAttempt()
            Stored.PaperCode = str(Rows[Index].get("PaperCode", ""))
            Stored.Attempt.QuestionID = str(Rows[Index].get("QuestionID", ""))
            Stored.Attempt.AttemptNo = int(Rows[Index].get("AttemptNo", 1))
            Stored.Attempt.AnswerText = str(Rows[Index].get("AnswerText", ""))
            Stored.Attempt.EstimatedMark = int(Rows[Index].get("EstimatedMark", 0))
            Stored.Attempt.Feedback = DictionaryToFeedback(Rows[Index].get("Feedback"))
            Database.Attempts.append(Stored)
    Rows = GetList(Data, "Errors")
    for Index in range(0, len(Rows)):
        if type(Rows[Index]) == dict:
            Error = ErrorRecord()
            Error.PaperCode = str(Rows[Index].get("PaperCode", ""))
            Error.QuestionID = str(Rows[Index].get("QuestionID", ""))
            Error.ErrorType = str(Rows[Index].get("ErrorType", ""))
            Database.Errors.append(Error)
    return Database


# ---------------------------------------------------------------- the database file

def LoadDatabase(FileName):
    # Reads the database file. Returns an empty database if there is no file yet.
    # A damaged file is kept as <name>.damaged so that no saved data is lost.
    # DECLARE Database : LearningDatabase
    # DECLARE FileText, ThisLine : STRING
    Database = LearningDatabase()
    if os.path.isfile(FileName) == False:
        print("No saved learning records yet - a new record will be started.")
        return Database
    FileText = ""
    try:
        File = open(FileName, "r", encoding="utf-8")
        ThisLine = File.readline()
        while ThisLine != "":
            FileText = FileText + ThisLine
            ThisLine = File.readline()
        File.close()
    except (IOError, UnicodeDecodeError):
        print("The learning records file could not be read.")
        return Database
    try:
        Database = DictionaryToDatabase(json.loads(FileText))
    except (ValueError, TypeError):
        print("The learning records file is damaged. It has been kept as", FileName + ".damaged")
        try:
            File = open(FileName + ".damaged", "w", encoding="utf-8")
            File.write(FileText)
            File.close()
        except IOError:
            print("The damaged file could not be copied.")
        Database = LearningDatabase()
    return Database


def SaveDatabase(Database, FileName):
    # Writes the database as JSON. The text is written to a temporary file first and then
    # swapped in, so the old records are not lost if writing fails part way.
    # Returns TRUE if the records were saved.
    # DECLARE TempName : STRING
    TempName = FileName + ".tmp"
    try:
        File = open(TempName, "w", encoding="utf-8")
        File.write(json.dumps(DatabaseToDictionary(Database), indent=2))
        File.close()
        os.replace(TempName, FileName)
    except IOError:
        print("The learning records could not be saved to", FileName)
        return False
    return True


# ---------------------------------------------------------------- adding results

def FindMistakeIndex(Database, PaperCode, QuestionID):
    # Linear search of the mistake notebook. Returns the position or -1.
    # DECLARE Index : INTEGER
    for Index in range(0, len(Database.Mistakes)):
        if Database.Mistakes[Index].PaperCode == PaperCode and Database.Mistakes[Index].QuestionID == QuestionID:
            return Index
    return -1


def NextAttemptNo(Database, PaperCode, QuestionID):
    # The next attempt number for a question is one more than the highest saved so far.
    # DECLARE Highest, Index : INTEGER
    Highest = 0
    for Index in range(0, len(Database.Attempts)):
        if Database.Attempts[Index].PaperCode == PaperCode and Database.Attempts[Index].Attempt.QuestionID == QuestionID:
            if Database.Attempts[Index].Attempt.AttemptNo > Highest:
                Highest = Database.Attempts[Index].Attempt.AttemptNo
    return Highest + 1


def SimplifyWord(Word):
    # Lower case and without a plural "s", so "Protons" matches the topic word "proton".
    # DECLARE Length : INTEGER
    Word = Word.lower()
    Length = len(Word)
    if Length > 3 and Word[Length - 1:] == "s" and Word[Length - 2:] != "ss":
        Word = Word[0:Length - 1]
    return Word


def SplitWords(Text):
    # Splits text into words of letters only.
    # DECLARE Words : ARRAY OF STRING
    # DECLARE ThisWord : STRING
    # DECLARE Index : INTEGER
    # DECLARE ThisChar : CHAR
    Words = []
    ThisWord = ""
    Text = Text.lower()
    for Index in range(0, len(Text)):
        ThisChar = Text[Index]
        if ThisChar >= "a" and ThisChar <= "z":
            ThisWord = ThisWord + ThisChar
        else:
            if ThisWord != "":
                Words.append(SimplifyWord(ThisWord))
            ThisWord = ""
    if ThisWord != "":
        Words.append(SimplifyWord(ThisWord))
    return Words


def FindTopicTags(Question):
    # Gives a question every topic whose topic words appear in its marking points.
    # Returns ["General"] if no topic is found.
    # DECLARE Tags, Words : ARRAY OF STRING
    # DECLARE PointIndex, TopicIndex, WordIndex, Index : INTEGER
    # DECLARE Found : BOOLEAN
    # DECLARE PointWords : ARRAY OF STRING
    Words = []
    for PointIndex in range(0, len(Question.MarkingPoints)):
        PointWords = SplitWords(Question.MarkingPoints[PointIndex].Requirement)
        for Index in range(0, len(PointWords)):
            Words.append(PointWords[Index])
    Tags = []
    for TopicIndex in range(0, len(TopicNames)):
        Found = False
        WordIndex = 0
        while WordIndex < len(TopicWords[TopicIndex]) and Found == False:
            for Index in range(0, len(Words)):
                if Words[Index] == TopicWords[TopicIndex][WordIndex]:
                    Found = True
            WordIndex = WordIndex + 1
        if Found == True:
            Tags.append(TopicNames[TopicIndex])
    if len(Tags) == 0:
        Tags.append("General")
    return Tags


def MakeStoredAttempt(PaperCode, Attempt, AttemptNo):
    # Copies an attempt into a StoredAttempt with the given attempt number.
    # DECLARE Stored : StoredAttempt
    Stored = StoredAttempt()
    Stored.PaperCode = PaperCode
    Stored.Attempt.QuestionID = Attempt.QuestionID
    Stored.Attempt.AttemptNo = AttemptNo
    Stored.Attempt.AnswerText = Attempt.AnswerText
    Stored.Attempt.Feedback = Attempt.Feedback
    Stored.Attempt.EstimatedMark = Attempt.EstimatedMark
    return Stored


def AddGradingResult(Database, Grading):
    # Saves the original paper score, an attempt for every question, a mistake-notebook
    # entry for every question that lost marks or needs review, and every error diagnosis.
    # The lists inside Database are changed by this procedure.
    # DECLARE Paper : PaperScoreRecord
    # DECLARE Result : QuestionResult
    # DECLARE Attempt : AttemptRecord
    # DECLARE Entry : MistakeEntry
    # DECLARE Error : ErrorRecord
    # DECLARE Index, MistakeIndex, DiagnosisIndex : INTEGER
    # DECLARE PaperCode, Status : STRING
    if len(Grading.QuestionResults) == 0:
        return
    PaperCode = Grading.Paper.PaperCode
    Paper = PaperScoreRecord()
    Paper.PaperCode = PaperCode
    Paper.Subject = Grading.Paper.Subject
    Paper.Session = Grading.Paper.Session
    Paper.TotalMark = Grading.TotalMark
    Paper.MaxTotal = Grading.MaxTotal
    Paper.DateSaved = datetime.datetime.now().isoformat(" ", "minutes")
    Database.Papers.append(Paper)

    for Index in range(0, len(Grading.QuestionResults)):
        Result = Grading.QuestionResults[Index]
        Attempt = SQRecords.AttemptRecord()
        Attempt.QuestionID = Result.Question.QuestionID
        Attempt.AnswerText = Result.Question.AnswerText
        Attempt.Feedback = Result.Feedback
        Attempt.EstimatedMark = Result.EstimatedMark
        Database.Attempts.append(MakeStoredAttempt(PaperCode, Attempt, NextAttemptNo(Database, PaperCode, Attempt.QuestionID)))

        MistakeIndex = FindMistakeIndex(Database, PaperCode, Result.Question.QuestionID)
        if Result.Feedback.NeedsReview == True:
            Status = SQRecords.StatusNeedsReview
        elif Result.EstimatedMark < Result.Question.MarkingRules.MaxMark:
            Status = SQRecords.StatusNotCorrected
        else:
            Status = SQRecords.StatusCorrected
        if MistakeIndex == -1 and Status != SQRecords.StatusCorrected:
            Entry = SQRecords.MistakeEntry()
            Entry.PaperCode = PaperCode
            Entry.QuestionID = Result.Question.QuestionID
            Entry.TopicTags = FindTopicTags(Result.Question)
            Entry.Status = Status
            Database.Mistakes.append(Entry)
        elif MistakeIndex != -1:
            Database.Mistakes[MistakeIndex].Status = Status     # the paper was marked again

        for DiagnosisIndex in range(0, len(Result.Diagnoses)):
            Error = ErrorRecord()
            Error.PaperCode = PaperCode
            Error.QuestionID = Result.Question.QuestionID
            Error.ErrorType = Result.Diagnoses[DiagnosisIndex].ErrorType
            Database.Errors.append(Error)


def FindQuestionResult(Grading, QuestionID):
    # Linear search of the GradingResult. Returns the position or -1.
    # DECLARE Index : INTEGER
    for Index in range(0, len(Grading.QuestionResults)):
        if Grading.QuestionResults[Index].Question.QuestionID == QuestionID:
            return Index
    return -1


def AddRegradeResult(Database, Grading, Regrade):
    # Saves the corrected attempt (attempt 1, the original, is already saved) and updates
    # the correction status of the mistake-notebook entry.
    # DECLARE NewAttempt : AttemptRecord
    # DECLARE Entry : MistakeEntry
    # DECLARE Index, MistakeIndex, ResultIndex, MaxMark : INTEGER
    # DECLARE PaperCode, Status : STRING
    if Regrade.HasCorrection == False:
        return
    PaperCode = Grading.Paper.PaperCode
    for Index in range(0, len(Regrade.Attempts)):
        if Regrade.Attempts[Index].AttemptNo > 1:
            Database.Attempts.append(MakeStoredAttempt(PaperCode, Regrade.Attempts[Index],
                                                       NextAttemptNo(Database, PaperCode, Regrade.QuestionID)))
    NewAttempt = Regrade.Attempts[len(Regrade.Attempts) - 1]
    MaxMark = 0
    ResultIndex = FindQuestionResult(Grading, Regrade.QuestionID)
    if ResultIndex != -1:
        MaxMark = Grading.QuestionResults[ResultIndex].Question.MarkingRules.MaxMark
    if NewAttempt.Feedback.NeedsReview == True:
        Status = SQRecords.StatusNeedsReview
    elif NewAttempt.EstimatedMark >= MaxMark:
        Status = SQRecords.StatusCorrected
    elif Regrade.MarkChange > 0:
        Status = SQRecords.StatusPartlyCorrected
    else:
        Status = SQRecords.StatusNotCorrected
    MistakeIndex = FindMistakeIndex(Database, PaperCode, Regrade.QuestionID)
    if MistakeIndex == -1:
        Entry = SQRecords.MistakeEntry()
        Entry.PaperCode = PaperCode
        Entry.QuestionID = Regrade.QuestionID
        if ResultIndex != -1:
            Entry.TopicTags = FindTopicTags(Grading.QuestionResults[ResultIndex].Question)
        Entry.Status = Status
        Database.Mistakes.append(Entry)
    else:
        Database.Mistakes[MistakeIndex].Status = Status


# ---------------------------------------------------------------- progress summary

def SortCounts(Names, Counts):
    # Bubble sort of two parallel arrays, largest count first. Both lists are changed.
    # DECLARE Boundary, Index, TempCount : INTEGER
    # DECLARE TempName : STRING
    # DECLARE NoSwaps : BOOLEAN
    Boundary = len(Counts) - 1
    NoSwaps = False
    while NoSwaps == False and Boundary > 0:      # REPEAT ... UNTIL NoSwaps = TRUE
        NoSwaps = True
        for Index in range(0, Boundary):
            if Counts[Index] < Counts[Index + 1]:
                TempCount = Counts[Index]
                Counts[Index] = Counts[Index + 1]
                Counts[Index + 1] = TempCount
                TempName = Names[Index]
                Names[Index] = Names[Index + 1]
                Names[Index + 1] = TempName
                NoSwaps = False
        Boundary = Boundary - 1


def CalculateProgress(Database):
    # Returns the ProgressSummary: the percentage for each original paper, the error types
    # from most to least frequent, and the number of fully corrected questions.
    # DECLARE Progress : ProgressSummary
    # DECLARE TypeNames : ARRAY[0:5] OF STRING
    # DECLARE TypeCounts : ARRAY[0:5] OF INTEGER
    # DECLARE Index, TypeIndex : INTEGER
    Progress = SQRecords.ProgressSummary()
    for Index in range(0, len(Database.Papers)):
        if Database.Papers[Index].MaxTotal > 0:
            Progress.PaperScores.append(round(Database.Papers[Index].TotalMark * 100 / Database.Papers[Index].MaxTotal))

    TypeNames = []
    TypeCounts = []
    for TypeIndex in range(0, len(SQRecords.ErrorTypes)):
        TypeNames.append(SQRecords.ErrorTypes[TypeIndex])
        TypeCounts.append(0)
    for Index in range(0, len(Database.Errors)):
        for TypeIndex in range(0, len(TypeNames)):
            if TypeNames[TypeIndex] == Database.Errors[Index].ErrorType:
                TypeCounts[TypeIndex] = TypeCounts[TypeIndex] + 1
    SortCounts(TypeNames, TypeCounts)
    for TypeIndex in range(0, len(TypeNames)):
        if TypeCounts[TypeIndex] > 0:
            Progress.CommonErrorTypes.append(TypeNames[TypeIndex] + " (" + str(TypeCounts[TypeIndex]) + ")")

    for Index in range(0, len(Database.Mistakes)):
        if Database.Mistakes[Index].Status == SQRecords.StatusCorrected:
            Progress.CorrectedCount = Progress.CorrectedCount + 1
    return Progress


def CountCorrectionAttempts(Database):
    # Attempts numbered 2 or more are corrections, not original answers.
    # DECLARE Count, Index : INTEGER
    Count = 0
    for Index in range(0, len(Database.Attempts)):
        if Database.Attempts[Index].Attempt.AttemptNo > 1:
            Count = Count + 1
    return Count


def DisplaySubjectAverages(Database):
    # Outputs the average original score for each subject, so progress can be inspected
    # by subject.
    # DECLARE Subjects : ARRAY OF STRING
    # DECLARE PercentTotals, PaperCounts : ARRAY OF INTEGER
    # DECLARE Index, SubjectIndex, SearchIndex, Percent : INTEGER
    Subjects = []
    PercentTotals = []
    PaperCounts = []
    for Index in range(0, len(Database.Papers)):
        if Database.Papers[Index].MaxTotal > 0:
            Percent = round(Database.Papers[Index].TotalMark * 100 / Database.Papers[Index].MaxTotal)
            SubjectIndex = -1
            for SearchIndex in range(0, len(Subjects)):
                if Subjects[SearchIndex] == Database.Papers[Index].Subject:
                    SubjectIndex = SearchIndex
            if SubjectIndex == -1:
                Subjects.append(Database.Papers[Index].Subject)
                PercentTotals.append(0)
                PaperCounts.append(0)
                SubjectIndex = len(Subjects) - 1
            PercentTotals[SubjectIndex] = PercentTotals[SubjectIndex] + Percent
            PaperCounts[SubjectIndex] = PaperCounts[SubjectIndex] + 1
    if len(Subjects) > 0:
        print("Average by subject:")
        for Index in range(0, len(Subjects)):
            print("  " + Subjects[Index] + ": " + str(PaperCounts[Index]) + " paper(s), average "
                  + str(round(PercentTotals[Index] / PaperCounts[Index])) + "%")


def DisplayDashboard(Database, Progress):
    # Outputs the progress dashboard. Original paper scores are shown apart from corrections.
    # DECLARE Index, Percent : INTEGER
    print()
    print("--- Progress dashboard ---")
    if len(Database.Papers) == 0:
        print("No papers have been marked yet.")
    else:
        print("Original paper results (corrections not included):")
        for Index in range(0, len(Database.Papers)):
            Percent = 0
            if Database.Papers[Index].MaxTotal > 0:
                Percent = round(Database.Papers[Index].TotalMark * 100 / Database.Papers[Index].MaxTotal)
            print("  " + Database.Papers[Index].DateSaved + "  " + Database.Papers[Index].PaperCode + "  "
                  + Database.Papers[Index].Subject + "  " + str(Database.Papers[Index].TotalMark) + " / "
                  + str(Database.Papers[Index].MaxTotal) + "  (" + str(Percent) + "%)")
        DisplaySubjectAverages(Database)
    print("Correction attempts saved:", CountCorrectionAttempts(Database))
    print("Questions now fully corrected:", Progress.CorrectedCount)
    if len(Progress.CommonErrorTypes) > 0:
        print("Most common reasons for lost marks:")
        for Index in range(0, len(Progress.CommonErrorTypes)):
            print("  " + str(Index + 1) + ". " + Progress.CommonErrorTypes[Index])
    print("Mistake notebook entries:", len(Database.Mistakes))


# ---------------------------------------------------------------- mistake notebook

def GetSubjectOfPaper(Database, PaperCode):
    # Finds the subject saved with a paper; uses the subject code if the paper is not found.
    # DECLARE Index : INTEGER
    for Index in range(0, len(Database.Papers)):
        if Database.Papers[Index].PaperCode == PaperCode:
            return Database.Papers[Index].Subject
    return PaperCode[0:4]                      # LEFT(PaperCode, 4) is the subject code


def EntryMatches(Database, Entry, FilterType, FilterValue):
    # TRUE if one mistake entry passes the filter (FilterType is a position in FilterTypes).
    # DECLARE Index : INTEGER
    if FilterType == 0:
        return GetSubjectOfPaper(Database, Entry.PaperCode) == FilterValue
    if FilterType == 1:
        for Index in range(0, len(Entry.TopicTags)):
            if Entry.TopicTags[Index] == FilterValue:
                return True
        return False
    if FilterType == 2:
        return Entry.PaperCode == FilterValue
    if FilterType == 3:
        return Entry.Status == FilterValue
    return True


def FilterMistakes(Database, FilterType, FilterValue):
    # Returns the mistake entries that pass the filter.
    # DECLARE Selected : ARRAY OF MistakeEntry
    # DECLARE Index : INTEGER
    Selected = []
    for Index in range(0, len(Database.Mistakes)):
        if EntryMatches(Database, Database.Mistakes[Index], FilterType, FilterValue) == True:
            Selected.append(Database.Mistakes[Index])
    return Selected


def AddIfNew(Values, NewValue):
    # Appends NewValue to the list only if it is not already there (linear search).
    # DECLARE Index : INTEGER
    for Index in range(0, len(Values)):
        if Values[Index] == NewValue:
            return
    Values.append(NewValue)


def CollectFilterValues(Database, FilterType):
    # Returns the different values that can be chosen for a filter.
    # DECLARE Values : ARRAY OF STRING
    # DECLARE Index, TagIndex : INTEGER
    Values = []
    for Index in range(0, len(Database.Mistakes)):
        if FilterType == 0:
            AddIfNew(Values, GetSubjectOfPaper(Database, Database.Mistakes[Index].PaperCode))
        elif FilterType == 1:
            for TagIndex in range(0, len(Database.Mistakes[Index].TopicTags)):
                AddIfNew(Values, Database.Mistakes[Index].TopicTags[TagIndex])
        elif FilterType == 2:
            AddIfNew(Values, Database.Mistakes[Index].PaperCode)
        elif FilterType == 3:
            AddIfNew(Values, Database.Mistakes[Index].Status)
    return Values


def DisplayMistakes(Database, Entries):
    # Outputs each mistake entry with its attempt history, so the question can be revised.
    # DECLARE Index, TagIndex, AttemptIndex, PointIndex : INTEGER
    # DECLARE ThisAttempt, LatestAttempt : AttemptRecord
    # DECLARE PointSummary : STRING
    if len(Entries) == 0:
        print("No mistake-notebook entries match this filter.")
        return
    for Index in range(0, len(Entries)):
        print()
        print(str(Index + 1) + ". " + Entries[Index].PaperCode + "  question " + Entries[Index].QuestionID
              + "  [" + Entries[Index].Status + "]")
        PointSummary = ""
        for TagIndex in range(0, len(Entries[Index].TopicTags)):
            if TagIndex > 0:
                PointSummary = PointSummary + ", "
            PointSummary = PointSummary + Entries[Index].TopicTags[TagIndex]
        print("   Topics: " + PointSummary)
        LatestAttempt = None
        for AttemptIndex in range(0, len(Database.Attempts)):
            if Database.Attempts[AttemptIndex].PaperCode == Entries[Index].PaperCode and Database.Attempts[AttemptIndex].Attempt.QuestionID == Entries[Index].QuestionID:
                ThisAttempt = Database.Attempts[AttemptIndex].Attempt
                PointSummary = ""
                for PointIndex in range(0, len(ThisAttempt.Feedback.Points)):
                    PointSummary = PointSummary + "  " + ThisAttempt.Feedback.Points[PointIndex].PointID + ": " + ThisAttempt.Feedback.Points[PointIndex].Category
                print("   Attempt " + str(ThisAttempt.AttemptNo) + " - mark " + str(ThisAttempt.EstimatedMark) + " -" + PointSummary)
                if LatestAttempt is None or ThisAttempt.AttemptNo > LatestAttempt.AttemptNo:
                    LatestAttempt = ThisAttempt
        # what the latest attempt still needs, so the question can be revised
        if LatestAttempt is not None:
            for PointIndex in range(0, len(LatestAttempt.Feedback.Points)):
                if LatestAttempt.Feedback.Points[PointIndex].Category != SQRecords.CategoryClearlyCorrect:
                    print("   To improve - " + LatestAttempt.Feedback.Points[PointIndex].PointID + ": "
                          + LatestAttempt.Feedback.Points[PointIndex].Explanation)


def InputChoice(Prompt, Options):
    # Numbered menu; returns the position chosen (0 to len(Options) - 1).
    # DECLARE Index, Choice : INTEGER
    print(Prompt)
    for Index in range(0, len(Options)):
        print("  " + str(Index + 1) + ". " + Options[Index])
    Choice = 0
    while Choice < 1 or Choice > len(Options):
        try:
            Choice = int(input("Enter a number from 1 to " + str(len(Options)) + ": "))
        except ValueError:
            Choice = 0
    return Choice - 1


def ReviewMistakeNotebook(Database):
    # Lets the user filter the mistake notebook until they choose to close it.
    # DECLARE FilterType, ValueChoice : INTEGER
    # DECLARE Values : ARRAY OF STRING
    if len(Database.Mistakes) == 0:
        return
    FilterType = InputChoice("Open the mistake notebook - filter by:", FilterTypes)
    while FilterType != len(FilterTypes) - 1:
        if FilterType == 4:
            DisplayMistakes(Database, Database.Mistakes)
        else:
            Values = CollectFilterValues(Database, FilterType)
            ValueChoice = InputChoice("Choose the " + FilterTypes[FilterType].lower() + ":", Values)
            DisplayMistakes(Database, FilterMistakes(Database, FilterType, Values[ValueChoice]))
        print()
        FilterType = InputChoice("Mistake notebook - filter by:", FilterTypes)


# ---------------------------------------------------------------- the module

def UpdateLearningRecords(Grading, Regrade):
    # Learning Records and Progress Module: returns one LearningData record.
    # DECLARE Learning : LearningData
    # DECLARE Database : LearningDatabase
    # DECLARE Index : INTEGER
    Learning = SQRecords.LearningData()
    print()
    print("=== Learning Records and Progress ===")
    Database = LoadDatabase(DatabasePath)
    AddGradingResult(Database, Grading)
    AddRegradeResult(Database, Grading, Regrade)
    Learning.SaveSuccess = SaveDatabase(Database, DatabasePath)
    if Learning.SaveSuccess == True and len(Grading.QuestionResults) > 0:
        print("Results saved to", DatabasePath)
    Learning.Progress = CalculateProgress(Database)
    Learning.MistakeEntries = Database.Mistakes
    for Index in range(0, len(Database.Attempts)):
        if len(Grading.QuestionResults) == 0 or Database.Attempts[Index].PaperCode == Grading.Paper.PaperCode:
            Learning.AttemptHistories.append(Database.Attempts[Index].Attempt)
    DisplayDashboard(Database, Learning.Progress)
    ReviewMistakeNotebook(Database)
    return Learning


# main - runs this module on its own: shows the saved records and the mistake notebook
if __name__ == "__main__":
    TestLearning = UpdateLearningRecords(SQRecords.GradingResult(), SQRecords.RegradeResult())
    print("SaveSuccess =", TestLearning.SaveSuccess)
