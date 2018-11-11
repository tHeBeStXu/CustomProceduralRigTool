"""
createNode utils @ utils 
"""
import maya.cmds as cmds
def createNode(nodeStr='',
               prefix='',
               name=''):

    if nodeStr == 'condition':
        Node = cmds.createNode(nodeStr, n=prefix+name+'_CD')
    elif nodeStr == 'blendColors':
        Node = cmds.createNode(nodeStr, n=prefix+name+'_BLC')
    return Node