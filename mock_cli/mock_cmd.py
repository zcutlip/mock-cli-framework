import sys
import os
from .responses import ResponseDirectory


class MockCommand:
    def __init__(self, responsedir_json_file):
        self.response_directory = ResponseDirectory(responsedir_json_file)

    def _write_binary(self, output_handle, data):
        with os.fdopen(output_handle.fileno(), "wb", closefd=False) as fd:
            fd.write(data)
            fd.flush()

    def respond(self, args) -> int:
        response = self.response_directory.response_lookup(args)

        exit_status = response.return_code
        if response.output:
            self._write_binary(sys.stdout, response.output)

        if response.error_output:
            self._write_binary(sys.stderr, response.error_output)

        return exit_status
