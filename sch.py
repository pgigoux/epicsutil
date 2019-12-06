import os
import re
from files import list_directory


class SchematicFiles:
    """
    Class used to extract information from Capfast schematics and symbol files.
    The information is stored in the following class members:

    sch_dict: A dictionary containing the full schematic names.
              It's indexed by schematic name (without path name or extension).

    sym_list: The list of symbol files found (without path name or extension).

    children_dict: A dictionary indexed by schematic name containing the sub schematics
                   referenced by each schematic.

    parent_dict: A dictionary indexed by schematic name containing the schematics that
                 reference each schematic.

    not_referenced: The list of schematics that are not referenced by any schematic.
                    Evaluated once for speed reasons.

    not_used: The list of schematics that are not referenced by any schematic and that do
              not reference any schematic.Evaluated once for speed reasons.
    """
    def __init__(self, directory_name=None):
        """
        Create and initialize class instance
        :param directory_name: directory to scan for files
        """
        self.directory = os.getcwd() if not directory_name else directory_name
        self.sch_dict = {}
        self.sym_list = []
        self.children_dict = {}
        self.parent_dict = {}
        # the last two are created for speed reasons
        self.not_referenced = []
        self.not_used = []

    def get_schematics(self):
        """
        Return the list of all schematic files found (without the .sch extension)
        :return: schematic list
        :rtype: list
        """
        return self.children_dict.keys()

    def get_symbols(self):
        """
        Return the list of all the symbol files found (without the .sym extension)
        :return: symbol list
        :rtype: list
        """
        return self.sym_list

    def get_children(self, sch_name):
        """
        Get the list (set) of schematics that are referenced in one schematic.
        :param sch_name: schematic name
        :type sch_name: str
        :return: list of children
        :rtype: set
        """
        return self.children_dict[sch_name]

    def get_parent(self, sch_name):
        """
        Return the list (set) of schematics that reference a given schematic.
        :param sch_name: schematic name
        :type sch_name: str
        :return: list of parent schematics
        :rtype: set
        """
        return self.parent_dict[sch_name]

    def get_not_referenced(self):
        """
        Return the list of schematics that are not referenced by other schematics.
        :return: list of schematics
        :rtype: list
        """
        return self.not_referenced

    def get_not_used(self):
        """
        Return the list of schematics that are not referenced by other schematics and
        that do not reference other schematics.
        :return: list of schematics
        :rtype: list
        """
        return self.not_used

    def _is_sym(self, sym):
        """
        Check whether a given symbol is in the symbol list.
        :param sym: symbol name
        :return: True if the symbol is in the symbol list, False otherwise.
        :rtype: bool
        """
        return sym in self.sym_list

    def _get_not_referenced(self):
        """
        Return the list of schematics that are not referenced by any other schematic.
        This happens in top level schematics or schematics that are not used.
        :return: list of schematics
        :rtype: list
        """
        return [s for s in self.sch_dict if s not in self.sym_list]

    def _get_not_used(self):
        """
        Return the list of schematics that are not used, i.e. not referenced in any other
        schematic and not referencing any schematic.
        Should be run after _get_not_referenced.
        :return: list of schematics
        :rtype: list
        """
        return [s for s in self.not_referenced if len(self.children_dict[s]) == 0]

    def _read_files(self):
        """
        Populate the schematic and symbol dictionaries with the files from the
        directory specified when the schematic list object was created.
        The dictionaries are indexed by schematic/symbol name and the value is
        the full file name of the schematic/symbol file.
        """
        # Loop over all files in the directory.
        # Enter in the schematic dictionary or the symbol list depending whether
        # the file name ends in a '.sch' or '.sym' substring.
        # The keys for the the schematic dictionary and the elements in the symbol
        # list will be the the file names without path name and extension.
        file_list = list_directory(self.directory)
        for file_name in file_list:
            name = os.path.basename(file_name).split('.')[0]
            if re.search(r'\.sym$', file_name):
                self.sym_list.append(name)
            elif re.search(r'\.sch$', file_name):
                self.sch_dict[name] = file_name

        # Exclude all symbol files that don't have a corresponding schematic.
        # This can happen, for instance, when the code has symbols for custom records.
        # print len(self.sch_dict.keys()), len(self.sym_list)
        self.sym_list = list(set(self.sym_list) & set(self.sch_dict.keys()))

    def _read_references(self, sch_file):
        """
        Read the references to other schematics in a schematic file (children) and
        store them in a set, so that duplicated references are discarded.
        Only references to symbols in the symbol list are considered valid
        (i.e. references to non existent symbols or standard EPICS symbols are ignored).
        :param sch_file: schematic name
        :return: reference set
        :rtype: set
        """
        # TODO: refactor exception handling
        file_name = self.sch_dict[sch_file]
        references = set()
        try:
            f = open(file_name, 'r')
            for line in f:
                if re.search('^use', line):
                    sym = line.split()[1]
                    if self._is_sym(sym):
                        references.add(sym)
        except Exception as e:
            raise e
        return references

    def read_schematics(self):
        """
        This is the main routine that does all the schematic table update.
        It first reads the schematic/symbol tables and then updates the table
        with all the references.
        """
        self._read_files()
        for sch_name in self.sch_dict:
            self.children_dict[sch_name] = self._read_references(sch_name)
            for r in self.children_dict[sch_name]:
                if r not in self.parent_dict:
                    self.parent_dict[r] = set()
                self.parent_dict[r].add(sch_name)
        self.not_referenced = self._get_not_referenced()
        self.not_used = self._get_not_used()

    def dump(self):
        """
        Print SchematicList object. For debugging only.
        """
        print('directory', self.directory)
        print('sch', len(self.sch_dict), self.sch_dict)
        print('sym', len(self.sym_list), self.sym_list)
        print('children', len(self.children_dict), self.children_dict)
        print('parent', len(self.parent_dict), self.parent_dict)
        print('notref', len(self.not_referenced), self.not_referenced)
        print('notused', len(self.not_used), self.not_used)


if __name__ == '__main__':
    sf = SchematicFiles('./sch_data/gws')
    sf.read_schematics()
    sf.dump()
