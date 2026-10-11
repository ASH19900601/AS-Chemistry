# Tests for Caroline's modules: CorrectionRegrading.py and LearningRecords.py

import json
import os
import tempfile
import unittest
from unittest import mock

from TestHelpers import SampleFolder, SampleGrading, MakeFeedback, RunWithInput, Quiet
import CorrectionRegrading as Correction
import LearningRecords as Records
import SQRecords

C = SQRecords.CategoryClearlyCorrect
P = SQRecords.CategoryPossiblyCorrect
I = SQRecords.CategoryIncorrect
N = SQRecords.CategoryNotAssessed
GoodAnswer = ('The rate of reaction increases at a higher temperature because more particles have energy '
              'greater than or equal to the activation energy.')


class TestCorrection(unittest.TestCase):

    def setUp(self):
        self.Grading = SampleGrading()

    def test_find_question_index(self):
        self.assertEqual(Correction.FindQuestionIndex(self.Grading, '2(B) '), 3)
        self.assertEqual(Correction.FindQuestionIndex(self.Grading, '7'), -1)

    def test_compare_feedback(self):
        Old = MakeFeedback([('P1', I), ('P2', P)])
        New = MakeFeedback([('P1', C), ('P2', P)])
        self.assertEqual(Correction.CompareFeedback(Old, New), ['P1: Incorrect -> Clearly correct'])
        self.assertEqual(Correction.CompareFeedback(Old, Old), ['No change in the marking-point feedback.'])

    def test_regrade_uses_original_criteria_and_keeps_original(self):
        Original = self.Grading.QuestionResults[3]
        Result = Correction.RegradeQuestion(self.Grading, 3, GoodAnswer, '', SQRecords.AISettings())
        self.assertTrue(Result.HasCorrection)
        self.assertEqual([A.AttemptNo for A in Result.Attempts], [1, 2])
        self.assertEqual(Result.Attempts[0].EstimatedMark, 0)
        self.assertEqual(Result.Attempts[1].EstimatedMark, 2)
        self.assertEqual(Result.MarkChange, 2)
        self.assertEqual(Result.FeedbackChanges, ['P1: Incorrect -> Clearly correct', 'P2: Incorrect -> Clearly correct',
                                                  'Content outside the mark scheme: 1 item(s) -> 0 item(s)'])
        self.assertTrue(Original.Question.AnswerText.startswith('The rate gets faster'))   # original not changed
        self.assertIsNot(Result.Attempts[1].Feedback, Original.Feedback)

    def test_image_correction_is_flagged(self):
        Result, _ = Quiet(Correction.RegradeQuestion, self.Grading, 3, '', os.path.join(SampleFolder, 'Sample_Answer_Q3.png'), SQRecords.AISettings())
        self.assertTrue(Result.Attempts[1].Feedback.NeedsReview)
        self.assertEqual(Result.MarkChange, 0)

    def test_no_correction(self):
        Result, Printed = RunWithInput(Correction.CorrectAndRegrade, ['maybe', 'N'], self.Grading, SQRecords.AISettings())
        self.assertFalse(Result.HasCorrection)
        self.assertIn('Please type Y or N.', Printed)
        self.assertIn('No correction submitted.', Printed)

    def test_typed_correction_after_invalid_question(self):
        Inputs = ['Y', '7', '2(b)', '4', '1', GoodAnswer, '']
        Result, Printed = RunWithInput(Correction.CorrectAndRegrade, Inputs, self.Grading, SQRecords.AISettings())
        self.assertIn('Question 7 is not in this paper.', Printed)
        self.assertIn('Estimated mark: 0 / 2 -> 2 / 2', Printed)
        self.assertIn('Well done: the corrected answer gains 2 more mark(s).', Printed)
        self.assertEqual(Result.QuestionID, '2(b)')

    def test_file_correction_and_empty_correction(self):
        Inputs = ['Y', '2(b)', '2', '"' + os.path.join(SampleFolder, 'Sample_Corrected_2b.txt') + '"']
        Result, _ = RunWithInput(Correction.CorrectAndRegrade, Inputs, self.Grading, SQRecords.AISettings())
        self.assertEqual(Result.MarkChange, 2)
        Result, Printed = RunWithInput(Correction.CorrectAndRegrade, ['Y', '2(b)', '1', ''], self.Grading, SQRecords.AISettings())
        self.assertFalse(Result.HasCorrection)
        self.assertIn('The corrected answer is empty', Printed)


