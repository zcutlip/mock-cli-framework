# Mock CLI Framework

## Description

This is a framework that can be called from a short Python console script to simulate the responses of an actual command-line tool.

`mock-cli-framework` provides API for two purposes:

- Playing back canned responses based on a provided list of command-line arguments in order to simulate an actual command-line tool's behavior
- Generating a directory of canned responses from invocations of the actual tool

A command "invocation" is a unique list of arguments to that command. A "response" is the output the command wrote to `stdout`, `stderr`, as well as the numerical exit status of the command.

## Why?

This is useful in cases where the real command-line tool can't be used. For example you might have a script or other program that shells out to a command. You want to test that your code processes that command's output and handles its errors properly, such as in automated tests. But the tests can't provide things the real command requires like human interaction or online account access that would be needed by the real tool. You can use `mock-cli-work` to "record" the responses of the real command-line tool, and then to "play back" those reponses in your testing environment.

## Using

To use `mock-cli-framework` to simulate a real command, it requires a few things:

- A JSON-encoded "response directory" listing all the command-line argument variations and a response dictionary for each
- An on-disk directory of "responses" that can be read and then written to `stdout` & `stderr`

For example, the JSON response directory for the `md5sum` command might look like:

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

Then, programmatically, use `mock_cli` API to make a short script that pretends to be the real command:

```Python
#!/usr/bin/env python3
# mock-md5sum.py

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
    response_directory_path = "./response-directory.json"
    cmd = MockCommand(response_directory_path)
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

If your code shells out to `md5sum` to hash really large files that you don't want to have in your testin harness, you can substitute `mock-md5sum.py` which will behave the same way (or similarly enough) as the real thing.
