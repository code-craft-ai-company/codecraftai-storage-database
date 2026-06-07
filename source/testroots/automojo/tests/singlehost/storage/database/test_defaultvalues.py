"""
.. module:: test_defaultvalues
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for :mod:`automojo.storage.database.defaultvalues`.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"

from datetime import datetime, timedelta, timezone
from unittest import mock
from uuid import UUID

from automojo.storage.database import defaultvalues


def test_returns_a_string() -> None:
    """
        Verify that :func:`new_uuid` returns a ``str`` value.
    """
    rtnval = defaultvalues.new_uuid()
    assert isinstance(rtnval, str)
    return


def test_returns_a_valid_uuid_format() -> None:
    """
        Verify that :func:`new_uuid` returns a string parseable as a UUID.
    """
    rtnval = defaultvalues.new_uuid()
    # UUID() raises if rtnval is not a valid UUID string.
    parsed = UUID(rtnval)
    assert str(parsed) == rtnval
    return


def test_returns_uuid4_variant() -> None:
    """
        Verify that :func:`new_uuid` returns a uuid4 (random) UUID.
    """
    rtnval = defaultvalues.new_uuid()
    parsed = UUID(rtnval)
    assert parsed.version == 4
    return


def test_returns_unique_values_across_calls() -> None:
    """
        Verify that calling :func:`new_uuid` repeatedly produces unique values.
    """
    first = defaultvalues.new_uuid()
    second = defaultvalues.new_uuid()
    assert first != second
    return


def test_returns_a_datetime() -> None:
    """
        Verify that :func:`utc_now` returns a :class:`datetime` instance.
    """
    rtnval = defaultvalues.utc_now()
    assert isinstance(rtnval, datetime)
    return


def test_returned_datetime_is_timezone_aware_utc() -> None:
    """
        Verify that the returned datetime carries the UTC timezone.
    """
    rtnval = defaultvalues.utc_now()
    assert rtnval.tzinfo is not None
    offset = rtnval.utcoffset()
    assert offset == timedelta(0)
    return


def test_uses_datetime_now_with_utc_timezone() -> None:
    """
        Verify that :func:`utc_now` calls :meth:`datetime.now` with UTC.
    """
    fixed_now = datetime(2026, 4, 27, 12, 0, 0, tzinfo=timezone.utc)
    with mock.patch.object(defaultvalues, "datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        rtnval = defaultvalues.utc_now()

    mock_datetime.now.assert_called_once_with(timezone.utc)
    assert rtnval == fixed_now
    return


def test_default_span_is_24_hours() -> None:
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

    assert expiration >= lower_bound
    assert expiration <= upper_bound
    return


def test_custom_span_overrides_default() -> None:
    """
        Verify that an explicit ``span`` is added to the current UTC time.
    """
    fixed_now = datetime(2026, 4, 27, 12, 0, 0, tzinfo=timezone.utc)
    custom_span = timedelta(hours=2)

    with mock.patch.object(defaultvalues, "utc_now", return_value=fixed_now):
        expiration = defaultvalues.reset_token_expiration(span=custom_span)

    expected = fixed_now + custom_span
    assert expiration == expected
    return


def test_zero_span_returns_now() -> None:
    """
        Verify that a zero ``span`` yields an expiration equal to "now".
    """
    fixed_now = datetime(2026, 4, 27, 12, 0, 0, tzinfo=timezone.utc)

    with mock.patch.object(defaultvalues, "utc_now", return_value=fixed_now):
        expiration = defaultvalues.reset_token_expiration(span=timedelta(0))

    assert expiration == fixed_now
    return


def test_returns_timezone_aware_utc() -> None:
    """
        Verify that the result is a UTC timezone-aware datetime.
    """
    expiration = defaultvalues.reset_token_expiration()
    assert expiration.tzinfo is not None
    assert expiration.utcoffset() == timedelta(0)
    return
