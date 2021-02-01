# Mock CLI Tool Framework

## Description

This is a framework that can be called from a simple Python CLI script to simulate the responses of an actual command-line tool. It's useful in instances where the real tool can't be used such as in automated tests that can't provide things like human interaction or an online account access that would be needed by the real tool.

`mock-cli-tool` provides API for two purposes:

- Playing back canned responses based on a list of command-line arguments given
- Generating a directory of canned responses from invocations of the actual tool
