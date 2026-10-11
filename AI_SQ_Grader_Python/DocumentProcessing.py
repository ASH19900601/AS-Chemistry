# DocumentProcessing.py
# AI SQ Grader - Document Processing Module                     (Kevin)
#
# Receives the DocumentSet and returns one ProcessedPaper record.
# 1. Reads the mark scheme and extracts question numbers, marking points, available marks
#    and marking rules.
# 2. Reads the student's answer files and finds the answer to each question.
# 3. Lists every uncertain match (no answer found, answer only in an image, or an answer
#    whose question number is not in the mark scheme) so that it is flagged for review.
#
# Mark scheme text format (see SampleData/Sample_Chemistry_MS.txt):
#     QUESTION 1(a) [2]
#     P1 [1] protons and neutrons are in the nucleus
#     RULE P2 DEPENDS ON P1
# Answer text format: each answer starts with its question number, e.g.  1(a) The nucleus ...
#
# Acknowledgement: the record types in SQRecords.py were agreed by the whole group.

import os                  # os.path finds the file extension and file name

import SQRecords

try:
    import pypdf           # optional library that reads the text of PDF files (pip install pypdf)
    PdfLibraryAvailable = True
except ImportError:
    PdfLibraryAvailable = False

# CONSTANT
TextTypes = [".txt"]
PdfTypes = [".pdf"]
ImageTypes = [".png", ".jpg", ".jpeg"]


def GetExtension(FileName):
    # os.path.splitext separates the extension: "Answers.TXT" -> ".TXT"
    return os.path.splitext(FileName)[1].lower()


def IsInList(Item, ItemList):
    # Linear search: TRUE if Item is in ItemList.
    # DECLARE Index : INTEGER
    for Index in range(0, len(ItemList)):
        if ItemList[Index] == Item:
            return True
    return False


def ContainsChar(Text, SearchChar):
    # TRUE if SearchChar appears anywhere in Text.
    # DECLARE Index : INTEGER
    for Index in range(0, len(Text)):
        if Text[Index] == SearchChar:
            return True
    return False


def ReadTextFile(FileName):
    # Reads a text file line by line. Returns the lines without their line endings.
    # DECLARE Lines : ARRAY OF STRING
    # DECLARE ThisLine : STRING
    Lines = []
    try:
        File = open(FileName, "r", encoding="utf-8")
    except IOError:
        print("Could not open", FileName)
        return Lines
    try:
        ThisLine = File.readline()
        while ThisLine != "":
            Lines.append(ThisLine.rstrip("\n"))
            ThisLine = File.readline()
    except UnicodeDecodeError:
        print("Could not read", FileName, "- save it as a UTF-8 text file.")
    File.close()
    return Lines


def ReadPdfText(FileName):
    # Reads the text layer of a PDF file, page by page. A scanned PDF has no text layer,
    # so it returns no lines and is treated as an image.
    # DECLARE Lines, PageLines : ARRAY OF STRING
    # DECLARE PageNumber, Index : INTEGER
    Lines = []
    if PdfLibraryAvailable == False:
        print("PDF text cannot be read because the pypdf library is not installed (pip install pypdf).")
        return Lines
    try:
        Reader = pypdf.PdfReader(FileName)
        for PageNumber in range(0, len(Reader.pages)):
            PageLines = Reader.pages[PageNumber].extract_text().split("\n")
            for Index in range(0, len(PageLines)):
                Lines.append(PageLines[Index])
    except (IOError, ValueError, pypdf.errors.PyPdfError):
        print("Could not read the PDF file", FileName)
    return Lines


def ReadDocumentLines(FileName):
    # Chooses how to read the file from its extension.
    # DECLARE Extension : STRING
    Extension = GetExtension(FileName)
    if IsInList(Extension, TextTypes) == True:
        return ReadTextFile(FileName)
    if IsInList(Extension, PdfTypes) == True:
        return ReadPdfText(FileName)
    return []


def IsDigit(ThisChar):
    return ThisChar >= "0" and ThisChar <= "9"


def IsLetter(ThisChar):
    return (ThisChar >= "a" and ThisChar <= "z") or (ThisChar >= "A" and ThisChar <= "Z")


