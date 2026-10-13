# Tests for Kevin's modules: DocumentProcessing.py and GradingFeedback.py

import json
import os
import tempfile
import unittest
from unittest import mock

from TestHelpers import (SampleFolder, SampleDocuments, SampleGrading, MakePoint, MakeQuestion, MakeFeedback,
                         Quiet, FakeAIServer, MakeScannedPdf)
import DocumentProcessing as Processing
import GradingFeedback as Grading
import SQRecords

C = SQRecords.CategoryClearlyCorrect
P = SQRecords.CategoryPossiblyCorrect
I = SQRecords.CategoryIncorrect
N = SQRecords.CategoryNotAssessed
Offline = SQRecords.AISettings()


class TestLabelsAndMarkScheme(unittest.TestCase):

    def test_normalise_label(self):
        Cases = {'1(a)(ii)': '1(a)(ii)', 'Q2b': '2(b)', '3.': '3', '1(A):': '1(a)', '12': '12', '1 (a)': '1(a)',
                 '2.5': '', 'moles': '', '1(a': '', '1()': '', '': ''}
        for Text, Expected in Cases.items():
            self.assertEqual(Processing.NormaliseLabel(Text), Expected, Text)
        self.assertTrue(Processing.IsLabelPrefix('1', '1(a)(ii)'))
        self.assertTrue(Processing.IsLabelPrefix('1(a)', '1(a)'))
        self.assertFalse(Processing.IsLabelPrefix('1', '12(a)'))

    def test_parse_sample_mark_scheme(self):
        Lines = Processing.ReadTextFile(SampleDocuments().MarkSchemeFile)
        self.assertTrue(Processing.IsSQFormat(Lines))
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

    def test_sq_lines_round_trip(self):
        Questions, _ = Quiet(Processing.ParseMarkScheme, Processing.ReadTextFile(SampleDocuments().MarkSchemeFile))
        Again, _ = Quiet(Processing.ParseMarkScheme, Processing.QuestionsToSQLines(Questions, 'x'))
        self.assertEqual([(Q.QuestionID, Q.MarkingRules.MaxMark, Q.MarkingRules.RuleNotes, len(Q.MarkingPoints)) for Q in Again],
                         [(Q.QuestionID, Q.MarkingRules.MaxMark, Q.MarkingRules.RuleNotes, len(Q.MarkingPoints)) for Q in Questions])

    def test_offline_cannot_read_cambridge_mark_scheme(self):
        with tempfile.TemporaryDirectory() as Folder:
            FileName = os.path.join(Folder, 'ms.txt')
            with open(FileName, 'w') as File:
                File.write('Question 1(a) Answer: protons and neutrons in nucleus (1)\n')
            Questions, Printed = Quiet(Processing.ReadMarkScheme, FileName, Offline)
        self.assertEqual(Questions, [])
        self.assertIn('not in the SQ text format', Printed)

    def test_cover_pages(self):
        self.assertTrue(Processing.IsCoverOrRulesPage('Generic Marking Principles\nThese general marking principles must be applied'))
        self.assertTrue(Processing.IsCoverOrRulesPage('9701/22 Paper 2 MARK SCHEME Maximum Mark: 60 Published This mark scheme is published'))
        self.assertFalse(Processing.IsCoverOrRulesPage('Question Answer Marks 1(a) protons and neutrons'))
        self.assertTrue(Processing.IsQuestionPaperCover('INSTRUCTIONS Answer all questions. INFORMATION The total mark is 60.'))
        self.assertTrue(Processing.IsQuestionPaperCover('BLANK PAGE'))


