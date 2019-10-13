#!/usr/bin/python
"""
Extract state set and state information from an SNL file and print it in different formats.
"""
import sys
import re
from argparse import ArgumentParser, SUPPRESS
from files import process_file_list

# Number of spaces used to indent output in graph output
DIGRAPH_INDENT = ' ' * 4

# Debug flag
debug_flag = False


class StateSet:
    """
    Class used to represent a state set object.
    An object of this class has a name and a list of children states.
    """

    def __init__(self, name):
        if debug_flag:
            print('__init__: creating state set', name)
        self.name = name
        self.state_list = []
        return

    def __str__(self):
        return self.name + ': ' + str(len(self.state_list)) + ' ' + str(self.state_list)

    def add_state(self, state):
        """
        Add a state to the state set object.
        The order of the objects in the file is preserved.
        :param state: state object to add to the list
        :type state: State
        :return: None
        """
        assert isinstance(state, State)
        if debug_flag:
            print('add_state:', state, 'to', self.name)
        self.state_list.append(state)

    def get_name(self):
        """
        Get the state set name/identifier
        :return: state set name
        :rtype: str
        """
        return self.name

    def get_state_list(self):
        """
        Get the list of states in the state set
        :return: list
        """
        return self.state_list


class State:
    """
        Class used to represent a state object.
        An object of this class has a name and a list of state references.
        """

    def __init__(self, name):
        if debug_flag:
            print('__init__: creating state', name)
        self.name = name
        self.reference_list = []
        return

    def __str__(self):
        return self.name + ': ' + str(len(self.reference_list)) + ' ' + str(self.reference_list)

    def add_state_reference(self, state_reference):
        """
        Add a reference to a state to the state object.
        State references are (normally?) found in a 'when' clause.
        :param state_reference: referenced state name
        :type state_reference: str
        :return: None
        """
        assert isinstance(state_reference, str)
        if debug_flag:
            print('add_reference:', state_reference, 'to', self.name)
        if state_reference not in self.reference_list:
            self.reference_list.append(state_reference)

    def get_name(self):
        """
        Get the state name
        :return: state name
        :rtype: str
        """
        return self.name

    def get_reference_list(self):
        """
        Get the list of referenced states in the state
        :return: list of the state references (strings)
        :rtype: list
        """
        return self.name + ': ' + str(self.reference_list)


def parse_file(f_in):
    """
    SNL file parser. This is the place where all the processing is done.
    It will return an empty list if the parser fails to process the file.
    :param f_in: input file object
    :type f_in: file
    :return: list of StateSet objects
    :rtype: list
    """

    # Initialize variables
    state_set_list = []
    last_state_set = None
    last_state = None

    # Iterate over all the lines in the file
    for line in f_in:

        # Skip blank and comment lines
        line = line.strip()
        if not line:
            continue
        if re.search(r'^#|^\*|/\*', line):
            continue

        # Check for a state set declaration.
        # Should be of the for 'ss <state_set_name> {'
        # The closing brace (}) is not always in the same line.
        if re.search('^ss .*', line):  # state set

            tmp = line.split()
            if len(tmp) < 2:
                print('skip what it seems an incomplete state set declaration', line)
                continue
            state_set_name = tmp[1]

            if debug_flag:
                print('SS', state_set_name, tmp)
                print('last_state', last_state)

            if last_state_set is None:
                last_state_set = StateSet(state_set_name)
            else:
                last_state_set.add_state(last_state)
                state_set_list.append(last_state_set)
                last_state_set = StateSet(state_set_name)

            last_state = None

        # Check for state declaration
        # Should be of the for 'state <state_name> {'
        # The closing brace (}) is not always in the same line.
        elif re.search('^state', line):  # state declaration

            tmp = line.split()
            if len(tmp) < 2:
                print('skipped what it seems an incomplete state declaration', line)
                return []
            state_name = tmp[1]

            if debug_flag:
                print('STATE', state_name, tmp, last_state)

            if last_state is None:
                last_state = State(state_name)
            else:
                last_state_set.add_state(last_state)
                last_state = State(state_name)

        # Check for a state reference within a state
        # These are of the form '} state'
        elif re.search('}.*state .+', line):  # state reference

            tmp = line.split()
            if len(tmp) < 3:
                print('skipped what it seems an incomplete state reference', line)
                continue
            reference_name = tmp[2]

            if debug_flag:
                print('REF', reference_name, tmp)

            if last_state is not None:
                last_state.add_state_reference(reference_name)
            else:
                print('Null state')
                return []

        else:
            # ignore all other lines
            pass

    # Make sure the last state set in the file is appended to the state set list
    # This will normally happen when the end of file is reached.
    if last_state_set is not None:
        state_set_list.append(last_state_set)

    if debug_flag:
        print(type(state_set_list), len(state_set_list))

    return state_set_list