def NormaliseLabel(Text):
    # Turns a question number into the standard form used by the mark scheme:
    # "1(a)(ii)" -> "1(a)(ii)", "Q2b" -> "2(b)", "3." -> "3", "1(A):" -> "1(a)".
    # Returns "" if the text is not a question number.
    # DECLARE Result, Group : STRING
    # DECLARE Position : INTEGER
    # DECLARE ThisChar : CHAR
    Text = Text.strip().lower()
    while len(Text) > 0 and (Text[len(Text) - 1:] == "." or Text[len(Text) - 1:] == ":"):
        Text = Text[0:len(Text) - 1]           # remove a full stop or colon at the end
    if Text[0:1] == "q":
        Text = Text[1:]
    Result = ""
    Position = 0
    while Position < len(Text) and IsDigit(Text[Position]) == True:
        Result = Result + Text[Position]
        Position = Position + 1
    if Result == "":
        return ""                              # a question number starts with a digit
    while Position < len(Text):
        ThisChar = Text[Position]
        Group = ""
        if ThisChar == "(":
            Position = Position + 1
            while Position < len(Text) and Text[Position] != ")":
                Group = Group + Text[Position]
                Position = Position + 1
            if Position == len(Text) or Group == "":
                return ""                      # bracket not closed, or empty brackets
            Position = Position + 1            # skip ")"
        elif IsLetter(ThisChar) == True:
            while Position < len(Text) and IsLetter(Text[Position]) == True:
                Group = Group + Text[Position]
                Position = Position + 1
        else:
            return ""                          # any other character: not a question number
        Result = Result + "(" + Group + ")"
    return Result


def ReadBracketNumber(Text):
    # "[2]" -> 2. Returns -1 if the text is not a whole number in square brackets.
    # DECLARE Inside : STRING
    Text = Text.strip()
    if len(Text) < 3 or Text[0:1] != "[" or Text[len(Text) - 1:] != "]":
        return -1
    Inside = Text[1:len(Text) - 1]
    try:
        return int(Inside)
    except ValueError:
        return -1


def IsPointID(Word):
    # A marking point is named P followed by digits, e.g. P1, P12.
    # DECLARE Index : INTEGER
    if len(Word) < 2 or Word[0:1].upper() != "P":
        return False
    for Index in range(1, len(Word)):
        if IsDigit(Word[Index]) == False:
            return False
    return True


def JoinWords(Words, StartIndex):
    # Joins Words[StartIndex] to the last word with single spaces.
    # DECLARE Result : STRING
    # DECLARE Index : INTEGER
    Result = ""
    for Index in range(StartIndex, len(Words)):
        if Result == "":
            Result = Words[Index]
        else:
            Result = Result + " " + Words[Index]
    return Result


def FindQuestion(Questions, QuestionID):
    # Linear search for a question number. Returns its position or -1.
    # DECLARE Index : INTEGER
    for Index in range(0, len(Questions)):
        if Questions[Index].QuestionID == QuestionID:
            return Index
    return -1


def FindPoint(Question, PointID):
    # Linear search for a marking point in one question. Returns its position or -1.
    # DECLARE Index : INTEGER
    for Index in range(0, len(Question.MarkingPoints)):
        if Question.MarkingPoints[Index].PointID == PointID:
            return Index
    return -1


