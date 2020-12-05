from .responses import ResponseDirectory


class CommandRegistryException(Exception):
    pass


class CommandRegistry:
    commands = {
    }

    @classmethod
    def register(cls, command, subcommand, command_class):
        cmd_dict = cls.commands.setdefault(command, {})
        if not subcommand:
            subcommand = "no_subcommand"
        if subcommand in cmd_dict:
            raise CommandRegistryException("Command already registered [{} {}]".format(command, subcommand))
        cmd_dict[subcommand] = command_class

    @classmethod
    def lookup(self, command, subcommand):
        if not subcommand:
            subcommand = "no_subcommand"
        try:
            command_class = self.commands[command][subcommand]
        except KeyError as ke:
            raise CommandRegistryException(
                "No command registered for [{} {}]".format(command, subcommand)) from ke

        return command_class


def register_command(command, subcommand=None):
    def _decorator(cls):
        CommandRegistry.register(command, subcommand, cls)
        return cls
    return _decorator


class CommandFactory:

    @classmethod
    def command_object(cls, config):
        command_cls = CommandRegistry.lookup(config.command, config.subcommand)
        command_obj = command_cls(config)
        return command_obj


class AbstractCommand:
    COMMAND = None
    SUBCOMMAND = None
    HAS_SUBCOMMANDS = True

    def __init__(self, config):
        self.response_directory = ResponseDirectory(config)

    def response(self):
        raise NotImplementedError()


class GetCommand(AbstractCommand):
    COMMAND = "get"

    def __init__(self, config):
        super().__init__(config)
        if config.get_subcmd == "item":
            self.sub_command = self.GetItemCommand(config)


@register_command("get", "item")
class GetItemCommand(GetCommand):
    SUBCOMMAND = "item"
    HAS_SUBCOMMANDS = False

    def __init__(self, config):
        super().__init__(config)
        args = [config.item]
        if config.vault:
            args.extend(["--vault", config.vault])
        if config.fields:
            args.extend(["--fields", config.fields])
        self.args = args

    def response(self):
        response_bytes = self.response_directory.response_lookup(self.COMMAND, self.SUBCOMMAND, args=self.args)
        return response_bytes
