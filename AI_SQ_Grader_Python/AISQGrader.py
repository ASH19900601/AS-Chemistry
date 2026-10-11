# AISQGrader.py
# AI SQ Grader - main module                                    (Fox)
#
# Controls a marking session by calling the six modules in order from left to right on
# the structure chart. It holds AISettings and DownloadSettings and passes each returned
# record to the modules that need it; all data between modules travels through here.
# Run this file to start the whole application:   python AISQGrader.py
#
# Acknowledgement: each imported module was written by the group member named in its
# header; the record types in SQRecords.py were agreed by the whole group.

import getpass             # reads the API key without showing it on the screen
import os                  # reads the API key from an environment variable; builds file paths

import CorrectionRegrading         # Caroline
import DocumentProcessing          # Kevin
import GradingFeedback             # Kevin
import LearningRecords             # Caroline
import PaperDocumentManagement     # Fox
import ReportManagement            # Andy
import SQRecords

# CONSTANT
ProgramFolder = os.path.dirname(os.path.abspath(__file__))
SettingsFileName = os.path.join(ProgramFolder, "Settings.txt")
APIKeyVariable = "SQ_API_KEY"              # environment variable that may hold the API key
ProviderChoices = ["Offline (built-in demo marker, no internet)", "OpenAI", "DeepSeek",
                   "Other OpenAI-compatible service (type its base URL)"]
DefaultModels = ["", "gpt-4o-mini", "deepseek-chat", ""]


def ReadSettingsFile(FileName):
    # Reads lines of the form Key=Value. Lines that start with # are comments.
    # Returns a table with one row [Key, Value] for each setting, or an empty table if
    # the file cannot be read.
    # DECLARE SettingsTable : ARRAY OF ARRAY[0:1] OF STRING
    # DECLARE ThisLine, Key, Value : STRING
    # DECLARE Position, Index : INTEGER
    SettingsTable = []
    try:
        File = open(FileName, "r", encoding="utf-8")
    except IOError:
        print("Settings file not found:", FileName, "- default settings will be used.")
        return SettingsTable
    ThisLine = File.readline()
    while ThisLine != "":
        ThisLine = ThisLine.strip()
        if ThisLine != "" and ThisLine[0:1] != "#":
            # find the first "=" in the line
            Position = -1
            Index = 0
            while Index < len(ThisLine) and Position == -1:
                if ThisLine[Index] == "=":
                    Position = Index
                Index = Index + 1
            if Position > 0:
                Key = ThisLine[0:Position].strip()
                Value = ThisLine[Position + 1:].strip()
                SettingsTable.append([Key, Value])
        ThisLine = File.readline()
    File.close()
    return SettingsTable


def GetSetting(SettingsTable, Key, DefaultValue):
    # Linear search of the settings table; the key is not case-sensitive.
    # DECLARE Row : INTEGER
    for Row in range(0, len(SettingsTable)):
        if SettingsTable[Row][0].upper() == Key.upper():
            return SettingsTable[Row][1]
    return DefaultValue


def AskForAPIKey(Provider):
    # The key is never written to a file. It comes from the environment variable
    # SQ_API_KEY, or the user types it (the typing is hidden).
    # DECLARE APIKey : STRING
    APIKey = os.environ.get(APIKeyVariable, "").strip()
    if APIKey == "":
        APIKey = getpass.getpass("Enter the API key for " + Provider + " (hidden, Enter to skip): ").strip()
    return APIKey


def LoadAISettings(SettingsTable):
    # Builds the AISettings record from the settings file.
    # DECLARE Settings : AISettings
    Settings = SQRecords.AISettings()
    Settings.Provider = GetSetting(SettingsTable, "Provider", SQRecords.OfflineProvider)
    Settings.ModelName = GetSetting(SettingsTable, "ModelName", "")
    if Settings.Provider.upper() == SQRecords.OfflineProvider.upper():
        Settings.Provider = SQRecords.OfflineProvider
    else:
        Settings.APIKey = AskForAPIKey(Settings.Provider)
        if Settings.APIKey == "":
            print("No API key was given, so the offline demo marker will be used.")
            Settings.Provider = SQRecords.OfflineProvider
    return Settings


def LoadDownloadSettings(SettingsTable):
    # Builds the DownloadSettings record from the settings file.
    # DECLARE Download : DownloadSettings
    Download = SQRecords.DownloadSettings()
    Download.ServiceURL = GetSetting(SettingsTable, "DownloadServiceURL", "")
    if GetSetting(SettingsTable, "DownloadEnabled", "FALSE").upper() == "TRUE" and Download.ServiceURL != "":
        Download.Enabled = True
    else:
        Download.Enabled = False
    return Download


