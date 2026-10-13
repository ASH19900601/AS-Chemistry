# DocumentProcessing.py
# AI SQ Grader - Document Processing Module                     (Kevin)
#
# Receives the DocumentSet and AISettings and returns one ProcessedPaper record.
# 1. Reads the mark scheme: a file in the SQ text format is read directly; a Cambridge
#    mark scheme PDF is read by the AI service, turned into the SQ text format and saved
#    so that it can be checked and corrected.
# 2. Reads the question text of each question from the question paper (optional, AI).
# 3. Reads the student's answers: typed text and PDF text directly; photos and scanned
#    pages of handwriting are transcribed by an AI service that accepts images.
# 4. Lists every uncertain match (no answer found, handwriting read with low confidence,
#    answer in an image that could not be read, or an answer whose question number is not
#    in the mark scheme) so that it is flagged for review instead of being marked.
#
# SQ text format for mark schemes (see SampleData/Sample_Chemistry_MS.txt):
#     QUESTION 1(a) [2]
#     P1 [1] protons and neutrons are in the nucleus
#     RULE P2 DEPENDS ON P1
# Typed answers: each answer starts with its question number, e.g.  1(a) The nucleus ...
#
# Integration: AI requests are sent through AIConnection.py (written by Fox).
# Acknowledgement: the record types in SQRecords.py were agreed by the whole group.

import os                  # os.path finds file names and extensions; os.makedirs creates a folder

import AIConnection        # Fox's module: sends every AI request and checks the reply
import SQRecords           # record types agreed by the whole group

try:
    import pymupdf         # optional: reads PDF text and turns scanned pages into pictures (pip install pymupdf)
    PyMuPDFAvailable = True
except ImportError:
    PyMuPDFAvailable = False
try:
    import pypdf           # optional: reads the text of PDF files (pip install pypdf)
    PypdfAvailable = True
except ImportError:
    PypdfAvailable = False

# CONSTANT
TextTypes = [".txt"]
PdfTypes = [".pdf"]
ImageTypes = [".png", ".jpg", ".jpeg", ".webp"]
MinimumPageText = 30                   # a PDF page with less text than this is treated as a picture
RenderResolution = 150                 # dots per inch when a PDF page is turned into a picture
MarkSchemePagesPerRequest = 3
QuestionPaperPagesPerRequest = 2
ConfidenceLevels = ["low", "medium", "high"]
ProgramFolder = os.path.dirname(os.path.abspath(__file__))
ParsedFolder = os.path.join(ProgramFolder, "ParsedMarkSchemes")


# ===================================================================== small tools

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


def ContainsText(Text, Search):
    # TRUE if Search appears anywhere in Text.
    # DECLARE Position : INTEGER
    for Position in range(0, len(Text) - len(Search) + 1):
        if Text[Position:Position + len(Search)] == Search:     # MID(Text, Position + 1, LENGTH(Search))
            return True
    return False


def IsDigit(ThisChar):
    return ThisChar >= "0" and ThisChar <= "9"


def IsLetter(ThisChar):
    return (ThisChar >= "a" and ThisChar <= "z") or (ThisChar >= "A" and ThisChar <= "Z")


def ToInteger(Value, DefaultValue):
    # INT() of a value from the AI reply; DefaultValue if it is not a whole number.
    try:
        return int(Value)
    except (ValueError, TypeError):
        return DefaultValue


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


def OneLine(Text):
    # Replaces line breaks with spaces so the text fits on one line of the SQ format.
    # DECLARE Result : STRING
    # DECLARE Index : INTEGER
    Result = ""
    for Index in range(0, len(Text)):
        if Text[Index] == "\n" or Text[Index] == "\r":
            Result = Result + " "
        else:
            Result = Result + Text[Index]
    return Result.strip()


# ===================================================================== reading files

def ReadTextFile(FileName):
    # FUNCTION ReadTextFile(FileName : STRING) RETURNS ARRAY OF STRING
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


def ReadPdfPages(FileName):
    # Reads the text of each page of a PDF file. Returns one string per page ("" for a
    # page that is only a picture).
    # DECLARE Pages : ARRAY OF STRING
    # DECLARE PageNumber : INTEGER
    Pages = []
    if PyMuPDFAvailable == True:
        try:
            Document = pymupdf.open(FileName)
            for PageNumber in range(0, Document.page_count):
                Pages.append(Document[PageNumber].get_text())
            Document.close()
        except (RuntimeError, ValueError, OSError):
            print("Could not read the PDF file", os.path.basename(FileName))
        return Pages
    if PypdfAvailable == True:
        try:
            Reader = pypdf.PdfReader(FileName)
            for PageNumber in range(0, len(Reader.pages)):
                Pages.append(Reader.pages[PageNumber].extract_text())
        except (IOError, ValueError, pypdf.errors.PyPdfError):
            print("Could not read the PDF file", os.path.basename(FileName))
        return Pages
    print("PDF files cannot be read because neither pymupdf nor pypdf is installed (pip install pymupdf).")
    return Pages


def CountPdfPictures(FileName, PageNumber):
    # Number of pictures on one page (page numbers start at 1). Needs PyMuPDF; returns 0
    # without it.
    # DECLARE Count : INTEGER
    if PyMuPDFAvailable == False:
        return 0
    try:
        Document = pymupdf.open(FileName)
        Count = len(Document[PageNumber - 1].get_images())
        Document.close()
    except (RuntimeError, ValueError, OSError, IndexError):
        Count = 0
    return Count


