# ReportManagement.py
# AI SQ Grader - Report Management Module                       (Andy)
#
# Receives the GradingResult and LearningData and returns one ReportOutcome record.
# 1. Creates a PDF report: paper details, estimated scores, marking-point explanations,
#    error diagnoses, attempt histories and the progress summary.
# 2. Exports a JSON backup of the learning records, including every previous attempt and
#    its feedback (a copy of the Learning Records Module's database file).
# 3. Imports a JSON backup. The file is checked first: a valid backup is restored to the
#    local database (after a safety copy of the current records is made); an invalid
#    file produces a clear message and the saved records are not changed.
#
# The PDF file is written directly (PDF 1.4 with the standard Helvetica font), so no extra
# library has to be installed.
# Acknowledgement: the record types in SQRecords.py were agreed by the whole group; the
# database file format is defined by the Learning Records Module (Caroline).

import datetime            # date and time for the report and the backup file names
import json                # reads the backup file to check it
import os                  # os.path builds file paths; os.makedirs creates the folders

import SQRecords

# CONSTANT
ProgramFolder = os.path.dirname(os.path.abspath(__file__))
ReportFolder = os.path.join(ProgramFolder, "Reports")
BackupFolder = os.path.join(ProgramFolder, "Backups")
DatabasePath = os.path.join(ProgramFolder, SQRecords.DatabaseFileName)
LeftMargin = 50                        # PDF positions are in points; an A4 page is 595 x 842
TopLine = 790
LineSpacing = 14
LinesPerPage = 52
CharactersPerLine = 95

# CONSTANT  the fields every entry of a backup file must have: [field name, type]
# DECLARE PaperFields, MistakeFields, AttemptFields, ErrorFields, PointFields : ARRAY OF ARRAY[0:1] OF STRING
PaperFields = [["PaperCode", "STRING"], ["Subject", "STRING"], ["Session", "STRING"],
               ["TotalMark", "INTEGER"], ["MaxTotal", "INTEGER"], ["DateSaved", "STRING"]]
MistakeFields = [["PaperCode", "STRING"], ["QuestionID", "STRING"], ["TopicTags", "LIST"], ["Status", "STRING"]]
AttemptFields = [["PaperCode", "STRING"], ["QuestionID", "STRING"], ["AttemptNo", "INTEGER"],
                 ["AnswerText", "STRING"], ["EstimatedMark", "INTEGER"], ["Feedback", "DICTIONARY"]]
ErrorFields = [["PaperCode", "STRING"], ["QuestionID", "STRING"], ["ErrorType", "STRING"]]
PointFields = [["PointID", "STRING"], ["Category", "STRING"], ["Marks", "INTEGER"],
               ["Explanation", "STRING"], ["Evidence", "STRING"]]
ValidStatuses = [SQRecords.StatusNotCorrected, SQRecords.StatusPartlyCorrected,
                 SQRecords.StatusCorrected, SQRecords.StatusNeedsReview]
ValidCategories = [SQRecords.CategoryClearlyCorrect, SQRecords.CategoryPossiblyCorrect,
                   SQRecords.CategoryIncorrect, SQRecords.CategoryNotAssessed]

# CONSTANT  characters that the standard PDF font cannot show, and what is printed instead
# DECLARE CharacterReplacements : ARRAY OF ARRAY[0:1] OF STRING
CharacterReplacements = [["\u2013", "-"], ["\u2014", "-"], ["\u2212", "-"], ["\u2018", "'"],
                         ["\u2019", "'"], ["\u201c", '"'], ["\u201d", '"'], ["\u2192", "->"],
                         ["\u2190", "<-"], ["\u21cc", "<=>"], ["\u21c4", "<=>"], ["\u21d2", "=>"],
                         ["\u2191", "(up)"], ["\u2193", "(down)"], ["\u2265", ">="], ["\u2264", "<="],
                         ["\u2248", "~"], ["\u2260", "!="], ["\u221a", "sqrt"], ["\u221e", "infinity"],
                         ["\u2206", "Delta "], ["\u0394", "Delta "], ["\u03a3", "Sigma "], ["\u03a9", "Omega "],
                         ["\u03b1", "alpha"], ["\u03b2", "beta"], ["\u03b3", "gamma"], ["\u03b4", "delta"],
                         ["\u03b5", "epsilon"], ["\u03b8", "theta"], ["\u03bb", "lambda"], ["\u03bc", "mu"],
                         ["\u03c0", "pi"], ["\u03c1", "rho"], ["\u03c3", "sigma"], ["\u03c9", "omega"],
                         ["\u207a", "+"], ["\u207b", "-"], ["\u2103", " deg C"], ["\u2219", "."],
                         ["\u22c5", "."], ["\u2026", "..."], ["\u2022", "-"], ["\t", " "]]


