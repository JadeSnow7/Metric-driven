COMMANDS = {}


def command(name):
    """Register a command handler under `name`."""

    def decorator(handler):
        COMMANDS[name] = handler
        return handler

    return decorator
