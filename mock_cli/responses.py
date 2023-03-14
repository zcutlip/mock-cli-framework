import json
from pathlib import Path
from typing import Dict, List, Optional

from .argv_conversion import arg_shlex_from_string, argv_to_string
from .hashing import digest_input
from .path import ActualPath


class ResponseRecordException(Exception):
    pass


class ResponseAddException(Exception):
    pass


class ResponseLookupException(Exception):
    pass


class ResponseReadException(Exception):
    """
    Exception for when a response definition exists in the directory,
    but can't be found on disk, or otherwise isn't accessible
    """
    pass


class ResponseDirectoryException(Exception):
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
        out = self._output
        if out is None:
            out = self._read_output()
        return out

    @property
    def error_output(self):
        err_out = self._error_output
        if err_out is None:
            err_out = self._read_error_output()
        return err_out

    @property
    def return_code(self):
        return self["exit_status"]

    @property
    def changes_state(self) -> bool:
        return self.get("changes_state", False)

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
    def __init__(self,
                 cmd_args: List[str],
                 output: bytes,
                 error_output: bytes,
                 returncode: int,
                 invocation_name: str,
                 changes_state: bool,
                 input: Optional[bytes] = None):
        _dict = {"args": cmd_args}
        response_dict = {}
        response_dict["exit_status"] = returncode
        stdout_name = "output"
        stderr_name = "error_output"

        # returns None if input is None
        # converts input to bytes if input is a string
        input_hash = digest_input(input)
        response_dict["stdout"] = stdout_name
        response_dict["stderr"] = stderr_name
        response_dict["name"] = invocation_name
        response_dict["changes_state"] = changes_state
        cmd_response = CommandResponse(
            response_dict, None, output=output,
            error_output=error_output)
        _dict["input_hash"] = input_hash
        _dict["response"] = cmd_response
        super().__init__(_dict)
        self._input = input

    @property
    def cmd_args(self):
        return self["args"]

    @property
    def response(self):
        return self["response"]

    @property
    def input_hash(self) -> Optional[str]:
        return self["input_hash"]

    def record_input(self, input_path):
        if input_path and self._input:
            input_path = Path(input_path, self.input_hash)
            input_path.mkdir(parents=True, exist_ok=True)
            input_path = Path(input_path, "input.bin")
            input = self._input
            if isinstance(input, str):
                input = input.encode()
            with open(input_path, "wb") as f:
                f.write(input)


class ResponseDirectory:
    default_directory = {
        "meta": {
            "response_dir": "responses",
            "input_dir": "input"
        },
        "commands": {},
        "commands_with_input": {}
    }

    def __init__(self, responsedir_json_file, create=False, response_dir=None, input_dir=None):
        if isinstance(responsedir_json_file, str):
            responsedir_json_file = Path(responsedir_json_file)
        dpath_base = responsedir_json_file.name
        # Ensure containing directory exists\
        # resolve symlinks, relative paths, userpaths (~/)
        dpath_dir = ActualPath(responsedir_json_file.parent, create=True)
        responsedir_json_file = ActualPath(dpath_dir, fname=dpath_base)
        self._input_dir = None
        if input_dir:
            self._input_dir = Path(input_dir)
        self._response_responsedir_json_filename = responsedir_json_file
        self._response_directory: Dict = self._load_or_create_directory(
            responsedir_json_file, create, response_dir)

    def _load_or_create_directory(self, responsedir_json_file, create, response_dir):
        try:
            directory = json.load(open(responsedir_json_file, "r"))
            directory_missing = False
        except (FileNotFoundError, json.JSONDecodeError) as e:
            directory_missing = True
            if not create:
                raise ResponseDirectoryException(
                    f"Directory path not found {responsedir_json_file}") from e
            else:
                directory = self.default_directory
                if response_dir:
                    if isinstance(response_dir, Path):
                        response_dir = str(response_dir)
                    directory["meta"]["response_dir"] = response_dir

        if directory_missing and create:
            self._save_to_disk(responsedir_json_file, directory)
        return directory

    @property
    def response_dir(self):
        meta = self._response_directory["meta"]
        response_dir = meta["response_dir"]
        return response_dir

    @property
    def commands(self):
        return self._response_directory["commands"]

    @property
    def commands_with_input(self):
        return self._response_directory["commands_with_input"]

    def response_lookup(self, args, input=None) -> CommandResponse:
        input_hash = digest_input(input)
        arg_string = argv_to_string(args)
        try:
            commands = self.commands
            if input_hash:
                commands = self.commands_with_input
                commands = commands[input_hash]

            response_dict = commands[arg_string]
        except KeyError:
            escaped_arg_str = arg_shlex_from_string(arg_string)
            raise ResponseLookupException(
                "No response for command args: {}".format(escaped_arg_str))

        response = CommandResponse(response_dict, self.response_dir)
        return response

    def _save_to_disk(self, responsedir_json_filename, directory):
        with open(responsedir_json_filename, "w") as f:
            json.dump(directory, f, indent=2)

    def add_command_invocation(self, cmd: CommandInvocation, overwrite=False, save=False):
        cmd_args = cmd.cmd_args
        arg_string = argv_to_string(cmd_args)
        if cmd.input_hash:
            # get the "command with input" dict
            commands: Dict = self._response_directory.setdefault(
                "commands_with_input", {})
            # then get the command dict for this specific input hash, or set an
            # empty dict if it wasn't already there
            commands = commands.setdefault(cmd.input_hash, {})
        else:
            commands: Dict = self._response_directory["commands"]
        if arg_string in commands and overwrite is False:
            raise ResponseAddException(
                f"Response already registered for command: '{cmd_args}'")
        cmd.record_input(self._input_dir)
        response: CommandResponse = cmd.response
        response.record_response(self.response_dir)
        commands[arg_string] = dict(response)
        if save:
            self._save_to_disk(
                self._response_responsedir_json_filename, self._response_directory)
