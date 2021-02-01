import sys
from argparse import ArgumentParser
from .responses import ResponseDirectory


class MockCommand:
    def __init__(self, argument_parser: ArgumentParser, response_directory_path):
        self.parser = argument_parser
        self.response_directory = ResponseDirectory(response_directory_path)

    def respond(self, args) -> int:
        self.parser.parse_args(args)
        response = self.response_directory.response_lookup(args)
        stdout_buf = response.output
        stderr_buf = response.error_output
        exit_status = response.return_code
        if stdout_buf:
            sys.stdout.write(stdout_buf)
        if stderr_buf:
            sys.stderr.write(stderr_buf)

        return exit_status