def RenderPdfPage(FileName, PageNumber):
    # Turns one PDF page into a PNG picture and returns it as an image data URL, or "" if
    # that is not possible (PyMuPDF is needed).
    # DECLARE ImageBytes : BYTES
    if PyMuPDFAvailable == False:
        print("A scanned PDF page can only be read with pymupdf installed (pip install pymupdf).")
        return ""
    try:
        Document = pymupdf.open(FileName)
        ImageBytes = Document[PageNumber - 1].get_pixmap(dpi=RenderResolution).tobytes("png")
        Document.close()
    except (RuntimeError, ValueError, OSError, IndexError):
        print("Could not turn page", PageNumber, "of", os.path.basename(FileName), "into a picture.")
        return ""
    return AIConnection.BytesToImageURL(ImageBytes, "image/png")


def MakeSourceRef(FileName, PageNumber):
    # A reference to a whole file, or to one PDF page: "Answers.pdf#2"
    if PageNumber == 0:
        return FileName
    return FileName + "#" + str(PageNumber)


def SplitSourceRef(SourceRef):
    # "Answers.pdf#2" -> ["Answers.pdf", "2"];  "Page1.jpg" -> ["Page1.jpg", "0"]
    # DECLARE Position : INTEGER
    # move back over the digits at the end; a page reference has "#" just before them
    Position = len(SourceRef) - 1
    while Position >= 0 and IsDigit(SourceRef[Position]) == True:
        Position = Position - 1
    if Position >= 0 and Position < len(SourceRef) - 1 and SourceRef[Position] == "#":
        return [SourceRef[0:Position], SourceRef[Position + 1:]]
    return [SourceRef, "0"]


def LoadSourceImages(SourceImageRef):
    # FUNCTION LoadSourceImages(SourceImageRef : STRING) RETURNS ARRAY OF STRING
    # Turns a list of references separated by "; " into image data URLs for the AI.
    # Text files are skipped.
    # DECLARE ImageURLs, Parts, FileAndPage : ARRAY OF STRING
    # DECLARE Index : INTEGER
    # DECLARE ImageURL : STRING
    ImageURLs = []
    if SourceImageRef.strip() == "":
        return ImageURLs
    Parts = SourceImageRef.split("; ")
    for Index in range(0, len(Parts)):
        FileAndPage = SplitSourceRef(Parts[Index].strip())
        ImageURL = ""
        if FileAndPage[1] != "0":
            ImageURL = RenderPdfPage(FileAndPage[0], int(FileAndPage[1]))
        elif IsInList(GetExtension(FileAndPage[0]), ImageTypes) == True:
            ImageURL = AIConnection.MakeImageURL(FileAndPage[0])
        if ImageURL != "":
            ImageURLs.append(ImageURL)
    return ImageURLs


def ReadDocumentParts(FileName):
    # FUNCTION ReadDocumentParts(FileName : STRING) RETURNS ARRAY OF ARRAY[0:2] OF STRING
    # Splits a document into parts. Each part is a row [SourceRef, Text, Kind]: Kind is
    # "text" for typed text, or "image" for a photo or a PDF page that is a picture
    # (a scan, or a page with handwriting pasted in).
    # DECLARE Parts : ARRAY OF ARRAY[0:2] OF STRING
    # DECLARE Pages : ARRAY OF STRING
    # DECLARE Extension, Kind, AllText : STRING
    # DECLARE Index, PageNumber : INTEGER
    Parts = []
    Extension = GetExtension(FileName)
    if IsInList(Extension, TextTypes) == True:
        AllText = ""
        Pages = ReadTextFile(FileName)
        for Index in range(0, len(Pages)):
            AllText = AllText + Pages[Index] + "\n"
        Parts.append([FileName, AllText, "text"])
    elif IsInList(Extension, ImageTypes) == True:
        Parts.append([FileName, "", "image"])
    elif IsInList(Extension, PdfTypes) == True:
        Pages = ReadPdfPages(FileName)
        for Index in range(0, len(Pages)):
            PageNumber = Index + 1
            # little text (a scan) or a picture on the page (e.g. handwriting pasted in): the AI must see it
            if len(Pages[Index].strip()) < MinimumPageText or CountPdfPictures(FileName, PageNumber) > 0:
                Kind = "image"
            else:
                Kind = "text"
            Parts.append([MakeSourceRef(FileName, PageNumber), Pages[Index], Kind])
    return Parts


def ReadDocumentLines(FileName):
    # All the typed text of a document, as lines.
    # DECLARE Parts : ARRAY OF ARRAY[0:2] OF STRING
    # DECLARE Lines, PartLines : ARRAY OF STRING
    # DECLARE Index, LineIndex : INTEGER
    Parts = ReadDocumentParts(FileName)
    Lines = []
    for Index in range(0, len(Parts)):
        PartLines = Parts[Index][1].split("\n")
        for LineIndex in range(0, len(PartLines)):
            Lines.append(PartLines[LineIndex].rstrip("\r"))
    return Lines


# ===================================================================== question numbers