# ===================================================================== small tools

def IsInList(Item, ItemList):
    # Linear search: TRUE if Item is in ItemList.
    # DECLARE Index : INTEGER
    for Index in range(0, len(ItemList)):
        if ItemList[Index] == Item:
            return True
    return False


def AskYesNo(Prompt):
    # REPEAT ... UNTIL the user types Y or N. Returns TRUE for Y.
    # DECLARE Reply : STRING
    Reply = input(Prompt + " (Y/N): ").strip().upper()
    while Reply != "Y" and Reply != "N":
        print("Please type Y or N.")
        Reply = input(Prompt + " (Y/N): ").strip().upper()
    return Reply == "Y"


def MakeTimeStamp():
    # e.g. 20261011_143005, used to give every report and backup its own file name
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def MakeSafeFileName(Text):
    # Replaces characters that cannot be used in a file name: 9701/22/M/J/23 -> 9701-22-M-J-23
    # DECLARE Result : STRING
    # DECLARE Index : INTEGER
    Result = ""
    for Index in range(0, len(Text)):
        if Text[Index] == "/" or Text[Index] == "\\" or Text[Index] == ":" or Text[Index] == " ":
            Result = Result + "-"
        else:
            Result = Result + Text[Index]
    return Result


def MakeFolder(FolderName):
    # Creates the folder if it does not exist yet. Returns TRUE if the folder is there.
    try:
        if os.path.isdir(FolderName) == False:
            os.makedirs(FolderName)
        return True
    except OSError:
        print("The folder", FolderName, "could not be created.")
        return False


def CopyTextFile(SourceName, TargetName):
    # Copies a text file line by line. Returns TRUE if the copy was made.
    # DECLARE ThisLine : STRING
    try:
        Source = open(SourceName, "r", encoding="utf-8")
    except IOError:
        return False
    try:
        Target = open(TargetName, "w", encoding="utf-8")
    except IOError:
        Source.close()
        return False
    ThisLine = Source.readline()
    while ThisLine != "":
        Target.write(ThisLine)
        ThisLine = Source.readline()
    Source.close()
    Target.close()
    return True


# ===================================================================== PDF report

def MakePdfSafe(Text):
    # Prepares text for a PDF string: \ ( ) are escaped with a backslash, and characters
    # that the standard font cannot show are replaced.
    # DECLARE Result, Replacement : STRING
    # DECLARE ThisChar : CHAR
    # DECLARE Index, Row, Code : INTEGER
    Result = ""
    for Index in range(0, len(Text)):
        ThisChar = Text[Index]
        Code = ord(ThisChar)                   # ASC(ThisChar)
        if ThisChar == "\\" or ThisChar == "(" or ThisChar == ")":
            Result = Result + "\\" + ThisChar
        elif (Code >= 32 and Code <= 126) or (Code >= 160 and Code <= 255):
            Result = Result + ThisChar
        elif Code >= 8320 and Code <= 8329:            # subscript digits, e.g. the 2 in H2O
            Result = Result + chr(Code - 8320 + 48)
        elif Code == 8304 or (Code >= 8308 and Code <= 8313):   # superscript 0 and 4 to 9
            Result = Result + "^" + chr(Code - 8304 + 48)
        else:
            Replacement = "?"
            for Row in range(0, len(CharacterReplacements)):
                if CharacterReplacements[Row][0] == ThisChar:
                    Replacement = CharacterReplacements[Row][1]
            Result = Result + Replacement
    return Result


