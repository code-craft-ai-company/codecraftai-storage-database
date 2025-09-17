"""
.. module:: defaultvalues
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Contains helper functions that are used to set default values.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

from typing import Optional

from uuid import uuid4

from datetime import datetime, timezone, timedelta

def new_uuid() -> str:
    """
        Creats a new UUID string in uuid4 format.
    """
    rtnval = str(uuid4())
    return rtnval

def utc_now() -> datetime:
    """
        Provides the current UTC time. This is used as a default value for datetime fields in models.
        
        :return: datetime
    """
    now = datetime.now(timezone.utc)
    return now

def reset_token_expiration(span: Optional[timedelta] = None) -> datetime:
    """
        Provides the expiration time for reset tokens. This is set to 24 hours from now.
        
        :param span: The time span that the token will be good for.  If not provided the default span is 24 hours.

        :return: datetime
    """
    if span is None:
        span =  timedelta(days=1)

    expiration = utc_now() + span

    return expiration
