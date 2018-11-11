"""
transform @ utils

Functions to manipulate and create transforms
"""

import maya.cmds as cmds
from . import name
import sys
"""
Dir = 'C:/Users/tHeBeStXu/Documents/maya/scripts/KOMODO/code/python'
if not Dir in sys.path:

    sys.path.append(Dir)
"""


def makeOffsetGrp (object, prefix=''):

    """
    make offset group for given object
    :param object:transform object to get offset group
    :param prefix:str, prefix to name new objects
    :return:str, name of new offset group
    """

    if not prefix:

        prefix = name.removeSuffix(object)

    offsetGrp = cmds.group(n=prefix + 'Offset_grp', em=1)

    objectParents = cmds.listRelatives(object, p=1)

    if objectParents:

        cmds.parent(offsetGrp, objectParents[0])

    # match object transform

    cmds.delete(cmds.parentConstraint(object, offsetGrp))
    cmds.delete(cmds.scaleConstraint(object, offsetGrp))

    # parent object under offset group

    cmds.parent(object, offsetGrp)

    return offsetGrp
