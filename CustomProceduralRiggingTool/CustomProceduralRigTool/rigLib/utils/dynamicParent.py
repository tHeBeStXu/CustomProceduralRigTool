import maya.cmds as cmds
import copy


def dynamicParent():
    sel = cmds.ls(sl=1)

    locatorList = []
    for i in xrange(len(sel)-1):
        locator = cmds.spaceLocator(n=sel[i] + '_Loc')
        cmds.delete(cmds.parentConstraint(sel[i], locator, mo=0))
        cmds.parent(locator, sel[i])
        locatorList.append(locator)

    DPGroup = cmds.group(n=sel[-1] + '_DPGrp', empty=1)
    cmds.delete(cmds.parentConstraint(sel[-1], DPGroup, mo=0))

    pcGroup = cmds.group(n=sel[-1] + '_pcDPGrp', empty=1)
    cmds.delete(cmds.parentConstraint(sel[-1], pcGroup, mo=0))

    cmds.parent(pcGroup, DPGroup)
    cmds.parent(sel[-1], pcGroup)

    newList = []
    for i in locatorList:
        newList.append(i[0])

    newList.insert(0, DPGroup)

    cmds.select(cl=1)

    for i in xrange(len(newList)):
        cmds.parentConstraint(newList[i], pcGroup, mo=0)

    parentConstraint = cmds.listRelatives(pcGroup, s=0, c=1, p=0, type='parentConstraint')[0]

    enumStr = ':'.join(newList)
    # add Attr
    cmds.addAttr(sel[-1], ln='Parent', at='enum', en=enumStr, k=1)

    for i in xrange(len(newList)):
        cmds.setAttr(parentConstraint + '.' + newList[i] + 'W' + str(i), 0)

    codeStr = '''import maya.cmds as cmds

def dynamicParentSwitch():
    constraintObj = '{0}'
    parentConstraint = '{1}'
    newList = {2}

    index = cmds.getAttr(constraintObj + '.Parent')

    wst = cmds.xform(constraintObj, q=1, ws=1, t=1)

    wsr = cmds.xform(constraintObj, q=1, ws=1, ro=1)

    cmds.setAttr(parentConstraint + '.' +  newList[index] + 'W' + str(index), 1)

    for i in xrange(len(newList)):
        if i == index:
            continue
        else:
            cmds.setAttr(parentConstraint + '.' +  newList[i] + 'W' + str(i), 0)

    cmds.xform(constraintObj, ws=1, t=wst)

    cmds.xform(constraintObj, ws=1, ro=wsr)

cmds.scriptJob(attributeChange=['{3}' + '.Parent', dynamicParentSwitch])
'''.format(sel[-1],
           parentConstraint,
           newList,
           sel[-1])
    nodeName = cmds.scriptNode(st=2, bs=codeStr.replace("'''", "''"), n='DynamicParent_#', stp='python')
    cmds.scriptNode(nodeName, executeBefore=1)
