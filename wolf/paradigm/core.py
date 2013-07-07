import os
import logging
import pkgutil


class Paradigm(object):
    def __init__(self, *args, **kwargs):
        # Set up a logger. Logger name will be same as the subclass.
        self.log = logging.getLogger(self.__class__.__name__)

    def scan(self, path):
        roots = []
        has_dir = hasattr(self, 'check_directory')
        has_file = hasattr(self, 'check_file')

        for root, files, dirs in os.walk(path):
            if has_dir:
                for d in dirs:
                    if self.check_directory(d):
                        roots.append(root)
                        break

            if has_file:
                for f in files:
                    if self.check_file(f):
                        roots.append(root)
                        break

        return roots


def find_paradigms():
    """
    Recursively find all installed paradigms

    Returns a list of tuples as returned by pkgutil.iter_modules()

    """

    # Find all top-level modules that are a part of "wolf".
    modules = pkgutil.iter_modules()
    modules = filter(lambda x: x[1] == 'wolf', modules)

    roots = [x[0].path for x in modules]

    for root in roots:
        print(root)
        for loader, name, ispkg in pkgutil.walk_packages(root):
            print(loader)

    # return packages
