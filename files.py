"""
File handling routines.
"""
import sys
import os


def process_file_list(file_list, func, args=None):
    """
    Open one file and a time and call the callback routine on each file.
    The callback routine should accept three arguments: file handler,
    file name and command line arguments (as an object).
    If the file list is empty then the standard input is used.
    This routine provides uniform way to process input files in a programs suite.
    :param file_list: list of files to process
    :type file_list: list
    :param func: callback function
    :type func: function
    :param args: command line arguments
    :type args: Namespace
    :return: None
    """
    # print 'process_file_list', file_list
    if len(file_list):
        for file_name in file_list:
            try:
                # print '-- file=' + file_name
                f = open(file_name, 'r')
                try:
                    func(f, file_name, args)
                except Exception as e:
                    print('Error while running', func, 'on', file_name, e)
                f.close()
            except Exception as e:
                print('Cannot open file', file_name, e)
    else:
        f = sys.stdin
        try:
            func(f, 'stdin', args)
        except Exception as e:
            print('Error while running', func, 'on stdin', e)


def list_directory(directory='.', skip_directories=True):
    """
    Return the list of files in directory. The files returned will have the
    directory name prepended to them.
    :param directory: directory name
    :type directory: str
    :param skip_directories: do not include directories in the output list
    :type skip_directories: bool
    :return: file list
    :rtype: list
    """
    output_list = []
    # print 'directory', directory
    if os.path.isdir(directory):
        try:
            file_list = os.listdir(directory)
        except Exception:
            raise IOError('Cannot get directory listing')
    else:
        raise IOError(directory + ' is not a directory')

    for file_name in file_list:
        file_name = os.path.join(directory, file_name)
        if skip_directories:
            if os.path.isfile(file_name):
                output_list.append(file_name)
        else:
            output_list.append(file_name)

    return output_list


def list_directories(directory_list=None, skip_directories=True):
    """
    Return the list of files in a list of directories. The files returned will have the
    corresponding directory name prepended to them so it will be possible to open the file
    using the name without worrying about what directory is located.
    :param directory_list: list of directories to list
    :type directory_list: list
    :param skip_directories: do not include directories in the output list
    :type skip_directories: bool
    :return: file list
    :rtype: list
    """
    if directory_list is None:
        directory_list = ['.']
    file_list = []
    for directory in directory_list:
        try:
            file_list.extend(list_directory(directory, skip_directories=skip_directories))
            # print '-', file_list
        except IOError as e:
            raise e
    return file_list


def _callback_test(f, file_name, args):
    """
    Callback function used to test process_file_list
    :param f: file handle
    :param file_name: file name
    :param args: list with command line arguments
    :return:
    """
    print('test callback', f, file_name, args)


if __name__ == '__main__':
    pass
    # process_file_list(['data'], _callback_test)
    # process_file_list(sys.argv[1:], _callback_test, None)
    # print list_directory('db_data')
    # print(list_directory('t', skip_directories=True))
    # print(list_directory('t', skip_directories=False))
    # print(list_directories(['t', 'db_data'], skip_directories=True))
    # print(list_directories(['t', 'db_data'], skip_directories=False))
    # # print list_directory('README'))
    # print(list_directories(['README', 't']))
