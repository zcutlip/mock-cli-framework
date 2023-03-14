import os
import sys
from pathlib import Path

from .mock_cmd_state import MockCMDState, MockCMDStateNoDirectoryException
from .responses import (
    CommandResponse,
    ResponseDirectory,
    ResponseReadException
)


class MockCommandResponseDirException(Exception):
    pass


class MockCommand:
    def __init__(self, response_directory=None, state_dir=None):
        self._mock_cmd_state = self._get_mock_cmd_state(state_dir)

        self.response_directory = self._get_response_directory(
            response_directory)

    def _get_response_directory(self, response_directory):
        if response_directory is None:
            if self._mock_cmd_state:
                response_directory = self._mock_cmd_state.response_directory_path()

        if isinstance(response_directory, (str, Path)):
            response_directory = ResponseDirectory(response_directory)
        elif isinstance(response_directory, ResponseDirectory):
            pass

        if response_directory is None:
            raise MockCommandResponseDirException(
                "No response directory provided")
        return response_directory

    def _write_binary(self, output_handle, data):
        with os.fdopen(output_handle.fileno(), "wb", closefd=False) as fd:
            fd.write(data)
            fd.flush()

    def get_response(self, args, input=None) -> CommandResponse:
        response = self.response_directory.response_lookup(args, input=input)
        return response

    def respond(self, args, input=None) -> int:
        response = self.get_response(args, input=input)

        exit_status = response.return_code

        try:
            output = response.output
            error_output = response.error_output
        except (FileNotFoundError, PermissionError, OSError) as err:
            err_msg = f"Response couldn't be read {err}"
            raise ResponseReadException(err_msg)

        if response.output:
            self._write_binary(sys.stdout, output)

        if response.error_output:
            self._write_binary(sys.stderr, error_output)

        if response.changes_state:
            self._iterate_state()

        return exit_status

    def _iterate_state(self):
        if self._mock_cmd_state:
            self._mock_cmd_state.iterate_config()

    def _get_mock_cmd_state(self, state_dir):
        try:
            cmd_state = MockCMDState(state_dir=state_dir)
        except MockCMDStateNoDirectoryException:
            cmd_state = None
        return cmd_state
