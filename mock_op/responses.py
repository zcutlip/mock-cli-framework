import json
import os
import shlex


class ResponseLookupException(Exception):
    pass


class ResponseDirectory:

    def __init__(self, config):
        self._response_directory = json.load(
            open(config.response_directory, "r"))

    @property
    def response_dir(self):
        meta = self._response_directory["meta"]
        response_dir = meta["response_dir"]
        return response_dir

    @property
    def commands(self):
        return self._response_directory["commands"]

    def response_lookup(self, command, subcommand, args=[]):
        command_dict = self.commands[command]
        subcommands = command_dict["subcommands"]
        subcmd = subcommands[subcommand]
        response_file = None
        for response_dict in subcmd["responses"]:
            if response_dict["args"] == args:
                response_file = response_dict["response_file"]

        if not response_file:
            command_string = command
            if subcommand:
                command_string = "{} {}".format(command_string, subcommand)
            if args:
                for arg in args:
                    arg = shlex.quote(arg)
                    command_string = "{} {}".format(command_string, arg)
            raise ResponseLookupException("No response for command {}".format(command_string))

        response = self._read_response_file(response_file)
        return response

    def _read_response_file(self, response_file):
        response_dir = self.response_dir
        response_path = os.path.join(response_dir, response_file)
        response = open(response_path, "r").read()

        return response