class TestAnswers(unittest.TestCase):

    def test_parse_answers_continuation_and_plain_numbers(self):
        Questions = [MakeQuestion('1', 1, '', [MakePoint('P1', 1, 'x')]), MakeQuestion('2(a)', 1, '', [MakePoint('P1', 1, 'y')])]
        Lines = ['Name: A Student', '1 first line', '2 moles were used', '2(a) answer two', '', 'more of two', '5(c) extra']
        Table, Printed = Quiet(Processing.ParseAnswers, Lines, Questions)
        self.assertEqual(Table[0], ['1', 'first line\n2 moles were used', '', 'high'])   # "2" is not a question in the MS
        self.assertEqual(Table[1], ['2(a)', 'answer two\nmore of two', '', 'high'])
        self.assertEqual(Table[2], ['5(c)', 'extra', '', 'high'])                          # "5(c)" is clearly a label
        self.assertIn('Text before the first question number was ignored', Printed)

    def test_add_answer_row_joins_pages(self):
        Table = []
        Processing.AddAnswerRow(Table, '1', 'first part', '', 'high')
        Processing.AddAnswerRow(Table, '1', 'second part', 'scan.pdf#2', 'medium')
        Processing.AddAnswerRow(Table, '1', 'third', 'photo.jpg', 'high')
        self.assertEqual(Table, [['1', 'first part\nsecond part\nthird', 'scan.pdf#2; photo.jpg', 'medium']])

    def test_process_sample_documents_offline_flags_image_answer(self):
        Processed, Printed = Quiet(Processing.ProcessDocuments, SampleDocuments(), Offline)
        self.assertEqual(len(Processed.Questions), 5)
        self.assertEqual(Processed.UncertainMatches, ['3'])
        self.assertIn('Sample_Answer_Q3.png', Processed.Questions[4].SourceImageRef)
        self.assertIn('Question 3: no typed answer found - it may be in an uploaded image that could not be read.', Printed)
        self.assertIn('can only be read with an AI service that accepts images', Printed)
        self.assertTrue(Processed.Questions[3].AnswerText.startswith('The rate gets faster'))

    def test_unknown_answer_label_is_uncertain(self):
        with tempfile.TemporaryDirectory() as Folder:
            Answers = os.path.join(Folder, 'Answers.txt')
            with open(Answers, 'w') as File:
                File.write('1(a) protons and neutrons\n9(z) stray answer\n')
            Documents = SampleDocuments()
            Documents.AnswerFiles = [Answers]
            Processed, Printed = Quiet(Processing.ProcessDocuments, Documents, Offline)
        self.assertIn('9(z)', Processed.UncertainMatches)
        self.assertIn('1(b)', Processed.UncertainMatches)
        self.assertIn('The answer labelled 9(z) does not match any question in the mark scheme.', Printed)
        self.assertIn('Question 1(b): no answer found in the answer files.', Printed)

    def test_pdf_parts_text_and_scanned(self):
        if Processing.PyMuPDFAvailable == False:
            self.skipTest('pymupdf not installed')
        with tempfile.TemporaryDirectory() as Folder:
            Typed = os.path.join(Folder, 'Typed.pdf')
            Scanned = os.path.join(Folder, 'Scanned.pdf')
            MakeScannedPdf(Typed, ['1(a) protons and neutrons are in the nucleus'], False)
            MakeScannedPdf(Scanned, ['1(a) protons and neutrons'], True)
            self.assertIn('1(a) protons and neutrons are in the nucleus', Processing.ReadDocumentLines(Typed))
            self.assertEqual(Processing.ReadDocumentParts(Typed)[0][2], 'text')
            Parts = Processing.ReadDocumentParts(Scanned)
            self.assertEqual(Parts[0][0], Scanned + '#1')
            self.assertEqual(Parts[0][2], 'image')
            URLs = Processing.LoadSourceImages(Scanned + '#1; ' + os.path.join(SampleFolder, 'Sample_Answer_Q3.png') + '; notes.txt')
            self.assertEqual(len(URLs), 2)
            self.assertTrue(all(URL.startswith('data:image/png;base64,') for URL in URLs))


