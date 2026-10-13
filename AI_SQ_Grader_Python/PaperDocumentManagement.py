# PaperDocumentManagement.py
# AI SQ Grader - Paper and Document Management Module          (Fox)
#
# Receives DownloadSettings from the main module and returns one DocumentSet record.
# The user selects the paper (level, subject, paper number, series, year), uploads the
# student's answer files (typed text, PDF, or photos of handwritten work) and uploads the
# mark scheme and, optionally, the question paper, or downloads them through the
# configured download service. Marking can begin only when DocumentSet.IsComplete = TRUE.
#
# Acknowledgement: the record types in SQRecords.py were agreed by the whole group.

import datetime            # gives the current year for checking the year that is typed
import os                  # os.path checks that a file exists and finds its size
import urllib.error
import urllib.request      # downloads the mark scheme from the download service

import SQRecords

# CONSTANT
LevelNames = ["IGCSE", "AS Level", "A Level"]

# CONSTANT  parallel arrays: SubjectNames[i] has code SubjectCodes[i] at level SubjectLevels[i]
# DECLARE SubjectNames, SubjectCodes, SubjectLevels : ARRAY[0:7] OF STRING
SubjectNames = ["Physics", "Chemistry", "Biology", "Computer Science",
                "Physics", "Chemistry", "Biology", "Computer Science"]
SubjectCodes = ["0625", "0620", "0610", "0478", "9702", "9701", "9700", "9618"]
SubjectLevels = ["IGCSE", "IGCSE", "IGCSE", "IGCSE",
                 "AS and A Level", "AS and A Level", "AS and A Level", "AS and A Level"]

# CONSTANT  parallel arrays for the exam series
# DECLARE SeriesNames, SeriesCodes, SeriesLetters : ARRAY[0:2] OF STRING
SeriesNames = ["February/March", "May/June", "October/November"]
SeriesCodes = ["F/M", "M/J", "O/N"]
SeriesLetters = ["m", "s", "w"]            # letter used in Cambridge file names, e.g. 9701_s23_ms_22

# CONSTANT
AnswerFileTypes = [".txt", ".pdf", ".png", ".jpg", ".jpeg", ".webp"]
MarkSchemeFileTypes = [".txt", ".pdf"]
QuestionPaperFileTypes = [".pdf", ".txt", ".png", ".jpg", ".jpeg"]
MaxAnswerFiles = 20
FirstYear = 2016
ProgramFolder = os.path.dirname(os.path.abspath(__file__))
DownloadFolder = os.path.join(ProgramFolder, "Downloads")


def InputMenuChoice(Prompt, Options):
    # Shows a numbered menu and returns the position (0 to len(Options) - 1) that is chosen.
    # REPEAT ... UNTIL a whole number from 1 to len(Options) is typed.
    # DECLARE Index, Choice : INTEGER
    # DECLARE Valid : BOOLEAN
    print(Prompt)
    for Index in range(0, len(Options)):
        print("  " + str(Index + 1) + ". " + Options[Index])
    Valid = False
    while Valid == False:
        try:
            Choice = int(input("Enter a number from 1 to " + str(len(Options)) + ": "))
            if Choice >= 1 and Choice <= len(Options):
                Valid = True
            else:
                print("That number is not in the list.")
        except ValueError:
            print("Please type a whole number.")
    return Choice - 1


def IsValidPaperNumber(PaperNumber):
    # A paper number has two digits: component 1 to 6, then variant 1 to 3 (e.g. "22").
    # DECLARE Component, Variant : STRING
    if len(PaperNumber) != 2:
        return False
    Component = PaperNumber[0:1]               # LEFT(PaperNumber, 1)
    Variant = PaperNumber[1:2]                 # MID(PaperNumber, 2, 1)
    if Component < "1" or Component > "6":
        return False
    if Variant < "1" or Variant > "3":
        return False
    return True


def InputPaperNumber():
    # REPEAT ... UNTIL a valid paper number is typed.
    # DECLARE PaperNumber : STRING
    PaperNumber = input("Enter the paper number (component and variant, e.g. 22): ").strip()
    while IsValidPaperNumber(PaperNumber) == False:
        print("A paper number is two digits: component 1-6 and variant 1-3, e.g. 22.")
        PaperNumber = input("Enter the paper number: ").strip()
    return PaperNumber


