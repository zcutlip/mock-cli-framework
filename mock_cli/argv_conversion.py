import shlex
from typing import AnyStr, List

DEFAULT_SEP = "|"


def argv_to_string(argv: List, args_to_pop=0, sep=DEFAULT_SEP):
    for i in range(0, args_to_pop):
        argv.pop(0)

    # avoid using format strings
    # in some cases pyonepassword uses RedactableString objects
    # and format strings will result in redacted versions of those strings
    arg_str = sep.join(argv)

    return arg_str


def argv_from_string(arg_str: AnyStr, popped_args=[], sep=DEFAULT_SEP):
    argv = list(popped_args)
    split_args = arg_str.split(sep)
    argv.extend(split_args)
    return argv


def arg_shlex_from_string(arg_str: AnyStr, popped_args=[], sep=DEFAULT_SEP):
    argv = argv_from_string(arg_str, popped_args=popped_args, sep=sep)
    arg_str = shlex.join(argv)
    return arg_str
