"""
name @utils

Utilities to work with names and strings
"""


def removeSuffix(name):

    """
    Remove suffix from given name string
    :param name: given name string to process
    :return: str, name without suffix
    """

    edits = name.split('_')

    if len(edits) < 2:

        return name

    suffix = '_' + edits[-1]
    nameNoSuffix = name[:-len(suffix)]

    return nameNoSuffix


def removePrefix(name):
    """
    remove prefix 
    :param name: str, name with no suffix
    :return: name with out prefix
    """
    edit = name.split('_')

    if len(edit) < 2:
        return name

    nameNoPrefix = edit[-1]
    return nameNoPrefix
