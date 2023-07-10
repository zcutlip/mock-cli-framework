# Mock CLI Framework

## Description

This is a framework that can be called from a short Python console script to simulate the responses of an actual command-line tool.

`mock-cli-framework` provides API for two purposes:

- Playing back canned responses based on a provided list of command-line arguments in order to simulate an actual command-line tool's behavior
- Generating a directory of canned responses from invocations of the actual tool

A command "invocation" is a unique list of arguments to that command. A "response" is the output the command wrote to `stdout`, `stderr`, as well as the numerical exit status of the command.

## Why?

This is useful in cases where the real command-line tool can't be used. For example you might have a script or other program that shells out to a command. You want to verify that your code processes that command's output and handles its errors properly, such as in automated tests. But the tests can't provide things the real command requires like human interaction or online account access that would be needed by the real tool. You can use `mock-cli-work` to "record" the responses of the real command-line tool as well as use `mock-cli-framework` to create a fake version of the command. You can then have your code shell out to the "fake" command (using symlinks, PATH variable, etc.) to play back those reponses in your testing environment.

## Usage

### Response Directory

To use `mock-cli-framework` to simulate a real command, it requires a few things:

- A JSON-encoded "response directory" listing all the command-line argument variations and a response dictionary for each
- An on-disk repository of "responses" that can be read and then written to `stdout` & `stderr`

The response directory is designed to be easily hand generated (or easily scripted), but there is also API to automate creation of it.

Before discussing the Response Generator API, let's look at the response directory's anatomy.

As an example, the JSON response directory for the `md5sum` command might look like:

```JSON
{
  "meta": {
    "response_dir": "./responses"
  },
  "commands": {
    "--binary|big-file.bin": {
      "exit_status": 0,
      "stdout": "output",
      "stderr": "error_output",
      "name": "binary-big-file-bin"
    },
    "--text|missing-file.txt": {
      "exit_status": 1,
      "stdout": "output",
      "stderr": "error_output",
      "name": "text-missing-file-txt"
    },
    "--check|file-list.txt": {
      "exit_status": 0,
      "stdout": "output",
      "stderr": "error_output",
      "name": "check-file-list-txt"
    }
  }
}
```

In the example above, each "command" dictionary is keyed by an encoded argument string, and contains:

- Numerical exit status
- Filename of `stdout` written to disk
- Filename of `stderr` written to disk
- An arbitary, unique name for this invocation which serves as the parent directory for the output files.

Then the "responses" directory looks like:

```
responses
├── binary-big-file-bin
│   ├── error_output
│   └── output
├── check-file-list-txt
│   ├── error_output
│   └── output
└── text-missing-file-txt
    ├── error_output
    └── output
```

The names of the response output files and their containing directories don't especially matter, but it is recommended to use names that relate to what the command is intended to simulate.

### Command Mock-up

Given the above response directory, you can programmatically use `mock_cli` API to make a short script that pretends to be the real command:

```Python
#!/usr/bin/env python3
# mock-md5sum.py

from mock_cli import MockCommand

def build_arg_parser():
  parser = argparse.ArgumentParser()
  # add arguments you want your command to be aware of
  return parser

def main():
    # We parse args in order to fail on args we don't understand
    # even though we don't actually use them
    # Ideally we should fail in the same way the real command would fail
    parser = build_arg_parser()
    parser.parse_args()
    responsedir_json_file = "./response-directory.json"
    cmd = MockCommand(responsedir_json_file)
    args = sys.argv[1:]
    exit_status = cmd.respond(args)
    return exit_status


if __name__ == "__main__":
    exit(main())
```

Now you can run your `mock-md5sum.py`, and it should play back responses from disk without having to actually md5 anything, or requiring the original input files:

```console
$ mock-md5sum.py --binary big-file.bin
f4c014ae60f420d90c2b52f4969f8d99 *big-file.bin
```

