# Tests for Fox's modules: PaperDocumentManagement.py and AISQGrader.py

import os
import tempfile
import unittest
import urllib.error
from unittest import mock

from TestHelpers import SampleFolder, RunWithInput, Quiet
import AISQGrader
import PaperDocumentManagement as Paper
import SQRecords


class FakeReply:
    def __init__(self, Data):
        self.Data = Data

    def read(self):
        return self.Data

    def close(self):
        pass


class TestPaperSelection(unittest.TestCase):

    def test_paper_number_rules(self):
        self.assertTrue(Paper.IsValidPaperNumber('22'))
        self.assertTrue(Paper.IsValidPaperNumber('11'))      # boundary: lowest
        self.assertTrue(Paper.IsValidPaperNumber('63'))      # boundary: highest
        for Bad in ['', '2', '222', '27', '70', '2a', '02', '20']:
            self.assertFalse(Paper.IsValidPaperNumber(Bad), Bad)

    def test_select_paper_builds_code_and_session(self):
        Inputs = ['2', '2', '27', '22', '2', '2015', 'twenty', '2023']
        Result, Printed = RunWithInput(Paper.SelectPaper, Inputs)
        self.assertEqual(Result.Level, 'AS Level')
        self.assertEqual(Result.Subject, 'Chemistry (9701)')
        self.assertEqual(Result.PaperCode, '9701/22/M/J/23')
        self.assertEqual(Result.Session, 'May/June 2023')
        self.assertIn('A paper number is two digits', Printed)
        self.assertIn('The year must be from 2016', Printed)
        self.assertIn('Please type the year as a number', Printed)

    def test_igcse_menu_only_shows_igcse_subjects(self):
        Result, Printed = RunWithInput(Paper.SelectPaper, ['1', '4', '12', '3', '2024'])
        self.assertEqual(Result.PaperCode, '0478/12/O/N/24')
        self.assertNotIn('9701', Printed)

    def test_menu_rejects_out_of_range_and_text(self):
        Result, Printed = RunWithInput(Paper.InputMenuChoice, ['0', 'x', '4', '3'], 'Pick', ['A', 'B', 'C'])
        self.assertEqual(Result, 2)
        self.assertIn('That number is not in the list.', Printed)
        self.assertIn('Please type a whole number.', Printed)


class TestDocuments(unittest.TestCase):

    def test_file_extension(self):
        self.assertEqual(Paper.GetFileExtension('Answers.TXT'), '.txt')
        self.assertEqual(Paper.GetFileExtension('folder.v2/answers'), '')
        self.assertEqual(Paper.GetFileExtension('scan.page1.jpeg'), '.jpeg')

    def test_check_document_messages(self):
        with tempfile.TemporaryDirectory() as Folder:
            Empty = os.path.join(Folder, 'Empty.txt')
            open(Empty, 'w').close()
            self.assertIn('not supported', Paper.CheckDocument('Answers.docx', Paper.AnswerFileTypes))
            self.assertIn('cannot be found', Paper.CheckDocument(os.path.join(Folder, 'None.txt'), Paper.AnswerFileTypes))
            self.assertIn('is empty', Paper.CheckDocument(Empty, Paper.AnswerFileTypes))
        self.assertEqual(Paper.CheckDocument(os.path.join(SampleFolder, 'Sample_Chemistry_MS.txt'), Paper.MarkSchemeFileTypes), '')

    def test_upload_answers_rejects_bad_and_duplicate_files(self):
        Good = os.path.join(SampleFolder, 'Sample_Chemistry_Answers.txt')
        Inputs = ['Answers.docx', '"' + Good + '"', Good, 'Missing.txt', '']
        Result, Printed = RunWithInput(Paper.InputAnswerFiles, Inputs)
        self.assertEqual(Result, [Good])
        self.assertIn('This file type is not supported', Printed)
        self.assertIn('already in the list', Printed)
        self.assertIn('cannot be found', Printed)

    def test_sample_paths_relative_to_program_folder(self):
        OldFolder = os.getcwd()
        try:
            os.chdir(tempfile.gettempdir())
            self.assertNotEqual(Paper.FindFile(os.path.join('SampleData', 'Sample_Chemistry_MS.txt')), '')
        finally:
            os.chdir(OldFolder)

    def test_mark_scheme_name(self):
        Details = SQRecords.PaperDetails()
        Details.PaperCode = '9701/22/M/J/23'
        self.assertEqual(Paper.MakeMarkSchemeName(Details), '9701_s23_ms_22')
        Details.PaperCode = '0478/12/F/M/24'
        self.assertEqual(Paper.MakeMarkSchemeName(Details), '0478_m24_ms_12')

    def test_download_saves_pdf_and_rejects_other_content(self):
        Details = SQRecords.PaperDetails()
        Details.PaperCode = '9701/22/M/J/23'
        Download = SQRecords.DownloadSettings()
        Download.Enabled = True
        Download.ServiceURL = 'https://example.org/ms/'
        with tempfile.TemporaryDirectory() as Folder:
            with mock.patch.object(Paper, 'DownloadFolder', Folder):
                with mock.patch('urllib.request.urlopen', return_value=FakeReply(b'%PDF-1.4 test')) as Opener:
                    Saved, _ = Quiet(Paper.DownloadMarkScheme, Details, Download)
                self.assertEqual(Opener.call_args[0][0], 'https://example.org/ms/9701_s23_ms_22.pdf')
                self.assertTrue(os.path.isfile(Saved))
                with mock.patch('urllib.request.urlopen', return_value=FakeReply(b'<html>not found</html>')):
                    Saved, Printed = Quiet(Paper.DownloadMarkScheme, Details, Download)
                self.assertEqual(Saved, '')
                self.assertIn('did not return a PDF file', Printed)
                with mock.patch('urllib.request.urlopen', side_effect=urllib.error.URLError('offline')):
                    Saved, Printed = Quiet(Paper.DownloadMarkScheme, Details, Download)
                self.assertEqual(Saved, '')
                self.assertIn('could not be reached', Printed)

    def test_manage_documents_complete(self):
        Inputs = ['2', '2', '22', '2', '2023',
                  os.path.join(SampleFolder, 'Sample_Chemistry_Answers.txt'), '',
                  os.path.join(SampleFolder, 'Sample_Chemistry_MS.txt')]
        Result, Printed = RunWithInput(Paper.ManageDocuments, Inputs, SQRecords.DownloadSettings())
        self.assertTrue(Result.IsComplete)
        self.assertIn('Marking can begin', Printed)

    def test_manage_documents_missing_uploads(self):
        Inputs = ['2', '2', '22', '2', '2023', '', '']
        Result, Printed = RunWithInput(Paper.ManageDocuments, Inputs, SQRecords.DownloadSettings())
        self.assertFalse(Result.IsComplete)
        self.assertIn('Missing: no student answer file has been uploaded.', Printed)
        self.assertIn('Missing: no mark scheme has been uploaded or downloaded.', Printed)
        self.assertIn('Marking cannot begin', Printed)


