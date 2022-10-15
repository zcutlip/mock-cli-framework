import json
import os
from pathlib import Path
from typing import Dict, List, Union

from . import data
from .pkg_resources import pkgfiles

STATE_DIR_ENV_NAME = "MOCK_CMD_STATE_DIR"


class MockCMDStateDirException(Exception):
    pass


class MockCMDStateNoDirectoryException(Exception):
    pass


class MockCMDStateMaxIterationException(Exception):
    pass


class MockCMDEnvironmentConfig(dict):

    def __init__(self, env_config_dict):
        super().__init__(env_config_dict)
        self._saved_env = dict(os.environ)

    @property
    def set_vars(self) -> Dict[str, str]:
        return self["set_vars"]

    @property
    def pop_vars(self) -> List[str]:
        return self["pop_vars"]

    def initialize_env(self):
        for var in self.pop_vars:
            os.environ.pop(var, None)

        for var, val in self.set_vars.items():
            os.environ[var] = val

    def restore_env(self):
        # in case we blow up during initialization,
        # check that _saved_env has been set
        # so we don't blow up again on the way down
        if hasattr(self, "_saved_env"):
            if self._saved_env:
                print("restoring env")
                os.environ.clear()
                os.environ.update(self._saved_env)
        self._saved_env = None

    def __del__(self):
        # call restore on obj delete in case owner doesn't get a chance to explicitly call it
        # not sure if relying on this is racey
        self.restore_env()

    @classmethod
    def from_template(cls):
        template_dict = {}
        with pkgfiles(data).joinpath(data.ENV_TEMPLATE_JSON).open("r") as _file:
            template_dict = json.load(_file)

        obj = cls(template_dict)
        return obj


class MockCMDStateConfig(dict):

    def __init__(self, config_path, config=None):
        if config:
            config_dict = config
        else:
            config_dict = json.load(open(config_path, "r"))
        super().__init__(config_dict)
        self._config_path = config_path
        self._env_config: MockCMDEnvironmentConfig = None
        self._initialize_env()

    @property
    def response_directory(self):
        response_dir_list = self["response-directory-list"]
        response_dir = response_dir_list[self.iteration]
        return response_dir

    @property
    def iteration(self) -> int:
        return self["iteration"]

    @iteration.setter
    def iteration(self, iteration):
        self["iteration"] = iteration

    @property
    def max_iterations(self) -> int:
        return self["max-iterations"]

    @property
    def env_config(self) -> MockCMDEnvironmentConfig:
        pass

    def iterate(self):
        if self.iteration >= self.max_iterations:
            raise MockCMDStateMaxIterationException(
                f"Already reached max iterations: {self.max_iterations}")
        self.iteration += 1
        self.save_config()

        # restore saved env
        self._env_config.restore_env()

        # explicitly set env_config to None
        self._env_config = None

        # initialize the next env
        self._initialize_env()

    def save_config(self):
        with open(self._config_path, "w") as f:
            json.dump(self, f, indent=2)

    def _initialize_env(self):
        # don't initialize a config if we have done so already
        # set to None before calling this in order to initialize
        # the next config otherwise we'll clobber the saved config
        if self._env_config is None:
            env_list = self["env-list"]
            env_config = env_list[self.iteration]
            env_config = MockCMDEnvironmentConfig(env_config)
            env_config.initialize_env()
            self._env_config = env_config


class MockCMDNewStateConfig(MockCMDStateConfig):

    @property
    def max_iterations(self):
        return super().max_iterations

    @max_iterations.setter
    def max_iterations(self, max_iter):
        self["max-iterations"] = max_iter

    def add_iteration(self, response_dir_path, env_config_dict):
        self["response-directory-list"].append(response_dir_path)
        self["env-list"].append(env_config_dict)
        self.max_iterations += 1
        self.save_config()

    @classmethod
    def from_template(cls, config_path):
        template_dict = {}
        with pkgfiles(data).joinpath(data.CONFIG_TEMPLATE_JSON).open("r") as _file:
            template_dict = json.load(_file)

        obj = cls(config_path, config=template_dict)
        obj.iteration = 0
        obj.max_iterations = 0
        return obj

    def _initialize_env(self):
        # override _initialize_env() so when the superclass's constructor calls it
        # it does nothing
        pass


class MockCMDState:
    CONFIG_FILE_NAME = "config.json"

    def __init__(self, state_dir: Union[str, Path] = None):
        if state_dir is None:
            state_dir = os.environ.get(STATE_DIR_ENV_NAME)

        if state_dir is None:
            raise MockCMDStateNoDirectoryException(
                "No state directory path provided")

        state_dir = Path(state_dir)
        if not state_dir.is_dir():
            raise MockCMDStateDirException(
                f"Invalid state directory: {state_dir}")
        self._state_dir = state_dir
        self._config = MockCMDStateConfig(
            Path(self._state_dir, self.CONFIG_FILE_NAME))

    def response_directory_path(self) -> str:
        return self._config.response_directory

    def iterate_config(self):
        self._config.iterate()
