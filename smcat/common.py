import re
import datetime
import ciso8601
import email.utils

JSON_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
"""datetime format string for generating JSON content
"""


def regex(x):
    if isinstance(x, str):
        return re.compile(x)
    return x


def dtnow():
    """
    Now, with UTC timezone.

    Returns: datetime
    """
    return datetime.datetime.now(datetime.timezone.utc)


def datetimeToJsonStr(dt):
    """
    Render datetime to JSON datetime string

    Args:
        dt: datetime

    Returns: string
    """
    if dt is None:
        return None
    return dt.strftime(JSON_TIME_FORMAT)


def parseDatetimeString(ds):
    dt = None
    if ds is None:
        return dt
    try:
        # try common ISO8601 representations
        dt = ciso8601.parse_datetime(ds)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        else:
            dt = dt.astimezone(datetime.timezone.utc)
    except ValueError as e:
        pass
    if dt is None:
        # try RFC 5322, e.g. HTTP header
        try:
            dt = email.utils.parsedate_to_datetime(ds)
        except TypeError as e:
            pass
    if ds.lower() in ["now","instant",]:
        dt = dtnow()

    return dt
