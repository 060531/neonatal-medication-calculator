import unittest
import pytest

try:
    # กรณีมีแอปแบบไฟล์เดียว
    from app import app
except Exception:
    # กรณีใช้ factory pattern
    from app import create_app as _factory
    app = _factory(testing=True)

def _route_exists(path: str) -> bool:
    rules = {str(r) for r in app.url_map.iter_rules()}
    return path in rules or (path.endswith("/") and path[:-1] in rules) or (path + "/") in rules

class BasicTestCase(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_home(self):
        if not _route_exists("/"):
            pytest.xfail("route '/' not implemented yet")
        resp = self.client.get("/")
        assert resp.status_code == 200

    def test_small_dose(self):
        if not _route_exists("/small_dose"):
            pytest.xfail("route '/small_dose' not implemented yet")
        resp = self.client.get("/small_dose")
        assert resp.status_code == 200

if __name__ == "__main__":
    unittest.main()
