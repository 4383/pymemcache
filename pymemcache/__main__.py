#!-*-coding:utf-8-*-
import argparse
import sys
import textwrap

from pymemcache import __version__
from pymemcache.cmd import Interpreter
from pymemcache.exceptions import MemcacheCommandsError
from pymemcache.cmd.console import Console
import pymemcache.cmd.utils as utils

quiet = False
ignore = ["set_mutli"]
quit = ["quit", "exit", "bye", "stop"]
helpme = ["-h", "--help", "h", "help"]


def parser():
    """
    Command line arguments parser.
    """
    description = textwrap.dedent('''
        Pymemcache command line client.

        Set and get values from a memcache server or cluster.
        Using pymemcache {version}
    '''.format(version=__version__))
    argparser = argparse.ArgumentParser(description=description)
    argparser.add_argument("--host", help="Memcache host address")
    argparser.add_argument("-p", "--port",
                           type=int, default=11211,
                           help="Memcache server port (default 11211)")
    argparser.add_argument("-c", "--cmd", help="Memcache command to execute",
                           default=None)
    argparser.add_argument("-r", "--raw", action='store_true',
                           help="Display raw commands results",
                           default=False)
    argparser.add_argument("-q", "--quiet", action='store_true',
                           help="Only print result command output",
                           default=False)
    argparser.add_argument("-v", "--version", action='store_true',
                           help="Display pymemcache version and quit",
                           default=None)
    return argparser.parse_args()


def main():
    """
    Pymemcache interactive client available via CLI.
    """
    args = parser()
    host = args.host
    port = args.port
    cmd = args.cmd
    raw = args.raw
    global quiet
    get_version = args.version
    quiet = args.quiet if not get_version else False
    console = Console(quiet)

    host = utils.get_host(args.host)
    try:
        interpreter = Interpreter(host, port, raw)
    except MemcacheCommandsError as err:
        console.error(err)
        sys.exit(1)
    if get_version:
        interpreter.get_version()
        sys.exit(0)
    if not cmd:
        try:
            interpreter.interactive()
        except KeyboardInterrupt:
            console.display(
                "\nUser keyboard interrupt...\nquit pymemcache CLI\nBye!",
                force=False)
    else:
        cmd, params = utils.format_cmd(cmd)
        return interpreter.execute(cmd, params)


if __name__ == "__main__":
    main()
