# Tests for Kevin's modules: DocumentProcessing.py and GradingFeedback.py

import http.server
import json
import os
import tempfile
import threading
import unittest
from unittest import mock

from TestHelpers import (SampleDocuments, SampleGrading, MakePoint, MakeQuestion, MakeFeedback,
                         Quiet)
import DocumentProcessing as Processing
import GradingFeedback as Grading
import SQRecords

C = SQRecords.CategoryClearlyCorrect
P = SQRecords.CategoryPossiblyCorrect
I = SQRecords.CategoryIncorrect
N = SQRecords.CategoryNotAssessed


class TestLabelsAndMarkScheme(unittest.TestCase):

    def test_normalise_label(self):
        Cases = {'1(a)(ii)': '1(a)(ii)', 'Q2b': '2(b)', '3.': '3', '1(A):': '1(a)', '12': '12',
                 '2.5': '', 'moles': '', '1(a': '', '1()': '', '': ''}
        for Text, Expected in Cases.items():
            self.assertEqual(Processing.NormaliseLabel(Text), Expected, Text)

    def test_parse_sample_mark_scheme(self):
        Lines = Processing.ReadTextFile(SampleDocuments().MarkSchemeFile)
        Questions, _ = Quiet(Processing.ParseMarkScheme, Lines)
        self.assertEqual([Q.QuestionID for Q in Questions], ['1(a)', '1(b)', '2(a)', '2(b)', '3'])
        self.assertEqual(Questions[2].MarkingRules.MaxMark, 3)
        self.assertEqual(Questions[2].MarkingRules.RuleNotes, 'P3 DEPENDS ON P2')
        self.assertEqual(Questions[0].MarkingPoints[1].Requirement, 'electrons are in shells / energy levels around the nucleus')

    def test_bad_mark_scheme_lines(self):
        Lines = ['P1 [1] before any question', 'QUESTION 4 two', 'QUESTION 5 [2]', 'P1 [1] first point',
                 'continued here', 'P1 [1] repeated id', 'QUESTION 5 [1]', 'QUESTION 6 [1]', 'nonsense line']
        Questions, Printed = Quiet(Processing.ParseMarkScheme, Lines)
        self.assertEqual([Q.QuestionID for Q in Questions], ['5'])
        self.assertEqual(Questions[0].MarkingPoints[0].Requirement, 'first point continued here')
        self.assertIn('line 1 ignored: it comes before the first QUESTION line', Printed)
        self.assertIn('line 2 ignored: write QUESTION <number> [<marks>]', Printed)
        self.assertIn('point P1 appears twice', Printed)
        self.assertIn('question 5 appears twice', Printed)
        self.assertIn('Question 6 has no marking points', Printed)
        self.assertIn('add up to 1 but the question is worth 2', Printed)

    def test_parse_answers_continuation_and_plain_numbers(self):
        Questions = [MakeQuestion('1', 1, '', [MakePoint('P1', 1, 'x')]), MakeQuestion('2(a)', 1, '', [MakePoint('P1', 1, 'y')])]
        Lines = ['Name: A Student', '1 first line', '2 moles were used', '2(a) answer two', '', 'more of two', '5(c) extra']
        Table, Printed = Quiet(Processing.ParseAnswers, Lines, Questions)
        self.assertEqual(Table[0], ['1', 'first line\n2 moles were used'])   # "2" is not a question in the MS...
        self.assertEqual(Table[1], ['2(a)', 'answer two\nmore of two'])
        self.assertEqual(Table[2], ['5(c)', 'extra'])           # ...but "5(c)" is clearly a label
        self.assertIn('Text before the first question number was ignored', Printed)

    def test_process_sample_documents_flags_image_answer(self):
        Processed, Printed = Quiet(Processing.ProcessDocuments, SampleDocuments())
        self.assertEqual(len(Processed.Questions), 5)
        self.assertEqual(Processed.UncertainMatches, ['3'])
        self.assertIn('Sample_Answer_Q3.png', Processed.Questions[4].SourceImageRef)
        self.assertIn('Question 3: no typed answer found - it may be in an uploaded image.', Printed)
        self.assertTrue(Processed.Questions[3].AnswerText.startswith('The rate gets faster'))

    def test_unknown_answer_label_is_uncertain(self):
        with tempfile.TemporaryDirectory() as Folder:
            Answers = os.path.join(Folder, 'Answers.txt')
            with open(Answers, 'w') as File:
                File.write('1(a) protons and neutrons\n9(z) stray answer\n')
            Documents = SampleDocuments()
            Documents.AnswerFiles = [Answers]
            Processed, Printed = Quiet(Processing.ProcessDocuments, Documents)
        self.assertIn('9(z)', Processed.UncertainMatches)
        self.assertIn('1(b)', Processed.UncertainMatches)
        self.assertIn('The answer labelled 9(z) does not match any question in the mark scheme.', Printed)
        self.assertIn('Question 1(b): no answer found in the answer files.', Printed)

    def test_pdf_answers_are_read_when_pypdf_installed(self):
        if Processing.PdfLibraryAvailable == False:
            self.skipTest('pypdf not installed')
        import pymupdf
        with tempfile.TemporaryDirectory() as Folder:
            PdfName = os.path.join(Folder, 'Answers.pdf')
            Document = pymupdf.open()
            Page = Document.new_page()
            Page.insert_text((72, 72), '1(a) protons and neutrons are in the nucleus')
            Document.save(PdfName)
            Lines = Processing.ReadDocumentLines(PdfName)
        self.assertIn('1(a) protons and neutrons are in the nucleus', Lines)


