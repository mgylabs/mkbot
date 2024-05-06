import pickle
import traceback

from mgylabs.db import database
from mgylabs.db.models import HashStore


class Storage:
    def __len__(self):
        return HashStore.count()

    def __getitem__(self, key):
        val = HashStore.get_one_or_none(key=key)
        if val is None:
            return None
        else:
            try:
                obj = pickle.loads(val.value)
            except Exception:
                traceback.print_exc()
            else:
                return obj

    def __contains__(self, key):
        return self.__getitem__(key) is not None

    def __setitem__(self, key, value):
        HashStore.update_or_create(key=key, defaults={"value": pickle.dumps(value)})

    def __delitem__(self, key):
        if item := HashStore.get_one(key=key):
            item.delete()

    def dict_get(self, key, dict_key):
        obj = self.__getitem__(key)
        if obj is None:
            return None
        assert isinstance(obj, dict)
        return obj.get(dict_key)

    def dict_include(self, key, dict_key):
        obj = self.__getitem__(key)
        if obj is None:
            return False
        assert isinstance(obj, dict)
        return dict_key in obj

    def dict_update(self, key, value: dict):
        with database.transaction():
            obj = self.__getitem__(key)
            if obj is None:
                obj = {}
            assert isinstance(obj, dict)
            obj.update(value)
            self.__setitem__(key, obj)

    def dict_pop(self, key, dict_key):
        obj = self.__getitem__(key)
        assert isinstance(obj, dict)
        r = obj.pop(dict_key)
        self.__setitem__(key, obj)
        return r


localStorage = Storage()