class TestMainModule(unittest.TestCase):

    def test_settings_file(self):
        with tempfile.TemporaryDirectory() as Folder:
            FileName = os.path.join(Folder, 'Settings.txt')
            with open(FileName, 'w') as File:
                File.write('# comment\nProvider = Offline\nModelName=gpt-4o-mini\nDownloadEnabled=TRUE\n'
                           'DownloadServiceURL=https://example.org/ms/?x=1\nnot a setting\n')
            Table = AISQGrader.ReadSettingsFile(FileName)
        self.assertEqual(AISQGrader.GetSetting(Table, 'provider', ''), 'Offline')
        self.assertEqual(AISQGrader.GetSetting(Table, 'DownloadServiceURL', ''), 'https://example.org/ms/?x=1')
        self.assertEqual(AISQGrader.GetSetting(Table, 'Missing', 'default'), 'default')
        self.assertTrue(AISQGrader.LoadDownloadSettings(Table).Enabled)
        self.assertEqual(AISQGrader.LoadAISettings(Table).Provider, SQRecords.OfflineProvider)

    def test_missing_settings_file_uses_defaults(self):
        Table, Printed = Quiet(AISQGrader.ReadSettingsFile, 'NoSuchSettings.txt')
        self.assertEqual(Table, [])
        self.assertIn('default settings will be used', Printed)

    def test_online_provider_without_key_falls_back_to_offline(self):
        Table = [['Provider', 'OpenAI'], ['ModelName', 'gpt-4o-mini']]
        with mock.patch.dict(os.environ, {'SQ_API_KEY': ''}):
            with mock.patch('getpass.getpass', return_value=''):
                Settings, Printed = Quiet(AISQGrader.LoadAISettings, Table)
        self.assertEqual(Settings.Provider, SQRecords.OfflineProvider)
        self.assertIn('offline demo marker will be used', Printed)

    def test_key_from_environment_is_used(self):
        Table = [['Provider', 'DeepSeek'], ['ModelName', 'deepseek-chat']]
        with mock.patch.dict(os.environ, {'SQ_API_KEY': 'sk-test'}):
            Settings = AISQGrader.LoadAISettings(Table)
        self.assertEqual(Settings.Provider, 'DeepSeek')
        self.assertEqual(Settings.APIKey, 'sk-test')

    def test_session_stops_when_documents_missing(self):
        Missing = SQRecords.DocumentSet()
        with mock.patch.object(AISQGrader.PaperDocumentManagement, 'ManageDocuments', return_value=Missing):
            with mock.patch.object(AISQGrader.DocumentProcessing, 'ProcessDocuments') as Processing:
                _, Printed = Quiet(AISQGrader.RunMarkingSession, SQRecords.AISettings(), SQRecords.DownloadSettings())
        Processing.assert_not_called()
        self.assertIn('stopped because documents are missing', Printed)


if __name__ == '__main__':
    unittest.main()