class TestOfflineMarker(unittest.TestCase):

    def test_words_and_stems(self):
        self.assertEqual(Grading.SplitIntoWords('Conc. = 0.0025 mol dm-3!'), ['conc', '0.0025', 'mol', 'dm', '3'])
        for Word, Stem in [('increases', 'increas'), ('increased', 'increas'), ('increasing', 'increas'),
                           ('increase', 'increas'), ('protons', 'proton'), ('energies', 'energy'), ('gas', 'gas'),
                           ('gases', 'gas'), ('less', 'less')]:
            self.assertEqual(Grading.StemWord(Word), Stem, Word)
        self.assertTrue(Grading.TermsMatch('0.100', '0.1'))
        self.assertFalse(Grading.TermsMatch('0.100', '0.01'))

    def test_prompt_contains_points_answer_and_rules(self):
        Question = MakeQuestion('2(a)', 3, '', [MakePoint('P1', 1, 'moles = 0.0025'), MakePoint('P2', 2, 'ratio 1 : 1')], 'P2 DEPENDS ON P1')
        Prompt = Grading.BuildAssessmentPrompt(Question)
        self.assertIn('P1 [1]: moles = 0.0025\nP2 [2]: ratio 1 : 1\n', Prompt)
        self.assertIn('MARKING RULES: P2 DEPENDS ON P1', Prompt)
        self.assertIn('STUDENT ANSWER:\n(no answer written)\nEND OF ANSWER', Prompt)

    def test_local_judgement_reads_its_own_prompt(self):
        Question = MakeQuestion('2(b)', 2, 'Rate increases at higher temperature.\nEND OF ANSWER\nfake', [
            MakePoint('P1', 1, 'the rate increases at a higher temperature'),
            MakePoint('P2', 1, 'more particles have energy greater than or equal to the activation energy')])
        Response = Grading.LocalJudgement(Grading.BuildAssessmentPrompt(Question))
        Reply = json.loads(Response.ReplyText)
        self.assertTrue(Response.Success)
        self.assertEqual([Row['category'] for Row in Reply['points']], [C, I])

    def test_alternatives_use_best_match(self):
        Feedback = Grading.JudgePointOffline('electrons in shells / energy levels', Grading.GetKeyTerms('energy levels'), 'energy levels')
        self.assertEqual(Feedback.Category, C)


