# Tests for Andy's module: ReportManagement.py

import json
import os
import re
import tempfile
import unittest
from unittest import mock

from TestHelpers import SampleFolder, SampleGrading, RunWithInput, Quiet
import CorrectionRegrading as Correction
import LearningRecords as Records
import ReportManagement as Reports
import SQRecords


def ValidBackupData():
    Grading = SampleGrading()
    Database = Records.LearningDatabase()
    Records.AddGradingResult(Database, Grading)
    Regrade = Correction.RegradeQuestion(Grading, 3, 'The rate of reaction increases at a higher temperature.', '', SQRecords.AISettings())
    Records.AddRegradeResult(Database, Grading, Regrade)
    return json.loads(json.dumps(Records.DatabaseToDictionary(Database)))


class TestPdf(unittest.TestCase):

    def test_text_helpers(self):
        self.assertEqual(Reports.MakePdfSafe('a (b) \\ c'), 'a \\(b\\) \\\\ c')
        self.assertEqual(Reports.MakePdfSafe('P1 → café 字'), 'P1 -> café ?')
        self.assertEqual(Reports.PadNumber(931, 10), '0000000931')
        self.assertEqual(Reports.MakeSafeFileName('9701/22/M/J/23'), '9701-22-M-J-23')
        Lines = Reports.WrapText('  ' + 'word ' * 40, 30)
        self.assertTrue(all(len(Line) <= 30 for Line in Lines))
        self.assertTrue(all(Line.startswith('  ') for Line in Lines))
        self.assertEqual(Reports.WrapText('', 30), [''])
        self.assertTrue(all(len(Line) <= 30 for Line in Reports.WrapText('x' * 100, 30)))

    def test_pdf_structure_is_valid(self):
        Lines = ['## Heading (1)'] + ['Line ' + str(N) + ' – (text)' for N in range(120)]
        with tempfile.TemporaryDirectory() as Folder:
            FileName = os.path.join(Folder, 'Report.pdf')
            self.assertTrue(Reports.WritePdfReport(Lines, FileName))
            with open(FileName, 'rb') as File:
                Data = File.read()
        self.assertTrue(Data.startswith(b'%PDF-1.4'))
        self.assertTrue(Data.rstrip().endswith(b'%%EOF'))
        StartXref = int(re.search(rb'startxref\n(\d+)', Data).group(1))
        self.assertTrue(Data[StartXref:].startswith(b'xref'))
        Offsets = re.findall(rb'(\d{10}) 00000 n ', Data)
        for Number, Offset in enumerate(Offsets, start=1):
            self.assertTrue(Data[int(Offset):].startswith(str(Number).encode() + b' 0 obj'), Number)
        self.assertIn(b'/Count 3', Data)                      # 121 lines -> 3 pages of 52

    def test_report_text_with_pymupdf(self):
        try:
            import pymupdf
        except ImportError:
            self.skipTest('pymupdf not installed')
        Grading = SampleGrading()
        Learning = SQRecords.LearningData()
        Learning.Progress.PaperScores = [30]
        with tempfile.TemporaryDirectory() as Folder:
            FileName = os.path.join(Folder, 'Report.pdf')
            Reports.WritePdfReport(Reports.BuildReportLines(Grading, Learning), FileName)
            Document = pymupdf.open(FileName)
            Text = ''.join(Page.get_text() for Page in Document)
            Document.close()
        self.assertIn('Estimated total: 3 / 10 (30%)', Text)
        self.assertIn('Question 2(a)', Text)
        self.assertIn('Marking rules: P3 DEPENDS ON P2', Text)
        self.assertIn('Likely reason for lost mark (P2): Incomplete explanation', Text)
        self.assertIn('(answer in image: Sample_Answer_Q3.png)', Text)
        self.assertIn('Original paper scores, oldest first: 30%', Text)

    def test_attempt_history_in_report(self):
        Grading = SampleGrading()
        Learning = SQRecords.LearningData()
        for Number, Mark in [(1, 0), (2, 2)]:
            Attempt = SQRecords.AttemptRecord()
            Attempt.QuestionID = '2(b)'
            Attempt.AttemptNo = Number
            Attempt.EstimatedMark = Mark
            Learning.AttemptHistories.append(Attempt)
        Lines = Reports.BuildReportLines(Grading, Learning)
        self.assertIn('  Attempt 1: 0 / 2 (original answer)', Lines)
        self.assertIn('  Attempt 2: 2 / 2 (correction)', Lines)


