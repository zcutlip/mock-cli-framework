import sys
from .config.mopconfig import MOPConfig
from .op_cmds import CommandFactory


def mock_op_main():
    config = MOPConfig(sys.argv[1:])
    cmd = CommandFactory.command_object(config)
    resp: bytes = cmd.response()
    sys.stdout.write(resp)


if __name__ == "__main__":
    mock_op_main()