def WrapText(Text, Width):
    # Splits one line of text into lines of at most Width characters, breaking at spaces.
    # Continuation lines keep the indentation of the first line plus four spaces.
    # DECLARE Lines, Words : ARRAY OF STRING
    # DECLARE Indent, ThisLine : STRING
    # DECLARE Index : INTEGER
    Lines = []
    Indent = ""
    Index = 0
    while Index < len(Text) and Text[Index] == " ":
        Indent = Indent + " "
        Index = Index + 1
    Words = Text.split()
    ThisLine = Indent
    for Index in range(0, len(Words)):
        while len(Words[Index]) > Width - len(Indent) - 4:              # a very long word is cut
            Lines.append(ThisLine)
            ThisLine = Indent + "    " + Words[Index][0:Width - len(Indent) - 4]
            Words[Index] = Words[Index][Width - len(Indent) - 4:]
        if ThisLine.strip() == "":
            ThisLine = ThisLine + Words[Index]
        elif len(ThisLine) + 1 + len(Words[Index]) <= Width:
            ThisLine = ThisLine + " " + Words[Index]
        else:
            Lines.append(ThisLine)
            ThisLine = Indent + "    " + Words[Index]
    Lines.append(ThisLine)
    return Lines


def PadNumber(Number, Width):
    # Writes a number with leading zeros, e.g. PadNumber(931, 10) -> "0000000931"
    # DECLARE Text : STRING
    Text = str(Number)
    while len(Text) < Width:
        Text = "0" + Text
    return Text


def BuildPageStream(PageLines, PageNumber, NumberOfPages):
    # Builds the drawing instructions for one page. A line that starts with "## " is a
    # heading and is printed in bold.
    # DECLARE Stream : STRING
    # DECLARE Index : INTEGER
    Stream = "BT\n/F1 10 Tf\n" + str(LineSpacing) + " TL\n" + str(LeftMargin) + " " + str(TopLine) + " Td\n"
    for Index in range(0, len(PageLines)):
        if PageLines[Index][0:3] == "## ":
            Stream = Stream + "/F2 12 Tf\n(" + MakePdfSafe(PageLines[Index][3:]) + ") Tj T*\n/F1 10 Tf\n"
        else:
            Stream = Stream + "(" + MakePdfSafe(PageLines[Index]) + ") Tj T*\n"
    Stream = Stream + "ET\nBT\n/F1 8 Tf\n" + str(LeftMargin) + " 30 Td\n"
    Stream = Stream + "(AI SQ Grader report - page " + str(PageNumber) + " of " + str(NumberOfPages) + ") Tj\nET"
    return Stream