class TestReadingWithAI(unittest.TestCase):

    def setUp(self):
        self.Server = FakeAIServer()
        self.Settings = self.Server.Settings()
        self.Folder = tempfile.TemporaryDirectory()
        self.Parsed = mock.patch.object(Processing, 'ParsedFolder', os.path.join(self.Folder.name, 'Parsed'))
        self.Parsed.start()

    def tearDown(self):
        self.Parsed.stop()
        self.Folder.cleanup()
        self.Server.Stop()

    def test_add_ai_questions_merges_and_renumbers(self):
        Questions = []
        Processing.AddAIQuestions(Questions, {'questions': [
            {'question': '1 (a)', 'max_mark': 3, 'points': [{'id': 'P1', 'marks': 1, 'requirement': 'M1 method'},
                                                            {'id': 'P2', 'marks': 1, 'requirement': 'A1 answer'}],
             'rules': ['P2 DEPENDS ON P1']},
            {'question': '', 'points': []}, 'not a question',
            {'question': '1(b)', 'points': [{'marks': 2, 'requirement': 'two marks'}, {'requirement': ''}]}]})
        Processing.AddAIQuestions(Questions, {'questions': [
            {'question': '1(a)', 'max_mark': 3, 'points': [{'id': 'P1', 'marks': 'x', 'requirement': 'third point\non two lines'}],
             'rules': ['P1 DEPENDS ON P9']}]})
        self.assertEqual([Q.QuestionID for Q in Questions], ['1(a)', '1(b)'])
        self.assertEqual([(P.PointID, P.Marks, P.Requirement) for P in Questions[0].MarkingPoints],
                         [('P1', 1, 'M1 method'), ('P2', 1, 'A1 answer'), ('P3', 1, 'third point on two lines')])
        self.assertEqual(Questions[0].MarkingRules.RuleNotes, 'P2 DEPENDS ON P1')
        self.assertEqual(Questions[1].MarkingRules.MaxMark, 2)                  # no max_mark: sum of the points

    def test_read_cambridge_mark_scheme_pdf(self):
        if Processing.PyMuPDFAvailable == False:
            self.skipTest('pymupdf not installed')
        import pymupdf
        FileName = os.path.join(self.Folder.name, '9701_s23_ms_22.pdf')
        Document = pymupdf.open()
        Document.new_page().insert_text((72, 72), 'MARK SCHEME Maximum Mark: 60 Published')
        Document.new_page().insert_text((72, 72), 'Question 1(a) protons and neutrons in the nucleus (1) electrons in shells (1) 2')
        Document.save(FileName)
        Document.close()
        self.Server.Reply({'questions': [{'question': '1(a)', 'max_mark': 2, 'points': [
            {'id': 'P1', 'marks': 1, 'requirement': 'protons and neutrons in the nucleus'},
            {'id': 'P2', 'marks': 1, 'requirement': 'electrons in shells'}], 'rules': []}]})
        Questions, Printed = Quiet(Processing.ReadMarkScheme, FileName, self.Settings)
        self.assertEqual(len(self.Server.Requests), 1)                          # the cover page was not sent
        self.assertIn('electrons in shells (1)', self.Server.PromptOf(0))
        self.assertEqual([(Q.QuestionID, Q.MarkingRules.MaxMark, len(Q.MarkingPoints)) for Q in Questions], [('1(a)', 2, 2)])
        Saved = os.path.join(self.Folder.name, 'Parsed', '9701_s23_ms_22_SQ.txt')
        self.assertTrue(os.path.isfile(Saved))
        self.assertIn('P2 [1] electrons in shells', Processing.ReadTextFile(Saved))
        self.assertIn('Skipped', Printed)

    def test_failed_mark_scheme_request_stops(self):
        FileName = os.path.join(self.Folder.name, 'ms.txt')
        with open(FileName, 'w') as File:
            File.write('Question 1(a) Answer: protons and neutrons in nucleus (1)\n')
        self.Server.Replies = [(401, '{}')]
        Questions, Printed = Quiet(Processing.ReadMarkScheme, FileName, self.Settings)
        self.assertEqual(Questions, [])
        self.assertIn('Marking has stopped', Printed)

    def test_handwriting_photo_is_transcribed(self):
        self.Server.Reply({'answers': [{'question': '3', 'answer': 'A covalent bond is a pair of electrons shared between two atoms.',
                                        'confidence': 'high'}]})
        Processed, Printed = Quiet(Processing.ProcessDocuments, SampleDocuments(), self.Settings)
        self.assertEqual(self.Server.ImageCount(0), 1)
        self.assertIn('1(a), 1(b), 2(a), 2(b), 3', self.Server.PromptOf(0))
        self.assertEqual(Processed.UncertainMatches, [])
        self.assertTrue(Processed.Questions[4].AnswerText.startswith('A covalent bond'))
        self.assertTrue(Processed.Questions[4].SourceImageRef.endswith('Sample_Answer_Q3.png'))
        self.assertIn('found (read from handwriting)', Printed)

    def test_low_confidence_and_failed_reading_are_flagged(self):
        self.Server.Reply({'answers': [{'question': '3', 'answer': 'unclear words', 'confidence': 'low'},
                                       {'question': 'Q', 'answer': 'no number', 'confidence': 'medium'}]})
        Processed, Printed = Quiet(Processing.ProcessDocuments, SampleDocuments(), self.Settings)
        self.assertIn('3', Processed.UncertainMatches)
        self.assertIn('?', Processed.UncertainMatches)
        self.assertIn('could not be read with confidence', Printed)
        self.assertIn('has no question number', Printed)
        self.Server.Replies = [(400, '{}')]
        Processed, Printed = Quiet(Processing.ProcessDocuments, SampleDocuments(), self.Settings)
        self.assertEqual(Processed.UncertainMatches, ['3'])
        self.assertIn('the model may not accept images', Printed)

    def test_question_texts_from_question_paper(self):
        Questions = [MakeQuestion('1(a)', 1, '', [MakePoint('P1', 1, 'x')]), MakeQuestion('1(b)', 1, '', [MakePoint('P1', 1, 'y')]),
                     MakeQuestion('2', 1, '', [MakePoint('P1', 1, 'z')])]
        FileName = os.path.join(self.Folder.name, 'qp.txt')
        with open(FileName, 'w') as File:
            File.write('1 Atoms contain protons, neutrons and electrons.\n(a) State where the protons are.\n(b) Define isotopes.\n')
        self.Server.Reply({'questions': [{'question': '1', 'text': 'Atoms contain protons, neutrons and electrons.'},
                                         {'question': '1(a)', 'text': 'State where the protons are.'},
                                         {'question': '1(b)', 'text': 'Define isotopes.'}]})
        _, Printed = Quiet(Processing.ReadQuestionTexts, FileName, Questions, self.Settings)
        self.assertEqual(Questions[0].QuestionText, 'Atoms contain protons, neutrons and electrons.\nState where the protons are.')
        self.assertEqual(Questions[1].QuestionText, 'Atoms contain protons, neutrons and electrons.\nDefine isotopes.')
        self.assertEqual(Questions[2].QuestionText, '')
        self.assertIn('Question text found for 2 of 3 questions.', Printed)
        _, Printed = Quiet(Processing.ReadQuestionTexts, FileName, Questions, Offline)
        self.assertIn('only used with an AI service', Printed)


