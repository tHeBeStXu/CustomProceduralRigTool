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
