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


def test_localStorage_dict_get(needs_database):
    localStorage["test_key"] = {"dict_key": 12}
    assert localStorage.dict_get("test_key", "dict_key") == 12

    assert localStorage.dict_get("test_key2", "dict_key") == None
    assert localStorage.dict_get("test_key", "dict_key2") == None


def test_localStorage_dict_update(needs_database):
    localStorage["test_key"] = {"dict_key1": 12, "dict_key2": 13, "dict_key3": 14}

    localStorage.dict_update("test_key", {"dict_key1": 22})
    assert localStorage["test_key"] == {
        "dict_key1": 22,
        "dict_key2": 13,
        "dict_key3": 14,
    }

    localStorage.dict_update("test_key", {"dict_key4": 25})
    assert localStorage["test_key"] == {
        "dict_key1": 22,
        "dict_key2": 13,
        "dict_key3": 14,
        "dict_key4": 25,
    }


def test_localStorage_dict_pop(needs_database):
    localStorage["test_key"] = {"dict_key1": 12, "dict_key2": 13, "dict_key3": 14}

    assert localStorage.dict_pop("test_key", "dict_key1") == 12
    assert localStorage["test_key"] == {
        "dict_key2": 13,
        "dict_key3": 14,
    }
