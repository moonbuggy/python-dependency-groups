#!/usr/bin/env python3

"""
Python Module Dependency Groups.

Accepts Python module names as arguments, determines the dependency tree and
then outputs groups of modules, one group per line, in the order they should
be built to satisfy dependencies.

This is useful if we're automatically building wheels from source in Docker
containers.

i.e. There's no point building cffi as part of the cryptography build when
we're building cffi standalone in another container anyway. Build cffi first,
then it can be imported into the cryptography build.
"""

import re
import sys
import signal
from requests_cache import CachedSession
from toposort import toposort


def signal_handler(_sig, _frame):
    """Handle SIGINT cleanly."""
    print('\nSignal interrupt. Exiting.')
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


class PythonModule():
    """A python module."""

    def __init__(self, mod_string, ses):
        """Populate self with relevant module data."""
        self.ses = ses

        self.parse_mod_string(mod_string)
        self.get_api_data()
        self.set_self()

    def parse_mod_string(self, mod_string):
        """Determine if module string includes version."""
        split_string = mod_string.rsplit('-', 1)
        self.name = mod_string
        self.version = None

        try:
            if re.fullmatch(r'[0-9\.]+', split_string[1]):
                self.name = split_string[0]
                self.version = split_string[1]
        except IndexError:
            pass

        self.name_lower = self.name.lower()

    def get_api_data(self):
        """
        Get PyPi API data for module.

        Try for version-specific deps, fall back to the global deps.
        """
        self.data = None
        if self.version:
            self.data = self.get_url(self.name + '/' + self.version)

        if not self.data or not self.data['info']['requires_dist']:
            self.data = self.get_url(self.name)

    def get_url(self, url):
        """Get JSON data from PyPi API."""
        res = self.ses.get('https://pypi.org/pypi/' + url + '/json')
        res.raise_for_status()
        return res.json()

    def set_self(self):
        """
        Set self variables from API data.

        Use the module name from the API, to get the correct case.
        """
        self.name = self.data['info']['name']

        self.deps = set()
        deps = self.data['info']['requires_dist']
        if deps:
            self.deps = [x.split(' ', 1)[0] for x in deps if ";" not in x]

        if self.version:
            self.name_ver = self.name + '-' + self.version
        else:
            self.name_ver = self.name
        self.name_ver_lower = self.name_ver.lower()


def add_modules(mods, mod_dict, dep_tree, ses):
    """
    Add modules from a list or set.

    The lowercase '<module>-<version>' is necessary as an index because deps
    from the API will be lowercase and won't match in the sort. 'mod_dict'
    provides the proper case for the module name in the output.
    """
    recurse_mods = set()
    for mod_string in mods:
        mod = PythonModule(mod_string, ses)

        if mod.name_ver_lower in mod_dict.keys():
            continue

        mod_dict[mod.name_ver_lower] = mod.name_ver
        dep_tree[mod.name_ver_lower] = mod.deps
        recurse_mods.update(mod.deps)

    if recurse_mods:
        add_modules(recurse_mods, mod_dict, dep_tree, ses)


def main():
    """Parse arguments matching <module>(-<version), then determine groups."""
    dep_tree = {}
    mod_dict = {}

    arg_modules = sys.argv[1:]

    ses = CachedSession(backend='memory')

    add_modules(arg_modules, mod_dict, dep_tree, ses)

    for group in toposort(dep_tree):
        group = [x if x not in mod_dict else mod_dict[x] for x in group]
        print(' '.join(map(str, sorted(group, key=str.casefold))))


if __name__ == '__main__':
    main()
