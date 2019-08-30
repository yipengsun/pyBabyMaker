#!/usr/bin/env python3
#
# Author: Yipeng Sun <syp at umd dot edu>
# License: BSD 2-clause
# Last Change: Fri Aug 30, 2019 at 02:00 PM -0400

import re

from pyBabyMaker.base import BaseCppGenerator, BaseConfigParser, BaseMaker


#################################
# n-tuple generation directives #
#################################

class NtupleGenDirectives(object):
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file

        self._input_branches = []
        self._output_branches = []
        self._dependencies = []


class BabyCppGenerator(BaseCppGenerator):
    pass


class BabyMaker(BaseCppGenerator, BaseMaker, BaseConfigParser):
    headers = ['TFile.h', 'TTree.h', 'TTreeReader.h', 'TBranch.h']
    cpp_input_file = 'input_file'
    cpp_output_file = 'output_file'

    def __init__(self, data_filename, headers):
        self.headers += headers
        self.io_directive = {}
        self.calc_directive = {}
        self.raw_datatype = self.dump(data_filename)

    def parse_conf(self, yaml_conf):
        conf = self.read(yaml_conf)

        for output_tree, opts in conf.items():
            self.io_directive[output_tree] = {}
            self.calc_directive[output_tree] = {}

            try:
                self.headers += opts['headers']
            except KeyError:
                pass

            if opts['force_lowercase']:
                normalizer = lambda x: x.lower()
            else:
                normalizer = lambda x: x

            for input_tree in opts['input']:
                initialized_vars = []
                if input_tree in self.raw_datatype.keys():
                    self.io_directive[output_tree][input_tree] = []

                    for input_branch, datatype \
                            in self.raw_datatype[input_tree].items():
                        if 'drop' in opts.keys() and self.match(
                                opts['drop'], input_branch):
                            print('Dropping branch: {}'.format(input_branch))

                        elif self.match(opts['keep'], input_branch):
                            directive = {'input_branch': input_branch,
                                         'datatype': datatype}
                            initialized_vars.append(input_branch)

                            try:
                                directive['output_branch'] = \
                                    normalizer(opts['rename'][input_branch])
                            except KeyError:
                                directive['output_branch'] = \
                                    normalizer(input_branch)
                            try:
                                directive['selection'] = \
                                    opts['selection'][input_branch]
                            except KeyError:
                                directive['selection'] = None

                            self.io_directive[output_tree][input_tree].append(directive)

                else:
                    print('Warning: tree {} not found in input file.'.format(
                        input_tree
                    ))

                if 'calculation' in opts.keys():
                    self.calc_directive[output_tree][input_tree] = []
                    for output_branch, instruction in \
                            opts['calculation'].items():
                        directive = {'output_branch': normalizer(output_branch)}

                        parsed = re.match(r'^(\w*)\((.*)\)', instruction)
                        directive['functor'] = parsed.group(1)

                        arguments = [a.strip()
                                     for a in parsed.group(2).split(',')]
                        directive['arguments'] = arguments

                        directive['datatype'] = \
                            self.raw_datatype[input_tree][arguments[0]]

                        directive['init'] = []
                        for arg in arguments:
                            if arg not in initialized_vars:
                                directive['init'].append(
                                    (arg, self.raw_datatype[input_tree][arg]))

                        self.calc_directive[output_tree][input_tree].append(
                            directive
                        )

    def write(self, cpp_file):
        filecontent = self.cpp_gen_date()
        filecontent += ('\n').join([self.cpp_header(h)
                                    for h in set(self.headers)]) + '\n'

        definitions = self.cpp_tuple_generators()
        main = self.cpp_main_addon(self.cpp_calls())
        filecontent += self.cpp_main(definitions, main)

        with open(cpp_file, 'w') as f:
            f.write(filecontent)

        self.reformat(cpp_file)

    def cpp_main_addon(self, calls):
        return '''
TFile *{0} = new TFile(argv[1], "read");
TFile *{1} = new TFile(argv[2], "recreate");

{2}

{1}->Close();

delete {0};
delete {1};
'''.format(self.cpp_input_file, self.cpp_output_file, calls)

    def cpp_calls(self):
        calls = ''

        for output_tree, input_trees in self.io_directive.items():
            for input_tree in input_trees:
                calls += '{0}_{1}({2}, {3});\n'.format(
                    self.cpp_make_variable(output_tree, prefix='generator_'),
                    self.cpp_make_variable(input_tree),
                    self.cpp_input_file,
                    self.cpp_output_file
                )

        return calls

    def cpp_tuple_generators(self):
        tuple_generators = ''

        for output_tree, input_trees in self.io_directive.items():
            for input_tree in input_trees:
                tuple_generators += \
                    'void {0}_{1}(TFile *{2}, TFile *{3}) {{\n'.format(
                        self.cpp_make_variable(output_tree,
                                               prefix='generator_'),
                        self.cpp_make_variable(input_tree),
                        self.cpp_input_file,
                        self.cpp_output_file
                    )
                tuple_generators += self.cpp_variables(output_tree, input_tree)
                tuple_generators += self.cpp_loops(output_tree, input_tree)
                tuple_generators += '{}->Write();'.format(self.cpp_output_file)
                tuple_generators += '}\n\n'

        return tuple_generators

    def cpp_variables(self, output_tree, input_tree):
        variables = 'TTree {0}("{1}", "{1}");\n'.format(
            self.cpp_make_variable(output_tree), output_tree)
        variables += 'TTreeReader {0}("{1}", {2});\n'.format(
            self.cpp_make_variable(input_tree),
            input_tree,
            self.cpp_input_file
        ) + '\n'

        for s in self.io_directive[output_tree][input_tree]:
            variables += '{0} {1};\n'.format(
                s['datatype'], self.cpp_make_variable(s['output_branch']))

            variables += '{0}.Branch("{1}", &{2});\n'.format(
                self.cpp_make_variable(output_tree),
                s['output_branch'],
                self.cpp_make_variable(s['output_branch'])
            )

            variables += 'TTreeReaderValue<{0}> {1}({2}, "{3}");\n'.format(
                s['datatype'],
                self.cpp_make_variable(s['input_branch'], suffix='_src'),
                self.cpp_make_variable(input_tree),
                s['input_branch']
            ) + '\n'

        try:
            for s in self.calc_directive[output_tree][input_tree]:
                variables += '{0} {1};\n'.format(
                    s['datatype'],
                    s['output_branch'])

                variables += '{0}.Branch("{1}", &{2});\n'.format(
                    self.cpp_make_variable(output_tree),
                    s['output_branch'],
                    self.cpp_make_variable(s['output_branch'])
                )

                for var in s['init']:
                    variables += \
                        'TTreeReaderValue<{0}> {1}({2}, "{3}");\n'.format(
                            var[1],
                            var[0]+'_src',
                            self.cpp_make_variable(input_tree),
                            var[0]
                        )

            variables += '\n'
        except KeyError:
            pass

        return variables

    def cpp_loops(self, output_tree, input_tree):
        loops = 'while ({0}.Next()) {{\n'.format(
            self.cpp_make_variable(input_tree),
            input_tree,
            self.cpp_input_file
        )
        loops += 'if ({}) {{\n'.format(self.cpp_selections(output_tree,
                                                           input_tree))

        for s in self.io_directive[output_tree][input_tree]:
            loops += '{0} = *{1};\n'.format(
                self.cpp_make_variable(s['output_branch']),
                self.cpp_make_variable(s['input_branch'], suffix='_src')
            )

        try:
            for s in self.calc_directive[output_tree][input_tree]:
                loops += '{0} = {1}({2});\n'.format(
                    self.cpp_make_variable(s['output_branch']),
                    s['functor'],
                    self.cpp_functor_args(s['arguments'])
                )

        except KeyError:
            pass

        loops += '{}.Fill();'.format(self.cpp_make_variable(output_tree))
        loops += '}\n}\n'

        return loops

    def cpp_selections(self, output_tree, input_tree):
        selections = ''

        for s in self.io_directive[output_tree][input_tree]:
            if s['selection']:
                selections += '*{0} {1} &&'.format(
                    self.cpp_make_variable(s['input_branch'], suffix='_src'),
                    s['selection']
                )

        return 'true' if selections == '' else selections[:-3]

    def cpp_functor_args(self, arguments):
        return ', '.join(['*{}'.format(self.cpp_make_variable(
            a, suffix='_src'))
            for a in arguments])

    @staticmethod
    def cpp_make_variable(string, prefix='', suffix=''):
        return prefix + re.sub('/', '_', string) + suffix