def InputAISettings():
    # Lets the user choose the AI service for this run. Returns a new AISettings record.
    # DECLARE Settings : AISettings
    # DECLARE Choice : INTEGER
    # DECLARE ModelName : STRING
    Settings = SQRecords.AISettings()
    Choice = PaperDocumentManagement.InputMenuChoice("Choose the AI service:", ProviderChoices)
    if Choice == 0:
        Settings.Provider = SQRecords.OfflineProvider
        return Settings
    if Choice == 3:
        Settings.Provider = input("Base URL (e.g. https://api.example.com/v1): ").strip()
        while Settings.Provider[0:8] != "https://" and Settings.Provider[0:7] != "http://":
            print("The base URL must start with https:// or http://")
            Settings.Provider = input("Base URL: ").strip()
    else:
        Settings.Provider = ProviderChoices[Choice]
    ModelName = input("Model name (Enter for " + DefaultModels[Choice] + "): ").strip()
    if ModelName == "":
        ModelName = DefaultModels[Choice]
    Settings.ModelName = ModelName
    Settings.APIKey = AskForAPIKey(Settings.Provider)
    if Settings.APIKey == "" or Settings.ModelName == "":
        print("The API key and model name are both needed; the offline demo marker will be used.")
        Settings = SQRecords.AISettings()
    return Settings


def DisplaySettings(Settings, Download):
    # Outputs the current settings without showing the API key.
    if Settings.Provider == SQRecords.OfflineProvider:
        print("AI service: Offline demo marker (key words only - use a real AI service for real marking)")
    else:
        print("AI service:", Settings.Provider, " Model:", Settings.ModelName, " API key: set")
    if Download.Enabled == True:
        print("Mark scheme download service:", Download.ServiceURL)
    else:
        print("Mark scheme download service: off (upload the mark scheme)")


def RunMarkingSession(Settings, Download):
    # Calls the six modules in order. Each call returns one record.
    # DECLARE Documents : DocumentSet
    # DECLARE Processed : ProcessedPaper
    # DECLARE Grading : GradingResult
    # DECLARE Regrade : RegradeResult
    # DECLARE Learning : LearningData
    # DECLARE Outcome : ReportOutcome
    Documents = PaperDocumentManagement.ManageDocuments(Download)
    if Documents.IsComplete == False:
        print("The marking session has stopped because documents are missing.")
        return
    Processed = DocumentProcessing.ProcessDocuments(Documents)
    if len(Processed.Questions) == 0:
        print("No questions could be read from the mark scheme, so nothing can be marked.")
        return
    Grading = GradingFeedback.GradePaper(Processed, Settings)
    Regrade = CorrectionRegrading.CorrectAndRegrade(Grading, Settings)
    Learning = LearningRecords.UpdateLearningRecords(Grading, Regrade)
    Outcome = ReportManagement.ManageReports(Grading, Learning)
    print()
    print("=== Session finished ===")
    print("Estimated total:", Grading.TotalMark, "/", Grading.MaxTotal)
    if Learning.SaveSuccess == True:
        print("Learning records saved.")
    if Outcome.ReportFile != "":
        print("Report:", Outcome.ReportFile)


def ReviewSavedRecords():
    # Opens the learning records and reports without marking a new paper. The Learning
    # Records and Report modules receive an empty GradingResult and an empty RegradeResult.
    # DECLARE Learning : LearningData
    # DECLARE Outcome : ReportOutcome
    Learning = LearningRecords.UpdateLearningRecords(SQRecords.GradingResult(), SQRecords.RegradeResult())
    Outcome = ReportManagement.ManageReports(SQRecords.GradingResult(), Learning)
    if Outcome.BackupFile != "" or Outcome.ImportValid == True:
        print("Records review finished.")


def RunMainMenu():
    # Main menu: repeats until the user chooses Exit.
    # DECLARE SettingsTable : ARRAY OF ARRAY[0:1] OF STRING
    # DECLARE Settings : AISettings
    # DECLARE Download : DownloadSettings
    # DECLARE Choice : INTEGER
    # DECLARE MenuOptions : ARRAY[0:3] OF STRING
    print("==============================================")
    print(" AI SQ Grader - structured question marking")
    print("==============================================")
    print("Estimated marks are for practice only. They are not official Cambridge grades.")
    SettingsTable = ReadSettingsFile(SettingsFileName)
    Settings = LoadAISettings(SettingsTable)
    Download = LoadDownloadSettings(SettingsTable)
    DisplaySettings(Settings, Download)
    MenuOptions = ["Mark a new paper", "Open the mistake notebook, progress and backups",
                   "Change the AI service", "Exit"]
    Choice = -1
    while Choice != 3:
        print()
        Choice = PaperDocumentManagement.InputMenuChoice("Main menu:", MenuOptions)
        if Choice == 0:
            RunMarkingSession(Settings, Download)
        elif Choice == 1:
            ReviewSavedRecords()
        elif Choice == 2:
            Settings = InputAISettings()
            DisplaySettings(Settings, Download)
    print("Goodbye.")


# main
if __name__ == "__main__":
    RunMainMenu()