def NormaliseLabel(Text):
    # Turns a question number into the standard form used by the mark scheme:
    # "1(a)(ii)" -> "1(a)(ii)", "Q2b" -> "2(b)", "3." -> "3", "1(A):" -> "1(a)", "1 (a)" -> "1(a)".
    # Returns "" if the text is not a question number.
    # DECLARE Result, Group, Squeezed : STRING
    # DECLARE Position, Index : INTEGER
    # DECLARE ThisChar : CHAR
    Squeezed = ""
    for Index in range(0, len(Text)):
        if Text[Index] != " ":
            Squeezed = Squeezed + Text[Index]
    Text = Squeezed.lower()
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


def IsLabelPrefix(Prefix, Label):
    # TRUE if Label is Prefix or one of its parts: "1" is a prefix of "1(a)(ii)".
    if Label[0:len(Prefix)] != Prefix:
        return False
    return len(Label) == len(Prefix) or Label[len(Prefix):len(Prefix) + 1] == "("


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


def QuestionList(Questions):
    # "1(a), 1(b), 2" - the question numbers, for the AI prompts
    # DECLARE Result : STRING
    # DECLARE Index : INTEGER
    Result = ""
    for Index in range(0, len(Questions)):
        if Index > 0:
            Result = Result + ", "
        Result = Result + Questions[Index].QuestionID
    return Result


# ===================================================================== mark scheme in SQ text format

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


def IsSQFormat(Lines):
    # TRUE if at least one line is a QUESTION line of the SQ text format.
    # DECLARE Words : ARRAY OF STRING
    # DECLARE Index : INTEGER
    for Index in range(0, len(Lines)):
        Words = Lines[Index].split()
        if len(Words) >= 3:
            if Words[0].upper() == "QUESTION" and ReadBracketNumber(Words[2]) > 0:
                return True
    return False


def ParseMarkScheme(Lines):
    # FUNCTION ParseMarkScheme(Lines : ARRAY OF STRING) RETURNS ARRAY OF QuestionItem
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
            # reset first, so lines after an invalid QUESTION line cannot join the previous question
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


def QuestionsToSQLines(Questions, SourceName):
    # Writes questions in the SQ text format, so they can be checked, edited and reused.
    # DECLARE Lines : ARRAY OF STRING
    # DECLARE Index, PointIndex : INTEGER
    # DECLARE Rules : ARRAY OF STRING
    Lines = ["# Mark scheme read by the AI service from " + SourceName,
             "# Check it against the original mark scheme. You can correct it and upload this file",
             "# as the mark scheme next time (format: QUESTION <number> [<marks>], <point> [<marks>] <requirement>).", ""]
    for Index in range(0, len(Questions)):
        Lines.append("QUESTION " + Questions[Index].QuestionID + " [" + str(Questions[Index].MarkingRules.MaxMark) + "]")
        for PointIndex in range(0, len(Questions[Index].MarkingPoints)):
            Lines.append(Questions[Index].MarkingPoints[PointIndex].PointID + " [" + str(Questions[Index].MarkingPoints[PointIndex].Marks)
                         + "] " + OneLine(Questions[Index].MarkingPoints[PointIndex].Requirement))
        if Questions[Index].MarkingRules.RuleNotes != "":
            Rules = Questions[Index].MarkingRules.RuleNotes.split(";")
            for PointIndex in range(0, len(Rules)):
                if Rules[PointIndex].strip() != "":
                    Lines.append("RULE " + Rules[PointIndex].strip())
        Lines.append("")
    return Lines


def SaveLines(Lines, FileName):
    # Writes lines to a text file. Returns TRUE if it worked.
    # DECLARE Index : INTEGER
    try:
        if os.path.isdir(os.path.dirname(FileName)) == False:
            os.makedirs(os.path.dirname(FileName))
        File = open(FileName, "w", encoding="utf-8")
        for Index in range(0, len(Lines)):
            File.write(Lines[Index] + "\n")
        File.close()
    except (IOError, OSError):
        return False
    return True


# ===================================================================== mark scheme read by the AI

def IsCoverOrRulesPage(PageText):
    # Cambridge mark schemes start with a cover page and pages of general marking principles,
    # which contain no marking points.
    # DECLARE Upper : STRING
    Upper = PageText.upper()
    if ContainsText(Upper, "GENERIC MARKING PRINCIPLE") == True:
        return True
    if ContainsText(Upper, "SPECIFIC MARKING PRINCIPLES") == True and ContainsText(Upper, "QUESTION") == False:
        return True
    return ContainsText(Upper, "MAXIMUM MARK") == True and ContainsText(Upper, "PUBLISHED") == True


def BuildMarkSchemePrompt():
    # Instructions for turning mark scheme pages into marking points.
    # DECLARE PromptText : STRING
    PromptText = "You are reading pages of a Cambridge (CAIE) mark scheme. Extract every question part and its marking points.\n"
    PromptText = PromptText + "- Use the question numbers as printed, e.g. 1(a)(ii).\n"
    PromptText = PromptText + "- Give each separately creditworthy point its own marking point with its marks (usually 1).\n"
    PromptText = PromptText + '- Keep alternative answers in the same marking point, separated by " / ".\n'
    PromptText = PromptText + "- Keep ALLOW, IGNORE, DO NOT ALLOW and similar guidance in brackets inside the requirement.\n"
    PromptText = PromptText + '- If a mark can only be given when another is given (an A mark after an M mark, "dep", "ecf"), add a rule such as "P2 DEPENDS ON P1".\n'
    PromptText = PromptText + '- max_mark is the mark for the question part; for "max 2" or "any two from" use that maximum.\n'
    PromptText = PromptText + "- Ignore cover pages and general marking principles.\n"
    PromptText = PromptText + "Number the marking points of each question P1, P2, ... in order.\n"
    PromptText = PromptText + "Reply with JSON only, in this form:\n"
    PromptText = PromptText + '{"questions": [{"question": "1(a)", "max_mark": 2, "points": [{"id": "P1", "marks": 1, "requirement": "..."}], "rules": ["P2 DEPENDS ON P1"]}]}\n'
    PromptText = PromptText + 'If these pages contain no marking points, reply {"questions": []}.\n'
    return PromptText