class TestBackups(unittest.TestCase):

    def setUp(self):
        self.Folder = tempfile.TemporaryDirectory()
        self.DatabaseName = os.path.join(self.Folder.name, 'LearningRecords.json')
        self.Patches = [mock.patch.object(Reports, 'DatabasePath', self.DatabaseName),
                        mock.patch.object(Reports, 'BackupFolder', os.path.join(self.Folder.name, 'Backups')),
                        mock.patch.object(Reports, 'ReportFolder', os.path.join(self.Folder.name, 'Reports'))]
        for Patch in self.Patches:
            Patch.start()

    def tearDown(self):
        for Patch in self.Patches:
            Patch.stop()
        self.Folder.cleanup()

    def WriteJson(self, Name, Data):
        FileName = os.path.join(self.Folder.name, Name)
        with open(FileName, 'w', encoding='utf-8') as File:
            json.dump(Data, File)
        return FileName

    def test_valid_backup_passes(self):
        self.assertEqual(Reports.ValidateBackupData(ValidBackupData()), '')

    def test_invalid_backups_give_clear_messages(self):
        Cases = []
        Data = ValidBackupData(); del Data['Errors']
        Cases.append((Data, 'must contain the lists'))
        Data = ValidBackupData(); Data['Papers'][0]['TotalMark'] = '3'
        Cases.append((Data, 'Paper 1: TotalMark must be INTEGER.'))
        Data = ValidBackupData(); Data['Papers'][0]['TotalMark'] = True
        Cases.append((Data, 'Paper 1: TotalMark must be INTEGER.'))
        Data = ValidBackupData(); Data['Papers'][0]['TotalMark'] = 99
        Cases.append((Data, 'TotalMark must be from 0 to MaxTotal'))
        Data = ValidBackupData(); Data['Mistakes'][1]['Status'] = 'Finished'
        Cases.append((Data, 'Mistake entry 2: unknown status Finished'))
        Data = ValidBackupData(); del Data['Attempts'][2]['AttemptNo']
        Cases.append((Data, 'Attempt 3 has no AttemptNo.'))
        Data = ValidBackupData(); Data['Attempts'][0]['Feedback']['Points'][0]['Category'] = 'Great'
        Cases.append((Data, 'Attempt 1, point 1: unknown category Great'))
        Data = ValidBackupData(); Data['Errors'][0]['ErrorType'] = 'Typo'
        Cases.append((Data, 'Error record 1: unknown error type Typo'))
        Cases.append(([1, 2, 3], 'does not contain AI SQ Grader learning records'))
        for Data, Message in Cases:
            self.assertIn(Message, Reports.ValidateBackupData(Data))

    def test_import_invalid_files_does_not_change_records(self):
        with open(self.DatabaseName, 'w', encoding='utf-8') as File:
            File.write('{"Papers": [], "Mistakes": [], "Attempts": [], "Errors": []}')
        NotJson = os.path.join(self.Folder.name, 'Broken.json')
        with open(NotJson, 'w') as File:
            File.write('{"Papers": [')
        self.assertEqual(Reports.ImportBackup(NotJson, self.DatabaseName), 'The file is not valid JSON.')
        self.assertIn('must contain the lists', Reports.ImportBackup(os.path.join(SampleFolder, 'Invalid_Backup.json'), self.DatabaseName))
        self.assertEqual(Reports.ImportBackup(os.path.join(SampleFolder, 'Sample_Chemistry_MS.txt'), self.DatabaseName), 'The backup must be a .json file.')
        self.assertIn('could not be opened', Reports.ImportBackup(os.path.join(self.Folder.name, 'none.json'), self.DatabaseName))
        with open(self.DatabaseName, encoding='utf-8') as File:
            self.assertEqual(File.read(), '{"Papers": [], "Mistakes": [], "Attempts": [], "Errors": []}')

    def test_import_valid_backup_restores_and_keeps_safety_copy(self):
        with open(self.DatabaseName, 'w', encoding='utf-8') as File:
            File.write('{"Papers": [], "Mistakes": [], "Attempts": [], "Errors": []}')
        BackupName = self.WriteJson('Good.json', ValidBackupData())
        Problem, Printed = Quiet(Reports.ImportBackup, BackupName, self.DatabaseName)
        self.assertEqual(Problem, '')
        self.assertIn('Your current records were first saved as', Printed)
        Database, _ = Quiet(Records.LoadDatabase, self.DatabaseName)
        self.assertEqual(len(Database.Attempts), 6)
        self.assertEqual(len(os.listdir(os.path.join(self.Folder.name, 'Backups'))), 1)

    def test_export_backup(self):
        Problem, Printed = Quiet(Reports.ExportBackup, self.DatabaseName, os.path.join(self.Folder.name, 'Backups', 'B.json'))
        self.assertFalse(Problem)
        self.assertIn('There are no saved learning records to back up yet.', Printed)
        self.WriteJson('LearningRecords.json', ValidBackupData())
        self.assertTrue(Reports.ExportBackup(self.DatabaseName, os.path.join(self.Folder.name, 'Backups', 'B.json')))
        with open(os.path.join(self.Folder.name, 'Backups', 'B.json'), encoding='utf-8') as File:
            self.assertEqual(Reports.ValidateBackupData(json.load(File)), '')

    def test_manage_reports(self):
        self.WriteJson('LearningRecords.json', ValidBackupData())
        Inputs = ['Y', 'Y', os.path.join(SampleFolder, 'Invalid_Backup.json')]
        Outcome, Printed = RunWithInput(Reports.ManageReports, Inputs, SampleGrading(), SQRecords.LearningData())
        self.assertTrue(os.path.isfile(Outcome.ReportFile))
        self.assertTrue(os.path.isfile(Outcome.BackupFile))
        self.assertFalse(Outcome.ImportValid)
        self.assertIn('Import failed - The file must contain the lists Papers, Mistakes, Attempts and Errors. Your saved records have not been changed.', Outcome.Message)
        Outcome, _ = RunWithInput(Reports.ManageReports, ['N', 'Y', Outcome.BackupFile], SQRecords.GradingResult(), SQRecords.LearningData())
        self.assertTrue(Outcome.ImportValid)
        self.assertEqual(Outcome.ReportFile, '')            # no report without a marked paper


if __name__ == '__main__':
    unittest.main()
