import pytest
import datetime
import smcat.common

date_cases = [
    [
        "2011-08-15T08:15:12.0",
        datetime.datetime(2011, 8, 15, 8, 15, 12, 0, datetime.timezone.utc),
    ],
    ["2011-08-15", datetime.datetime(2011, 8, 15, 0, 0, 0, 0, datetime.timezone.utc)],
    [
        "2011-08-15T08:15:12.0+0000",
        datetime.datetime(2011, 8, 15, 8, 15, 12, 0, datetime.timezone.utc),
    ],
    [
        "2011-08-15T08:15:12.0+0100",
        datetime.datetime(2011, 8, 15, 7, 15, 12, 0, datetime.timezone.utc),
    ],
    [
        "Sun, 06 Nov 1994 08:49:37 GMT",
        datetime.datetime(1994, 11, 6, 8, 49, 37, tzinfo=datetime.timezone.utc)
    ],
    [
        "today",
        None
    ]
]


@pytest.mark.parametrize("ds,expected", date_cases)
def test_parseDateTimeString(ds, expected):
    dt = smcat.common.parseDatetimeString(ds)
    assert dt == expected