def WritePdfReport(ReportLines, FileName):
    # Writes the report lines to a PDF file. Returns TRUE if the file was written.
    # A PDF file is a list of numbered objects followed by a table (xref) giving the byte
    # position of each object. Objects: 1 catalogue, 2 page list, 3 and 4 fonts, then a
    # page object and a content object for each page.
    # DECLARE Lines, ThisPage, Objects : ARRAY OF STRING
    # DECLARE Pages : ARRAY OF ARRAY OF STRING
    # DECLARE Offsets : ARRAY OF INTEGER
    # DECLARE PdfText, Kids, Stream : STRING
    # DECLARE Index, WrapIndex, PageIndex, XrefPosition : INTEGER
    # DECLARE Wrapped : ARRAY OF STRING
    Lines = []
    for Index in range(0, len(ReportLines)):
        if ReportLines[Index][0:3] == "## ":
            Lines.append(ReportLines[Index])
        else:
            Wrapped = WrapText(ReportLines[Index], CharactersPerLine)
            for WrapIndex in range(0, len(Wrapped)):
                Lines.append(Wrapped[WrapIndex])

    Pages = []
    ThisPage = []
    for Index in range(0, len(Lines)):
        if len(ThisPage) == LinesPerPage or (len(ThisPage) > LinesPerPage - 4 and Lines[Index][0:3] == "## "):
            Pages.append(ThisPage)             # start a new page (a heading never ends a page)
            ThisPage = []
        ThisPage.append(Lines[Index])
    Pages.append(ThisPage)

    Objects = []
    Objects.append("<< /Type /Catalog /Pages 2 0 R >>")
    Kids = ""
    for PageIndex in range(0, len(Pages)):
        Kids = Kids + str(5 + PageIndex * 2) + " 0 R "
    Objects.append("<< /Type /Pages /Kids [" + Kids + "] /Count " + str(len(Pages)) + " >>")
    Objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    Objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
    for PageIndex in range(0, len(Pages)):
        Stream = BuildPageStream(Pages[PageIndex], PageIndex + 1, len(Pages))
        Objects.append("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents "
                       + str(6 + PageIndex * 2) + " 0 R >>")
        Objects.append("<< /Length " + str(len(Stream)) + " >>\nstream\n" + Stream + "\nendstream")

    # every character is one byte (Latin-1), so the length of the text is its byte position
    PdfText = "%PDF-1.4\n"
    Offsets = []
    for Index in range(0, len(Objects)):
        Offsets.append(len(PdfText))
        PdfText = PdfText + str(Index + 1) + " 0 obj\n" + Objects[Index] + "\nendobj\n"
    XrefPosition = len(PdfText)
    PdfText = PdfText + "xref\n0 " + str(len(Objects) + 1) + "\n0000000000 65535 f \n"
    for Index in range(0, len(Offsets)):
        PdfText = PdfText + PadNumber(Offsets[Index], 10) + " 00000 n \n"
    PdfText = PdfText + "trailer\n<< /Size " + str(len(Objects) + 1) + " /Root 1 0 R >>\n"
    PdfText = PdfText + "startxref\n" + str(XrefPosition) + "\n%%EOF\n"

    try:
        File = open(FileName, "wb")
        File.write(PdfText.encode("latin-1"))
        File.close()
    except IOError:
        print("The PDF report could not be saved as", FileName)
        return False
    return True


def ShortSourceNames(SourceImageRef):
    # "C:/work/Page1.jpg; C:/work/Answers.pdf#2" -> "Page1.jpg, Answers.pdf page 2"
    # DECLARE Parts : ARRAY OF STRING
    # DECLARE Result, Name : STRING
    # DECLARE Index, Position : INTEGER
    Parts = SourceImageRef.split("; ")
    Result = ""
    for Index in range(0, len(Parts)):
        Name = os.path.basename(Parts[Index].strip())
        Position = len(Name) - 1
        while Position >= 0 and Name[Position] >= "0" and Name[Position] <= "9":
            Position = Position - 1
        if Position >= 0 and Position < len(Name) - 1 and Name[Position] == "#":
            Name = Name[0:Position] + " page " + Name[Position + 1:]
        if Result != "":
            Result = Result + ", "
        Result = Result + Name
    return Result


def FindRequirement(Question, PointID):
    # Linear search for the requirement of one marking point.
    # DECLARE Index : INTEGER
    for Index in range(0, len(Question.MarkingPoints)):
        if Question.MarkingPoints[Index].PointID == PointID:
            return Question.MarkingPoints[Index].Requirement
    return ""


