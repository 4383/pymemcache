import argparse
import inspect
import socket
import sys
import textwrap

import pymemcache


pymemcache_version = pymemcache.__version__
quiet = False
ignore = ["set_mutli"]
quit = ["quit", "exit", "bye", "stop"]
helpme = ["-h", "--help", "h", "help"]


def fprint(message, force=False):
    """
    Stdout printin helper.
    """
    if quiet and not force:
        return
    print(message)


def parser():
    """
    Command line arguments parser.
    """
    description = textwrap.dedent('''
        Pymemcache command line client.

        Set and get values from a memcache server or cluster.
        Using pymemcache {version}
    '''.format(version=pymemcache_version))
    argparser = argparse.ArgumentParser(description=description)
    argparser.add_argument("--host", help="Memcache host address")
    argparser.add_argument("-p", "--port",
                           type=int, default=11211,
                           help="Memcache server port (default 11211)")
    argparser.add_argument("-c", "--cmd", help="Memcache command to execute",
                           default=None)
    argparser.add_argument("-q", "--quiet", action='store_true',
                           help="Only print result command output",
                           default=False)
    argparser.add_argument("-v", "--version", action='store_true',
                           help="Display pymemcache version and quit",
                           default=None)
    return argparser.parse_args()


def get_host():
    """
    Ask for host if not provided as a CLI parameter.
    """
    while True:
        host = input("Host to connect: ")
        if host:
            return host


def get_client(host, port):
    """
    Initialize pymemcache Client.
    """
    try:
        client = pymemcache.Client((host, port))
        version = client.version().decode('utf-8')
    except pymemcache.MemcacheServerError as err:
        fprint(err, force=True)
        sys.exit(1)
    except pymemcache.MemcacheClientError as err:
        fprint(err, force=True)
        sys.exit(1)
    except pymemcache.MemcacheUnknownError as err:
        fprint(err, force=True)
        sys.exit(1)
    except pymemcache.MemcacheUnexpectedCloseError as err:
        fprint(err, force=True)
        sys.exit(1)
    except OSError as err:
        fprint("{err} ({host}:{port})\nServer not found... abort".format(
            err=err,
            host=host,
            port=port), force=True)
        sys.exit(1)
    else:
        fprint("Connected to {host}:{port}".format(host=host, port=port))
        fprint("Memcache server version: {version}".format(version=version))
    return client, version


def display_version():
    """
    Display CLI version.
    """
    fprint("Pymemcache CLI {version}".format(version=pymemcache_version))


def main():
    """
    Pymemcache interactive client available via CLI.
    """
    args = parser()
    host = args.host
    port = args.port
    cmd = args.cmd
    global quiet
    get_version = args.version
    quiet = args.quiet if not get_version else False
    display_version()
    if get_version:
        return

    host = args.host if args.host else get_host()
    client, version = get_client(host, port)
    if not cmd:
        try:
            interactive(client, version)
        except KeyboardInterrupt:
            fprint("\nUser keyboard interrupt...\nquit pymemcache CLI\nBye!")
    else:
        cmd, params = format_cmd(cmd)
        execute(cmd, params, client)


def get_cmds(client):
    """
    Get pymemcache Client available commands (based on public methods).
    """
    return [cmd for cmd in dir(client)
            if callable(getattr(client, cmd)) and not cmd.startswith("_")
            and cmd not in ignore]


def format_cmd(cmd):
    """
    Extract command name and parameters.
    """
    cmd = cmd.split()
    return cmd[0], [el.replace(",", "") for el in cmd[1:]]


