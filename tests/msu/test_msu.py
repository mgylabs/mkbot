from sys import path
from unittest import TestCase
from unittest import mock
from unittest.mock import patch, mock_open
from src.msu import msu


class MSUTest(TestCase):
    mock_get = None
    # def setUp(self) -> None:
    #     patcher_get = patch('src.msu.msu.requests.get',
    #                         side_effect=self.mock_requests_get)
    #     self.mock_get = patcher_get.start()
    #     self.addCleanup(patcher_get.stop())

    @classmethod
    def setUpClass(cls):
        cls.patcher_get = patch('src.msu.msu.requests.get',
                                side_effect=cls.mock_requests_get)
        cls.mock_get = cls.patcher_get.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.patcher_get.stop()

    @patch('src.msu.msu.sys')
    def test_is_development_mode(self, mock_sys):
        mock_sys.frozen = True
        self.assertFalse(msu.is_development_mode())

    def test_VersionInfo_stable(self):
        info = 'MKBotSetup-stable-1.3.3-16bb694a133c33fe80c4b67be2a3e000facd883c'
        url = 'https://api.github.com/repos/mgylabs/mulgyeol-mkbot/releases/assets/29427634'

        vi = msu.VersionInfo(info, url)
        from packaging import version
        expected = {'commit': None, 'url': url,
                    'rtype': 'stable', 'version': version.parse('1.3.3'), 'sha': '16bb694a133c33fe80c4b67be2a3e000facd883c'}

        self.assertEqual(vi.__dict__, expected)

    def test_VersionInfo_canary(self):
        info = 'MKBotSetup-canary-1.3.3.82980060b4606ef9bc428932736647d45e400fd9-8214d361d2826779517f7fb0502405aafdf0ec54'
        url = 'https://api.github.com/repos/mgylabs/mulgyeol-mkbot/releases/assets/29427634'

        vi = msu.VersionInfo(info, url)
        from packaging import version
        expected = {'commit': '82980060b4606ef9bc428932736647d45e400fd9', 'url': url,
                    'rtype': 'canary', 'version': version.parse('1.3.3'), 'sha': '8214d361d2826779517f7fb0502405aafdf0ec54'}

        self.assertEqual(vi.__dict__, expected)

    @staticmethod
    def mock_requests_get(*args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code

            def json(self):
                return self.json_data

            def raise_for_status(self):
                pass

        if args[0] == 'https://api.github.com/repos/mgylabs/mulgyeol-mkbot/releases/latest':
            test_json = {
                "assets": [
                    {
                        "name": "MKBotSetup-1.3.3.zip",
                        "label": "MKBotSetup-stable-1.3.3-16bb694a133c33fe80c4b67be2a3e000facd883c",
                        "browser_download_url": "https://github.com/mgylabs/mulgyeol-mkbot/releases/download/v1.3.3/MKBotSetup-1.3.3.zip"
                    }
                ]
            }
            return MockResponse(test_json, 200)
        elif args[0] == 'https://api.github.com/repos/mgylabs/mulgyeol-mkbot/releases/tags/canary':
            test_json = {
                "assets": [
                    {
                        "name": "MKBotCanarySetup-1.4.0.8298006.zip",
                        "label": "MKBotSetup-canary-1.4.0.82980060b4606ef9bc428932736647d45e400fd9-8214d361d2826779517f7fb0502405aafdf0ec54",
                        "browser_download_url": "https://github.com/mgylabs/mulgyeol-mkbot/releases/download/canary/MKBotCanarySetup-1.4.0.8298006.zip"
                    }
                ]
            }
            return MockResponse(test_json, 200)

    def get_version_json(self, version, commit):
        import json
        if commit == None:
            return json.loads('{"name": "MK Bot", "version": "' + version + '", "commit": null}')
        else:
            return json.loads('{"name": "MK Bot", "version": "' + version + '", "commit": "' + commit + '"}')

    def test_Updater_init(self):
        from packaging import version
        # mock_get.side_effect = self.mock_requests_get

        ### --- When commit is set to null
        current_version = self.get_version_json('1.3.2', None)
        with self.assertRaises(SystemExit) as se:
            updater = msu.Updater(current_version, True)

        self.assertEqual(se.exception.code, 1)

        ### --- When there are no updates available
        current_version = self.get_version_json(
            '1.5.4', '04a87e226add7197f3538b3349e562cc4135451d')
        with self.assertRaises(SystemExit) as se:
            updater = msu.Updater(current_version, True)

        self.assertEqual(se.exception.code, 1)

        ### --- When a stable update is available
        current_version = self.get_version_json(
            '1.3.2', '5be84dc9dfaa24003dfe4c7c88db1f6d212c226f')
        updater = msu.Updater(current_version, False)
        stable_expected = {'commit': None, 'url': 'https://github.com/mgylabs/mulgyeol-mkbot/releases/download/v1.3.3/MKBotSetup-1.3.3.zip',
                           'rtype': 'stable', 'version': version.parse('1.3.3'), 'sha': '16bb694a133c33fe80c4b67be2a3e000facd883c'}

        self.assertEqual(updater.last_stable.__dict__, stable_expected)
        self.assertEqual(updater.last_canary, None)
        self.assertEqual(updater.target, updater.last_stable)

        ### --- When a canary update is available
        #### --- If CanaryuUpdate is set to true
        current_version = self.get_version_json(
            '1.3.3', '04a87e226add7197f3538b3349e562cc4135451d')
        updater = msu.Updater(current_version, True)
        canary_expected = {'commit': '82980060b4606ef9bc428932736647d45e400fd9', 'url': 'https://github.com/mgylabs/mulgyeol-mkbot/releases/download/canary/MKBotCanarySetup-1.4.0.8298006.zip',
                           'rtype': 'canary', 'version': version.parse('1.4.0'), 'sha': '8214d361d2826779517f7fb0502405aafdf0ec54'}

        self.assertEqual(updater.last_stable.__dict__, stable_expected)
        self.assertNotEqual(updater.last_canary, None)
        self.assertEqual(updater.last_canary.__dict__, canary_expected)
        self.assertEqual(updater.target, updater.last_canary)

        #### --- If CanaryuUpdate is set to false
        current_version = self.get_version_json(
            '1.3.3', '04a87e226add7197f3538b3349e562cc4135451d')
        with self.assertRaises(SystemExit) as se:
            updater = msu.Updater(current_version, False)
        canary_expected = {'commit': '82980060b4606ef9bc428932736647d45e400fd9', 'url': 'https://github.com/mgylabs/mulgyeol-mkbot/releases/download/canary/MKBotCanarySetup-1.4.0.8298006.zip',
                           'rtype': 'canary', 'version': version.parse('1.4.0'), 'sha': '8214d361d2826779517f7fb0502405aafdf0ec54'}

        self.assertEqual(updater.last_stable.__dict__, stable_expected)
        self.assertNotEqual(updater.last_canary, None)
        self.assertEqual(updater.last_canary.__dict__, canary_expected)
        self.assertEqual(se.exception.code, 1)

    def test_find_asset(self):
        current_version = self.get_version_json(
            '1.3.2', '5be84dc9dfaa24003dfe4c7c88db1f6d212c226f')
        assets = [
            {
                "name": "MKBotSetup-1.3.3.zip",
                "label": "MKBotSetup-stable-1.3.3-16bb694a133c33fe80c4b67be2a3e000facd883c",
                "browser_download_url": "https://github.com/mgylabs/mulgyeol-mkbot/releases/download/v1.3.3/MKBotSetup-1.3.3.zip"
            }
        ]
        self.assertEqual(msu.Updater(
            current_version).find_asset(assets), assets[0])

    @patch("builtins.open", new_callable=mock_open, read_data='{"name": "MK Bot", "version": "1.3.2", "commit": "5be84dc9dfaa24003dfe4c7c88db1f6d212c226f"}')
    @patch('src.msu.msu.sys.argv')
    def test_main(self, mock_argv, mock_file):
        with patch('src.msu.msu.instance_already_running', return_value=True), self.assertRaises(SystemExit) as se:
            msu.main()
            self.assertEqual(se.exception.code, 1)

        with patch('src.msu.msu.instance_already_running', return_value=False), self.assertRaises(SystemExit) as se:
            mock_argv = []
            msu.main()
            mock_file.assert_called_with('../info/version.json', 'rt')
            self.assertEqual(se.exception.code, 1)