def AddQuestionLines(Lines, Result, Learning):
    # Adds the report lines for one question to the list Lines (the list is changed).
    # DECLARE Index, AttemptCount : INTEGER
    # DECLARE AnswerLines : ARRAY OF STRING
    # DECLARE ThisAttempt : AttemptRecord
    # DECLARE MarkWord, Summary : STRING
    Lines.append("## Question " + Result.Question.QuestionID + "    estimated mark " + str(Result.EstimatedMark)
                 + " / " + str(Result.Question.MarkingRules.MaxMark))
    if Result.Feedback.NeedsReview == True:
        Lines.append("This question needs review by a teacher.")
    if Result.Question.QuestionText != "":
        Lines.append("Question:")
        AnswerLines = Result.Question.QuestionText.split("\n")
        for Index in range(0, len(AnswerLines)):
            Lines.append("    " + AnswerLines[Index])
    Lines.append("Student answer:")
    if Result.Question.AnswerText.strip() == "":
        if Result.Question.SourceImageRef != "":
            Lines.append("    (answer in image: " + ShortSourceNames(Result.Question.SourceImageRef) + ")")
        else:
            Lines.append("    (no answer found)")
    else:
        AnswerLines = Result.Question.AnswerText.split("\n")
        for Index in range(0, len(AnswerLines)):
            Lines.append("    " + AnswerLines[Index])
        if Result.Question.SourceImageRef != "":
            Lines.append("    (read from handwriting in: " + ShortSourceNames(Result.Question.SourceImageRef) + ")")
    Lines.append("Marking points:")
    if Result.Question.MarkingRules.RuleNotes != "":
        Lines.append("  Marking rules: " + Result.Question.MarkingRules.RuleNotes)
    for Index in range(0, len(Result.Feedback.Points)):
        MarkWord = " marks"
        if Result.Feedback.Points[Index].Marks == 1:
            MarkWord = " mark"
        Lines.append("  " + Result.Feedback.Points[Index].PointID + " (" + str(Result.Feedback.Points[Index].Marks) + MarkWord + ") ["
                     + Result.Feedback.Points[Index].Category + "] " + FindRequirement(Result.Question, Result.Feedback.Points[Index].PointID))
        Lines.append("      " + Result.Feedback.Points[Index].Explanation)
        if Result.Feedback.Points[Index].Evidence != "":
            Lines.append("      Evidence: " + Result.Feedback.Points[Index].Evidence)
    for Index in range(0, len(Result.Feedback.OutsideMSContent)):
        Lines.append("Outside the mark scheme: " + Result.Feedback.OutsideMSContent[Index])
    for Index in range(0, len(Result.Diagnoses)):
        Lines.append("Likely reason for lost mark (" + Result.Diagnoses[Index].PointID + "): "
                     + Result.Diagnoses[Index].ErrorType + " - " + Result.Diagnoses[Index].Explanation)

    # attempt history from the learning records (only shown when there is a correction)
    AttemptCount = 0
    for Index in range(0, len(Learning.AttemptHistories)):
        if Learning.AttemptHistories[Index].QuestionID == Result.Question.QuestionID:
            AttemptCount = AttemptCount + 1
    if AttemptCount > 1:
        Lines.append("Attempt history:")
        for Index in range(0, len(Learning.AttemptHistories)):
            ThisAttempt = Learning.AttemptHistories[Index]
            if ThisAttempt.QuestionID == Result.Question.QuestionID:
                Summary = "  Attempt " + str(ThisAttempt.AttemptNo) + ": " + str(ThisAttempt.EstimatedMark) + " / " + str(Result.Question.MarkingRules.MaxMark)
                if ThisAttempt.AttemptNo == 1:
                    Summary = Summary + " (original answer)"
                else:
                    Summary = Summary + " (correction)"
                Lines.append(Summary)
    Lines.append("")