def AddAIQuestions(Questions, Data):
    # PROCEDURE AddAIQuestions(BYREF Questions : ARRAY OF QuestionItem, Data : dictionary)
    # Adds the questions in one AI reply to the list Questions (the list is changed). A
    # question continued from an earlier page gets its new points numbered after the old
    # ones, and its rules are renumbered in the same way.
    # DECLARE Rows, PointRows, RuleRows, Words, OldIDs, NewIDs : ARRAY
    # DECLARE Row, PointIndex, RuleIndex, IDIndex, Offset, Index, Total : INTEGER
    # DECLARE Label, Requirement, FirstID, SecondID : STRING
    # DECLARE Question : QuestionItem
    Rows = AIConnection.GetJsonList(Data, "questions")
    for Row in range(0, len(Rows)):
        if type(Rows[Row]) == dict:
            Label = NormaliseLabel(str(Rows[Row].get("question", "")))
            if Label != "":
                Index = FindQuestion(Questions, Label)
                if Index == -1:
                    Question = SQRecords.QuestionItem()
                    Question.QuestionID = Label
                    Questions.append(Question)
                else:
                    Question = Questions[Index]
                if ToInteger(Rows[Row].get("max_mark"), 0) > Question.MarkingRules.MaxMark:
                    Question.MarkingRules.MaxMark = ToInteger(Rows[Row].get("max_mark"), 0)
                Offset = len(Question.MarkingPoints)    # more than 0 if the question continues from earlier pages
                # parallel arrays: OldIDs[i] is the AI's ID for a point and NewIDs[i] the ID given here,
                # so that the rules can be renumbered in the same way
                OldIDs = []
                NewIDs = []
                PointRows = AIConnection.GetJsonList(Rows[Row], "points")
                for PointIndex in range(0, len(PointRows)):
                    if type(PointRows[PointIndex]) == dict:
                        Requirement = OneLine(str(PointRows[PointIndex].get("requirement", "")))
                        if Requirement != "":
                            NewPoint = SQRecords.MarkingPoint()
                            NewPoint.PointID = "P" + str(len(Question.MarkingPoints) + 1)
                            NewPoint.Marks = ToInteger(PointRows[PointIndex].get("marks"), 1)
                            if NewPoint.Marks < 1:
                                NewPoint.Marks = 1
                            NewPoint.Requirement = Requirement
                            Question.MarkingPoints.append(NewPoint)
                            OldIDs.append(str(PointRows[PointIndex].get("id", "P" + str(PointIndex + 1))).strip().upper())
                            NewIDs.append(NewPoint.PointID)
                RuleRows = AIConnection.GetJsonList(Rows[Row], "rules")
                for RuleIndex in range(0, len(RuleRows)):
                    Words = str(RuleRows[RuleIndex]).upper().split()
                    if len(Words) == 4 and Words[1] == "DEPENDS" and Words[2] == "ON":
                        FirstID = ""
                        SecondID = ""
                        for IDIndex in range(0, len(OldIDs)):
                            if OldIDs[IDIndex] == Words[0]:
                                FirstID = NewIDs[IDIndex]
                            if OldIDs[IDIndex] == Words[3]:
                                SecondID = NewIDs[IDIndex]
                        if FirstID != "" and SecondID != "":
                            if Question.MarkingRules.RuleNotes != "":
                                Question.MarkingRules.RuleNotes = Question.MarkingRules.RuleNotes + "; "
                            Question.MarkingRules.RuleNotes = Question.MarkingRules.RuleNotes + FirstID + " DEPENDS ON " + SecondID
                # no max_mark in the reply for a new question: use the total of its points
                if Question.MarkingRules.MaxMark == 0 and Offset == 0:
                    Total = 0
                    for PointIndex in range(0, len(Question.MarkingPoints)):
                        Total = Total + Question.MarkingPoints[PointIndex].Marks
                    Question.MarkingRules.MaxMark = Total


