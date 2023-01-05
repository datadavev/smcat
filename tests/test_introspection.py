import pytest
import smcat.models


def test_getroot():
    engine = smcat.models.init_db("sqlite:///test.db")
    result = smcat.models.getSitemapRoots(engine)
    for row in result:
        print(f"RESULT = {row}")