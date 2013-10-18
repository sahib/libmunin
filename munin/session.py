#!/usr/bin/env python
# encoding: utf-8

from munin.caching import get_cache_path, check_or_mkdir
import shutil


class Session:
    def __init__(self, name, attribute_mask):
        self._attr_mask = attribute_mask

    @staticmethod
    def load_from(session_name):
        base = get_cache_path(session_name)
        os.path.join()
        return Session(session_name, {})

    def save_to(self, name):
        base = get_cache_path(name)
        if os.path.exists(path):
            shutil.rmtree(base)
        check_or_mkdir(base)



if __name__ == '__main__':
    pass
