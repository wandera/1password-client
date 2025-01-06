import json
from unittest import TestCase
from unittest.mock import patch

from onepassword import client


class TestCliVersion(TestCase):
    @patch.object(client, "read_bash_return")
    @patch.object(client.OnePassword, "cli_version", (2, 29, 0))
    def test_get_item_no_reveal(self, mock_read_bash_return):
        op = client.OnePassword()

        mock_read_bash_return.return_value = json.dumps([])
        op.get_item("uuid")
        mock_read_bash_return.assert_called_once_with(
            "op item get uuid  --format=json",
            single=False,
        )
        mock_read_bash_return.reset_mock()

        mock_read_bash_return.return_value = json.dumps(
            [{"id": "field", "value": "value"}]
        )
        op.get_item("uuid", "field")
        mock_read_bash_return.assert_called_once_with(
            "op item get uuid  --fields label=field", single=False
        )
        mock_read_bash_return.reset_mock()

        mock_read_bash_return.return_value = json.dumps(
            [
                {"id": "list", "value": "value"},
                {"id": "of", "value": "value"},
                {"id": "fields", "value": "value"},
            ]
        )
        op.get_item("uuid", ["list", "of", "fields"])
        mock_read_bash_return.assert_called_once_with(
            "op item get uuid  --format=json --fields label=list,label=of,label=fields",
            single=False,
        )

    @patch.object(client, "read_bash_return")
    @patch.object(client.OnePassword, "cli_version", (2, 30, 0))
    def test_get_item_reveal(self, mock_read_bash_return):
        op = client.OnePassword()

        mock_read_bash_return.return_value = json.dumps([])
        op.get_item("uuid")
        mock_read_bash_return.assert_called_once_with(
            "op item get uuid --reveal --format=json",
            single=False,
        )
        mock_read_bash_return.reset_mock()

        mock_read_bash_return.return_value = json.dumps(
            [{"id": "field", "value": "value"}]
        )
        op.get_item("uuid", "field")
        mock_read_bash_return.assert_called_once_with(
            "op item get uuid --reveal --fields label=field", single=False
        )
        mock_read_bash_return.reset_mock()

        mock_read_bash_return.return_value = json.dumps(
            [
                {"id": "list", "value": "value"},
                {"id": "of", "value": "value"},
                {"id": "fields", "value": "value"},
            ]
        )
        op.get_item("uuid", ["list", "of", "fields"])
        mock_read_bash_return.assert_called_once_with(
            "op item get uuid --reveal --format=json --fields label=list,label=of,label=fields",
            single=False,
        )