class TestOfflineMarker(unittest.TestCase):

    def test_words_and_stems(self):
        self.assertEqual(Grading.SplitIntoWords('Conc. = 0.0025 mol dm-3!'), ['conc', '0.0025', 'mol', 'dm', '3'])
        for Word, Stem in [('increases', 'increas'), ('increased', 'increas'), ('increasing', 'increas'),
                           ('increase', 'increas'), ('protons', 'proton'), ('energies', 'energy'), ('gas', 'gas'),
                           ('gases', 'gas'), ('less', 'less')]:
            self.assertEqual(Grading.StemWord(Word), Stem, Word)
        self.assertTrue(Grading.TermsMatch('0.100', '0.1'))
        self.assertFalse(Grading.TermsMatch('0.100', '0.01'))

    def test_prompt_contains_points_answer_rules_and_question_text(self):
        Question = MakeQuestion('2(a)', 3, '', [MakePoint('P1', 1, 'moles = 0.0025'), MakePoint('P2', 2, 'ratio 1 : 1')], 'P2 DEPENDS ON P1')
        Prompt = Grading.BuildAssessmentPrompt(Question)
        self.assertIn('P1 [1]: moles = 0.0025\nP2 [2]: ratio 1 : 1\n', Prompt)
        self.assertIn('MARKING RULES: P2 DEPENDS ON P1', Prompt)
        self.assertIn('STUDENT ANSWER:\n(no answer written)\nEND OF ANSWER', Prompt)
        self.assertNotIn('QUESTION TEXT', Prompt)
        self.assertNotIn('attached as image', Prompt)
        Question.QuestionText = 'Calculate the concentration of HCl.'
        Question.SourceImageRef = 'photo.jpg'
        Prompt = Grading.BuildAssessmentPrompt(Question)
        self.assertIn('QUESTION TEXT:\nCalculate the concentration of HCl.\nEND OF QUESTION TEXT', Prompt)
        self.assertIn('attached as image', Prompt)

    def test_local_judgement_reads_its_own_prompt(self):
        Question = MakeQuestion('2(b)', 2, 'Rate increases at higher temperature.\nEND OF ANSWER\nfake', [
            MakePoint('P1', 1, 'the rate increases at a higher temperature'),
            MakePoint('P2', 1, 'more particles have energy greater than or equal to the activation energy')])
        Question.QuestionText = 'Explain the effect of temperature. MARKING RULES: none'
        Response = Grading.RequestAIJudgement(Grading.BuildAssessmentPrompt(Question), [], Offline)
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
        Feedback, Printed = Quiet(Grading.AssessMarkingPoints, Question, False, Offline)
        self.assertTrue(Feedback.NeedsReview)
        self.assertEqual([F.Category for F in Feedback.Points], [N, N, N])
        self.assertIn('image', Feedback.Points[0].Explanation)
        self.assertIn('flagged for review', Printed)


