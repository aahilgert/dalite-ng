import email
import os
from pathlib import Path

import pytest
from django.conf import settings


class Outbox(object):
    def __init__(self, *args, **kwargs):
        self.volume = Path(settings.EMAIL_FILE_PATH)

    def __len__(self):
        count = 0
        for file in self.volume.iterdir():
            if file.is_file():
                count += 1
        return count

    def __getitem__(self, position):
        """
        Return file as email object
        """
        email_files = [
            file for file in self.volume.iterdir() if file.is_file()
        ]
        try:
            email_file = email_files[position]
        except IndexError:
            raise Exception

        with email_file.open() as f:
            return email.message_from_file(f, policy=email.policy.default)

    def __del__(self):
        """
        Clear the email directory when fixture is out of scope
        """
        for file in self.volume.iterdir():
            if file.is_file():
                file.unlink()
        return


@pytest.fixture(scope="function")
def mail_outbox(mailoutbox):
    """
    Django uses the locmem email backend for testing that exposes an outbox
    which can be queried, cleared, etc.  The pytest-django fixture mailoutbox
    is a shortcut to the output attribute.

    Using a multi-container dockerized test environment means email is on the
    process acting as the host, not the process executing the functional test
    scripts.  The file-based email backend can be used to save emails to a
    shared network volume and accessed across processes, but we need to
    implement the outbox interface.
    """
    staging_server = os.environ.get("STAGING_SERVER")
    if staging_server:
        print("Using staging server > replacing default mailoutbox fixture")
        outbox = Outbox()
        yield outbox
        outbox.clear()
    else:
        return mailoutbox
