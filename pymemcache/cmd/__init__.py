#!-*-coding:utf-8-*-

import sys
import socket
import pymemcache
from pymemcache.cmd.console import Console
import pymemcache.cmd.utils as utils

console = Console(True)


class CommandsError(Exception):
    pass


class Interpreter:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.ignore = {
            "client": ["set_mutli", "quit"],
            "interpreter": ["execute", "interactive", "command_help"],
        }
        self._get_client()
        self._get_commands()

    def _get_client(self):
        """
        Initialize pymemcache Client.
        """
        try:
            self.client = pymemcache.Client((self.host, self.port))
            self.version = self.client.version().decode('utf-8')
        except (pymemcache.MemcacheServerError,
                pymemcache.MemcacheClientError,
                pymemcache.MemcacheUnknownError,
                pymemcache.MemcacheUnexpectedCloseError) as err:
            raise CommandsError(str(err))
        except OSError as err:
            err = "{err} ({host}:{port})\nServer not found... abort".format(
                err=err,
                host=self.host,
                port=seifl.port)
            raise CommandsError(err)
        else:
            console.info("Connected to {host}:{port}".format(
                         host=self.host, port=self.port))
            console.info("Memcache server version: {version}".format(
                         version=self.version))

    def interactive(self):
        """
        Execute commands interpreter.
    
        Interact with Memcache server by using pymemcache API.
        """
        console.info('Enter interactive mode, use "help" for help', force=True)
        while True:
            cmd, params = utils.format_cmd(input("> "))
            if cmd not in self.commands:
                console.error(
                    'Command not found: {cmd}\nUse "help" for help'.format(
                        cmd=cmd), force=True)
                continue
            self.execute(cmd, params)

    def execute(self, cmd, params):
        if params and params[0] == "-h":
            self.command_help(cmd)
            return
        try:
            result = self.commands[cmd]["method"]()
        except (TypeError,
                pymemcache.MemcacheServerError,
                pymemcache.MemcacheClientError,
                pymemcache.MemcacheUnknownError,
                pymemcache.MemcacheUnknownCommandError,
                pymemcache.MemcacheIllegalInputError,
                pymemcache.MemcacheUnexpectedCloseError) as err:
            console.error(err, force=True)
        except socket.timeout:
            console.error("Connection timeout... abort", force=True)
            sys.exit(1)
        except socket.error:
            console.error("Socket error... abort", force=True)
            sys.exit(1)
        else:
            if result:
                console.info(result, force=True)

    def command_help(self, cmd):
        console.display(self.commands[cmd]["usage"], force=True)

    def _get_commands(self):
        """
        Get pymemcache Client available commands (based on public methods).
        """
        self.commands = {}
        self.client_cmd = utils.get_cmds(
            self.client,
            ignore=self.ignore["client"])
        self.interpreter_cmd = utils.get_cmds(
            self, 
            ignore=self.ignore["interpreter"])
        self.commands.update(self.client_cmd)
        self.commands.update(self.interpreter_cmd)

    def get_version(self):
        """
        Display version
        """
        console.info("Pymemcache CLI {version}".format(
                        version=pymemcache.__version__), force=True)
        console.info("Memcache server {version}".format(
                        version=self.version), force=True)

    def quit(self):
        """
        Quit pymemcache interpreter
        """
        console.display("Bye!", force=True)
        sys.exit(0)

    def exit(self):
        """
        Quit pymemcache interpreter
        """
        self.quit()

    def bye(self):
        """
        Quit pymemcache interpreter
        """
        self.quit()

    def stop(self):
        """
        Quit pymemcache interpreter
        """
        self.quit()

    def help(self):
        """
        Display this helping message.
        """
        console.display("Available commands:", force=True)
        for cmd in self.commands:
            console.display("\t- {cmd}: {usage}".format(
                cmd=cmd,
                usage=self.commands[cmd]["short_usage"]), force=True)
        console.display("Display command help by using:", force=True)
        console.display("<command> -h", force=True)

    def h(self):
        """
        Display this helping message.
        """
        self.help()