def BuildReportLines(Grading, Learning):
    # Builds every line of the report. Returns ARRAY OF STRING.
    # DECLARE Lines : ARRAY OF STRING
    # DECLARE Index, StatusIndex, Count, Percent : INTEGER
    # DECLARE ScoreText, StatusText : STRING
    Lines = []
    Lines.append("## AI SQ Grader - Marking Report")
    Lines.append("Paper: " + Grading.Paper.Level + "   " + Grading.Paper.Subject)
    Lines.append("Paper code: " + Grading.Paper.PaperCode + "    Session: " + Grading.Paper.Session)
    Lines.append("Report created: " + datetime.datetime.now().isoformat(" ", "minutes"))
    Percent = 0
    if Grading.MaxTotal > 0:
        Percent = round(Grading.TotalMark * 100 / Grading.MaxTotal)
    Lines.append("Estimated total: " + str(Grading.TotalMark) + " / " + str(Grading.MaxTotal) + " (" + str(Percent) + "%)")
    Lines.append("Estimated marks count only Clearly correct points. They are practice estimates, not official grades.")
    Lines.append("")
    for Index in range(0, len(Grading.QuestionResults)):
        AddQuestionLines(Lines, Grading.QuestionResults[Index], Learning)

    Lines.append("## Progress summary")
    ScoreText = ""
    for Index in range(0, len(Learning.Progress.PaperScores)):
        if Index > 0:
            ScoreText = ScoreText + ", "
        ScoreText = ScoreText + str(Learning.Progress.PaperScores[Index]) + "%"
    if ScoreText == "":
        ScoreText = "none saved"
    Lines.append("Original paper scores, oldest first: " + ScoreText)
    Lines.append("Questions fully corrected: " + str(Learning.Progress.CorrectedCount))
    for Index in range(0, len(Learning.Progress.CommonErrorTypes)):
        Lines.append("Common reason for lost marks " + str(Index + 1) + ": " + Learning.Progress.CommonErrorTypes[Index])
    StatusText = ""
    for StatusIndex in range(0, len(ValidStatuses)):
        Count = 0
        for Index in range(0, len(Learning.MistakeEntries)):
            if Learning.MistakeEntries[Index].Status == ValidStatuses[StatusIndex]:
                Count = Count + 1
        StatusText = StatusText + "  " + ValidStatuses[StatusIndex] + ": " + str(Count)
    Lines.append("Mistake notebook entries: " + str(len(Learning.MistakeEntries)) + "  -" + StatusText)
    return Lines


# ===================================================================== JSON backup and import

def ExportBackup(DatabaseFileName, BackupFileName):
    # Copies the learning records file to a backup file. Returns TRUE if it worked.
    if os.path.isfile(DatabaseFileName) == False:
        print("There are no saved learning records to back up yet.")
        return False
    if MakeFolder(os.path.dirname(BackupFileName)) == False:
        return False
    if CopyTextFile(DatabaseFileName, BackupFileName) == False:
        print("The backup file could not be written.")
        return False
    return True


def HasType(Value, TypeName):
    # TRUE if Value has the pseudocode type TypeName. (type(True) is bool, not int, so a
    # BOOLEAN is not accepted as an INTEGER.)
    if TypeName == "STRING":
        return type(Value) == str
    if TypeName == "INTEGER":
        return type(Value) == int
    if TypeName == "LIST":
        return type(Value) == list
    if TypeName == "DICTIONARY":
        return type(Value) == dict
    if TypeName == "BOOLEAN":
        return type(Value) == bool
    return False


def CheckEntry(Entry, FieldTable, Description):
    # Checks that one entry has every field in FieldTable with the right type.
    # Returns "" if the entry is valid, otherwise a message naming the first problem.
    # DECLARE Row : INTEGER
    if type(Entry) != dict:
        return Description + " is not a record."
    for Row in range(0, len(FieldTable)):
        if Entry.get(FieldTable[Row][0]) is None:
            return Description + " has no " + FieldTable[Row][0] + "."
        if HasType(Entry[FieldTable[Row][0]], FieldTable[Row][1]) == False:
            return Description + ": " + FieldTable[Row][0] + " must be " + FieldTable[Row][1] + "."
    return ""


def CheckFeedback(Feedback, Description):
    # Checks the saved feedback of one attempt. Returns "" if valid.
    # DECLARE Problem : STRING
    # DECLARE Index : INTEGER
    if HasType(Feedback.get("Points"), "LIST") == False:
        return Description + ": Feedback has no list of Points."
    if HasType(Feedback.get("NeedsReview"), "BOOLEAN") == False:
        return Description + ": Feedback.NeedsReview must be BOOLEAN."
    if HasType(Feedback.get("OutsideMSContent"), "LIST") == False:
        return Description + ": Feedback.OutsideMSContent must be a list."
    for Index in range(0, len(Feedback["Points"])):
        Problem = CheckEntry(Feedback["Points"][Index], PointFields, Description + ", point " + str(Index + 1))
        if Problem != "":
            return Problem
        if IsInList(Feedback["Points"][Index]["Category"], ValidCategories) == False:
            return Description + ", point " + str(Index + 1) + ": unknown category " + Feedback["Points"][Index]["Category"]
    return ""


