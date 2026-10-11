# Shared helpers for the unit tests. Tests may use ordinary Python idioms; the program
# modules themselves follow the CAIE style.

import contextlib
import io
import os
import sys
from unittest import mock

ProgramFolder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, ProgramFolder)

SampleFolder = os.path.join(ProgramFolder, 'SampleData')

import SQRecords  # noqa: E402


def RunWithInput(Function, Inputs, *Arguments):
    # Runs Function with the given keyboard inputs and returns (result, printed text).
    Output = io.StringIO()
    with mock.patch('builtins.input', side_effect=list(Inputs)):
        with contextlib.redirect_stdout(Output):
            Result = Function(*Arguments)
    return Result, Output.getvalue()


def Quiet(Function, *Arguments):
    # Runs Function without showing its printed output; returns (result, printed text).
    Output = io.StringIO()
    with contextlib.redirect_stdout(Output):
        Result = Function(*Arguments)
    return Result, Output.getvalue()


def MakePoint(PointID, Marks, Requirement):
    Point = SQRecords.MarkingPoint()
    Point.PointID = PointID
    Point.Marks = Marks
    Point.Requirement = Requirement
    return Point


def MakeQuestion(QuestionID, MaxMark, AnswerText, Points, RuleNotes=''):
    Question = SQRecords.QuestionItem()
    Question.QuestionID = QuestionID
    Question.MarkingRules.MaxMark = MaxMark
    Question.MarkingRules.RuleNotes = RuleNotes
    Question.AnswerText = AnswerText
    for Point in Points:
        Question.MarkingPoints.append(Point)
    return Question


def MakeFeedback(Categories, Marks=None):
    # Categories: list of (PointID, Category)
    Feedback = SQRecords.PointFeedbackSet()
    for Index, (PointID, Category) in enumerate(Categories):
        Point = SQRecords.PointFeedback()
        Point.PointID = PointID
        Point.Category = Category
        Point.Marks = 1 if Marks is None else Marks[Index]
        Feedback.Points.append(Point)
    return Feedback


def SampleDocuments():
    Documents = SQRecords.DocumentSet()
    Documents.Paper.Level = 'AS Level'
    Documents.Paper.Subject = 'Chemistry (9701)'
    Documents.Paper.PaperCode = '9701/22/M/J/23'
    Documents.Paper.Session = 'May/June 2023'
    Documents.MarkSchemeFile = os.path.join(SampleFolder, 'Sample_Chemistry_MS.txt')
    Documents.AnswerFiles = [os.path.join(SampleFolder, 'Sample_Chemistry_Answers.txt'),
                             os.path.join(SampleFolder, 'Sample_Answer_Q3.png')]
    Documents.IsComplete = True
    return Documents


def SampleGrading():
    # Processes and grades the sample paper with the offline demo marker.
    import DocumentProcessing
    import GradingFeedback
    Processed, _ = Quiet(DocumentProcessing.ProcessDocuments, SampleDocuments())
    Grading, _ = Quiet(GradingFeedback.GradePaper, Processed, SQRecords.AISettings())
    return Grading
