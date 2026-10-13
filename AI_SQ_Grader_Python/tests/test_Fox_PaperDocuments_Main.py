# Tests for Fox's modules: PaperDocumentManagement.py, AIConnection.py and AISQGrader.py

import base64
import os
import tempfile
import unittest
import urllib.error
from unittest import mock

from TestHelpers import SampleFolder, RunWithInput, Quiet, FakeAIServer
import AIConnection
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

    def test_paper_file_names(self):
        Details = SQRecords.PaperDetails()
        Details.PaperCode = '9701/22/M/J/23'
        self.assertEqual(Paper.MakePaperFileName(Details, 'ms'), '9701_s23_ms_22')
        self.assertEqual(Paper.MakePaperFileName(Details, 'qp'), '9701_s23_qp_22')
        Details.PaperCode = '0478/12/F/M/24'
        self.assertEqual(Paper.MakePaperFileName(Details, 'ms'), '0478_m24_ms_12')

    def test_download_saves_pdf_and_rejects_other_content(self):
        Details = SQRecords.PaperDetails()
        Details.PaperCode = '9701/22/M/J/23'
        Download = SQRecords.DownloadSettings()
        Download.Enabled = True
        Download.ServiceURL = 'https://example.org/papers/'
        with tempfile.TemporaryDirectory() as Folder:
            with mock.patch.object(Paper, 'DownloadFolder', Folder):
                with mock.patch('urllib.request.urlopen', return_value=FakeReply(b'%PDF-1.4 test')) as Opener:
                    Saved, Printed = Quiet(Paper.DownloadPaperFile, Details, 'ms', Download)
                self.assertEqual(Opener.call_args[0][0], 'https://example.org/papers/9701_s23_ms_22.pdf')
                self.assertTrue(os.path.isfile(Saved))
                self.assertIn('Mark scheme saved as', Printed)
                with mock.patch('urllib.request.urlopen', return_value=FakeReply(b'%PDF-1.4 qp')) as Opener:
                    Saved, Printed = Quiet(Paper.DownloadPaperFile, Details, 'qp', Download)
                self.assertTrue(Saved.endswith('9701_s23_qp_22.pdf'))
                self.assertIn('Question paper saved as', Printed)
                with mock.patch('urllib.request.urlopen', return_value=FakeReply(b'<html>not found</html>')):
                    Saved, Printed = Quiet(Paper.DownloadPaperFile, Details, 'ms', Download)
                self.assertEqual(Saved, '')
                self.assertIn('did not return a PDF file', Printed)
                with mock.patch('urllib.request.urlopen', side_effect=urllib.error.URLError('offline')):
                    Saved, Printed = Quiet(Paper.DownloadPaperFile, Details, 'ms', Download)
                self.assertEqual(Saved, '')
                self.assertIn('could not be reached', Printed)

    def test_question_paper_is_optional(self):
        Details = SQRecords.PaperDetails()
        Result, Printed = RunWithInput(Paper.InputQuestionPaper, ['Paper.docx', ''], Details, SQRecords.DownloadSettings())
        self.assertEqual(Result, '')
        self.assertIn('Not accepted', Printed)
        Result, _ = RunWithInput(Paper.InputQuestionPaper, [os.path.join(SampleFolder, 'Sample_Answer_Q3.png')], Details, SQRecords.DownloadSettings())
        self.assertTrue(Result.endswith('Sample_Answer_Q3.png'))

    def test_manage_documents_complete(self):
        Inputs = ['2', '2', '22', '2', '2023',
                  os.path.join(SampleFolder, 'Sample_Chemistry_Answers.txt'), '',
                  os.path.join(SampleFolder, 'Sample_Chemistry_MS.txt'), '']
        Result, Printed = RunWithInput(Paper.ManageDocuments, Inputs, SQRecords.DownloadSettings())
        self.assertTrue(Result.IsComplete)
        self.assertEqual(Result.QuestionPaperFile, '')
        self.assertIn('Marking can begin', Printed)
        self.assertIn('Question paper: (none', Printed)

    def test_manage_documents_missing_uploads(self):
        Inputs = ['2', '2', '22', '2', '2023', '', '']
        Result, Printed = RunWithInput(Paper.ManageDocuments, Inputs, SQRecords.DownloadSettings())
        self.assertFalse(Result.IsComplete)
        self.assertIn('Missing: no student answer file has been uploaded.', Printed)
        self.assertIn('Missing: no mark scheme has been uploaded or downloaded.', Printed)
        self.assertIn('Marking cannot begin', Printed)


