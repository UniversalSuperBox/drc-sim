import os

import importlib.resources
import importlib.util
import sys

from drcsim.server.util.logging.logger import Logger


def join(*args):
    return os.path.join(*args)


class Resource:
    def __init__(self, in_path):
        pre = "resources/"
        Logger.debug("Loading resource \"%s\"", join(pre, in_path))
        try:
            ref = importlib.resources.files("drcsim").joinpath(pre, in_path)
            with open(ref, "rb") as f:
                self.resource = f.read()
            Logger.extra("Found resource in package.")
        except FileNotFoundError:
            Logger.throw("Could not find resource: %s" % join(pre, in_path))
            sys.exit()

    def _set_self_to_file(self, file_path):
        return
