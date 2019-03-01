#!-*-coding:utf-8-*-
import argparse
import inspect
from inspect import Parameter
import shlex
import textwrap


def get_host(host):
    """
    Ask for host if not provided as a CLI parameter.
    """
    if host:
        return host
    while True:
        host = input("Host to connect: ")
        if host:
            return host


def get_parser(signature, cmd, description):
    parser = argparse.ArgumentParser(
        prog=cmd,
        description=description)
    for param in signature.parameters.values():
        nargs = None
        if param.annotation is list:
            nargs = "+"
        if param.default is not Parameter.empty:
            parser.add_argument('--{name}'.format(name=param.name),
                       type=param.annotation, default=param.default)
        else:
            if nargs:
                parser.add_argument(param.name, nargs=nargs,
                                    type=param.annotation)
            else:
                parser.add_argument(param.name, nargs=nargs,
                                    type=param.annotation)
    return parser


def get_cmds(obj, ignore=[], ignore_private=True):
    commands = {}
    for cmd in dir(obj):
        if not callable(getattr(obj, cmd)) or cmd in ignore:
           continue
        if ignore_private:
            if cmd.startswith("_"):
                continue
        method = getattr(obj, cmd)
        signature = inspect.signature(method)
        params = ", ".join([str(param) for param in
                          signature.parameters.values()])
        description = textwrap.dedent(method.__doc__)
        usage = "Usage ({cmd}): {params}\nDescription:\n{description}".format(
            cmd=cmd, params=params, description=description)
        short_usage = description.split("\n")
        short_usage = short_usage[0] if short_usage[0] else short_usage[1]
        short_usage = short_usage.split(".")[0].strip()
        parser = get_parser(signature, cmd, description)
        commands.update({cmd: {
            "method": method,
            "usage": usage,
            "params": params,
            "short_usage": short_usage,
            "return": signature.return_annotation,
            "parser": parser,
        }})
    return commands


def format_cmd(cmd):
    """
    Extract command name and parameters.
    """
    cmd = shlex.split(cmd)
    return cmd[0], cmd[1:]
