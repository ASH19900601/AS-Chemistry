# Shared helpers for the unit tests. Tests may use ordinary Python idioms; the program
# modules themselves follow the CAIE style.

import contextlib
import http.server
import io
import json
import os
import sys
import threading
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
    Processed, _ = Quiet(DocumentProcessing.ProcessDocuments, SampleDocuments(), SQRecords.AISettings())
    Grading, _ = Quiet(GradingFeedback.GradePaper, Processed, SQRecords.AISettings())
    return Grading


def Completion(Content):
    # A /chat/completions reply whose message content is Content (a string or a dictionary).
    if type(Content) != str:
        Content = json.dumps(Content)
    return json.dumps({'choices': [{'message': {'role': 'assistant', 'content': Content}}]})


class FakeAIServer:
    # A local web server that answers like an OpenAI-compatible AI service. Replies is a
    # list of (status, body) returned in order; Requests records (path, Authorization, body).
    def __init__(self):
        Outer = self
        self.Replies = []
        self.Requests = []

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                Body = self.rfile.read(int(self.headers['Content-Length']))
                Outer.Requests.append((self.path, self.headers.get('Authorization'), json.loads(Body)))
                if Outer.Replies:
                    Status, Text = Outer.Replies.pop(0)
                else:
                    Status, Text = 500, '{"error": "no reply queued"}'
                self.send_response(Status)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(Text.encode('utf-8'))

            def log_message(self, *Arguments):
                pass

        self.Server = http.server.HTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=self.Server.serve_forever, daemon=True).start()
        self.Environment = mock.patch.dict(os.environ, {'no_proxy': '127.0.0.1,localhost', 'NO_PROXY': '127.0.0.1,localhost'})
        self.Environment.start()
        import AIConnection
        self.Sleep = mock.patch.object(AIConnection.time, 'sleep')
        self.Sleep.start()

    def Settings(self):
        Settings = SQRecords.AISettings()
        Settings.Provider = 'http://127.0.0.1:' + str(self.Server.server_port) + '/v1/'
        Settings.ModelName = 'test-model'
        Settings.APIKey = 'sk-test'
        return Settings

    def Reply(self, Content, Status=200):
        self.Replies.append((Status, Completion(Content) if Status == 200 else json.dumps({'error': Content})))

    def ImageCount(self, RequestIndex):
        Content = self.Requests[RequestIndex][2]['messages'][0]['content']
        if type(Content) == str:
            return 0
        return len([Part for Part in Content if Part.get('type') == 'image_url'])

    def PromptOf(self, RequestIndex):
        Content = self.Requests[RequestIndex][2]['messages'][0]['content']
        return Content if type(Content) == str else Content[0]['text']

    def Stop(self):
        self.Sleep.stop()
        self.Environment.stop()
        self.Server.shutdown()
        self.Server.server_close()


def MakeScannedPdf(FileName, Lines, AsImage):
    # Writes a one-page PDF. With AsImage = True the text is drawn into a picture (like a
    # scan), so the page has no text layer.
    import pymupdf
    Document = pymupdf.open()
    Page = Document.new_page()
    if AsImage:
        from PIL import Image, ImageDraw
        Picture = Image.new('RGB', (600, 200), 'white')
        Draw = ImageDraw.Draw(Picture)
        for Index, Line in enumerate(Lines):
            Draw.text((10, 10 + 20 * Index), Line, fill='black')
        Buffer = io.BytesIO()
        Picture.save(Buffer, format='PNG')
        Page.insert_image(pymupdf.Rect(50, 50, 550, 250), stream=Buffer.getvalue())
    else:
        for Index, Line in enumerate(Lines):
            Page.insert_text((72, 72 + 16 * Index), Line)
    Document.save(FileName)
    Document.close()