class TestLearningRecords(unittest.TestCase):

    def setUp(self):
        self.Folder = tempfile.TemporaryDirectory()
        self.DatabaseName = os.path.join(self.Folder.name, 'LearningRecords.json')
        self.Patch = mock.patch.object(Records, 'DatabasePath', self.DatabaseName)
        self.Patch.start()
        self.Grading = SampleGrading()

    def tearDown(self):
        self.Patch.stop()
        self.Folder.cleanup()

    def Regrade(self):
        return Correction.RegradeQuestion(self.Grading, 3, GoodAnswer, '', SQRecords.AISettings())

    def test_topic_tags(self):
        Tags = [Records.FindTopicTags(R.Question) for R in self.Grading.QuestionResults]
        self.assertEqual(Tags[0], ['Atomic structure'])
        self.assertEqual(Tags[2], ['Moles and stoichiometry'])
        self.assertEqual(Tags[3], ['Reaction kinetics'])
        self.assertEqual(Tags[4], ['Atomic structure', 'Chemical bonding'])

    def test_sort_counts(self):
        Names = ['A', 'B', 'C', 'D']
        Counts = [1, 3, 0, 3]
        Records.SortCounts(Names, Counts)
        self.assertEqual(Counts, [3, 3, 1, 0])
        self.assertEqual(Names, ['B', 'D', 'A', 'C'])

    def test_add_results_and_progress(self):
        Database = Records.LearningDatabase()
        Records.AddGradingResult(Database, self.Grading)
        Records.AddRegradeResult(Database, self.Grading, self.Regrade())
        self.assertEqual(len(Database.Papers), 1)
        self.assertEqual(len(Database.Attempts), 6)                      # 5 originals + 1 correction
        self.assertEqual([(M.QuestionID, M.Status) for M in Database.Mistakes],
                         [('1(a)', 'Not corrected'), ('2(a)', 'Not corrected'), ('2(b)', 'Corrected'), ('3', 'Needs review')])
        Progress = Records.CalculateProgress(Database)
        self.assertEqual(Progress.PaperScores, [30])
        self.assertEqual(Progress.CorrectedCount, 1)
        self.assertEqual(Progress.CommonErrorTypes[0], 'Incomplete explanation (2)')
        self.assertEqual(Records.NextAttemptNo(Database, '9701/22/M/J/23', '2(b)'), 3)

    def test_partly_corrected_status(self):
        Database = Records.LearningDatabase()
        Records.AddGradingResult(Database, self.Grading)
        Result = Correction.RegradeQuestion(self.Grading, 3, 'The rate of reaction increases at a higher temperature.', '', SQRecords.AISettings())
        Records.AddRegradeResult(Database, self.Grading, Result)
        self.assertEqual(Database.Mistakes[2].Status, SQRecords.StatusPartlyCorrected)

    def test_save_and_reopen(self):
        Learning, _ = RunWithInput(Records.UpdateLearningRecords, ['6'], self.Grading, self.Regrade())
        self.assertTrue(Learning.SaveSuccess)
        self.assertEqual(len(Learning.AttemptHistories), 6)
        # "close and reopen the application": a new call reads the saved file
        Learning, Printed = RunWithInput(Records.UpdateLearningRecords, ['6'], SQRecords.GradingResult(), SQRecords.RegradeResult())
        self.assertEqual(len(Learning.MistakeEntries), 4)
        self.assertEqual(Learning.Progress.PaperScores, [30])
        self.assertIn('Original paper results (corrections not included):', Printed)
        self.assertIn('Correction attempts saved: 1', Printed)
        with open(self.DatabaseName, encoding='utf-8') as File:
            Data = json.load(File)
        self.assertEqual(Data['Attempts'][5]['AttemptNo'], 2)
        self.assertEqual(Data['Attempts'][5]['Feedback']['Points'][0]['Category'], C)

    def test_filter_notebook(self):
        Database = Records.LearningDatabase()
        Records.AddGradingResult(Database, self.Grading)
        self.assertEqual([M.QuestionID for M in Records.FilterMistakes(Database, 1, 'Atomic structure')], ['1(a)', '3'])
        self.assertEqual([M.QuestionID for M in Records.FilterMistakes(Database, 3, 'Needs review')], ['3'])
        self.assertEqual(len(Records.FilterMistakes(Database, 0, 'Chemistry (9701)')), 4)
        self.assertEqual(len(Records.FilterMistakes(Database, 2, '9702/22/M/J/23')), 0)
        self.assertEqual(Records.CollectFilterValues(Database, 3), ['Not corrected', 'Needs review'])
        _, Printed = RunWithInput(Records.ReviewMistakeNotebook, ['2', '1', '6'], Database)
        self.assertIn('question 1(a)  [Not corrected]', Printed)
        self.assertIn('question 3  [Needs review]', Printed)
        self.assertNotIn('question 2(a)', Printed)

    def test_damaged_file_is_kept(self):
        with open(self.DatabaseName, 'w', encoding='utf-8') as File:
            File.write('{ this is not JSON')
        Database, Printed = Quiet(Records.LoadDatabase, self.DatabaseName)
        self.assertEqual(len(Database.Papers), 0)
        self.assertIn('is damaged', Printed)
        self.assertTrue(os.path.isfile(self.DatabaseName + '.damaged'))

    def test_missing_file_starts_new_record(self):
        Database, Printed = Quiet(Records.LoadDatabase, os.path.join(self.Folder.name, 'none.json'))
        self.assertEqual(len(Database.Mistakes), 0)
        self.assertIn('No saved learning records yet', Printed)


if __name__ == '__main__':
    unittest.main()