def InputYear():
    # REPEAT ... UNTIL a year from FirstYear to this year is typed.
    # DECLARE Year, ThisYear : INTEGER
    # DECLARE Valid : BOOLEAN
    ThisYear = datetime.date.today().year
    Valid = False
    while Valid == False:
        try:
            Year = int(input("Enter the year of the exam (" + str(FirstYear) + " to " + str(ThisYear) + "): "))
            if Year >= FirstYear and Year <= ThisYear:
                Valid = True
            else:
                print("The year must be from", FirstYear, "to", ThisYear)
        except ValueError:
            print("Please type the year as a number, e.g. 2023.")
    return Year


def SelectPaper():
    # Asks for the paper details and returns them as one PaperDetails record.
    # DECLARE Paper : PaperDetails
    # DECLARE LevelChoice, SubjectChoice, SeriesChoice, Year, Index : INTEGER
    # DECLARE SubjectLevel, PaperNumber, YearText : STRING
    # DECLARE MenuNames : ARRAY OF STRING
    # DECLARE MenuPositions : ARRAY OF INTEGER   positions in the subject arrays
    Paper = SQRecords.PaperDetails()
    LevelChoice = InputMenuChoice("Select the examination level:", LevelNames)
    Paper.Level = LevelNames[LevelChoice]
    if Paper.Level == "IGCSE":
        SubjectLevel = "IGCSE"
    else:
        SubjectLevel = "AS and A Level"

    # build a menu of the subjects offered at this level
    MenuNames = []
    MenuPositions = []
    for Index in range(0, len(SubjectNames)):
        if SubjectLevels[Index] == SubjectLevel:
            MenuNames.append(SubjectNames[Index] + " (" + SubjectCodes[Index] + ")")
            MenuPositions.append(Index)
    SubjectChoice = InputMenuChoice("Select the subject:", MenuNames)
    Index = MenuPositions[SubjectChoice]
    Paper.Subject = MenuNames[SubjectChoice]

    PaperNumber = InputPaperNumber()
    SeriesChoice = InputMenuChoice("Select the exam series:", SeriesNames)
    Year = InputYear()
    YearText = str(Year)
    # Cambridge prints the paper code as subject/paper/series/year, e.g. 9701/22/M/J/23
    Paper.PaperCode = SubjectCodes[Index] + "/" + PaperNumber + "/" + SeriesCodes[SeriesChoice] + "/" + YearText[2:4]
    Paper.Session = SeriesNames[SeriesChoice] + " " + YearText
    return Paper


def GetFileExtension(FileName):
    # Returns the file extension in lower case, including the dot, e.g. ".pdf".
    # Searches backwards from the last character for a dot.
    # DECLARE Position : INTEGER
    # DECLARE ThisChar : CHAR
    # DECLARE Found : BOOLEAN
    Position = len(FileName) - 1
    Found = False
    while Position >= 0 and Found == False:
        ThisChar = FileName[Position]
        if ThisChar == ".":
            Found = True
        elif ThisChar == "/" or ThisChar == "\\":
            Position = -1                      # reached the folder name: no extension
        else:
            Position = Position - 1
    if Found == False:
        return ""
    return FileName[Position:].lower()         # RIGHT(FileName, LENGTH(FileName) - Position)


def IsAllowedType(FileName, AllowedTypes):
    # Linear search for the file's extension in the list of allowed types.
    # DECLARE Extension : STRING
    # DECLARE Index : INTEGER
    # DECLARE Found : BOOLEAN
    Extension = GetFileExtension(FileName)
    Index = 0
    Found = False
    while Index < len(AllowedTypes) and Found == False:
        if AllowedTypes[Index] == Extension:
            Found = True
        else:
            Index = Index + 1
    return Found


def RemoveQuotes(FileName):
    # Windows "Copy as path" puts quotes round a path; they are not part of the name.
    # DECLARE Text : STRING
    Text = FileName.strip()
    if len(Text) >= 2 and Text[0:1] == '"' and Text[len(Text) - 1:] == '"':
        Text = Text[1:len(Text) - 1]
    return Text


def FindFile(FileName):
    # Returns the path of the file, looking in the current folder first and then in the
    # program's folder (so the sample files can be typed as SampleData/...).
    # Returns "" if the file cannot be found.
    # DECLARE OtherPath : STRING
    if os.path.isfile(FileName):
        return FileName
    OtherPath = os.path.join(ProgramFolder, FileName)
    if os.path.isfile(OtherPath):
        return OtherPath
    return ""