def ValidateBackupData(Data):
    # Checks the whole backup. Returns "" if it is valid, otherwise a clear message.
    # DECLARE Problem, Description : STRING
    # DECLARE Index, TagIndex : INTEGER
    if type(Data) != dict:
        return "The file does not contain AI SQ Grader learning records."
    if HasType(Data.get("Papers"), "LIST") == False or HasType(Data.get("Mistakes"), "LIST") == False or HasType(Data.get("Attempts"), "LIST") == False or HasType(Data.get("Errors"), "LIST") == False:
        return "The file must contain the lists Papers, Mistakes, Attempts and Errors."
    for Index in range(0, len(Data["Papers"])):
        Description = "Paper " + str(Index + 1)
        Problem = CheckEntry(Data["Papers"][Index], PaperFields, Description)
        if Problem != "":
            return Problem
        if Data["Papers"][Index]["TotalMark"] < 0 or Data["Papers"][Index]["TotalMark"] > Data["Papers"][Index]["MaxTotal"]:
            return Description + ": TotalMark must be from 0 to MaxTotal."
    for Index in range(0, len(Data["Mistakes"])):
        Description = "Mistake entry " + str(Index + 1)
        Problem = CheckEntry(Data["Mistakes"][Index], MistakeFields, Description)
        if Problem != "":
            return Problem
        if IsInList(Data["Mistakes"][Index]["Status"], ValidStatuses) == False:
            return Description + ": unknown status " + Data["Mistakes"][Index]["Status"]
        for TagIndex in range(0, len(Data["Mistakes"][Index]["TopicTags"])):
            if HasType(Data["Mistakes"][Index]["TopicTags"][TagIndex], "STRING") == False:
                return Description + ": every topic tag must be text."
    for Index in range(0, len(Data["Attempts"])):
        Description = "Attempt " + str(Index + 1)
        Problem = CheckEntry(Data["Attempts"][Index], AttemptFields, Description)
        if Problem != "":
            return Problem
        if Data["Attempts"][Index]["AttemptNo"] < 1 or Data["Attempts"][Index]["EstimatedMark"] < 0:
            return Description + ": AttemptNo must be 1 or more and EstimatedMark 0 or more."
        Problem = CheckFeedback(Data["Attempts"][Index]["Feedback"], Description)
        if Problem != "":
            return Problem
    for Index in range(0, len(Data["Errors"])):
        Description = "Error record " + str(Index + 1)
        Problem = CheckEntry(Data["Errors"][Index], ErrorFields, Description)
        if Problem != "":
            return Problem
        if IsInList(Data["Errors"][Index]["ErrorType"], SQRecords.ErrorTypes) == False:
            return Description + ": unknown error type " + Data["Errors"][Index]["ErrorType"]
    return ""


def ReadWholeFile(FileName):
    # Reads a text file into one string. Returns None if it cannot be read.
    # DECLARE FileText, ThisLine : STRING
    FileText = ""
    try:
        File = open(FileName, "r", encoding="utf-8")
    except IOError:
        return None
    try:
        ThisLine = File.readline()
        while ThisLine != "":
            FileText = FileText + ThisLine
            ThisLine = File.readline()
    except UnicodeDecodeError:
        FileText = None
    File.close()
    return FileText