class TestAIConnection(unittest.TestCase):

    def setUp(self):
        self.Server = FakeAIServer()
        self.Settings = self.Server.Settings()

    def tearDown(self):
        self.Server.Stop()

    def test_base_url(self):
        self.assertEqual(AIConnection.GetBaseURL('openai'), 'https://api.openai.com/v1')
        self.assertEqual(AIConnection.GetBaseURL('https://x.org/v1//'), 'https://x.org/v1')
        self.assertEqual(AIConnection.GetBaseURL('NoSuchAI'), '')

    def test_image_url(self):
        URL = AIConnection.MakeImageURL(os.path.join(SampleFolder, 'Sample_Answer_Q3.png'))
        self.assertTrue(URL.startswith('data:image/png;base64,'))
        self.assertTrue(base64.b64decode(URL.split(',')[1]).startswith(b'\x89PNG'))
        URL, Printed = Quiet(AIConnection.MakeImageURL, os.path.join(SampleFolder, 'Sample_Chemistry_MS.txt'))
        self.assertEqual(URL, '')
        self.assertIn('Not an image file', Printed)

    def test_request_shape_text_and_images(self):
        self.Server.Reply({'points': []})
        Response = AIConnection.SendChatRequest('PROMPT', [], self.Settings)
        self.assertTrue(Response.Success)
        self.assertEqual(Response.ReplyText, '{"points": []}')
        Path, Authorisation, Body = self.Server.Requests[0]
        self.assertEqual(Path, '/v1/chat/completions')
        self.assertEqual(Authorisation, 'Bearer sk-test')
        self.assertEqual(Body['model'], 'test-model')
        self.assertEqual(Body['messages'][0]['content'], 'PROMPT')
        self.Server.Reply({'answers': []})
        AIConnection.SendChatRequest('READ', ['data:image/png;base64,AAAA', 'data:image/png;base64,BBBB'], self.Settings)
        self.assertEqual(self.Server.ImageCount(1), 2)
        self.assertEqual(self.Server.PromptOf(1), 'READ')

    def test_retry_after_server_error(self):
        self.Server.Replies = [(503, '{}'), (429, '{}')]
        self.Server.Reply({'ok': True})
        Response = AIConnection.SendChatRequest('PROMPT', [], self.Settings)
        self.assertTrue(Response.Success)
        self.assertEqual(len(self.Server.Requests), 3)

    def test_no_retry_for_bad_key_and_give_up_after_three(self):
        self.Server.Replies = [(401, '{"error": "bad key"}')]
        Response = AIConnection.SendChatRequest('PROMPT', [], self.Settings)
        self.assertFalse(Response.Success)
        self.assertIn('HTTP error 401', Response.ErrorMessage)
        self.assertEqual(len(self.Server.Requests), 1)
        self.Server.Replies = [(500, '{}'), (500, '{}'), (500, '{}')]
        Response = AIConnection.SendChatRequest('PROMPT', [], self.Settings)
        self.assertFalse(Response.Success)
        self.assertEqual(len(self.Server.Requests), 4)

    def test_image_refused_message(self):
        self.Server.Replies = [(400, '{"error": "image input not supported"}')]
        Response = AIConnection.SendChatRequest('READ', ['data:image/png;base64,AAAA'], self.Settings)
        self.assertIn('the model may not accept images', Response.ErrorMessage)

    def test_reply_without_content_and_bad_settings(self):
        self.Server.Replies = [(200, '{"choices": []}')]
        self.assertIn('no content', AIConnection.SendChatRequest('P', [], self.Settings).ErrorMessage)
        self.Settings.Provider = 'NoSuchAI'
        self.assertIn('Unknown AI provider', AIConnection.SendChatRequest('P', [], self.Settings).ErrorMessage)
        self.Settings.Provider = 'OpenAI'
        self.Settings.APIKey = ''
        self.assertIn('missing', AIConnection.SendChatRequest('P', [], self.Settings).ErrorMessage)
        self.assertIn('No AI service', AIConnection.SendChatRequest('P', [], SQRecords.AISettings()).ErrorMessage)

    def test_read_json_reply(self):
        Response = SQRecords.AIResponse()
        Response.Success = True
        Response.ReplyText = 'Sure!\n```json\n{"a": [1, 2]}\n```'
        self.assertEqual(AIConnection.ReadJsonReply(Response), {'a': [1, 2]})
        self.assertEqual(AIConnection.GetJsonList(AIConnection.ReadJsonReply(Response), 'a'), [1, 2])
        Response.ReplyText = '[1, 2]'
        self.assertIsNone(AIConnection.ReadJsonReply(Response))
        Response.ReplyText = 'no json'
        self.assertIsNone(AIConnection.ReadJsonReply(Response))

    def test_connection_test(self):
        self.Server.Reply({'ok': True})
        Result, Printed = Quiet(AIConnection.TestConnection, self.Settings)
        self.assertTrue(Result)
        self.assertIn('The AI service is working.', Printed)
        self.Server.Reply('I am a chatbot.')
        Result, Printed = Quiet(AIConnection.TestConnection, self.Settings)
        self.assertFalse(Result)
        self.assertIn('not with JSON', Printed)
        self.Server.Replies = [(401, '{}')]
        Result, Printed = Quiet(AIConnection.TestConnection, self.Settings)
        self.assertIn('The test failed: The AI service returned HTTP error 401', Printed)
        Result, Printed = Quiet(AIConnection.TestConnection, SQRecords.AISettings())
        self.assertFalse(Result)
        self.assertIn('no AI service to test', Printed)


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

    def test_choose_ai_service_from_menu(self):
        with mock.patch.dict(os.environ, {'SQ_API_KEY': 'sk-menu'}):
            Settings, _ = RunWithInput(AISQGrader.InputAISettings, ['4', 'ftp://x', 'https://ai.example.org/v1', 'my-model'])
        self.assertEqual(Settings.Provider, 'https://ai.example.org/v1')
        self.assertEqual(Settings.ModelName, 'my-model')
        Settings, _ = RunWithInput(AISQGrader.InputAISettings, ['1'])
        self.assertEqual(Settings.Provider, SQRecords.OfflineProvider)

    def test_session_stops_when_documents_missing(self):
        Missing = SQRecords.DocumentSet()
        with mock.patch.object(AISQGrader.PaperDocumentManagement, 'ManageDocuments', return_value=Missing):
            with mock.patch.object(AISQGrader.DocumentProcessing, 'ProcessDocuments') as Processing:
                _, Printed = Quiet(AISQGrader.RunMarkingSession, SQRecords.AISettings(), SQRecords.DownloadSettings())
        Processing.assert_not_called()
        self.assertIn('stopped because documents are missing', Printed)


if __name__ == '__main__':
    unittest.main()