def ConvertMarkSchemeWithAI(FileName, Settings):
    # FUNCTION ConvertMarkSchemeWithAI(FileName : STRING, Settings : AISettings) RETURNS ARRAY OF QuestionItem
    # Sends the mark scheme to the AI a few pages at a time and collects the questions.
    # Returns ARRAY OF QuestionItem, or [] if any part could not be read (an incomplete
    # mark scheme would give a wrong total, so nothing is marked).
    # DECLARE Questions : ARRAY OF QuestionItem
    # DECLARE Parts : ARRAY OF ARRAY[0:2] OF STRING
    # DECLARE ImageURLs : ARRAY OF STRING
    # DECLARE Index, PartsInRequest : INTEGER
    # DECLARE PromptText, ImageURL : STRING
    # DECLARE Response : AIResponse
    # DECLARE Data : dictionary
    Questions = []
    Parts = ReadDocumentParts(FileName)
    Index = 0
    while Index < len(Parts):
        PromptText = BuildMarkSchemePrompt() + "MARK SCHEME PAGES:\n"
        ImageURLs = []
        PartsInRequest = 0
        # one request holds up to MarkSchemePagesPerRequest pages: text in the prompt, pictures as images
        while Index < len(Parts) and PartsInRequest < MarkSchemePagesPerRequest:
            if Parts[Index][2] == "text" and IsCoverOrRulesPage(Parts[Index][1]) == True:
                print("  Skipped", os.path.basename(Parts[Index][0]), "(cover or general marking principles)")
            elif Parts[Index][2] == "text":
                PromptText = PromptText + "[" + os.path.basename(Parts[Index][0]) + "]\n" + Parts[Index][1] + "\n"
                PartsInRequest = PartsInRequest + 1
            else:
                ImageURL = LoadSourceImages(Parts[Index][0])
                if len(ImageURL) == 0:
                    print("Could not read", os.path.basename(Parts[Index][0]), "of the mark scheme, so marking has stopped.")
                    return []
                ImageURLs.append(ImageURL[0])
                PartsInRequest = PartsInRequest + 1
            Index = Index + 1
        if PartsInRequest > 0:
            Response = AIConnection.SendChatRequest(PromptText, ImageURLs, Settings)
            Data = AIConnection.ReadJsonReply(Response)
            if Data is None:
                print("The AI could not read part of the mark scheme:", Response.ErrorMessage)
                print("Marking has stopped so that no incomplete mark scheme is used.")
                return []
            AddAIQuestions(Questions, Data)
            print("  Mark scheme read up to", os.path.basename(Parts[Index - 1][0]), "-", len(Questions), "questions so far")
    return Questions


def ReadMarkScheme(FileName, Settings):
    # FUNCTION ReadMarkScheme(FileName : STRING, Settings : AISettings) RETURNS ARRAY OF QuestionItem
    # Returns the questions of the mark scheme. The SQ text format is read directly;
    # anything else is read by the AI and saved in the SQ text format for checking.
    # DECLARE Lines : ARRAY OF STRING
    # DECLARE Questions : ARRAY OF QuestionItem
    # DECLARE SavedName : STRING
    Lines = ReadDocumentLines(FileName)
    if IsSQFormat(Lines) == True:
        return ParseMarkScheme(Lines)
    if AIConnection.IsOnline(Settings) == False:
        print("This mark scheme is not in the SQ text format. Choose an AI service (main menu) to read a")
        print("Cambridge mark scheme PDF, or type the marking points in the SQ text format (see the README).")
        return []
    print("Reading the mark scheme with the AI service. This can take a minute ...")
    Questions = ConvertMarkSchemeWithAI(FileName, Settings)
    if len(Questions) == 0:
        return []
    Lines = QuestionsToSQLines(Questions, os.path.basename(FileName))
    SavedName = os.path.join(ParsedFolder, os.path.splitext(os.path.basename(FileName))[0] + "_SQ.txt")
    if SaveLines(Lines, SavedName) == True:
        print("The marking points read by the AI were saved as", SavedName)
        print("Check them against the original. You can correct the file and upload it as the mark scheme.")
    return ParseMarkScheme(Lines)          # the same checks as a typed mark scheme


# ===================================================================== question paper

def IsQuestionPaperCover(PageText):
    # The cover and blank pages of a Cambridge question paper contain no questions.
    # DECLARE Upper : STRING
    Upper = PageText.upper()
    if ContainsText(Upper, "BLANK PAGE") == True and len(PageText.strip()) < 200:
        return True
    return ContainsText(Upper, "INSTRUCTIONS") == True and ContainsText(Upper, "INFORMATION") == True