If your code shells out to `md5sum` to hash really large files that you don't want to have in your testing harness, you can substitute `mock-md5sum.py` which will behave the same way as the real thing (or similarly enough). Presumably you can trust that `md5sum` hashes `big-file.bin` properly, so there's no need to replicate that part.

### Response Generation API

To generate responses, there are two classes to know about;

- `CommandInvocation`
- `ResponseDirectory`

The `ResponseDirectory` class takes one required arguments and two optional ones:

- `responsedir_json_file` is the path and filename of the response JSON dictionary that either exists or is to be created.
- `create` Is an optional boolean flag to create the JSON dictionary if it doesn't already exist, defaulting to `False`
- `response_dir` Is an optional path to a directory on disk that will contain recorded response output files.
  - It is required if `create` is true, so that it can be stored in the response dictionary for later use

`ResponseDirectory` provides a method to record a command invocation: `add_command_invocation()`. It takes two arguments:

- `cmd` is a `CommandInvocation` object (discussed next)
- `save` is an optional boolean flag to write the response dictionary to disk for later use, defaulting to False.
  - If the response directory is not saved to disk it will be held in memory and discarded when not in use.
  - If the response directory is to be used later or by a different program, pass `save=True`

The `CommandInvocation` class serves to bundle up a set of command-line arguments as well as command response context, including normal and error output and exit status. It takes several required arguments:

- `cmd_args` is a list of strings represengting command-line arguments
- `output` is a `bytes` object read from the command's standard output.
- `error_output` is a `bytes` object read from the command's standard error.
- `returncode` is the command's numerical exit status when executed with the provided command-line arguments
- `invocation_name` is a unique, arbitrary name given to this particular invocation
  - It is recommended that the name be related to the command's arguments and intended action
  - The name should be filesystem-safe as it will be used as the directory name on disk to hold the output files
- `changes_state` a boolean flag indicating if this command should trigger a state iteration
- `input` is an optional bytes-like object that will be hashed if provided.
  - The command invocation will be added under "commands_with_input" using its hash as a key
  - Since more than one command may work with the same input, the invocations will be further keyed by their command-line arguments

Here's an example:

```Python
import subprocess
from mock_cli import ResponseDirectory, CommandInvocation


def main():
    directory = ResponseDirectory("./resopnse-directory.json", create=True, response_dir="./responses")
    argv = ["md5sum", "--binary", "big-file.bin"]
    p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = p.stdout
    stderr = p.stderr
    returncode = p.returncode

    # something to hint at what this command was doing
    invocation_name = "md5sum-[binary]-[big-file-bin]"

    # omit argv[0] program name. Only args to program are necessary
    # e.g., ["--binary", "big-file.bin"]
    cmd_args = argv[1:]

    invocation = CommandInvocation(cmd_args, stdout, stderr, returncode, invocation_name)


    # When adding a command invocation, the following happens:
    # - The command context (args, output, & exit status) is added to the dictionary of responses
    # - The invocation name is used to create a subdirectory under the top-level responses directory
    # - The normal and error output bytes are written to files inside the invocation subdirectory
    # - The response dictionary is optionally written to disk as JSON
    directory.add_command_invocation(invocation, save=True)
)
```

## Limitations

There are a number of limitations to be aware of that prevent `mock-cli-framework` from fully simulating some commands:

- Environment variables aren't processed, so behavior that is affected by them isn't simulated
- Normal and error output can't be interleaved on the console
  - Standard output, if any, is written first
  - Standard error, if any, is written next
- Timing/performance can't be simulated, and will usually be virtually instaneous
  - A command's typical run-time for a given input/workload can't be simulated
  - No assumptions can be made about one workload being faster/slower than another
- Commands that run interactively can't be simulated
- No side effects such as data written to disk can be simulated
- If the output contains any time-sensitive details such as time-stamped logs, those details will reflect whatever was recorded and may not be current
