from mgylabs.db.storage import localStorage


def test_localStorage_set(needs_database):
    localStorage["test_key"] = 12
    assert localStorage["test_key"] == 12


def test_localStorage_get(needs_database):
    assert localStorage["test_key"] is None

    localStorage["test_key"] = 12
    assert localStorage["test_key"] == 12


def test_localStorage_update(needs_database):
    localStorage["test_key"] = 12
    assert localStorage["test_key"] == 12

    localStorage["test_key"] = 135
    assert localStorage["test_key"] == 135


def test_localStorage_delete(needs_database):
    localStorage["test_key"] = 12
    assert localStorage["test_key"] == 12

    del localStorage["test_key"]

    assert "test_key" not in localStorage
    assert localStorage["test_key"] is None