def print_as_text(state_set_list):
    """
    Print a state set list to the standar output as a text.
    :param state_set_list: list of StateSet objects
    :type state_set_list: list
    :return: None
    """
    # print '-' * 80
    for state_set in state_set_list:
        print('ss', state_set.get_name())
        assert isinstance(state_set, StateSet)
        # print state_set.get_state_list()
        for state in state_set.get_state_list():
            assert isinstance(state, State)
            print('   state', state.get_name())
            for reference in state.reference_list:
                print('      ', reference)
        print()
    return


def write_as_digraph(f_out, state_set_list):
    """
    Write the state set list to the an output file as a DOT digraph.
    This routine is not used in the program anymore, but was left here just in case.
    :param f_out: output file object
    :type f_out: file
    :param state_set_list: list of StateSet objects
    :type state_set_list: list
    :return:
    """
    f_out.write('digraph G {\n')

    for state_set in state_set_list:
        assert isinstance(state_set, StateSet)
        for state in state_set.get_state_list():
            assert isinstance(state, State)
            f_out.write(DIGRAPH_INDENT + state_set.get_name() + ' -> ' + state.get_name() + ';\n')
            for reference in state.reference_list:
                f_out.write(DIGRAPH_INDENT + state.get_name() + ' -> ' + reference + ';\n')

    f_out.write('}\n')

    return


def print_as_digraph(state_set_list):
    """
    Print the state set list to the standar output as a DOT digraph.
    :param state_set_list: list of StateSet objects
    :type state_set_list: list
    :return: None
    """
    print('digraph G {')

    for state_set in state_set_list:
        assert isinstance(state_set, StateSet)
        for state in state_set.get_state_list():
            assert isinstance(state, State)
            print(DIGRAPH_INDENT + state_set.get_name() + ' -> ' + state.get_name() + ';')
            for reference in state.reference_list:
                print(DIGRAPH_INDENT + state.get_name() + ' -> ' + reference + ';')

    print('}\n')

    return


def process_input_files(input_file_list):
    """
    Process all the input files in the input and write them to the standard output.
    The standard input is used if no files are specified.
    :param input_file_list: list of file names
    :type input_file_list: list
    :return: None
    """
    # print file_list
    state_set_list = []
    if len(input_file_list):
        for input_file_name in input_file_list:
            try:
                # print '-- file=' + file_name
                f_in = open(input_file_name, 'r')
                state_set_list = parse_file(f_in)
                f_in.close()
            except Exception as ex:
                print(ex)
    else:
        f_in = sys.stdin
        state_set_list = parse_file(f_in)

    return state_set_list


def process_file(f, file_name, p_args):
    """
    This is the callback function for process_file_list.
    Read the database snl file and print it in the selected format.
    :param f: database file
    :param file_name: file name (needed, but not used)
    :param p_args: command line arguments (not used)
    :return: None
    """
    if debug_flag:
        print('\n-- process_file', f, file_name, p_args)

    state_set_list = parse_file(f)

    if p_args.text:
        print_as_text(state_set_list)
    elif p_args.dot:
        print_as_digraph(state_set_list)

    return


def get_args(argv):
    """
    Process command line arguments
    :param argv: command line arguments from sys.argv
    :type argv: list
    :return: arguments
    :rtype: argparse.Namespace
    """

    parser = ArgumentParser(epilog='The standard input is used if no input files are supplied')

    parser.add_argument('-t', '--text',
                        action='store_true',
                        dest='text',
                        default=True,
                        help='print text output (default)')

    parser.add_argument('-d', '--dot',
                        action='store_true',
                        dest='dot',
                        default=False,
                        help='print dot graph output')

    parser.add_argument(action='store',
                        nargs='*',
                        dest='files',
                        default=[])

    parser.add_argument('--debug',
                        action='store_true',
                        dest='debug',
                        default=False,
                        help=SUPPRESS)

    return parser.parse_args(argv[1:])


if __name__ == '__main__':
    try:
        # args = get_args(['snldump', 'scs_st.st', '--text'])
        # args = get_args(['snldump', 'scs_st.st', '--text'])
        args = get_args(sys.argv)
        if args.dot:
            args.text = False
        debug_flag = args.debug
        if debug_flag:
            print(args)
        process_file_list(args.files, process_file, args=args)
    except Exception as e:
        print(e)
        sys.exit(1)
