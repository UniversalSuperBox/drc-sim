#!/usr/bin/env python3
import os
import sys

from drcsim.server.data import constants
from drcsim.server.data.args import Args
from drcsim.server.data.config_general import ConfigGeneral
from drcsim.server.ui.cli.cli_main import CliMain
from drcsim.server.util.logging.logger import Logger
from drcsim.server.util.logging.logger_backend import LoggerBackend
from drcsim.server.util.logging.logger_cli import LoggerCli
from drcsim.server.util.logging.logger_gui import LoggerGui
from drcsim.server.util.logging.logger_wpa import LoggerWpa
from drcsim.server.util.os_util import OsUtil


def init_loggers():
    """
    Initialize loggers with a specified log level if they have the argument.
    :return: None
    """
    loggers = (Logger, LoggerBackend, LoggerGui, LoggerCli, LoggerWpa)
    for logger in loggers:
        if Args.args.debug:
            logger.set_level(Logger.DEBUG)
        elif Args.args.extra:
            logger.set_level(Logger.EXTRA)
        elif Args.args.finer:
            logger.set_level(Logger.FINER)
        elif Args.args.verbose:
            logger.set_level(Logger.VERBOSE)
        else:
            logger.set_level(Logger.INFO)


def start():
    """
    Main loop. It can be GUI or CLI based on args. Dies if an error makes it way here or main loop stops.
    :return: None
    """
    ui = None
    try:
        if Args.args.cli:
            Logger.info("Enabling CLI")
            ui = CliMain()
        else:
            Logger.info("Enabling GUI")
            from drcsim.server.ui.gui.gui_main import GuiMain
            ui = GuiMain()
        ui.start()
    except KeyboardInterrupt:
        if ui:
            ui.stop()
    except Exception as e:
        if ui:
            ui.stop()
        Logger.exception(e)
    Logger.info("Exiting")


def log_level():
    """
    Log at every level to display the levels that are enabled.
    :return: None
    """
    # Logger info
    Logger.debug("Debug logging enabled")
    Logger.extra("Extra debug logging enabled")
    Logger.finer("Finer debug logging enabled")
    Logger.verbose("Verbose logging enabled")
    if LoggerWpa.get_level() <= Logger.FINER:
        LoggerWpa.warn("At this log level SSIDs are logged!")


def check_root():
    """
    Exit if not root
    :return:
    """
    if os.getuid() != 0:
        Logger.throw("Not running as root!")
        sys.exit()
    else:
        Logger.extra("I am root!")


def main():
    """
    Main entry point. Parses arguments, loads configuration files, initialized loggers and starts the main loop.
    :return: None
    """
    Args.parse_args()
    ConfigGeneral.load()
    ConfigGeneral.save()
    init_loggers()
    check_root()
    Logger.info("Initializing drc-sim-backend version %s", constants.VERSION)
    Logger.info("Using \"%s\" as home folder.", constants.PATH_ROOT)
    log_level()
    OsUtil.log_info(Logger)
    start()


if __name__ == '__main__':
    main()