def ParseMarkScheme(Lines):
    # Extracts one QuestionItem for each QUESTION line, with its marking points and rules.
    # Questions without marking points or marks are left out, with a warning.
    # DECLARE Questions, ValidQuestions : ARRAY OF QuestionItem
    # DECLARE Words : ARRAY OF STRING
    # DECLARE LineNumber, Marks, Index, PointTotal, PointIndex : INTEGER
    # DECLARE ThisLine, Label : STRING
    # DECLARE CurrentQuestion : QuestionItem    (None before the first QUESTION line)
    Questions = []
    CurrentQuestion = None
    for LineNumber in range(0, len(Lines)):
        ThisLine = Lines[LineNumber].strip()
        Words = ThisLine.split()
        if ThisLine == "" or ThisLine[0:1] == "#":
            pass                               # blank line or comment
        elif Words[0].upper() == "QUESTION":
            CurrentQuestion = None
            Label = ""
            Marks = -1
            if len(Words) >= 3:
                Label = NormaliseLabel(Words[1])
                Marks = ReadBracketNumber(Words[2])
            if Label == "" or Marks <= 0:
                print("Mark scheme line", LineNumber + 1, "ignored: write QUESTION <number> [<marks>]")
            elif FindQuestion(Questions, Label) != -1:
                print("Mark scheme line", LineNumber + 1, "ignored: question", Label, "appears twice")
            else:
                CurrentQuestion = SQRecords.QuestionItem()
                CurrentQuestion.QuestionID = Label
                CurrentQuestion.MarkingRules.MaxMark = Marks
                Questions.append(CurrentQuestion)
        elif CurrentQuestion is None:
            print("Mark scheme line", LineNumber + 1, "ignored: it comes before the first QUESTION line")
        elif Words[0].upper() == "RULE":
            if CurrentQuestion.MarkingRules.RuleNotes == "":
                CurrentQuestion.MarkingRules.RuleNotes = JoinWords(Words, 1)
            else:
                CurrentQuestion.MarkingRules.RuleNotes = CurrentQuestion.MarkingRules.RuleNotes + "; " + JoinWords(Words, 1)
        elif IsPointID(Words[0]) == True and len(Words) >= 3 and ReadBracketNumber(Words[1]) > 0:
            if FindPoint(CurrentQuestion, Words[0].upper()) != -1:
                print("Mark scheme line", LineNumber + 1, "ignored: point", Words[0], "appears twice")
            else:
                NewPoint = SQRecords.MarkingPoint()
                NewPoint.PointID = Words[0].upper()
                NewPoint.Marks = ReadBracketNumber(Words[1])
                NewPoint.Requirement = JoinWords(Words, 2)
                CurrentQuestion.MarkingPoints.append(NewPoint)
        elif len(CurrentQuestion.MarkingPoints) > 0:
            # a long marking point continued on the next line
            PointIndex = len(CurrentQuestion.MarkingPoints) - 1
            CurrentQuestion.MarkingPoints[PointIndex].Requirement = CurrentQuestion.MarkingPoints[PointIndex].Requirement + " " + ThisLine
        else:
            print("Mark scheme line", LineNumber + 1, "ignored: it is not a marking point")

    # keep only questions that can be marked
    ValidQuestions = []
    for Index in range(0, len(Questions)):
        if len(Questions[Index].MarkingPoints) == 0:
            print("Question", Questions[Index].QuestionID, "has no marking points and will not be marked.")
        else:
            PointTotal = 0
            for PointIndex in range(0, len(Questions[Index].MarkingPoints)):
                PointTotal = PointTotal + Questions[Index].MarkingPoints[PointIndex].Marks
            if PointTotal < Questions[Index].MarkingRules.MaxMark:
                print("Warning: the marking points of question", Questions[Index].QuestionID,
                      "add up to", PointTotal, "but the question is worth", Questions[Index].MarkingRules.MaxMark)
            ValidQuestions.append(Questions[Index])
    return ValidQuestions


def FindAnswerRow(AnswerTable, Label):
    # Linear search of the answer table (rows of [Label, AnswerText]). Returns the row or -1.
    # DECLARE Row : INTEGER
    for Row in range(0, len(AnswerTable)):
        if AnswerTable[Row][0] == Label:
            return Row
    return -1


def ParseAnswers(Lines, Questions):
    # Splits the answer lines into a table with one row [Label, AnswerText] per question.
    # A line starts a new answer when its first word is a question number that is in the
    # mark scheme, or is clearly written as a question number (with brackets or a Q).
    # Other lines continue the answer above. Answers to the same question are joined.
    # DECLARE AnswerTable : ARRAY OF ARRAY[0:1] OF STRING
    # DECLARE Words : ARRAY OF STRING
    # DECLARE ThisLine, Label, FirstWord, Rest : STRING
    # DECLARE LineNumber, CurrentRow : INTEGER
    # DECLARE IgnoredText : BOOLEAN
    AnswerTable = []
    CurrentRow = -1
    IgnoredText = False
    for LineNumber in range(0, len(Lines)):
        ThisLine = Lines[LineNumber].strip()
        Words = ThisLine.split()
        Label = ""
        if len(Words) > 0:
            FirstWord = Words[0]
            Label = NormaliseLabel(FirstWord)
            if Label != "" and FindQuestion(Questions, Label) == -1:
                if ContainsChar(FirstWord, "(") == False and FirstWord[0:1].upper() != "Q":
                    Label = ""                 # a plain number such as "2" may be part of an answer
        if Label != "":
            Rest = JoinWords(Words, 1)
            CurrentRow = FindAnswerRow(AnswerTable, Label)
            if CurrentRow == -1:
                AnswerTable.append([Label, Rest])
                CurrentRow = len(AnswerTable) - 1
            elif Rest != "":
                AnswerTable[CurrentRow][1] = AnswerTable[CurrentRow][1] + "\n" + Rest
        elif ThisLine != "":
            if CurrentRow == -1:
                IgnoredText = True             # text before the first question number
            elif AnswerTable[CurrentRow][1] == "":
                AnswerTable[CurrentRow][1] = ThisLine
            else:
                AnswerTable[CurrentRow][1] = AnswerTable[CurrentRow][1] + "\n" + ThisLine
    if IgnoredText == True:
        print("Text before the first question number was ignored (e.g. a name or heading).")
    return AnswerTable


