#!-*-coding:utf-8-*-

import sys
import socket
import re
import pymemcache
from pymemcache.cmd.console import Console
import pymemcache.cmd.utils as utils

console = Console(True)


class Interpreter:

    def __init__(self, host, port, raw_output=False):
        self.host = host
        self.port = port
        self.raw_output = raw_output
        self.cmd_history = []
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
            raise pymemcache.MemcacheCommandsError(str(err))
        except OSError as err:
            err = "{err} ({host}:{port})\nServer not found... abort".format(
                err=err,
                host=self.host,
                port=self.port)
            raise pymemcache.MemcacheCommandsError(err)
        else:
            console.info("Connected to {host}:{port}".format(
                         host=self.host, port=self.port))
            console.info("Memcache server version: {version}".format(
                         version=self.version))

    def history(self):
        """
        Display commands history.
        """
        if not self.cmd_history:
            console.display("No history available...", force=True)
        for index, entry in enumerate(self.cmd_history, 1):
            console.display("{index} {entry}".format(index=index, entry=entry),
                            force=True)

    def _retrieve_from_history(self, cmd):
        match = re.match(r"![0-9]+", cmd)
        if match:
            try:
                cmd_index = int(match.string.replace("!", "")) - 1
                return self.cmd_history[cmd_index]
            except IndexError:
                console.error("Index not found in history", force=True)
        return cmd

    def interactive(self):
        """
        Execute commands interpreter.
    
        Interact with Memcache server by using pymemcache API.
        """
        console.info('Enter interactive mode, use "help" for help', force=True)
        while True:
            user_input = self._retrieve_from_history(input(">>> "))
            cmd, params = utils.format_cmd(user_input)
            if cmd not in self.commands:
                console.error(
                    'Command not found: {cmd}\nUse "help" for help'.format(
                        cmd=cmd), force=True)
                continue
            self.execute(cmd, params)
            self.cmd_history.append(user_input)

    def _params_to_func_parameters(self, cmd, params):
        """
        Transform command line given by user into args list
        compatible with called command method signature.
        """
        params = self.commands[cmd]["parser"].parse_args(params)
        expected_params = self.commands[cmd]["params"]
        unordered_kwargs = {}
        for param in [name for name in dir(params)
            if not name.startswith("_")]:
            key = param
            value = getattr(params, param)
            unordered_kwargs.update({key: value})
        # Now using a list instead of a dict to keep parameters order
        # to pass to the called function by respecting signature.
        # dict is unordered and we want to ordered items to avoid errors.
        args = []
        if expected_params:
            for el in expected_params.split(","):
                name, typeof = el.replace(" ", "").split(":")
                value = unordered_kwargs[name]
                # Special treatment for list parameters
                # argparse split char by char
                if typeof == "list":
                    tmp = []
                    for el in value:
                        tmp.append("".join(el))
                    value = tmp
                args.append(value)
        return args

    def execute(self, cmd, params):
        """
        Execute the given command and passing parameters
        """
        if "-h" in params or "--help" in params:
            # turn off help managed by argparse to avoid sys exit
            # raised by arparse if we use -h/--help on it
            self.command_help(cmd)
            return
        try:
            args = self._params_to_func_parameters(cmd, params)
        except SystemExit:
            # SystemExit catch sys.exit(1) raised by argparse
            # when something went wrong with commands parameters parse
            # example: missing a required positional argument or something
            # like that
            # At this point argparse have already display the command helping
            # message and we want to return status code to inform the CLI mode
            # that something went wrong. Interactive mode doesn't need to
            # know the command status code since we already display an error
            # message by using argparse
            return 1
        try:
            result = self.commands[cmd]["method"](*args)
        except (TypeError,
                pymemcache.MemcacheCommandsError,
                pymemcache.MemcacheServerError,
                pymemcache.MemcacheClientError,
                pymemcache.MemcacheUnknownError,
                pymemcache.MemcacheUnknownCommandError,
                pymemcache.MemcacheIllegalInputError,
                pymemcache.MemcacheUnexpectedCloseError) as err:
            console.error(err, force=True)
            return 1
        except socket.timeout:
            console.error("Connection timeout... abort", force=True)
            sys.exit(1)
        except socket.error:
            console.error("Socket error... abort", force=True)
            sys.exit(1)
        else:
            if result:
                if isinstance(
                    self.commands[cmd]["return"],
                    (list, tuple, dict)):
                    console.info(result, force=True)
                else:
                    if self.raw_output:
                        console.info(result, force=True)
                    else:
                        console.info(result, force=True)
            return 0

    def command_help(self, cmd):
        """
        Display help related to command

        Args:
          cmd: str, command to display helping message
        """
        console.display(self.commands[cmd]["parser"].print_help(), force=True)

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

    def inspect(self, cmd: str) -> None:
        """
        Inspect available commands.

        Like a debug mode where you can get informations about
        the specified command.

        Args:
          cmd: str, the command to inspect.

        Return:
          None
        """
        try:
            cmd = self.commands[cmd]
        except KeyError:
            message = "Command to inspect not found ({})".format(cmd)
            raise pymemcache.MemcacheCommandsError(message)
        for el in cmd:
            console.warning(
                "{} informations:".format(el.capitalize()),
                force=True)
            console.info(cmd[el], force=True)

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
