import json
from typing import Dict
from pathlib import Path
from .path import ActualPath
from .argv_conversion import argv_to_string


class ResponseRecordException(Exception):
    pass


class ResponseAddException(Exception):
    pass


class ResponseLookupException(Exception):
    pass


class CommandResponse(dict):
    def __init__(self, response_dict, response_dir, output=None, error_output=None):
        super().__init__(response_dict)
        if response_dir:
            response_dir = ActualPath(response_dir)
        self._response_dir = response_dir
        self._output = output
        self._error_output = error_output

    @property
    def response_dir(self):
        return self._response_dir

    @property
    def output(self):
        return self._read_output()

    @property
    def error_output(self):
        return self._read_error_output()

    @property
    def return_code(self):
        return self["exit_status"]

    def record_response(self, response_dir):
        if None in [self._output, self._error_output]:
            raise ResponseRecordException(
                "Missing stdout and/or stderr response")

        resp_path: Path
        stdout_name = self["stdout"]
        stderr_name = self["stderr"]
        resp_path = Path(response_dir, self["name"])
        resp_path = ActualPath(resp_path, create=True)

        output_path = Path(resp_path, f"{stdout_name}")
        error_output_path = Path(resp_path, f"{stderr_name}")

        output_path.write_bytes(self._output)
        error_output_path.write_bytes(self._error_output)

    def _out_path(self, out_name):
        response_name = self["name"]
        out_path = Path(self._response_dir, response_name, out_name)
        return out_path

    def _stdout_path(self):
        out_name = self["stdout"]
        stdout_path = self._out_path(out_name)
        return stdout_path

    def _stderr_path(self):
        out_name = self["stderr"]
        stderr_path = self._out_path(out_name)
        return stderr_path

    def _read_output(self):
        stdout_path = self._stdout_path()
        output = open(stdout_path, "rb").read()
        return output

    def _read_error_output(self):
        stder_path = self._stderr_path()
        output = open(stder_path, "rb").read()
        return output


class CommandInvocation(dict):
    def __init__(self, cmd_args, output, error_output,
                 returncode, invocation_name, response_dir=None):
        _dict = {"args": cmd_args}
        response_dict = {}
        response_dict["exit_status"] = returncode
        stdout_name = "output"
        stderr_name = "error_output"
        response_dict["stdout"] = stdout_name
        response_dict["stderr"] = stderr_name
        response_dict["name"] = invocation_name
        cmd_response = CommandResponse(
            response_dict, response_dir, output=output,
            error_output=error_output)
        _dict["response"] = cmd_response
        super().__init__(_dict)
        self._response_dir = response_dir

    @property
    def cmd_args(self):
        return self["args"]

    @property
    def response(self):
        return self["response"]


class ResponseDirectory:
    default_directory = {
        "meta": {
            "response_dir": Path("responses")
        },
        "commands": {}
    }

    def __init__(self, directory_path, create=False, response_dir=None):
        self._response_directory_filename = directory_path
        self._response_directory: Dict = self._load_or_create_directory(directory_path, create, response_dir)

    def _load_or_create_directory(self, directory_path, create, response_dir):

        try:
            directory = json.load(open(directory_path, "r"))
            directory_missing = False
        except FileNotFoundError:
            directory_missing = True
            if not create:
                raise
            else:
                directory = self.default_directory
                if response_dir:
                    directory["meta"]["response_dir"] = response_dir

        if directory_missing and create:
            self._save_to_disk(directory_path, directory)
        return directory

    @property
    def response_dir(self):
        meta = self._response_directory["meta"]
        response_dir = meta["response_dir"]
        return response_dir

    @property
    def commands(self):
        return self._response_directory["commands"]

    def response_lookup(self, args) -> CommandResponse:
        arg_string = argv_to_string(args)
        try:
            response_dict = self.commands[arg_string]
        except KeyError:
            raise ResponseLookupException("No response for command {}".format(arg_string))

        response = CommandResponse(response_dict, self.response_dir)
        return response

    def _save_to_disk(self, directory_filename, directory):
        with open(directory_filename, "w") as f:
            json.dump(directory, f, indent=2)

    def add_command_invocation(self, cmd: CommandInvocation, save=False):
        cmd_args = cmd.cmd_args
        arg_string = argv_to_string(cmd_args)

        commands: Dict = self._response_directory["commands"]
        if arg_string in commands:
            raise ResponseAddException(f"Response already registered for command: '{cmd_args}'")
        response = cmd.response
        response.record_response(self.response_dir)
        commands[arg_string] = dict(response)
        if save:
            self._save_to_disk(self._response_directory_filename, self._response_directory)
