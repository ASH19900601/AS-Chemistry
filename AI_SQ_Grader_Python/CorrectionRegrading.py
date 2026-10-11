# CorrectionRegrading.py
# AI SQ Grader - Correction and Regrading Module                 (Caroline)
#
# Receives the GradingResult and AISettings. The student selects one question and submits
# a corrected answer as text (typed or from a .txt file) or as a photo of handwriting,
# which is read by the AI service. The answer is reassessed against the SAME marking points
# and rules stored in the GradingResult and the two attempts are compared. Returns one
# RegradeResult record; HasCorrection = FALSE when no correction is submitted.
#
# Integration: reassessment calls AssessMarkingPoints and CalculateEstimatedMark from the
# Grading and Feedback Module, and photos are read with TranscribeAnswerImage from the
# Document Processing Module (both written by Kevin); images are loaded by AIConnection.py (Fox).
# Acknowledgement: the record types in SQRecords.py were agreed by the whole group.

import os                  # os.path checks that an image or text file exists

import AIConnection        # Fox's module, loads the photo for the AI
import DocumentProcessing  # Kevin's module, reads the handwriting in a photo
import GradingFeedback     # Kevin's module, used to mark the corrected answer
import SQRecords

# CONSTANT
ImageTypes = [".png", ".jpg", ".jpeg", ".webp"]
CorrectionMethods = ["Type the corrected answer", "Load the corrected answer from a .txt file",
                     "Upload a photo of the corrected answer (.png or .jpg)"]


def AskYesNo(Prompt):
    # REPEAT ... UNTIL the user types Y or N. Returns TRUE for Y.
    # DECLARE Reply : STRING
    Reply = input(Prompt + " (Y/N): ").strip().upper()
    while Reply != "Y" and Reply != "N":
        print("Please type Y or N.")
        Reply = input(Prompt + " (Y/N): ").strip().upper()
    return Reply == "Y"


def FindQuestionIndex(Grading, QuestionID):
    # Linear search of the question results. Returns the position or -1.
    # DECLARE Index : INTEGER
    # DECLARE Found : BOOLEAN
    Index = 0
    Found = False
    while Index < len(Grading.QuestionResults) and Found == False:
        if Grading.QuestionResults[Index].Question.QuestionID.lower() == QuestionID.strip().lower():
            Found = True
        else:
            Index = Index + 1
    if Found == False:
        Index = -1
    return Index


def DisplayQuestionList(Grading):
    # Outputs every question with its estimated mark, so the student can choose one.
    # DECLARE Index : INTEGER
    # DECLARE Note : STRING
    print()
    print("Question    Mark")
    for Index in range(0, len(Grading.QuestionResults)):
        Note = ""
        if Grading.QuestionResults[Index].Feedback.NeedsReview == True:
            Note = "   (needs review)"
        elif Grading.QuestionResults[Index].EstimatedMark < Grading.QuestionResults[Index].Question.MarkingRules.MaxMark:
            Note = "   (marks lost)"
        print(Grading.QuestionResults[Index].Question.QuestionID.ljust(12)
              + str(Grading.QuestionResults[Index].EstimatedMark) + " / "
              + str(Grading.QuestionResults[Index].Question.MarkingRules.MaxMark) + Note)


def SelectQuestion(Grading):
    # Asks for a question number until one in the paper is typed, or Enter to cancel.
    # Returns the position of the question, or -1 if cancelled.
    # DECLARE QuestionID : STRING
    # DECLARE Index : INTEGER
    Index = -2
    while Index == -2:
        QuestionID = input("Question number to correct (e.g. 2(b)), or Enter to cancel: ").strip()
        if QuestionID == "":
            Index = -1
        else:
            Index = FindQuestionIndex(Grading, QuestionID)
            if Index == -1:
                print("Question", QuestionID, "is not in this paper.")
                Index = -2
    return Index


def InputCorrectionMethod():
    # Shows the ways to submit a correction and returns 1, 2 or 3.
    # DECLARE Index, Method : INTEGER
    print("How will you submit the correction?")
    for Index in range(0, len(CorrectionMethods)):
        print("  " + str(Index + 1) + ". " + CorrectionMethods[Index])
    Method = 0
    while Method < 1 or Method > len(CorrectionMethods):
        try:
            Method = int(input("Enter 1, 2 or 3: "))
        except ValueError:
            Method = 0
    return Method


