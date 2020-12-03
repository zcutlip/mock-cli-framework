from argparse import ArgumentParser


from scruffy.config import (
    ConfigFile,
    ConfigNode
)
from scruffy.file import (
    Directory,
    PackageDirectory,
    File
)
from pprint import pprint
# from ..version import SwPlanetsCsvAbout


# Making this a singleton allows us to later use a decorator to automatically
# register handlers as command line arguments
# class MOPParsedArgs(argparse.ArgumentParser):
#     def __init__(self, exit_on_error=True, **kwargs):
#         super().__init__(**kwargs)
#         self.exit_on_error = exit_on_error
#         self.add_argument("--global-flag", help="the global flag")
#         subparsers = self.add_subparsers(title="Available Commands")
#         subparsers.add_parser("my_parser", add_help=False)
#         # parser_get = subparsers.add_parser("get", parents=[self], add_help=False, help="the get command")
#         # parser_get.add_argument("--foo")


#     def _configure_get_subcommand(self, subparser: _SubParsersAction):
#         get_sp = subparser.add_parser("get")
#         get_item_sp = get_sp.add_subparsers("item")
#         get_item_sp.add_parser("--fields", help="only return data from these fields")
#         return get_sp


#     def parse_args(self, args=None):
#         parsed_args = None
#         try:
#             parsed_args = super().parse_args(args)
#             # TODO: later if we need two discrete argument dictionaries,
#             # look at grumpy _regsiter_parsed_args()
#         except SystemExit as se:
#             if self.exit_on_error:
#                 raise se
#             else:
#                 pass

#         return parsed_args

def arg_parser():
    parser = ArgumentParser()
    parser.add_argument("--global-flag", help="the global flag")
    subparsers = parser.add_subparsers(description="Available Commands", help="Commands", dest="command")
    parser_get = subparsers.add_parser("get", help="the get command")

    parser_get_subparsers = parser_get.add_subparsers(
        title="Available Commands", metavar="[command]", dest="get_subcommands", required=True)

    parser_get_subcmd = parser_get_subparsers.add_parser(
        "document", description="Download & print a document to standard output", help="Download a document")
    parser_get_subcmd.add_argument(
        "document", metavar="<document>", help="The document to get")

    parser_get_subcmd = parser_get_subparsers.add_parser(
        "item", description="Returns details about an item.", help="Get item details")
    parser_get_subcmd.add_argument(
        "item", metavar="<item>", help="The item to get")
    parser_get_subcmd.add_argument("--fields", help="comma-separated list of fields to get about the item")

    return parser


class MOPConfig:
    DEFAULT_CONFIG_DIR = "~/.config/mock-op"
    DEFAULT_CONFIG_FILE = "mock-op.yaml"

    def __init__(self, args, exit_on_error=True):
        # # TODO: Later we'll take parsed args to override
        # config dir and config file paths
        parser = arg_parser()
        parsed_args = parser.parse_args(args)
        self.config_dir = self.DEFAULT_CONFIG_DIR
        self.config_file = self.DEFAULT_CONFIG_FILE

        self._dir = Directory(
            path=self.config_dir,
            # TODO: Later, turn on create=True
            create=False,
            config=ConfigFile(
                self.config_file,
                defaults=File('./default.yaml', parent=PackageDirectory())
            )
        )
        self._dir.prepare()

        self.config = self._dir.config
        self.config.load()
        if parsed_args:
            self._update_config(vars(parsed_args))
        if self.config.pprint_config:
            pprint(vars(parsed_args))
            print("Configuration dictionary:")

            pprint(self.config.to_dict(), width=1)

    def __getattr__(self, attr):
        _value = None
        if hasattr(self.config, attr):
            _value = getattr(self.config, attr)
        else:
            raise AttributeError("%r has no attribute %r" %
                                 (self.__class__.__name__, attr))
        if isinstance(_value, ConfigNode):
            _value = _value._get_value()
        return _value

    def _prune_dict(self, old_thing, prune_val):
        pruned = None
        if isinstance(old_thing, dict):
            pruned = {
                k: self._prune_dict(v, prune_val) for k, v in old_thing.items() if v != prune_val
            }
        else:
            # Since we recursively call ourselves for all nested dictionaries
            # we need to handle the eventual case when we're passed in a thing
            # that isn't a dictionary
            pruned = old_thing
        return pruned

    def _update_config(self, args_dict):
        pruned_args = self._prune_dict(args_dict, None)
        self.config.update(pruned_args)
