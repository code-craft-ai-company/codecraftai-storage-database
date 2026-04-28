"""
.. module:: test_defaultvalues
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for :mod:`automojo.storage.database.defaultvalues`.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"

import unittest

from datetime import datetime, timedelta, timezone
from unittest import mock
from uuid import UUID

from automojo.storage.database import defaultvalues


class TestNewUuid(unittest.TestCase):
    """
        Verify the behavior of :func:`automojo.storage.database.defaultvalues.new_uuid`.
    """

    def test_returns_a_string(self) -> None:
        """
            Verify that :func:`new_uuid` returns a ``str`` value.
        """
        rtnval = defaultvalues.new_uuid()
        self.assertIsInstance(rtnval, str)
        return

    def test_returns_a_valid_uuid_format(self) -> None:
        """
            Verify that :func:`new_uuid` returns a string parseable as a UUID.
        """
        rtnval = defaultvalues.new_uuid()
        # UUID() raises if rtnval is not a valid UUID string.
        parsed = UUID(rtnval)
        self.assertEqual(str(parsed), rtnval)
        return

    def test_returns_uuid4_variant(self) -> None:
        """
            Verify that :func:`new_uuid` returns a uuid4 (random) UUID.
        """
        rtnval = defaultvalues.new_uuid()
        parsed = UUID(rtnval)
        self.assertEqual(parsed.version, 4)
        return

    def test_returns_unique_values_across_calls(self) -> None:
        """
            Verify that calling :func:`new_uuid` repeatedly produces unique values.
        """
        first = defaultvalues.new_uuid()
        second = defaultvalues.new_uuid()
        self.assertNotEqual(first, second)
        return


class TestUtcNow(unittest.TestCase):
    """
        Verify the behavior of :func:`automojo.storage.database.defaultvalues.utc_now`.
    """

    def test_returns_a_datetime(self) -> None:
        """
            Verify that :func:`utc_now` returns a :class:`datetime` instance.
        """
        rtnval = defaultvalues.utc_now()
        self.assertIsInstance(rtnval, datetime)
        return

    def test_returned_datetime_is_timezone_aware_utc(self) -> None:
        """
            Verify that the returned datetime carries the UTC timezone.
        """
        rtnval = defaultvalues.utc_now()
        self.assertIsNotNone(rtnval.tzinfo)
        offset = rtnval.utcoffset()
        self.assertEqual(offset, timedelta(0))
        return

    def test_uses_datetime_now_with_utc_timezone(self) -> None:
        """
            Verify that :func:`utc_now` calls :meth:`datetime.now` with UTC.
        """
        fixed_now = datetime(2026, 4, 27, 12, 0, 0, tzinfo=timezone.utc)
        with mock.patch.object(defaultvalues, "datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_now
            rtnval = defaultvalues.utc_now()

        mock_datetime.now.assert_called_once_with(timezone.utc)
        self.assertEqual(rtnval, fixed_now)
        return


class TestResetTokenExpiration(unittest.TestCase):
    """
        Verify the behavior of :func:`automojo.storage.database.defaultvalues.reset_token_expiration`.
    """

    def test_default_span_is_24_hours(self) -> None:
        """
            Verify that omitting ``span`` results in an expiration 24 hours from now.
        """
        before = datetime.now(timezone.utc)
        expiration = defaultvalues.reset_token_expiration()
        after = datetime.now(timezone.utc)

        # The expiration should be roughly 24 hours after 'before' and at most
        # 24 hours after 'after'. Allow for a small skew window between the two
        # timestamps captured around the call.
        lower_bound = before + timedelta(days=1) - timedelta(seconds=1)
        upper_bound = after + timedelta(days=1) + timedelta(seconds=1)

        self.assertGreaterEqual(expiration, lower_bound)
        self.assertLessEqual(expiration, upper_bound)
        return

    def test_custom_span_overrides_default(self) -> None:
        """
            Verify that an explicit ``span`` is added to the current UTC time.
        """
        fixed_now = datetime(2026, 4, 27, 12, 0, 0, tzinfo=timezone.utc)
        custom_span = timedelta(hours=2)

        with mock.patch.object(defaultvalues, "utc_now", return_value=fixed_now):
            expiration = defaultvalues.reset_token_expiration(span=custom_span)

        expected = fixed_now + custom_span
        self.assertEqual(expiration, expected)
        return

    def test_zero_span_returns_now(self) -> None:
        """
            Verify that a zero ``span`` yields an expiration equal to "now".
        """
        fixed_now = datetime(2026, 4, 27, 12, 0, 0, tzinfo=timezone.utc)

        with mock.patch.object(defaultvalues, "utc_now", return_value=fixed_now):
            expiration = defaultvalues.reset_token_expiration(span=timedelta(0))

        self.assertEqual(expiration, fixed_now)
        return

    def test_returns_timezone_aware_utc(self) -> None:
        """
            Verify that the result is a UTC timezone-aware datetime.
        """
        expiration = defaultvalues.reset_token_expiration()
        self.assertIsNotNone(expiration.tzinfo)
        self.assertEqual(expiration.utcoffset(), timedelta(0))
        return


if __name__ == "__main__":
    unittest.main()