def ReadQuestionTexts(FileName, Questions, Settings):
    # PROCEDURE ReadQuestionTexts(FileName : STRING, BYREF Questions : ARRAY OF QuestionItem,
    #                           Settings : AISettings)
    # Reads the text of each question from the question paper and stores it in
    # QuestionItem.QuestionText (the list of questions is changed). Optional: marking
    # continues without it.
    # DECLARE Parts : ARRAY OF ARRAY[0:2] OF STRING
    # DECLARE Table : ARRAY OF ARRAY[0:1] OF STRING   [question number, text]
    # DECLARE ImageURLs, ImageURL : ARRAY OF STRING
    # DECLARE Rows : ARRAY      (the questions in one AI reply)
    # DECLARE Index, PartsInRequest, Row, QuestionIndex, Found : INTEGER
    # DECLARE PromptText, Label : STRING
    if FileName == "":
        return
    if AIConnection.IsOnline(Settings) == False:
        print("The question paper is only used with an AI service; marking continues without it.")
        return
    print("Reading the question paper ...")
    Parts = ReadDocumentParts(FileName)
    Table = []
    Index = 0
    while Index < len(Parts):
        PromptText = "These are pages of a Cambridge (CAIE) question paper. For each question part on these pages, copy the question text,\n"
        PromptText = PromptText + "including the stem it shares with other parts and any data. Describe diagrams, graphs and tables briefly in square brackets.\n"
        PromptText = PromptText + "The question numbers in the mark scheme are: " + QuestionList(Questions) + "\n"
        PromptText = PromptText + 'Reply with JSON only: {"questions": [{"question": "1(a)", "text": "..."}]}\n'
        PromptText = PromptText + "QUESTION PAPER PAGES:\n"
        ImageURLs = []
        PartsInRequest = 0
        while Index < len(Parts) and PartsInRequest < QuestionPaperPagesPerRequest:
            if Parts[Index][2] == "text" and IsQuestionPaperCover(Parts[Index][1]) == True:
                pass                           # cover or blank page
            elif Parts[Index][2] == "text":
                PromptText = PromptText + Parts[Index][1] + "\n"
                PartsInRequest = PartsInRequest + 1
            else:
                ImageURL = LoadSourceImages(Parts[Index][0])
                if len(ImageURL) > 0:
                    ImageURLs.append(ImageURL[0])
                    PartsInRequest = PartsInRequest + 1
            Index = Index + 1
        if PartsInRequest > 0:
            Data = AIConnection.ReadJsonReply(AIConnection.SendChatRequest(PromptText, ImageURLs, Settings))
            if Data is None:
                print("Part of the question paper could not be read; marking continues without it.")
            else:
                Rows = AIConnection.GetJsonList(Data, "questions")
                for Row in range(0, len(Rows)):
                    if type(Rows[Row]) == dict:
                        Label = NormaliseLabel(str(Rows[Row].get("question", "")))
                        if Label != "" and str(Rows[Row].get("text", "")).strip() != "":
                            Table.append([Label, str(Rows[Row].get("text", "")).strip()])

    # a question gets its own text and the text of the question it belongs to ("1" for "1(a)")
    Found = 0
    for QuestionIndex in range(0, len(Questions)):
        for Row in range(0, len(Table)):
            if IsLabelPrefix(Table[Row][0], Questions[QuestionIndex].QuestionID) == True:
                if Questions[QuestionIndex].QuestionText == "":
                    Questions[QuestionIndex].QuestionText = Table[Row][1]
                else:
                    Questions[QuestionIndex].QuestionText = Questions[QuestionIndex].QuestionText + "\n" + Table[Row][1]
        if Questions[QuestionIndex].QuestionText != "":
            Found = Found + 1
    print("Question text found for", Found, "of", len(Questions), "questions.")


# ===================================================================== student answers

def FindAnswerRow(AnswerTable, Label):
    # Linear search of the answer table (rows of [Label, AnswerText, SourceRef, Confidence]).
    # Returns the row or -1.
    # DECLARE Row : INTEGER
    for Row in range(0, len(AnswerTable)):
        if AnswerTable[Row][0] == Label:
            return Row
    return -1


def LowerConfidence(First, Second):
    # The lower of two confidence levels ("low" < "medium" < "high").
    # DECLARE Index : INTEGER
    # ConfidenceLevels is ordered from low to high, so the first level found is the lower one
    for Index in range(0, len(ConfidenceLevels)):
        if ConfidenceLevels[Index] == First or ConfidenceLevels[Index] == Second:
            return ConfidenceLevels[Index]
    return "low"


def AddAnswerRow(AnswerTable, Label, AnswerText, SourceRef, Confidence):
    # PROCEDURE AddAnswerRow(BYREF AnswerTable : ARRAY OF ARRAY[0:3] OF STRING,
    #                        Label, AnswerText, SourceRef, Confidence : STRING)
    # Adds an answer to the table, or joins it to an earlier answer to the same question
    # (an answer can continue on another page). The table is changed.
    # DECLARE Row : INTEGER
    Row = FindAnswerRow(AnswerTable, Label)
    if Row == -1:
        AnswerTable.append([Label, AnswerText, SourceRef, Confidence])
        return
    if AnswerText != "":
        if AnswerTable[Row][1] == "":
            AnswerTable[Row][1] = AnswerText
        else:
            AnswerTable[Row][1] = AnswerTable[Row][1] + "\n" + AnswerText
    if SourceRef != "" and AnswerTable[Row][2] == "":
        AnswerTable[Row][2] = SourceRef
    elif SourceRef != "" and AnswerTable[Row][2] != SourceRef:
        AnswerTable[Row][2] = AnswerTable[Row][2] + "; " + SourceRef
    AnswerTable[Row][3] = LowerConfidence(AnswerTable[Row][3], Confidence)


def ParseAnswers(Lines, Questions):
    # FUNCTION ParseAnswers(Lines : ARRAY OF STRING, Questions : ARRAY OF QuestionItem)
    #          RETURNS ARRAY OF ARRAY[0:3] OF STRING
    # Splits typed answer lines into a table with one row [Label, AnswerText, "", "high"]
    # per question. A line starts a new answer when its first word is a question number
    # that is in the mark scheme, or is clearly written as a question number (with
    # brackets or a Q). Other lines continue the answer above.
    # DECLARE AnswerTable : ARRAY OF ARRAY[0:3] OF STRING
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
                AnswerTable.append([Label, Rest, "", "high"])
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


