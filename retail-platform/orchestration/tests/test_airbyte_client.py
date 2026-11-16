import unittest
import os
from unittest.mock import Mock
os.environ.setdefault("AIRBYTE_CONNECTION_ID", "test-connection")
from airbyte_client import AirbyteClient, AirbyteError

class ClientTests(unittest.TestCase):
    def client(self):
        return AirbyteClient(client_id="test-id", client_secret="test-secret")

    def test_attach_does_not_post_duplicate_job(self):
        client = self.client()
        client.request = Mock(return_value={"data": [{"jobId": 12, "status": "running"}]})
        job, attached = client.start_or_attach()
        self.assertTrue(attached)
        self.assertEqual(job["jobId"], 12)
        client.request.assert_called_once()
        self.assertEqual(client.request.call_args.args[0], "GET")

    def test_no_active_job_creates_sync(self):
        client = self.client()
        client.request = Mock(side_effect=[{"data": []}, {"jobId": 13, "status": "pending"}])
        job, attached = client.start_or_attach()
        self.assertFalse(attached)
        self.assertEqual(job["jobId"], 13)
        self.assertEqual(client.request.call_args.args[2]["jobType"], "sync")

    def test_failed_sync_blocks_success(self):
        client = self.client()
        client.request = Mock(return_value={"jobId": 1, "status": "failed"})
        with self.assertRaises(AirbyteError):
            client.wait_for_success(1, log=lambda x: None, poll_seconds=0)

    def test_successful_sync_returns_status(self):
        client = self.client()
        client.request = Mock(side_effect=[
            {"jobId": 1, "status": "running"}, {"jobId": 1, "status": "succeeded"},
        ])
        self.assertEqual(client.wait_for_success(1, log=lambda x: None,
                         poll_seconds=0)["status"], "succeeded")

    def test_timeout_does_not_report_success(self):
        client = self.client()
        client.request = Mock()
        with self.assertRaises(AirbyteError):
            client.wait_for_success(1, timeout_seconds=0)
        client.request.assert_not_called()

    def test_unknown_status_is_not_success(self):
        client = self.client()
        client.request = Mock(return_value={"status": "unexpected"})
        with self.assertRaises(AirbyteError):
            client.wait_for_success(1, log=lambda x: None)


class RetryTests(unittest.TestCase):
    def client(self):
        c = AirbyteClient(client_id="test-id", client_secret="test-secret")
        c.token = "test-token"
        c.expires = 10 ** 20
        return c

    def test_get_recovers_after_network_interruption(self):
        from urllib.error import URLError
        from unittest.mock import patch, MagicMock
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'{"status":"succeeded"}'
        with patch("airbyte_client.urlopen", side_effect=[URLError("temporary"), response]) as call:
            with patch("airbyte_client.time.sleep"):
                self.assertEqual(self.client().request("GET", "/jobs/2")["status"], "succeeded")
        self.assertEqual(call.call_count, 2)

    def test_post_network_failure_is_never_retried(self):
        from urllib.error import URLError
        from unittest.mock import patch
        with patch("airbyte_client.urlopen", side_effect=URLError("temporary")) as call:
            with self.assertRaises(AirbyteError):
                self.client().request("POST", "/jobs", {"jobType": "sync"})
        self.assertEqual(call.call_count, 1)

    def test_resume_checks_connection_and_does_not_post(self):
        from airbyte_client import CONNECTION_ID
        client = self.client()
        client.request = Mock(return_value={"jobId": 2, "connectionId": CONNECTION_ID,
                                           "jobType": "sync", "status": "succeeded"})
        self.assertEqual(client.resume_job(2)["jobId"], 2)
        client.request.assert_called_once_with("GET", "/jobs/2")

    def test_resume_rejects_wrong_connection(self):
        client = self.client()
        client.request = Mock(return_value={"jobId": 2, "connectionId": "other", "status": "running"})
        with self.assertRaises(AirbyteError):
            client.resume_job(2)

    def test_resume_rejects_failed_job(self):
        from airbyte_client import CONNECTION_ID
        client = self.client()
        client.request = Mock(return_value={"jobId": 2, "connectionId": CONNECTION_ID,
                                           "status": "failed"})
        with self.assertRaises(AirbyteError):
            client.resume_job(2)

    def test_401_refreshes_token_once(self):
        from airbyte_client import AirbyteHTTPError
        client = self.client()
        client._http = Mock(side_effect=[AirbyteHTTPError(401, "expired"), {"status": "succeeded"}])
        client.authenticate = Mock()
        self.assertEqual(client.request("GET", "/jobs/2")["status"], "succeeded")
        client.authenticate.assert_called_once()

    def test_forbidden_is_not_retried(self):
        from airbyte_client import AirbyteHTTPError
        client = self.client()
        client._http = Mock(side_effect=AirbyteHTTPError(403, "forbidden"))
        client.authenticate = Mock()
        with self.assertRaises(AirbyteHTTPError):
            client.request("GET", "/jobs/2")
        client.authenticate.assert_not_called()

if __name__ == "__main__":
    unittest.main()
