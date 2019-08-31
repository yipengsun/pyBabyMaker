#!/usr/bin/env python3
#
# Author: Yipeng Sun <syp at umd dot edu>
# License: BSD 2-clause
# Last Change: Fri Aug 30, 2019 at 09:09 PM -0400

import pytest

from pyBabyMaker.base import UniqueList
from pyBabyMaker.base import BaseConfigParser
from pyBabyMaker.base import BaseCppGenerator


##################
# Data structure #
##################

@pytest.fixture
def default_UniqueList():
    return UniqueList([1, 2, 3, 1])


def test_UniqueList__init__normal():
    test_list = UniqueList()
    assert test_list == []


def test_UniqueList__init__duplicate(default_UniqueList):
    assert default_UniqueList == [1, 2, 3]


def test_UniqueList__init__exception():
    test_list = UniqueList([1, 2, 3, 4])
    assert test_list == [1, 2, 3, 4]


def test_UniqueList__add__normal(default_UniqueList):
    test_list = default_UniqueList + [7]
    assert test_list == [1, 2, 3, 7]


def test_UniqueList__add__duplicate(default_UniqueList):
    test_list = default_UniqueList + [7, 1, 2]
    assert test_list == [1, 2, 3, 7]


def test_UniqueList__iadd__normal(default_UniqueList):
    default_UniqueList += [7]
    assert default_UniqueList == [1, 2, 3, 7]


def test_UniqueList__iadd__duplicate(default_UniqueList):
    default_UniqueList += [7, 1, 2]
    assert default_UniqueList == [1, 2, 3, 7]


def test_UniqueList_append_normal(default_UniqueList):
    default_UniqueList.append(4)
    assert default_UniqueList == [1, 2, 3, 4]


def test_UniqueList_append_duplicate(default_UniqueList):
    default_UniqueList.append(1)
    assert default_UniqueList == [1, 2, 3]


def test_UniqueList_insert_normal(default_UniqueList):
    default_UniqueList.insert(0, 0)
    assert default_UniqueList == [0, 1, 2, 3]


def test_UniqueList_insert_duplicate(default_UniqueList):
    default_UniqueList.insert(0, 1)
    assert default_UniqueList == [1, 2, 3]


###########
# Parsers #
###########

@pytest.fixture
def default_BaseConfigParser():
    return BaseConfigParser()


def test_BaseConfigParser_match_True(default_BaseConfigParser):
    assert default_BaseConfigParser.match(['quick', 'brown', 'fox'], r'fox')


def test_BaseConfigParser_match_False(default_BaseConfigParser):
    assert not default_BaseConfigParser.match(['quick', 'brown', 'fox'], r'Fox')


def test_BaseConfigParser_match_True_inverse(default_BaseConfigParser):
    assert not default_BaseConfigParser.match(['quick', 'brown', 'fox'], r'fox',
                                              False)


#######################
# C++ code generators #
#######################

class SimpleCppGenerator(BaseCppGenerator):
    def gen_preamble(self):
        pass

    def gen_body(self):
        pass


@pytest.fixture
def default_SimpleCppGenerator():
    return SimpleCppGenerator(
        additional_system_headers=['iostream'],
        additional_user_headers=['include/dummy.h']
    )


# Headers ######################################################################

def test_SimpleCppGenerator_custom_system_headers(default_SimpleCppGenerator):
    assert default_SimpleCppGenerator.system_headers == \
        ['TFile.h', 'TTree.h', 'TTreeReader.h', 'TBranch.h', 'iostream']


def test_SimpleCppGenerator_custom_user_headers(default_SimpleCppGenerator):
    assert default_SimpleCppGenerator.user_headers == ['include/dummy.h']


def test_SimpleCppGenerator_gen_headers(default_SimpleCppGenerator):
    assert default_SimpleCppGenerator.gen_headers() == \
        '''#include <TFile.h>
#include <TTree.h>
#include <TTreeReader.h>
#include <TBranch.h>
#include <iostream>

#include "include/dummy.h"
'''


def test_SimpleCppGenerator_gen_headers_no_user():
    cpp_generator = SimpleCppGenerator()
    assert cpp_generator.gen_headers() == \
        '''#include <TFile.h>
#include <TTree.h>
#include <TTreeReader.h>
#include <TBranch.h>

'''


# C++ snippets #################################################################

def test_SimpleCppGenerator_cpp_header_system(default_SimpleCppGenerator):
    assert default_SimpleCppGenerator.cpp_header('iostream') == \
        '#include <iostream>\n'


def test_SimpleCppGenerator_cpp_header_user(default_SimpleCppGenerator):
    assert default_SimpleCppGenerator.cpp_header('include/dummy.h', False) == \
        '#include "include/dummy.h"\n'


def test_SimpleCppGenerator_cpp_make_var(default_SimpleCppGenerator):
    assert default_SimpleCppGenerator.cpp_make_var(
        'Variable1/Old',
        prefix='pre', suffix='suf', separator='_'
    ) == 'pre_Variable1_Old_suf'


def test_SimpleCppGenerator_cpp_main(default_SimpleCppGenerator):
    assert default_SimpleCppGenerator.cpp_main('body') == \
        '''
int main(int, char** argv) {
  body
  return 0;
}'''


def test_SimpleCppGenerator_cpp_TTree(default_SimpleCppGenerator):
    assert default_SimpleCppGenerator.cpp_TTree('tree', 'tree') == \
        'TTree tree("tree", "tree");\n'


def test_SimpleCppGenerator_cpp_TTreeReader(default_SimpleCppGenerator):
    assert default_SimpleCppGenerator.cpp_TTreeReader(
        'reader', 'tree', 'input_file') == \
        'TTreeReader reader("tree", input_file);\n'


def test_SimpleCppGenerator_cpp_TTreeReaderValue(default_SimpleCppGenerator):
    assert default_SimpleCppGenerator.cpp_TTreeReaderValue(
        'float', 'value', 'reader', 'some_branch') == \
        'TTreeReaderValue<float> value(reader, "some_branch");\n'