def BuildTranscriptionPrompt(Questions):
    # Instructions for reading a photo or scan of handwritten answers.
    # DECLARE PromptText : STRING
    PromptText = "This is a photo or scan of a student's answers to a Cambridge (CAIE) exam paper.\n"
    PromptText = PromptText + "Transcribe exactly what the student wrote for each question, including working, units, formulas and labels.\n"
    PromptText = PromptText + "Describe any diagram, graph or drawing briefly in square brackets.\n"
    PromptText = PromptText + "Do not correct the student's mistakes and do not answer the questions yourself.\n"
    PromptText = PromptText + "The question numbers in this paper are: " + QuestionList(Questions) + "\n"
    PromptText = PromptText + "Use these numbers. If the student did not write a number, decide from the content and give low confidence.\n"
    PromptText = PromptText + 'For each answer give confidence "high", "medium" or "low" for how sure you are of the reading and the question number.\n'
    PromptText = PromptText + 'Reply with JSON only: {"answers": [{"question": "1(a)", "answer": "...", "confidence": "high"}]}\n'
    PromptText = PromptText + 'If there are no answers on the page, reply {"answers": []}.\n'
    return PromptText


def TranscribeAnswerImage(ImageURL, SourceRef, Questions, Settings):
    # FUNCTION TranscribeAnswerImage(ImageURL, SourceRef : STRING, Questions : ARRAY OF QuestionItem,
    #                                Settings : AISettings) RETURNS ARRAY OF ARRAY[0:3] OF STRING
    # Asks the AI to read one photo or scanned page. Returns rows [Label, AnswerText,
    # SourceRef, Confidence]; a label "?" means the AI found no question number. If the
    # request fails, the only row is ["", "", SourceRef, "failed"].
    # DECLARE Rows : ARRAY OF ARRAY[0:3] OF STRING
    # DECLARE ReplyRows : ARRAY
    # DECLARE Response : AIResponse
    # DECLARE Data : dictionary
    # DECLARE Index : INTEGER
    # DECLARE Label, Confidence : STRING
    Rows = []
    Response = AIConnection.SendChatRequest(BuildTranscriptionPrompt(Questions), [ImageURL], Settings)
    Data = AIConnection.ReadJsonReply(Response)
    if Data is None:
        print("Could not read", os.path.basename(SourceRef) + ":", Response.ErrorMessage)
        Rows.append(["", "", SourceRef, "failed"])
        return Rows
    ReplyRows = AIConnection.GetJsonList(Data, "answers")
    for Index in range(0, len(ReplyRows)):
        if type(ReplyRows[Index]) == dict:
            Label = NormaliseLabel(str(ReplyRows[Index].get("question", "")))
            if Label == "":
                Label = "?"
            Confidence = str(ReplyRows[Index].get("confidence", "low")).strip().lower()
            # an unknown confidence counts as low, so the answer is checked instead of marked
            if IsInList(Confidence, ConfidenceLevels) == False:
                Confidence = "low"
            Rows.append([Label, str(ReplyRows[Index].get("answer", "")).strip(), SourceRef, Confidence])
    return Rows


def MatchAnswers(Questions, AnswerTable, UnreadImages, UncertainMatches):
    # PROCEDURE MatchAnswers(BYREF Questions : ARRAY OF QuestionItem, AnswerTable : ARRAY OF ARRAY[0:3] OF STRING,
    #                        UnreadImages : ARRAY OF STRING, BYREF UncertainMatches : ARRAY OF STRING)
    # Copies each answer into its QuestionItem. The lists Questions and UncertainMatches
    # are changed by this procedure (Python passes the list itself, not a copy).
    # DECLARE Index, Row : INTEGER
    # DECLARE ImageList : STRING
    # the images that could not be read, joined into one SourceImageRef
    ImageList = ""
    for Index in range(0, len(UnreadImages)):
        if ImageList == "":
            ImageList = UnreadImages[Index]
        else:
            ImageList = ImageList + "; " + UnreadImages[Index]

    # a low-confidence reading or a missing answer is uncertain: the question is flagged, not marked
    for Index in range(0, len(Questions)):
        Row = FindAnswerRow(AnswerTable, Questions[Index].QuestionID)
        if Row != -1:
            Questions[Index].AnswerText = AnswerTable[Row][1]
            Questions[Index].SourceImageRef = AnswerTable[Row][2]
            if AnswerTable[Row][3] == "low":
                UncertainMatches.append(Questions[Index].QuestionID)
                print("Question " + Questions[Index].QuestionID + ": the handwriting or question number could not be read with confidence.")
        else:
            Questions[Index].AnswerText = ""
            UncertainMatches.append(Questions[Index].QuestionID)
            if ImageList != "":
                Questions[Index].SourceImageRef = ImageList
                print("Question " + Questions[Index].QuestionID + ": no typed answer found - it may be in an uploaded image that could not be read.")
            else:
                print("Question " + Questions[Index].QuestionID + ": no answer found in the answer files.")

    # answers whose question number is not in the mark scheme
    for Row in range(0, len(AnswerTable)):
        if FindQuestion(Questions, AnswerTable[Row][0]) == -1:
            UncertainMatches.append(AnswerTable[Row][0])
            if AnswerTable[Row][0] == "?":
                print("An answer in", os.path.basename(AnswerTable[Row][2]), "has no question number.")
            else:
                print("The answer labelled", AnswerTable[Row][0], "does not match any question in the mark scheme.")


