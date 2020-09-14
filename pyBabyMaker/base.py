#!/usr/bin/env python3
#
# Author: Yipeng Sun <syp at umd dot edu>
# License: BSD 2-clause
# Last Change: Tue Sep 15, 2020 at 01:18 AM +0800
"""
This module provides basic infrastructure for ntuple related C++ code
generation.
"""

import abc
import yaml
import subprocess

from collections import namedtuple
from shutil import which
from os import path


###########
# Helpers #
###########

class TermColor:
    """
    Color sequences for UNIX terminal.
    """
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


class UniqueList(list):
    """
    An extension to the standard ``list`` class such that every element stored
    inside is unique.
    """
    def __init__(self, iterable=None):
        """
        This initializer takes an optional iterable and store the unique
        elements inside that iterable only.
        """
        if iterable:
            uniq = []
            [uniq.append(i) for i in iterable if not uniq.count(i)]
            super().__init__(uniq)
        else:
            super().__init__()

    def append(self, obj):
        if not super().__contains__(obj):
            super().append(obj)

    def insert(self, index, obj):
        if not super().__contains__(obj):
            super().insert(index, obj)

    def __add__(self, value):
        return UniqueList(super().__add__(value))

    def __iadd__(self, value):
        return UniqueList(super().__iadd__(value))


def load_file(filepath, current_file_path=__file__):
    """
    Return relative path based on current file directory if ``filepath`` starts
    with ``!:``.
    """
    if filepath.startswith('!:'):
        filepath = filepath[2:]
        return path.join(path.abspath(path.dirname(current_file_path)),
                         filepath)
    else:
        return filepath


Variable = namedtuple('Variable', 'type name rvalue', defaults=(None,))


##############
# Base maker #
##############

class BaseMaker(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def directive_gen(self, config_filename):
        """
        Generate template macro directive from YAML file.
        """

    @abc.abstractmethod
    def gen(self, filename):
        """
        Generate C++ code and write it to file.
        """

    @staticmethod
    def read(yaml_filename):
        """
        Read C++ code generation instruction stored in a YAML.
        """
        from pyBabyMaker.io.NestedYAMLLoader import NestedYAMLLoader
        with open(yaml_filename) as f:
            return yaml.load(f, NestedYAMLLoader)

    @staticmethod
    def dump(data_filename):
        """
        Dump ``TTree`` structures inside a ntuple
        """
        from pyBabyMaker.io.TupleDump import PyTupleDump
        dumper = PyTupleDump(data_filename)
        return dumper.dump()

    @staticmethod
    def reformat(cpp_filename, formatter='clang-format', flags=['-i']):
        """
        Optionally reformat C++ code after generation, if the ``formatter`` is
        in ``$PATH``.
        """
        if which(formatter):
            cmd = [formatter] + flags + [cpp_filename]
            subprocess.Popen(cmd)
