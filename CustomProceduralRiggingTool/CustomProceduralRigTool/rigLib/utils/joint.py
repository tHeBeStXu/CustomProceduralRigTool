"""
joint utils @ utils
"""

import maya.cmds as cmds
from . import name


def listHierarchy(topJoint,
                  withEndJoints=True):

    """
    list joint hierarchy starting with top joint
    :param topJoint: str, joint to get listed with its joint hierarchy
    :param withEndJoints: bool, list hierarchy including end joints
    :return: list(str), listed joints starting with top joint
    """

    listedJoints = cmds.listRelatives(topJoint,
                                      type='joint',
                                      ad=1)
    listedJoints.append(topJoint)
    listedJoints.reverse()

    completeJoints = listedJoints[:]

    if not withEndJoints:

        completeJoints = [j for j in listedJoints if cmds.listRelatives(j, c=1, type='joint')]

    return completeJoints



def createRevJnts(revLocator,
                  orientCtrl,
                  suffix):
    """
    create revJnts for IK  
    :param revLocator: list(str), ['CBank_LOC','EBank_LOC','heel_LOC'...]
    :param orientCtrl: 
    :return: list(str),revJntChain
    """

    # create joints for each LOC with correct name and orientation
    revJoints=[]
    for loc in revLocator:
        revJnt = cmds.joint(n=name.removeSuffix(loc) + suffix)
        cmds.delete(cmds.orientConstraint(orientCtrl, loc, mo=0))
        cmds.delete(cmds.pointConstraint(loc, revJnt, mo=0))
        revJoints.append(revJnt)

    return revJoints


def createFKjnts(CurveCVs,
                 orientObj,
                 prefix):
    """
    create FK Joints by Specified curveCVs
    :param CurveCVs: list(str), CurveCVs in builder Curve
    :param orientJnt: str, orient Object
    :param prefix: str, prefix of FK joints
    :return: list(str), list of FKjoints chain
    """
    fkJoints = []
    fkClusters = []

    for i in range(len(CurveCVs)):
        cls = cmds.cluster(CurveCVs[i], n=prefix + 'Cluster%d' % (i+1))[1]
        cmds.hide(cls)
        fkJnt = cmds.joint(n=prefix + '_FK%d' % i)
        cmds.delete(cmds.orientConstraint(orientObj, fkJnt, mo=0))
        cmds.delete(cmds.pointConstraint(cls, fkJnt, mo=0))
        fkJoints.append(fkJnt)
        fkClusters.append(cls)

    for i in range((len(fkJoints)-1)):
        cmds.parent(fkJoints[i+1], fkJoints[i])

    return {'fkJoints': fkJoints, 'fkClusters': fkClusters}


def dupSpecifiedJnts(startDupJnt,
                     endDupJnt,
                     suffix):
    dupDirtyJnt = cmds.duplicate(startDupJnt, n=startDupJnt + suffix)
    dupFullPath = cmds.listRelatives(dupDirtyJnt[0], f=1, ad=1)
    # remove endJnt Children
    for jnt in dupFullPath:
        if endDupJnt in jnt:
            if (len(endDupJnt) + jnt.index(endDupJnt)) < len(jnt):
                cmds.removeJoint(jnt)


    # rename cleanJnt
    dupCleanJnt = cmds.listRelatives(dupDirtyJnt[0], ad=1, f=1)
    for Jnt in dupCleanJnt:
        cmds.select(Jnt, add=1)
    for sel in cmds.ls(sl=1):
        cmds.rename(sel, sel.split('|')[-1] + suffix)

    dupCleanJnt = cmds.listRelatives(dupDirtyJnt[0], ad=1, f=1)
    dupCleanJnt = appendAndReverse(addtargetEndJnt=dupDirtyJnt[0], reverseList=dupCleanJnt)

    # clean returnList
    finalJnts = listHierarchy(topJoint=dupCleanJnt[0])

    return finalJnts


def appendAndReverse(addtargetEndJnt='',reverseList=''):
    reverseList.append(addtargetEndJnt)
    reverseList.reverse()
    return reverseList