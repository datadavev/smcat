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
        datetime.datetime(1994, 11, 6, 8, 49, 37, tzinfo=datetime.timezone.utc),
    ],
    ["today", None],
]

content_type_cases = [
    ["text/plain", ("text/plain", None)],
    ["text/plain; charset=UTF-8", ("text/plain", "UTF-8")],
    ["text/html; charset=UTF-8", ("text/html", "UTF-8")],
    [" text/html; charset=ISO-8859-4 ", ("text/html", "ISO-8859-4")],
    [
        "type/x.subtype+suffix;parameter; charset=UTF-8",
        ("type/x.subtype+suffix;parameter", "UTF-8"),
    ],
]

media_type_cases = [
    [
        "text/plain",
        [
            "text",
        ],
    ],
    [
        "text/html",
        [
            "html",
        ],
    ],
    [
        "application/xhtml+xml",
        [
            "html",
        ],
    ],
    ["application/octet-stream", []],
    [
        "text/strings",
        [
            "text",
        ],
    ],
    ["text/json", []],
    ["application/json", ["json", "jsonld"]],
    ["application/ld+json", ["json", "jsonld"]],
]

bool_test_cases = [
    (True, True),
    (False, False),
    ("ok", True),
    ("true", True),
    ("yes", True),
    ("YES", True),
    (1, True),
    ("1", True),
    ("999", True),
    ("no", False),
    ("0", False),
    ("False", False),
]


@pytest.mark.parametrize("ds,expected", date_cases)
def test_parseDateTimeString(ds, expected):
    dt = smcat.common.parseDatetimeString(ds)
    assert dt == expected


@pytest.mark.parametrize("ct,expected", content_type_cases)
def test_parseContentTpe(ct, expected):
    content_type, charset = smcat.common.parseContentType(ct)
    assert content_type == expected[0]
    assert charset == expected[1]


@pytest.mark.parametrize("mt,expected", media_type_cases)
def test_isMediaKind(mt, expected):
    res = smcat.common.mediaKind(mt)
    assert len(res) == len(expected)
    for v in res:
        assert v in expected


@pytest.mark.parametrize("v,expected", bool_test_cases)
def test_asbool(v, expected):
    assert smcat.common.asbool(v) == expected
