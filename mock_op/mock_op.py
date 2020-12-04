from .config.mopconfig import MOPConfig
from .op_cmds import GetCommand


def mock_op_main(argv):
    config = MOPConfig(argv)
    get_cmd = GetCommand(config)


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    mock_op_main(args)
