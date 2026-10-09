"""Shared guards that keep the test suite offline."""

import boto3
import pytest


class OfflineClient:
    def __getattr__(self, operation):
        raise AssertionError(f"Unexpected AWS operation during tests: {operation}")


class OfflineSession:
    def client(self, *args, **kwargs):
        return OfflineClient()


@pytest.fixture(autouse=True)
def block_aws_calls(monkeypatch):
    """Return local stub clients instead of allowing boto3 to contact AWS."""
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test-access-key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test-secret-key")

    monkeypatch.setattr(boto3, "client", lambda *args, **kwargs: OfflineClient())
    monkeypatch.setattr(boto3, "Session", lambda *args, **kwargs: OfflineSession())