def MatchAnswers(Questions, AnswerTable, ImageFiles, UncertainMatches):
    # Copies each answer into its QuestionItem. The lists Questions and UncertainMatches
    # are changed by this procedure (Python passes the list itself, not a copy).
    # DECLARE Index, Row : INTEGER
    # DECLARE ImageList : STRING
    ImageList = ""
    for Index in range(0, len(ImageFiles)):
        if ImageList == "":
            ImageList = ImageFiles[Index]
        else:
            ImageList = ImageList + "; " + ImageFiles[Index]

    for Index in range(0, len(Questions)):
        Row = FindAnswerRow(AnswerTable, Questions[Index].QuestionID)
        if Row != -1:
            Questions[Index].AnswerText = AnswerTable[Row][1]
        else:
            Questions[Index].AnswerText = ""
            UncertainMatches.append(Questions[Index].QuestionID)
            if ImageList != "":
                Questions[Index].SourceImageRef = ImageList
                print("Question " + Questions[Index].QuestionID + ": no typed answer found - it may be in an uploaded image.")
            else:
                print("Question " + Questions[Index].QuestionID + ": no answer found in the answer files.")

    for Row in range(0, len(AnswerTable)):
        if FindQuestion(Questions, AnswerTable[Row][0]) == -1:
            UncertainMatches.append(AnswerTable[Row][0])
            print("The answer labelled", AnswerTable[Row][0], "does not match any question in the mark scheme.")


def DisplayProcessedPaper(Processed):
    # Outputs one line per question: marks, number of marking points and match status.
    # DECLARE Index : INTEGER
    # DECLARE Status : STRING
    print()
    print("Question    Marks  Points  Answer")
    for Index in range(0, len(Processed.Questions)):
        if IsInList(Processed.Questions[Index].QuestionID, Processed.UncertainMatches) == True:
            Status = "UNCERTAIN - will be flagged for review"
        else:
            Status = "found"
        print(Processed.Questions[Index].QuestionID.ljust(12) + str(Processed.Questions[Index].MarkingRules.MaxMark).ljust(7)
              + str(len(Processed.Questions[Index].MarkingPoints)).ljust(8) + Status)
    print("Questions:", len(Processed.Questions), "  Uncertain matches:", len(Processed.UncertainMatches))


def ProcessDocuments(Documents):
    # Document Processing Module: returns one ProcessedPaper record.
    # DECLARE Processed : ProcessedPaper
    # DECLARE AnswerLines, FileLines, ImageFiles : ARRAY OF STRING
    # DECLARE AnswerTable : ARRAY OF ARRAY[0:1] OF STRING
    # DECLARE Index, LineIndex : INTEGER
    # DECLARE FileName, Extension : STRING
    Processed = SQRecords.ProcessedPaper()
    Processed.Paper = Documents.Paper
    print()
    print("=== Document Processing ===")
    Processed.Questions = ParseMarkScheme(ReadDocumentLines(Documents.MarkSchemeFile))
    if len(Processed.Questions) == 0:
        print("No questions were found in the mark scheme.")
        return Processed
    print("Mark scheme read:", len(Processed.Questions), "questions.")

    AnswerLines = []
    ImageFiles = []
    for Index in range(0, len(Documents.AnswerFiles)):
        FileName = Documents.AnswerFiles[Index]
        Extension = GetExtension(FileName)
        if IsInList(Extension, ImageTypes) == True:
            ImageFiles.append(FileName)
        else:
            FileLines = ReadDocumentLines(FileName)
            if len(FileLines) == 0:
                print(os.path.basename(FileName), "has no readable text, so it is treated as an image.")
                ImageFiles.append(FileName)
            for LineIndex in range(0, len(FileLines)):
                AnswerLines.append(FileLines[LineIndex])

    AnswerTable = ParseAnswers(AnswerLines, Processed.Questions)
    MatchAnswers(Processed.Questions, AnswerTable, ImageFiles, Processed.UncertainMatches)
    DisplayProcessedPaper(Processed)
    return Processed


# main - runs this module on its own with the sample files
if __name__ == "__main__":
    TestDocuments = SQRecords.DocumentSet()
    TestDocuments.Paper.Level = "AS Level"
    TestDocuments.Paper.Subject = "Chemistry (9701)"
    TestDocuments.Paper.PaperCode = "9701/22/M/J/23"
    TestDocuments.Paper.Session = "May/June 2023"
    SampleFolder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SampleData")
    TestDocuments.MarkSchemeFile = os.path.join(SampleFolder, "Sample_Chemistry_MS.txt")
    TestDocuments.AnswerFiles = [os.path.join(SampleFolder, "Sample_Chemistry_Answers.txt"),
                                 os.path.join(SampleFolder, "Sample_Answer_Q3.png")]
    TestDocuments.IsComplete = True
    TestProcessed = ProcessDocuments(TestDocuments)