def DisplayProcessedPaper(Processed):
    # PROCEDURE DisplayProcessedPaper(Processed : ProcessedPaper)
    # Outputs one line per question: marks, number of marking points and match status.
    # DECLARE Index : INTEGER
    # DECLARE Status : STRING
    print()
    print("Question    Marks  Points  Answer")
    for Index in range(0, len(Processed.Questions)):
        if IsInList(Processed.Questions[Index].QuestionID, Processed.UncertainMatches) == True:
            Status = "UNCERTAIN - will be flagged for review"
        elif Processed.Questions[Index].SourceImageRef != "":
            Status = "found (read from handwriting)"
        else:
            Status = "found"
        print(Processed.Questions[Index].QuestionID.ljust(12) + str(Processed.Questions[Index].MarkingRules.MaxMark).ljust(7)
              + str(len(Processed.Questions[Index].MarkingPoints)).ljust(8) + Status)
    print("Questions:", len(Processed.Questions), "  Uncertain matches:", len(Processed.UncertainMatches))


def ProcessDocuments(Documents, Settings):
    # FUNCTION ProcessDocuments(Documents : DocumentSet, Settings : AISettings) RETURNS ProcessedPaper
    # Document Processing Module: returns one ProcessedPaper record.
    # DECLARE Processed : ProcessedPaper
    # DECLARE Parts, Rows : ARRAY OF ARRAY OF STRING
    # DECLARE TextLines, PartLines, UnreadImages, ImageURL : ARRAY OF STRING
    # DECLARE AnswerTable, ImageAnswers : ARRAY OF ARRAY[0:3] OF STRING
    # DECLARE FileIndex, PartIndex, LineIndex, Row : INTEGER
    # DECLARE SourceRef : STRING
    Processed = SQRecords.ProcessedPaper()
    Processed.Paper = Documents.Paper
    print()
    print("=== Document Processing ===")
    # 1. the mark scheme, then the question text from the question paper (optional)
    Processed.Questions = ReadMarkScheme(Documents.MarkSchemeFile, Settings)
    if len(Processed.Questions) == 0:
        print("No questions were found in the mark scheme.")
        return Processed
    print("Mark scheme read:", len(Processed.Questions), "questions.")
    ReadQuestionTexts(Documents.QuestionPaperFile, Processed.Questions, Settings)

    # 2. answer files: typed text is collected; photos and scanned pages are read by the AI
    TextLines = []
    UnreadImages = []
    AnswerTable = []
    ImageAnswers = []
    for FileIndex in range(0, len(Documents.AnswerFiles)):
        Parts = ReadDocumentParts(Documents.AnswerFiles[FileIndex])
        for PartIndex in range(0, len(Parts)):
            SourceRef = Parts[PartIndex][0]
            if Parts[PartIndex][2] == "text":
                PartLines = Parts[PartIndex][1].split("\n")
                for LineIndex in range(0, len(PartLines)):
                    TextLines.append(PartLines[LineIndex])
            elif AIConnection.IsOnline(Settings) == False:
                UnreadImages.append(SourceRef)     # the offline demo marker cannot read images
            else:
                ImageURL = LoadSourceImages(SourceRef)
                if len(ImageURL) == 0:
                    UnreadImages.append(SourceRef)
                else:
                    print("Reading the handwriting in", os.path.basename(SourceRef), "...")
                    Rows = TranscribeAnswerImage(ImageURL[0], SourceRef, Processed.Questions, Settings)
                    # TranscribeAnswerImage returns one "failed" row if the request did not work
                    if Rows[0][3] == "failed":
                        UnreadImages.append(SourceRef)
                    else:
                        for Row in range(0, len(Rows)):
                            ImageAnswers.append(Rows[Row])
                        print("  " + str(len(Rows)) + " answer(s) read from", os.path.basename(SourceRef))
    if len(UnreadImages) > 0 and AIConnection.IsOnline(Settings) == False:
        print(len(UnreadImages), "photo(s) or scanned page(s) can only be read with an AI service that accepts images.")

    # 3. typed answers first, then the answers read from images (which may continue them)
    Rows = ParseAnswers(TextLines, Processed.Questions)
    for Row in range(0, len(Rows)):
        AddAnswerRow(AnswerTable, Rows[Row][0], Rows[Row][1], Rows[Row][2], Rows[Row][3])
    for Row in range(0, len(ImageAnswers)):
        AddAnswerRow(AnswerTable, ImageAnswers[Row][0], ImageAnswers[Row][1], ImageAnswers[Row][2], ImageAnswers[Row][3])
    MatchAnswers(Processed.Questions, AnswerTable, UnreadImages, Processed.UncertainMatches)
    DisplayProcessedPaper(Processed)
    return Processed


# main - runs this module on its own with the sample files and the offline demo marker
if __name__ == "__main__":
    TestDocuments = SQRecords.DocumentSet()
    TestDocuments.Paper.Level = "AS Level"
    TestDocuments.Paper.Subject = "Chemistry (9701)"
    TestDocuments.Paper.PaperCode = "9701/22/M/J/23"
    TestDocuments.Paper.Session = "May/June 2023"
    SampleFolder = os.path.join(ProgramFolder, "SampleData")
    TestDocuments.MarkSchemeFile = os.path.join(SampleFolder, "Sample_Chemistry_MS.txt")
    TestDocuments.AnswerFiles = [os.path.join(SampleFolder, "Sample_Chemistry_Answers.txt"),
                                 os.path.join(SampleFolder, "Sample_Answer_Q3.png")]
    TestDocuments.IsComplete = True
    TestProcessed = ProcessDocuments(TestDocuments, SQRecords.AISettings())
