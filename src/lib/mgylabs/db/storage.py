from mgylabs.db.models import HashStore


class Storage:
    def __len__(self):
        return HashStore.count()

    def __getitem__(self, key):
        return HashStore.get(key=key).first()

    def __contains__(self, key):
        return self.__getitem__(key) is not None

    def __setitem__(self, key, value):
        return HashStore.update_or_create(key=key, defaults={"value": value})[0]

    def __delitem__(self, key):
        self.__getitem__(key).delete()


LocalStorage = Storage()