def InputFileName(Prompt):
    # Reads a file path. Windows "Copy as path" adds quotes, which are removed.
    # DECLARE FileName : STRING
    FileName = input(Prompt).strip()
    if len(FileName) >= 2 and FileName[0:1] == '"' and FileName[len(FileName) - 1:] == '"':
        FileName = FileName[1:len(FileName) - 1]
    return FileName


def InputTypedAnswer():
    # Reads lines until an empty line is entered. Returns the lines joined with line breaks.
    # DECLARE AnswerText, ThisLine : STRING
    print("Type the corrected answer. Press Enter on an empty line to finish.")
    AnswerText = ""
    ThisLine = input("> ")
    while ThisLine != "":
        if AnswerText == "":
            AnswerText = ThisLine
        else:
            AnswerText = AnswerText + "\n" + ThisLine
        ThisLine = input("> ")
    return AnswerText


def ReadAnswerFile(FileName):
    # Reads a corrected answer from a text file. Returns "" if the file cannot be read.
    # DECLARE AnswerText, ThisLine : STRING
    AnswerText = ""
    try:
        File = open(FileName, "r", encoding="utf-8")
    except IOError:
        print("The file", FileName, "could not be opened.")
        return AnswerText
    ThisLine = File.readline()
    while ThisLine != "":
        AnswerText = AnswerText + ThisLine
        ThisLine = File.readline()
    File.close()
    return AnswerText.strip()


def HasImageType(FileName):
    # TRUE if the file name ends with one of the image types (linear search).
    # DECLARE Index : INTEGER
    for Index in range(0, len(ImageTypes)):
        if FileName.lower()[len(FileName) - len(ImageTypes[Index]):] == ImageTypes[Index]:
            return True
    return False


def ReadCorrectionPhoto(FileName, Question, Settings):
    # Reads the handwriting in a photo of a corrected answer. Returns the text, or "" if it
    # cannot be read with confidence (the correction is then flagged for review).
    # DECLARE ImageURL, AnswerText : STRING
    # DECLARE Rows : ARRAY OF ARRAY[0:3] OF STRING
    # DECLARE Index : INTEGER
    if AIConnection.IsOnline(Settings) == False:
        print("Without an AI service the photo cannot be read, so the correction will be flagged for review.")
        return ""
    ImageURL = AIConnection.MakeImageURL(FileName)
    if ImageURL == "":
        return ""
    print("Reading the handwriting in", os.path.basename(FileName), "...")
    Rows = DocumentProcessing.TranscribeAnswerImage(ImageURL, FileName, [Question], Settings)
    AnswerText = ""
    for Index in range(0, len(Rows)):
        if Rows[Index][3] == "failed" or Rows[Index][3] == "low":
            print("The handwriting could not be read with confidence, so the correction will be flagged for review.")
            return ""
        if AnswerText == "":
            AnswerText = Rows[Index][1]
        else:
            AnswerText = AnswerText + "\n" + Rows[Index][1]
    if AnswerText == "":
        print("No answer was found in the photo, so the correction will be flagged for review.")
    else:
        print("Read from the photo:", AnswerText)
    return AnswerText


def CopyQuestionItem(Question, NewAnswerText, NewImageRef):
    # Makes a new QuestionItem with the same marking points and rules but a new answer.
    # The marking points are copied one by one so the original question is not changed.
    # DECLARE NewQuestion : QuestionItem
    # DECLARE NewPoint : MarkingPoint
    # DECLARE Index : INTEGER
    NewQuestion = SQRecords.QuestionItem()
    NewQuestion.QuestionID = Question.QuestionID
    NewQuestion.QuestionText = Question.QuestionText
    NewQuestion.AnswerText = NewAnswerText
    NewQuestion.SourceImageRef = NewImageRef
    NewQuestion.MarkingRules.MaxMark = Question.MarkingRules.MaxMark
    NewQuestion.MarkingRules.RuleNotes = Question.MarkingRules.RuleNotes
    for Index in range(0, len(Question.MarkingPoints)):
        NewPoint = SQRecords.MarkingPoint()
        NewPoint.PointID = Question.MarkingPoints[Index].PointID
        NewPoint.Requirement = Question.MarkingPoints[Index].Requirement
        NewPoint.Marks = Question.MarkingPoints[Index].Marks
        NewQuestion.MarkingPoints.append(NewPoint)
    return NewQuestion