def ImportBackup(BackupFileName, DatabaseFileName):
    # Checks a backup file and, if it is valid, restores it as the learning records.
    # Returns "" if the records were restored, otherwise the reason it failed.
    # DECLARE FileText, SafetyName : STRING
    # DECLARE Data : the decoded JSON
    if BackupFileName == "":
        return "No file name was given."
    if BackupFileName.lower()[len(BackupFileName) - 5:] != ".json":
        return "The backup must be a .json file."
    FileText = ReadWholeFile(BackupFileName)
    if FileText is None:
        return "The file " + BackupFileName + " could not be opened."
    try:
        Data = json.loads(FileText)
    except ValueError:
        return "The file is not valid JSON."
    Problem = ValidateBackupData(Data)
    if Problem != "":
        return Problem
    # keep a safety copy of the current records before they are replaced
    if os.path.isfile(DatabaseFileName) == True:
        SafetyName = os.path.join(BackupFolder, "BeforeImport_" + MakeTimeStamp() + ".json")
        if ExportBackup(DatabaseFileName, SafetyName) == False:
            return "A safety copy of the current records could not be made, so nothing was imported."
        print("Your current records were first saved as", SafetyName)
    if CopyTextFile(BackupFileName, DatabaseFileName) == False:
        return "The learning records file could not be written."
    return ""


# ===================================================================== the module

def ManageReports(Grading, Learning):
    # Report Management Module: returns one ReportOutcome record.
    # DECLARE Outcome : ReportOutcome
    # DECLARE FileName, Problem : STRING
    Outcome = SQRecords.ReportOutcome()
    print()
    print("=== Report Management ===")
    if len(Grading.QuestionResults) > 0:
        FileName = os.path.join(ReportFolder, "Report_" + MakeSafeFileName(Grading.Paper.PaperCode) + "_" + MakeTimeStamp() + ".pdf")
        if MakeFolder(ReportFolder) == True and WritePdfReport(BuildReportLines(Grading, Learning), FileName) == True:
            Outcome.ReportFile = FileName
            print("PDF report saved:", FileName)

    if AskYesNo("Export a JSON backup of all learning records?") == True:
        FileName = os.path.join(BackupFolder, "LearningBackup_" + MakeTimeStamp() + ".json")
        if ExportBackup(DatabasePath, FileName) == True:
            Outcome.BackupFile = FileName
            print("Backup saved:", FileName)

    if AskYesNo("Import (restore) learning records from a JSON backup?") == True:
        FileName = input("Backup file (.json): ").strip()
        if len(FileName) >= 2 and FileName[0:1] == '"' and FileName[len(FileName) - 1:] == '"':
            FileName = FileName[1:len(FileName) - 1]
        Problem = ImportBackup(FileName, DatabasePath)
        if Problem == "":
            Outcome.ImportValid = True
            Outcome.Message = "Backup imported: the learning records have been restored from " + FileName
        else:
            Outcome.ImportValid = False
            Outcome.Message = "Import failed - " + Problem + " Your saved records have not been changed."
        print(Outcome.Message)
    return Outcome


# main - runs this module on its own: a report for one sample question, then backup / import
if __name__ == "__main__":
    TestGrading = SQRecords.GradingResult()
    TestGrading.Paper.Level = "AS Level"
    TestGrading.Paper.Subject = "Chemistry (9701)"
    TestGrading.Paper.PaperCode = "9701/22/M/J/23"
    TestGrading.Paper.Session = "May/June 2023"
    TestResult = SQRecords.QuestionResult()
    TestResult.Question.QuestionID = "1(b)"
    TestResult.Question.AnswerText = "Isotopes have the same number of protons."
    TestResult.Question.MarkingRules.MaxMark = 1
    TestPoint = SQRecords.MarkingPoint()
    TestPoint.PointID = "P1"
    TestPoint.Marks = 1
    TestPoint.Requirement = "isotopes have the same number of protons but different numbers of neutrons"
    TestResult.Question.MarkingPoints.append(TestPoint)
    TestFeedback = SQRecords.PointFeedback()
    TestFeedback.PointID = "P1"
    TestFeedback.Marks = 1
    TestFeedback.Category = SQRecords.CategoryPossiblyCorrect
    TestFeedback.Explanation = "The neutrons are not mentioned."
    TestResult.Feedback.Points.append(TestFeedback)
    TestGrading.QuestionResults.append(TestResult)
    TestGrading.MaxTotal = 1
    TestOutcome = ManageReports(TestGrading, SQRecords.LearningData())
    print("ReportFile =", TestOutcome.ReportFile)
