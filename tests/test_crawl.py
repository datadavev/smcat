import pytest
import tests.testserver
import smcat.sitemap

@pytest.fixture(scope="module")
def address():
    """
    Fire up a test server that serves content from the ./data folder
    """
    _server = tests.testserver.TestServer()
    _server.start()
    yield _server.getAddress()
    _server.stop()


def test_robotstxt(address):
    url = f"{address}robots.txt"
    sm = smcat.sitemap.SiteMap(url)
    items = []
    for item in sm:
        print(item)
        items.append(item)