def display_cmds_help(client, cmds):
    """
    Display interpreter help.
    """
    native_cmd = [
            ("h", "Display this helping message"),
            ("help", "Display this helping message"),
            ("bye", "Stop this pymemcache client"),
            ("stop", "Stop this pymemcache client")]
    fprint("Available commands:", force=True)
    for cmd in cmds:
        available_doc = getattr(client, cmd).__doc__.split("\n")
        doc = available_doc[0] if available_doc[0] != "" else available_doc[1]
        doc = doc.split(".")[0].strip()
        fprint("\t- {cmd}: {doc}".format(cmd=cmd, doc=doc), force=True)

    for cmd in native_cmd:
        fprint("\t- {cmd}: {doc}".format(cmd=cmd[0], doc=cmd[1]), force=True)

    fprint("Display help command for available commands by using:", force=True)
    fprint("\t<command> -h", force=True)
    fprint("Example:\n\t{example}".format(
           example="{cmd} -h".format(cmd=cmds[0])), force=True)


def interactive(client, version):
    """
    Execute commands interpreter.

    Interact with Memcache server by using pymemcache API.
    """
    cmds = get_cmds(client)
    while True:
        cmd, params = format_cmd(input("> "))
        if cmd in quit:
            break
        if cmd == "version":
            display_version()
            fprint("Memcache server version: {version}".format(
                version=version))
            continue
        if cmd in helpme:
            display_cmds_help(client, cmds)
            continue
        if cmd in ignore:
            fprint("Command not available: {cmd}".format(cmd=cmd), force=True)
            continue
        if cmd not in cmds:
            fprint("Command not found: {cmd}".format(cmd=cmd), force=True)
            continue

        execute(cmd, params, client)


def cmd_help(cmd, method, signature):
    """
    Display command helping message
    """
    usage = ", ".join([str(param) for param in
                      signature.parameters.values()])
    fprint("Usage ({cmd}): {usage}".format(cmd=cmd, usage=usage),
           force=True)
    description = textwrap.dedent(method.__doc__)
    fprint("Description:\n{description}".format(description=description),
           force=True)


def transform_params(params, signature, method):
    """
    Transform parameters to match method signature.
    """
    result = []
    expected_params = len(signature.parameters.values())
    if len(params) > expected_params:
        # Check if method need can receive list
        # If params number is superior than signature values
        # and if method doesn't receive list then something went wrong
        # so display message and return is not ok.
        if "list" not in method.__doc__.lower():
            fprint("Something went wrong with the given parameters",
                   force=True)
            fprint(params, force=True)
            return result, False
        if expected_params == 1:
            result.append(params[:len(params)])
            return result, True
        else:
            result.append(params[:len(params) - 1])
        try:
            for el in params[expected_params]:
                result.append(el)
        except IndexError:
            pass
    else:
        result = params
    return result, True


def execute(cmd, params, client):
    """
    Execute single command and display result.
    """
    if cmd in helpme:
        cmds = get_cmds(client)
        display_cmds_help(client, cmds)
        return
    method = getattr(client, cmd)
    signature = inspect.signature(method)
    if params and params[0] in ["-h", "--help"]:
        cmd_help(cmd, method, signature)
        return
    result = None
    params, is_ok = transform_params(params, signature, method)
    if not is_ok:
        cmd_help(cmd, method, signature)
        return
    try:
        result = method(*params)
    except TypeError as err:
        fprint(str(err))
    except pymemcache.MemcacheUnknownCommandError as err:
        fprint(str(err), force=True)
        return
    except pymemcache.MemcacheClientError as err:
        fprint(str(err), force=True)
        return
    except pymemcache.MemcacheServerError as err:
        fprint(str(err), force=True)
        return
    except pymemcache.MemcacheUnknownError as err:
        fprint(str(err), force=True)
        return
    except pymemcache.MemcacheUnexpectedCloseError as err:
        fprint(str(err), force=True)
        return
    except pymemcache.MemcacheIllegalInputError as err:
        fprint(str(err), force=True)
        return
    except socket.timeout:
        fprint("Connection timeout... abort")
        sys.exit(1)
    except socket.error:
        fprint("Socket error... abort")
        sys.exit(1)
    else:
        if result:
            fprint(result, force=True)


if __name__ == "__main__":
    main()
