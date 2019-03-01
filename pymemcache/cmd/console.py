#!-*-coding:utf-8-*-


colors = {
    "black": "30",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "purple": "35",
    "cyan": "36",
    "white": "37",
}

styles = {
    "none": "0",
    "bold": "1",
    "underline": "2",
    "negative1": "3",
    "negative2": "5",
}

bgcolors = {
    "black": "40",
    "red": "41",
    "green": "42",
    "yellow": "43",
    "blue": "34",
    "purple": "35",
    "cyan": "36",
    "white": "37",
}


class Console:

    _instance = None

    def __init__(self, quiet):
        self.quiet = quiet

    def __call__(cls):
        if not cls._instance:
            cls._instance = super(Console, cls).__call__(*args, **kwargs)
        return cls._instance

    def stylised(self, message, color=None, bgcolor=None, style=None):
        """
        Apply style on output stream.
        """
        stylish = []
        if style:
            stylish.append(styles[style])
        if color:
            stylish.append(colors[color])
        if bgcolor:
            stylish.append(bgcolors[bgcolor])
        if stylish:
            message = "\033[{style}m{message}\033[0m".format(
                style=";".join(stylish), message=message)
        return message

    def display(self, message, force=False):
        if self.quiet and not force:
            return
        print(message)

    def info(self, message, force=False):
        """
        Print information message with related style.
        """
        message = self.stylised(message, color="blue", style="bold")
        self.display(message, force)

    def warning(self, message, force=False):
        message = self.stylised(message, color="yellow", style="bold")
        self.display(message, force)

    def error(self, message, force=False):
        message = self.stylised(message, color="red", style="bold")
        self.display(message, force)
