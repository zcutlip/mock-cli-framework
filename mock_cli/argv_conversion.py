import shlex
from typing import List, AnyStr

DEFAULT_SEP = "|"


def argv_to_string(argv: List, args_to_pop=0, sep=DEFAULT_SEP):
    popped_args = []
    for i in range(0, args_to_pop):
        popped = argv.pop(0)
        popped_args.append(popped)

    arg_str = ""
    for arg in argv:
        arg_str += f"{arg}{sep}"
    arg_str = arg_str.rstrip(sep)
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
