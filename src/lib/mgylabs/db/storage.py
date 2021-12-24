import pickle
import traceback

from mgylabs.db.models import HashStore


class Storage:
    def __len__(self):
        return HashStore.count()

    def __getitem__(self, key):
        val = HashStore.get(key=key).first()
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
        HashStore.get(key=key).first().delete()


localStorage = Storage()
