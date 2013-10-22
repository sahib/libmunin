#!/usr/bin/env python
# encoding: utf-8


import os

try:
    from xdg import BaseDirectory
    HAS_XDG = True
except ImportError:
    HAS_XDG = False


def check_or_mkdir(path):
    'Check if path does exist, if not mkdir it.'
    if not os.path.exists(path):
        os.mkdir(path)


def get_cache_path(extra_name=None):
    '''Tries to find out the XDG caching path of your system.

    This is done preferrably with PyXDG. If it's not installed,
    we try the XDG_CACHE_HOME environment variable or default to ~/.cache/

    If the path does not exist yet it will be created for you.

    :param extra_name: Extra path component to append to the path (or None).
    :returns: The full path, e.g.: /home/user/.cache/libmunin/<extra_name>
    '''
    if HAS_XDG:
        base_dir = BaseDirectory.xdg_cache_home
    else:
        base_dir = os.environ.get('XDG_CACHE_HOME') or os.path.join(os.path.expanduser('~', '.cache'))

    base_dir = os.path.join(base_dir, 'libmunin')
    check_or_mkdir(base_dir)
    return base_dir if not extra_name else os.path.join(base_dir, extra_name)


if __name__ == '__main__':
    print('Your cache path seems to be:', get_cache_path())
    print('Here, Ill get you this file:', get_cache_path('new_file'))