def MakeAttempt(QuestionID, AttemptNo, AnswerText, Feedback, EstimatedMark):
    # Builds one AttemptRecord.
    # DECLARE Attempt : AttemptRecord
    Attempt = SQRecords.AttemptRecord()
    Attempt.QuestionID = QuestionID
    Attempt.AttemptNo = AttemptNo
    Attempt.AnswerText = AnswerText
    Attempt.Feedback = Feedback
    Attempt.EstimatedMark = EstimatedMark
    return Attempt


def FindCategory(Feedback, PointID):
    # Linear search for the category given to one marking point.
    # DECLARE Index : INTEGER
    for Index in range(0, len(Feedback.Points)):
        if Feedback.Points[Index].PointID == PointID:
            return Feedback.Points[Index].Category
    return SQRecords.CategoryNotAssessed


def CompareFeedback(OldFeedback, NewFeedback):
    # Returns one line for each marking point whose category changed between attempts.
    # DECLARE Changes : ARRAY OF STRING
    # DECLARE Index : INTEGER
    # DECLARE OldCategory, NewCategory : STRING
    Changes = []
    for Index in range(0, len(NewFeedback.Points)):
        OldCategory = FindCategory(OldFeedback, NewFeedback.Points[Index].PointID)
        NewCategory = NewFeedback.Points[Index].Category
        if OldCategory != NewCategory:
            Changes.append(NewFeedback.Points[Index].PointID + ": " + OldCategory + " -> " + NewCategory)
    if len(NewFeedback.OutsideMSContent) != len(OldFeedback.OutsideMSContent):
        Changes.append("Content outside the mark scheme: " + str(len(OldFeedback.OutsideMSContent))
                       + " item(s) -> " + str(len(NewFeedback.OutsideMSContent)) + " item(s)")
    if len(Changes) == 0:
        Changes.append("No change in the marking-point feedback.")
    return Changes


def RegradeQuestion(Grading, QuestionIndex, NewAnswerText, NewImageRef, Settings):
    # Reassesses one question with the original marking criteria and compares the attempts.
    # Returns one RegradeResult record.
    # DECLARE Result : RegradeResult
    # DECLARE Original : QuestionResult
    # DECLARE NewQuestion : QuestionItem
    # DECLARE NewFeedback : PointFeedbackSet
    # DECLARE NewMark : INTEGER
    # DECLARE IsMatched : BOOLEAN
    Result = SQRecords.RegradeResult()
    Original = Grading.QuestionResults[QuestionIndex]
    NewQuestion = CopyQuestionItem(Original.Question, NewAnswerText, NewImageRef)
    # the corrected answer belongs to the selected question; a photo that could not be read
    # (no text) is flagged for review
    IsMatched = NewAnswerText.strip() != ""
    NewFeedback = GradingFeedback.AssessMarkingPoints(NewQuestion, IsMatched, Settings)
    NewMark = GradingFeedback.CalculateEstimatedMark(NewFeedback, NewQuestion.MarkingRules)

    Result.HasCorrection = True
    Result.QuestionID = Original.Question.QuestionID
    Result.Attempts.append(MakeAttempt(Result.QuestionID, 1, Original.Question.AnswerText, Original.Feedback, Original.EstimatedMark))
    Result.Attempts.append(MakeAttempt(Result.QuestionID, 2, NewAnswerText, NewFeedback, NewMark))
    Result.MarkChange = NewMark - Original.EstimatedMark
    Result.FeedbackChanges = CompareFeedback(Original.Feedback, NewFeedback)
    return Result