def CheckDocument(FileName, AllowedTypes):
    # Returns "" if the file can be used, otherwise a message saying what is wrong.
    # DECLARE Index : INTEGER
    # DECLARE TypeList : STRING
    if FileName == "":
        return "No file name was given."
    if IsAllowedType(FileName, AllowedTypes) == False:
        TypeList = ""
        for Index in range(0, len(AllowedTypes)):
            TypeList = TypeList + " " + AllowedTypes[Index]
        return "This file type is not supported. Use one of:" + TypeList
    if FindFile(FileName) == "":
        return "The file " + FileName + " cannot be found."
    if os.path.getsize(FindFile(FileName)) == 0:
        return "The file " + FileName + " is empty."
    return ""


def IsAlreadyListed(FileName, FileList):
    # Linear search so that the same file is not uploaded twice.
    # DECLARE Index : INTEGER
    for Index in range(0, len(FileList)):
        if FileList[Index] == FileName:
            return True
    return False


def InputAnswerFiles():
    # Asks for the student's answer files one at a time until Enter is pressed on its own.
    # Returns the list of accepted file paths.
    # DECLARE AnswerFiles : ARRAY OF STRING
    # DECLARE FileName, Problem : STRING
    # DECLARE Finished : BOOLEAN
    AnswerFiles = []
    print("Upload the student's answers: typed (.txt), PDF, or photos of handwritten pages (.png, .jpg).")
    print("Type one file path at a time and press Enter on an empty line to finish.")
    Finished = False
    while Finished == False:
        FileName = RemoveQuotes(input("Answer file " + str(len(AnswerFiles) + 1) + ": "))
        if FileName == "":
            Finished = True
        else:
            Problem = CheckDocument(FileName, AnswerFileTypes)
            if Problem != "":
                print("Not added:", Problem)
            elif IsAlreadyListed(FindFile(FileName), AnswerFiles) == True:
                print("Not added: this file is already in the list.")
            else:
                AnswerFiles.append(FindFile(FileName))
                print("Added:", FileName)
                if len(AnswerFiles) == MaxAnswerFiles:
                    print("The maximum of", MaxAnswerFiles, "answer files has been reached.")
                    Finished = True
    return AnswerFiles


def MakePaperFileName(Paper, PaperType):
    # Builds the Cambridge file name of a paper. PaperType is "ms" (mark scheme) or "qp"
    # (question paper), e.g. 9701/22/M/J/23 and "ms" -> 9701_s23_ms_22
    # DECLARE SubjectCode, PaperNumber, SeriesCode, YearDigits, Letter : STRING
    # DECLARE Index : INTEGER
    SubjectCode = Paper.PaperCode[0:4]         # LEFT(PaperCode, 4)
    PaperNumber = Paper.PaperCode[5:7]         # MID(PaperCode, 6, 2)
    SeriesCode = Paper.PaperCode[8:11]         # MID(PaperCode, 9, 3)
    YearDigits = Paper.PaperCode[12:14]        # MID(PaperCode, 13, 2)
    Letter = ""
    for Index in range(0, len(SeriesCodes)):
        if SeriesCodes[Index] == SeriesCode:
            Letter = SeriesLetters[Index]
    return SubjectCode + "_" + Letter + YearDigits + "_" + PaperType + "_" + PaperNumber


def DescribePaperType(PaperType):
    if PaperType == "ms":
        return "mark scheme"
    return "question paper"


def DownloadPaperFile(Paper, PaperType, Download):
    # Downloads the mark scheme or question paper PDF from the download service (an online
    # data stream). Returns the path of the saved file, or "" if the download failed.
    # DECLARE URL, SavedName, FileStem, Description : STRING
    # DECLARE FileData : BYTES
    FileStem = MakePaperFileName(Paper, PaperType)
    Description = DescribePaperType(PaperType)
    URL = Download.ServiceURL + FileStem + ".pdf"
    print("Downloading the " + Description + " from", URL)
    try:
        Reply = urllib.request.urlopen(URL, timeout=30)
        FileData = Reply.read()
        Reply.close()
    except urllib.error.HTTPError as Error:
        print("Download failed: the service returned HTTP error", Error.code)
        return ""
    except (urllib.error.URLError, OSError):
        print("Download failed: the service could not be reached. Check the internet connection and the service URL.")
        return ""
    if FileData[0:4] != b"%PDF":               # every PDF file starts with %PDF
        print("Download failed: the service did not return a PDF file.")
        return ""
    SavedName = os.path.join(DownloadFolder, FileStem + ".pdf")
    try:
        if os.path.isdir(DownloadFolder) == False:
            os.makedirs(DownloadFolder)
        File = open(SavedName, "wb")
        File.write(FileData)
        File.close()
    except IOError:
        print("Download failed: the file could not be saved in", DownloadFolder)
        return ""
    print(Description[0:1].upper() + Description[1:] + " saved as", SavedName)
    return SavedName


