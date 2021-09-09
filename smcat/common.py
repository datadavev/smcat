import re
import time
import datetime
import ciso8601
import email.utils
import hashids

JSON_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
"""datetime format string for generating JSON content
"""

TEXT_MEDIA = re.compile(r"^text/(plain|strings|markdown)")
HTML_MEDIA = re.compile(r"^(text/html)|(application/(xml|xhtml\+xml))")
XML_MEDIA = re.compile(r"^(text|application)/xml")
JSON_MEDIA = re.compile(r"application/(.*\+)?json")
JSONLD_MEDIA = re.compile(r"application/(ld\+)?json")

HASH_ZERO = 1631199000000
HASHIDS = hashids.Hashids()

def regex(x):
    if isinstance(x, str):
        return re.compile(x)
    return x

def getId():
    time.sleep(0.001)
    v = int(time.time()*1000)-HASH_ZERO
    return HASHIDS.encode(v)


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
    if ds.lower() in [
        "now",
        "instant",
    ]:
        dt = dtnow()

    return dt


def parseContentType(content_type:str) -> [str,str]:
    '''
    Parse content-type header to media_type and charset

    Args:
        content_type: content-type header string

    Returns:
        media-type, charset
    '''
    if isinstance(content_type, bytes):
        content_type = content_type.decode("utf-8")
    content_type = content_type.strip()
    if len(content_type) < 2:
        return None, None
    parts = content_type.split("; ")
    media_type = parts[0]
    charset = None
    if len(parts) > 1:
        k,v = parts[1].strip().split("=")
        if k.lower() == "charset":
            charset = v
    return media_type, charset


def isText(media_type:str)->bool:
    if TEXT_MEDIA.match(media_type) is not None:
        return True
    return False

def isHtml(media_type:str)->bool:
    if HTML_MEDIA.match(media_type) is not None:
        return True
    return False

def isXml(media_type: str)->bool:
    if XML_MEDIA.match(media_type) is not None:
        return True
    return False

def isJson(media_type: str)->bool:
    if JSON_MEDIA.match(media_type) is not None:
        return True
    return False

def isJsonld(media_type: str)->bool:
    if JSONLD_MEDIA.match(media_type) is not None:
        return True
    return False

def mediaKind(media_type:str)->[str]:
    res = []
    if isText(media_type):
        res.append("text")
    if isHtml(media_type):
        res.append("html")
    if isXml(media_type):
        res.append("xml")
    if isJson(media_type):
        res.append("json")
    if isJsonld(media_type):
        res.append("jsonld")
    return res