def DisplayComparison(Result, MaxMark):
    # Outputs the original and corrected attempts side by side.
    # DECLARE OldAttempt, NewAttempt : AttemptRecord
    # DECLARE Index : INTEGER
    OldAttempt = Result.Attempts[0]
    NewAttempt = Result.Attempts[len(Result.Attempts) - 1]
    print()
    print("Comparison for question", Result.QuestionID)
    print("Point   Original attempt      Corrected attempt")
    for Index in range(0, len(NewAttempt.Feedback.Points)):
        print(NewAttempt.Feedback.Points[Index].PointID.ljust(8)
              + FindCategory(OldAttempt.Feedback, NewAttempt.Feedback.Points[Index].PointID).ljust(22)
              + NewAttempt.Feedback.Points[Index].Category)
    print("Estimated mark: " + str(OldAttempt.EstimatedMark) + " / " + str(MaxMark) + " -> "
          + str(NewAttempt.EstimatedMark) + " / " + str(MaxMark))
    if Result.MarkChange > 0:
        print("Well done: the corrected answer gains", Result.MarkChange, "more mark(s).")
    elif Result.MarkChange < 0:
        print("The corrected answer scores", -Result.MarkChange, "mark(s) fewer than the original.")
    else:
        print("The estimated mark has not changed.")
    print("Feedback changes:")
    for Index in range(0, len(Result.FeedbackChanges)):
        print("  " + Result.FeedbackChanges[Index])
    for Index in range(0, len(NewAttempt.Feedback.Points)):
        if NewAttempt.Feedback.Points[Index].Category != SQRecords.CategoryClearlyCorrect:
            print("  Still to improve - " + NewAttempt.Feedback.Points[Index].PointID + ": " + NewAttempt.Feedback.Points[Index].Explanation)


def CorrectAndRegrade(Grading, Settings):
    # Correction and Regrading Module: returns one RegradeResult record.
    # DECLARE Result : RegradeResult
    # DECLARE QuestionIndex, Method : INTEGER
    # DECLARE NewAnswerText, NewImageRef, FileName : STRING
    Result = SQRecords.RegradeResult()
    print()
    print("=== Correction and Regrading ===")
    if len(Grading.QuestionResults) == 0:
        print("There are no marked questions to correct.")
        return Result
    if AskYesNo("Do you want to submit a corrected answer for one question?") == False:
        print("No correction submitted.")
        return Result
    DisplayQuestionList(Grading)
    QuestionIndex = SelectQuestion(Grading)
    if QuestionIndex == -1:
        print("No correction submitted.")
        return Result

    NewAnswerText = ""
    NewImageRef = ""
    Method = InputCorrectionMethod()
    if Method == 1:
        NewAnswerText = InputTypedAnswer()
    elif Method == 2:
        FileName = InputFileName("Text file with the corrected answer: ")
        NewAnswerText = ReadAnswerFile(FileName)
    else:
        FileName = InputFileName("Image file of the corrected answer: ")
        if HasImageType(FileName) == True and os.path.isfile(FileName) == True:
            NewImageRef = FileName
            NewAnswerText = ReadCorrectionPhoto(FileName, Grading.QuestionResults[QuestionIndex].Question, Settings)
        else:
            print("That is not an existing .png or .jpg file.")

    if NewAnswerText == "" and NewImageRef == "":
        print("The corrected answer is empty, so no correction was submitted.")
        return Result
    Result = RegradeQuestion(Grading, QuestionIndex, NewAnswerText, NewImageRef, Settings)
    DisplayComparison(Result, Grading.QuestionResults[QuestionIndex].Question.MarkingRules.MaxMark)
    return Result


# main - runs this module on its own: marks one sample question, then asks for a correction
if __name__ == "__main__":
    TestSettings = SQRecords.AISettings()          # offline demo marker
    TestQuestion = SQRecords.QuestionItem()
    TestQuestion.QuestionID = "2(b)"
    TestQuestion.MarkingRules.MaxMark = 2
    TestQuestion.AnswerText = "The rate gets faster because the particles collide more often."
    TestPoint = SQRecords.MarkingPoint()
    TestPoint.PointID = "P1"
    TestPoint.Marks = 1
    TestPoint.Requirement = "the rate of reaction increases at a higher temperature"
    TestQuestion.MarkingPoints.append(TestPoint)
    TestPoint = SQRecords.MarkingPoint()
    TestPoint.PointID = "P2"
    TestPoint.Marks = 1
    TestPoint.Requirement = "more particles have energy greater than or equal to the activation energy"
    TestQuestion.MarkingPoints.append(TestPoint)
    TestGrading = SQRecords.GradingResult()
    TestResult = SQRecords.QuestionResult()
    TestResult.Question = TestQuestion
    TestResult.Feedback = GradingFeedback.AssessMarkingPoints(TestQuestion, True, TestSettings)
    TestResult.EstimatedMark = GradingFeedback.CalculateEstimatedMark(TestResult.Feedback, TestQuestion.MarkingRules)
    TestGrading.QuestionResults.append(TestResult)
    TestRegrade = CorrectAndRegrade(TestGrading, TestSettings)
    print("HasCorrection =", TestRegrade.HasCorrection, " MarkChange =", TestRegrade.MarkChange)
