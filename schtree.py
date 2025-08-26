#!/usr/bin/env python
import sys
from argparse import ArgumentParser, SUPPRESS, Namespace
from sch import SchematicFiles

# Variable used to control debug output
debug_flag = True


def print_tree(sfo, top_schematics=None):
    """
    Print top level tree starting at the specified schematic.
    If no schematic is specified the list of not referenced schematics will be used.
    This functions protects itself from circular references.
    :param sfo: SchematicFiles object
    :type sfo: SchematicFiles
    :type sfo: SchematicFiles
    :param top_schematics: list of top level schematics to traverse
    :type top_schematics: list
    :return: None
    """
    if top_schematics is None:
        top_schematics = []
    sch_list = top_schematics if top_schematics else sfo.get_not_referenced()
    for sch_name in sch_list:
        sch_name = sch_name.replace('.sch', '')
        traversed_list = []
        if sch_name in sfo.get_schematics():
            print_tree_hierarchy(sfo, sch_name, traversed_list, 0)
        else:
            print(sch_name, 'not found')
        print('')


def print_tree_hierarchy(sfo, sch_name, traversed_list, indent):
    """
    Print the hierarchy starting at a given schematic.
    This function calls itself recursively for all sub schematics.
    :param sfo: SchematicFiles object
    :type sfo: SchematicFiles
    :param sch_name: name of the schematic to print hierarchy from
    :type sch_name: str
    :param traversed_list: list of traversed schematics
    :type traversed_list: list
    :param indent: number of spaces to indent output
    :type indent: int
    :return:
    """
    debug_info = ' ' + str(list(sfo.get_children(sch_name))) if debug_flag else ''
    print(' ' * indent + sch_name + debug_info)
    traversed_list.append(sch_name)
    for ref_name in sfo.get_children(sch_name):
        if ref_name not in traversed_list:
            print_tree_hierarchy(sfo, ref_name, traversed_list, indent=indent + 2)


def print_search(sfo, schematic_name):
    """
    Print the tree starting at the given schematic up to the top level schematic
    that references it. The tree is printed backwards, i.e. the schematic to
    search for is printed at the leftmost position.
    :param sfo: SchematicFiles object
    :type sfo: SchematicFiles
    :param schematic_name: name of the schematic to look for
    :type schematic_name: str
    :return:
    """
    sch_name = schematic_name.replace('.sch', '')
    if sch_name in sfo.get_schematics():
        print_search_hierarchy(sfo, sch_name, 0)
    else:
        print(schematic_name, 'not found')


def print_search_hierarchy(sfo, sch_name, indent):
    """
    Print the search hierarchy starting at a given schematic.
    This function calls itself recursively for all sub schematics.
    The routine will descend up to a certain indent value to protect
    against circular references (there's no way to use a traversed
    list in this case).
    :param sfo: SchematicFiles object
    :type sfo: SchematicFiles
    :param sch_name: name of the schematic to look for
    :param indent: number of spaces to indent output
    :type indent: int
    :return: None
    """
    if indent < 100:
        parent_list = [] if sch_name in sfo.get_not_referenced() else sfo.get_parent(sch_name)
        debug_info = ' ' + str(list(parent_list)) if debug_flag else ''
        print(' ' * indent + sch_name + debug_info)
        for parent_name in parent_list:
            print_search_hierarchy(sfo, parent_name, indent + 2)
    else:
        # Too many loops!
        print(' ' * indent + '...truncated')
        return


def get_args(argv):
    """
    Process command line arguments
    :param argv: command line arguments from sys.argv
    :type argv: list
    :return: arguments
    :rtype: Namespace
    """

    epilog_text = \
        """Print the hierarchy(ies) of schematic in the current directory if no command arguments are supplied. """ + \
        """Except for --directory, only one command line option can be used at a time. """ + \
        """Schematics can be specified with or without the '.sch' extension."""

    parser = ArgumentParser(epilog=epilog_text)

    parser.add_argument(action='store',
                        nargs='*',
                        dest='top',
                        default=[])

    parser.add_argument('-s', '--search',
                        action='store',
                        dest='search',
                        default='',
                        help='schematic to search for')

    parser.add_argument('--nr', '--notreferenced',
                        action='store_true',
                        dest='notreferenced',
                        default=False,
                        help='print schematics not referenced by other schematics')

    parser.add_argument('--nu', '--notused',
                        action='store_true',
                        dest='notused',
                        default=False,
                        help='print schematics that are not used')

    parser.add_argument('-d', '--directory',
                        action='store',
                        dest='directory',
                        default='',
                        help='directory where schematics are stored, default=(./)')

    parser.add_argument('--debug',
                        action='store_true',
                        dest='debug',
                        default=False,
                        help=SUPPRESS)

    return parser.parse_args(argv[1:])


def print_not_referenced(sfo):
    """
    Print the list of schematics that are not used (one per line)
    :param sfo: SchematicFiles object
    :type sfo: SchematicFiles
    :return: None
    """
    for name in sfo.get_not_referenced():
        print(name + '.sch')


def print_not_used(sfo):
    """
    Print the list of schematics that are not used (one per line)
    :param sfo: SchematicFiles object
    :type sfo: SchematicFiles
    :return: None
    """
    for name in sfo.get_not_used():
        print(name + '.sch')


if __name__ == '__main__':
    args = get_args(sys.argv)
    # args = get_args(['schtree', '-h'])
    # args = get_args(['schtree', '-d', './sch_data/gws', '--debug'])
    # args = get_args(['schtree', 'gwsTop.sch', '-d', './sch_data/gws'])
    # args = get_args(['schtree', 'gwsTop.sch', '-d', './sch_data/gws', '--debug'])
    # args = get_args(['schtree', 'ecs.sch', '-d', './sch_data/ecs', '--debug'])
    # args = get_args(['schtree', 'gwsCommands.sch', '-d', './sch_data/gws', '--debug'])
    # args = get_args(['schtree', 'gwsCommands.sch', '-d', './sch_data/gws'])
    # args = get_args(['schtree', '-s', 'simMask.sch', '-d', './sch_data/gws', '--debug'])
    # args = get_args(['schtree', '-s', 'simMask.sch', '-d', './sch_data/gws'])
    # args = get_args(['schtree', '-s', 'gwsTop.sch', '-d', './sch_data/gws'])
    # args = get_args(['schtree', 'gwsTop.sch', 'gwsSad', '-d', './sch_data/gws'])
    # args = get_args(['schtree', '--nu', '-d', './sch_data/gws', '--debug'])
    # args = get_args(['schtree', '--nu', '-d', './sch_data/gws'])
    # args = get_args(['schtree', '--nr', '-d', './sch_data/gws', '--debug'])
    # args = get_args(['schtree', '--nr', '-d', './sch_data/gws'])
    # args = get_args(['schtree', '--nr', '--nr', './sch_data/gws'])
    debug_flag = args.debug
    if debug_flag:
        print(args)

    # Process the schematics
    sf = SchematicFiles(args.directory)
    sf.read_schematics()
    if debug_flag:
        sf.dump()

    # Check for incompatible command line options
    if [args.notreferenced, args.notused, len(args.search) > 0, len(args.top) > 0].count(True) > 1:
        print('Use only one command line option a time')
        exit(1)

    # Take action based on the command line option
    if args.notused:
        print_not_used(sf)
    elif args.notreferenced:
        print_not_referenced(sf)
    elif args.search:
        print_search(sf, args.search)
    else:
        print_tree(sf, args.top)