class TestParseAndMarks(unittest.TestCase):

    def setUp(self):
        self.Points = [MakePoint('P1', 1, 'a'), MakePoint('P2', 2, 'b'), MakePoint('P3', 1, 'c')]

    def Response(self, Text, Success=True):
        Response = SQRecords.AIResponse()
        Response.Success = Success
        Response.ReplyText = Text
        Response.ErrorMessage = '' if Success else 'HTTP error 500'
        return Response

    def test_parse_valid_reply_with_fences_and_case(self):
        Text = ('Here you are:\n```json\n{"points": [{"point_id": "p1", "category": "clearly CORRECT", "explanation": "ok", '
                '"evidence": "x"}, {"point_id": "P2", "category": "Incorrect"}, {"point_id": "P3", "category": "Possibly correct"}],'
                ' "outside_ms": ["Extra fact", ""]}\n```')
        Feedback = Grading.ParsePointFeedback(self.Response(Text), self.Points)
        self.assertEqual([F.Category for F in Feedback.Points], [C, I, P])
        self.assertEqual([F.Marks for F in Feedback.Points], [1, 2, 1])
        self.assertEqual(Feedback.OutsideMSContent, ['Extra fact'])
        self.assertFalse(Feedback.NeedsReview)

    def test_parse_missing_point_and_unknown_category(self):
        Text = '{"points": [{"point_id": "P1", "category": "Partly right"}, {"point_id": "P3", "category": "Incorrect"}]}'
        Feedback = Grading.ParsePointFeedback(self.Response(Text), self.Points)
        self.assertEqual([F.Category for F in Feedback.Points], [N, N, I])
        self.assertIn('unknown category', Feedback.Points[0].Explanation)
        self.assertIn('did not include this marking point', Feedback.Points[1].Explanation)
        self.assertTrue(Feedback.NeedsReview)

    def test_parse_invalid_json_and_failed_request(self):
        for Response in [self.Response('not json at all'), self.Response('{"points": [', True), self.Response('', False)]:
            Feedback = Grading.ParsePointFeedback(Response, self.Points)
            self.assertEqual([F.Category for F in Feedback.Points], [N, N, N])
            self.assertTrue(Feedback.NeedsReview)

    def test_estimated_mark_rules(self):
        Rules = SQRecords.MarkRules()
        Rules.MaxMark = 3
        Feedback = MakeFeedback([('P1', C), ('P2', C), ('P3', P)], [1, 2, 1])
        self.assertEqual(Grading.CalculateEstimatedMark(Feedback, Rules), 3)
        Rules.MaxMark = 2                                         # boundary: capped at the maximum
        self.assertEqual(Grading.CalculateEstimatedMark(Feedback, Rules), 2)
        Rules.MaxMark = 4
        Rules.RuleNotes = 'P2 DEPENDS ON P3'                     # P3 only possibly correct
        self.assertEqual(Grading.CalculateEstimatedMark(Feedback, Rules), 1)
        Rules.RuleNotes = 'P1 DEPENDS ON P2; P2 DEPENDS ON P1'   # circular rule must not loop for ever
        self.assertEqual(Grading.CalculateEstimatedMark(Feedback, Rules), 0)
        Feedback = MakeFeedback([('P1', C), ('P2', C), ('P3', C)])
        Rules.RuleNotes = 'P3 DEPENDS ON P2; P2 DEPENDS ON P1'   # chain of dependencies
        self.assertEqual(Grading.CalculateEstimatedMark(Feedback, Rules), 3)

    def test_assess_selects_flag_for_review(self):
        Question = MakeQuestion('3', 2, '', self.Points)
        Question.SourceImageRef = 'photo.png'
        Feedback, Printed = Quiet(Grading.AssessMarkingPoints, Question, False, SQRecords.AISettings())
        self.assertTrue(Feedback.NeedsReview)
        self.assertEqual([F.Category for F in Feedback.Points], [N, N, N])
        self.assertIn('image', Feedback.Points[0].Explanation)
        self.assertIn('flagged for review', Printed)