def InputPaperFile(Paper, PaperType, AllowedTypes, Download):
    # Uploads the mark scheme or question paper, or downloads it when the download service
    # is enabled. Returns the path of the file, or "" if there is none.
    # DECLARE FileName, Problem, Prompt, TypeList : STRING
    # DECLARE Index : INTEGER
    # DECLARE Finished : BOOLEAN
    TypeList = ""
    for Index in range(0, len(AllowedTypes)):
        TypeList = TypeList + " " + AllowedTypes[Index]
    Prompt = DescribePaperType(PaperType)
    Prompt = Prompt[0:1].upper() + Prompt[1:] + " file (" + TypeList.strip() + ")"
    if PaperType == "qp":
        Prompt = Prompt + " - optional, it helps the AI understand each question"
    if Download.Enabled == True:
        Prompt = Prompt + ", or press Enter to download it: "
    elif PaperType == "qp":
        Prompt = Prompt + ", or press Enter to skip: "
    else:
        Prompt = Prompt + ", or press Enter if you do not have it: "
    FileName = ""
    Finished = False
    while Finished == False:
        FileName = RemoveQuotes(input(Prompt))
        if FileName == "":
            if Download.Enabled == True:
                FileName = DownloadPaperFile(Paper, PaperType, Download)
            Finished = True
        else:
            Problem = CheckDocument(FileName, AllowedTypes)
            if Problem == "":
                FileName = FindFile(FileName)
                Finished = True
            else:
                print("Not accepted:", Problem)
    return FileName


def InputMarkScheme(Paper, Download):
    return InputPaperFile(Paper, "ms", MarkSchemeFileTypes, Download)


def InputQuestionPaper(Paper, Download):
    return InputPaperFile(Paper, "qp", QuestionPaperFileTypes, Download)


def CheckCompleteness(Documents):
    # Returns TRUE only when the paper details, at least one answer file and the mark scheme
    # are all present (the question paper is optional). Outputs a message for each item
    # that is missing.
    # DECLARE Complete : BOOLEAN
    Complete = True
    if Documents.Paper.PaperCode == "":
        print("Missing: the paper details have not been selected.")
        Complete = False
    if len(Documents.AnswerFiles) == 0:
        print("Missing: no student answer file has been uploaded.")
        Complete = False
    if Documents.MarkSchemeFile == "":
        print("Missing: no mark scheme has been uploaded or downloaded.")
        Complete = False
    return Complete


def DisplayDocumentSet(Documents):
    # Outputs the selected paper and the documents linked to it.
    # DECLARE Index : INTEGER
    print()
    print("Paper:", Documents.Paper.Level, "-", Documents.Paper.Subject)
    print("Paper code:", Documents.Paper.PaperCode, "  Session:", Documents.Paper.Session)
    print("Answer files:", len(Documents.AnswerFiles))
    for Index in range(0, len(Documents.AnswerFiles)):
        print("  " + str(Index + 1) + ". " + os.path.basename(Documents.AnswerFiles[Index]))
    if Documents.MarkSchemeFile == "":
        print("Mark scheme: (none)")
    else:
        print("Mark scheme:", os.path.basename(Documents.MarkSchemeFile))
    if Documents.QuestionPaperFile == "":
        print("Question paper: (none - the AI will mark without the question text)")
    else:
        print("Question paper:", os.path.basename(Documents.QuestionPaperFile))


def ManageDocuments(Download):
    # Paper and Document Management Module: returns one DocumentSet record.
    # DECLARE Documents : DocumentSet
    Documents = SQRecords.DocumentSet()
    print()
    print("=== Paper and Document Management ===")
    Documents.Paper = SelectPaper()
    Documents.AnswerFiles = InputAnswerFiles()
    Documents.MarkSchemeFile = InputMarkScheme(Documents.Paper, Download)
    if Documents.MarkSchemeFile != "":
        Documents.QuestionPaperFile = InputQuestionPaper(Documents.Paper, Download)
    Documents.IsComplete = CheckCompleteness(Documents)
    DisplayDocumentSet(Documents)
    if Documents.IsComplete == True:
        print("All documents are ready. Marking can begin.")
    else:
        print("Marking cannot begin until the missing documents are added.")
    return Documents


# main - runs this module on its own, with the download service switched off
if __name__ == "__main__":
    TestDownload = SQRecords.DownloadSettings()
    TestDocuments = ManageDocuments(TestDownload)
    print("IsComplete =", TestDocuments.IsComplete)
