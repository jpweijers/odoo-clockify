import unittest
import os

from src.packages.clockify import clockify

CLOCKIFY_URL = os.environ["CLOCKIFY_URL"]
CLOCKIFY_KEY = os.environ["CLOCKIFY_KEY"]
CLOCKIFY_WORKSPACE = os.environ["CLOCKIFY_WORKSPACE"]
CLOCKIFY_CLIENT_ID = os.environ["CLOCKIFY_CLIENT_ID"]
CLOCKIFY_USER = os.environ["CLOCKIFY_USER"]


class TestCase(unittest.TestCase):
    @classmethod
    def create_clockify_session(self) -> clockify.ClockifySession:
        return clockify.ClockifySession(
            CLOCKIFY_URL,
            CLOCKIFY_KEY,
            CLOCKIFY_WORKSPACE,
            CLOCKIFY_CLIENT_ID,
            CLOCKIFY_USER,
        )