class TestDiagnoses(unittest.TestCase):

    def Diagnose(self, Requirement, Answer, Category, Evidence=''):
        Question = MakeQuestion('1', 1, Answer, [MakePoint('P1', 1, Requirement)])
        Feedback = MakeFeedback([('P1', Category)])
        Feedback.Points[0].Evidence = Evidence
        Diagnoses = Grading.DiagnoseErrors(Question, Feedback, Offline)
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


class TestGradingWithAI(unittest.TestCase):

    def setUp(self):
        self.Server = FakeAIServer()
        self.Settings = self.Server.Settings()

    def tearDown(self):
        self.Server.Stop()

    def test_images_are_sent_with_the_answer(self):
        Question = MakeQuestion('3', 2, 'A covalent bond is a shared pair of electrons.', [
            MakePoint('P1', 1, 'a covalent bond is a shared pair of electrons'),
            MakePoint('P2', 1, 'electrostatic attraction between the shared pair and both nuclei')])
        Question.SourceImageRef = os.path.join(SampleFolder, 'Sample_Answer_Q3.png')
        self.Server.Reply({'points': [{'point_id': 'P1', 'category': 'Clearly correct'},
                                      {'point_id': 'P2', 'category': 'Possibly correct'}], 'outside_ms': []})
        Feedback, _ = Quiet(Grading.CompareWithMarkingPoints, Question, self.Settings)
        self.assertEqual(self.Server.ImageCount(0), 1)
        self.assertIn('attached as image', self.Server.PromptOf(0))
        self.assertEqual([F.Category for F in Feedback.Points], [C, P])

    def test_failed_ai_question_is_flagged_not_marked_wrong(self):
        self.Server.Replies = [(401, '{}')]
        Question = MakeQuestion('1(a)', 1, 'answer', [MakePoint('P1', 1, 'answer')])
        Feedback, Printed = Quiet(Grading.CompareWithMarkingPoints, Question, self.Settings)
        self.assertEqual(Feedback.Points[0].Category, N)
        self.assertTrue(Feedback.NeedsReview)
        self.assertIn('AI request for question 1(a) failed', Printed)

    def test_ai_diagnosis_used_when_available(self):
        Question = MakeQuestion('2(b)', 2, 'The rate gets faster.', [MakePoint('P1', 1, 'rate increases'), MakePoint('P2', 1, 'more particles')])
        Feedback = MakeFeedback([('P1', C), ('P2', I)])
        self.Server.Reply({'diagnoses': [{'point_id': 'P2', 'error_type': 'Missing information', 'evidence': 'The rate gets faster.',
                                          'explanation': 'Particle energies are not mentioned.'}]})
        Diagnoses = Grading.DiagnoseErrors(Question, Feedback, self.Settings)
        self.assertEqual([(D.PointID, D.ErrorType) for D in Diagnoses], [('P2', 'Missing information')])
        self.assertIn('P2: more particles (judged: Incorrect)', self.Server.PromptOf(0))

    def test_whole_paper_with_fake_ai(self):
        Processed, _ = Quiet(Processing.ProcessDocuments, SampleDocuments(), Offline)
        Points = {'1(a)': ['P1', 'P2'], '1(b)': ['P1'], '2(a)': ['P1', 'P2', 'P3'], '2(b)': ['P1', 'P2']}
        for QuestionID in ['1(a)', '1(b)', '2(a)', '2(b)']:
            self.Server.Reply({'points': [{'point_id': ID, 'category': 'Clearly correct', 'explanation': 'ok', 'evidence': ''}
                                          for ID in Points[QuestionID]], 'outside_ms': []})
        Result, _ = Quiet(Grading.GradePaper, Processed, self.Settings)
        self.assertEqual(Result.TotalMark, 8)                     # question 3 is flagged, not sent to the AI
        self.assertEqual(Result.MaxTotal, 10)
        self.assertEqual(len(self.Server.Requests), 4)


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