class TestDiagnoses(unittest.TestCase):

    def Diagnose(self, Requirement, Answer, Category, Evidence=''):
        Question = MakeQuestion('1', 1, Answer, [MakePoint('P1', 1, Requirement)])
        Feedback = MakeFeedback([('P1', Category)])
        Feedback.Points[0].Evidence = Evidence
        Diagnoses = Grading.DiagnoseErrors(Question, Feedback, SQRecords.AISettings())
        return Diagnoses[0].ErrorType if Diagnoses else ''

    def test_offline_rules(self):
        self.assertEqual(self.Diagnose('rate increases', '', I), 'Missing information')
        self.assertEqual(self.Diagnose('concentration = 0.100 mol dm-3', 'the concentration doubles', I), 'Missing information')
        self.assertEqual(self.Diagnose('concentration = 0.100 mol dm-3', 'concentration = 0.1', P), 'Incorrect units')
        self.assertEqual(self.Diagnose('concentration = 0.100 mol dm-3', 'concentration = 0.2 mol', I), 'Calculation mistake')
        self.assertEqual(self.Diagnose('shared pair of electrons', 'electrons are shared', P), 'Inaccurate terminology')
        self.assertEqual(self.Diagnose('rate increases at higher temperature', 'the rate changes', I, 'rate'), 'Incomplete explanation')
        self.assertEqual(self.Diagnose('rate increases at higher temperature', 'catalysts speed it up', I), 'Conceptual error')
        self.assertEqual(self.Diagnose('rate increases', 'rate increases', C), '')      # nothing lost
        self.assertEqual(self.Diagnose('rate increases', '', N), '')                    # needs review instead

    def test_ai_diagnoses_are_validated(self):
        Text = ('{"diagnoses": [{"point_id": "P1", "error_type": "incomplete explanation", "evidence": "e", "explanation": "x"},'
                ' {"point_id": "P9", "error_type": "Conceptual error"}, {"point_id": "P1", "error_type": "Bad type"}]}')
        Diagnoses = Grading.ParseDiagnoses(Text, ['P1'])
        self.assertEqual(len(Diagnoses), 1)
        self.assertEqual(Diagnoses[0].ErrorType, 'Incomplete explanation')


class FakeAIHandler(http.server.BaseHTTPRequestHandler):
    Replies = []          # list of (status, body) returned in order
    Requests = []

    def do_POST(self):
        Body = self.rfile.read(int(self.headers['Content-Length']))
        FakeAIHandler.Requests.append((self.path, self.headers.get('Authorization'), json.loads(Body)))
        Status, Text = FakeAIHandler.Replies.pop(0)
        self.send_response(Status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(Text.encode('utf-8'))

    def log_message(self, *Arguments):
        pass


class TestRequestAIJudgement(unittest.TestCase):

    def setUp(self):
        self.Server = http.server.HTTPServer(('127.0.0.1', 0), FakeAIHandler)
        threading.Thread(target=self.Server.serve_forever, daemon=True).start()
        self.Settings = SQRecords.AISettings()
        self.Settings.Provider = 'http://127.0.0.1:' + str(self.Server.server_port) + '/v1/'
        self.Settings.ModelName = 'test-model'
        self.Settings.APIKey = 'sk-test'
        FakeAIHandler.Requests = []
        self.Environment = mock.patch.dict(os.environ, {'no_proxy': '127.0.0.1,localhost', 'NO_PROXY': '127.0.0.1,localhost'})
        self.Environment.start()
        self.Sleep = mock.patch.object(Grading.time, 'sleep')
        self.Sleep.start()

    def tearDown(self):
        self.Sleep.stop()
        self.Environment.stop()
        self.Server.shutdown()
        self.Server.server_close()

    def Completion(self, Content):
        return json.dumps({'choices': [{'message': {'role': 'assistant', 'content': Content}}]})

    def test_success_request_shape(self):
        FakeAIHandler.Replies = [(200, self.Completion('{"points": []}'))]
        Response = Grading.RequestAIJudgement('PROMPT', self.Settings)
        self.assertTrue(Response.Success)
        self.assertEqual(Response.ReplyText, '{"points": []}')
        Path, Authorisation, Body = FakeAIHandler.Requests[0]
        self.assertEqual(Path, '/v1/chat/completions')
        self.assertEqual(Authorisation, 'Bearer sk-test')
        self.assertEqual(Body['model'], 'test-model')
        self.assertEqual(Body['messages'][0]['content'], 'PROMPT')

    def test_retry_after_server_error(self):
        FakeAIHandler.Replies = [(503, '{}'), (429, '{}'), (200, self.Completion('{"points": []}'))]
        Response = Grading.RequestAIJudgement('PROMPT', self.Settings)
        self.assertTrue(Response.Success)
        self.assertEqual(len(FakeAIHandler.Requests), 3)

    def test_no_retry_for_bad_key_and_give_up_after_three(self):
        FakeAIHandler.Replies = [(401, '{"error": "bad key"}')]
        Response = Grading.RequestAIJudgement('PROMPT', self.Settings)
        self.assertFalse(Response.Success)
        self.assertIn('HTTP error 401', Response.ErrorMessage)
        self.assertEqual(len(FakeAIHandler.Requests), 1)
        FakeAIHandler.Replies = [(500, '{}'), (500, '{}'), (500, '{}')]
        Response = Grading.RequestAIJudgement('PROMPT', self.Settings)
        self.assertFalse(Response.Success)
        self.assertEqual(len(FakeAIHandler.Requests), 4)

    def test_reply_without_content(self):
        FakeAIHandler.Replies = [(200, '{"choices": []}')]
        Response = Grading.RequestAIJudgement('PROMPT', self.Settings)
        self.assertFalse(Response.Success)
        self.assertIn('no content', Response.ErrorMessage)

    def test_unknown_provider_and_missing_key(self):
        self.Settings.Provider = 'NoSuchAI'
        self.assertIn('Unknown AI provider', Grading.RequestAIJudgement('P', self.Settings).ErrorMessage)
        self.Settings.Provider = 'OpenAI'
        self.Settings.APIKey = ''
        self.assertIn('missing', Grading.RequestAIJudgement('P', self.Settings).ErrorMessage)

    def test_failed_ai_question_is_flagged_not_marked_wrong(self):
        FakeAIHandler.Replies = [(401, '{}')]
        Question = MakeQuestion('1(a)', 1, 'answer', [MakePoint('P1', 1, 'answer')])
        Feedback, Printed = Quiet(Grading.CompareWithMarkingPoints, Question, self.Settings)
        self.assertEqual(Feedback.Points[0].Category, N)
        self.assertTrue(Feedback.NeedsReview)
        self.assertIn('AI request for question 1(a) failed', Printed)

    def test_whole_paper_with_fake_ai(self):
        Processed, _ = Quiet(Processing.ProcessDocuments, SampleDocuments())
        Points = {'1(a)': ['P1', 'P2'], '1(b)': ['P1'], '2(a)': ['P1', 'P2', 'P3'], '2(b)': ['P1', 'P2']}
        for QuestionID in ['1(a)', '1(b)', '2(a)', '2(b)']:
            Reply = {'points': [{'point_id': ID, 'category': 'Clearly correct', 'explanation': 'ok', 'evidence': ''}
                                for ID in Points[QuestionID]], 'outside_ms': []}
            FakeAIHandler.Replies.append((200, self.Completion(json.dumps(Reply))))
        Result, _ = Quiet(Grading.GradePaper, Processed, self.Settings)
        self.assertEqual(Result.TotalMark, 8)                     # question 3 is flagged, not sent to the AI
        self.assertEqual(Result.MaxTotal, 10)
        self.assertEqual(len(FakeAIHandler.Requests), 4)


class TestGradePaperOffline(unittest.TestCase):

    def test_sample_paper(self):
        Result = SampleGrading()
        self.assertEqual([R.EstimatedMark for R in Result.QuestionResults], [1, 1, 1, 0, 0])
        self.assertEqual((Result.TotalMark, Result.MaxTotal), (3, 10))
        self.assertTrue(Result.QuestionResults[4].Feedback.NeedsReview)
        self.assertEqual(len(Result.QuestionResults[3].Feedback.OutsideMSContent), 1)
        self.assertEqual(Result.QuestionResults[2].Feedback.Points[2].Category, C)   # P3 correct but depends on P2


if __name__ == '__main__':
    unittest.main()
