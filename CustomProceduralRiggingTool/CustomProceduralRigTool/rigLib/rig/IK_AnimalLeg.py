import maya.cmds as cmds

from ..base import module
from ..base import control

from ..utils import name

reload(module)
reload(control)
reload(name)


def build(legJoints,
          revJntlocList,
          ankleRollLoc,
          spineJnt='',
          prefix='L_',
          rigScale=1.0,
          baseRig=None):
    """
    IK animal leg rig, for
    :param legJoints: list(str), leg joints.[hip, knee, ankle, ball, toe, toeEnd]
    :param revJntlocList: list(str), rev_joint locator list.[CBank, EBank, Heel, Pivot]
    :param ankleRollLoc: str, ankleRoll locator.
    :param spineJnt: str, start joint of the spine(i.e. spine_0)
    :param prefix: str, 'L_' OR 'L_Front'...
    :param rigScale: float, rig scale of the module.
    :param baseRig: instance, base attach of the rig. Base Class instance is used.
    :return: None.
    """
    rigPartName = 'AnimLeg'

    if spineJnt:
        try:
            cmds.objectType(spineJnt) == 'joint'
        except:
            cmds.error('%s is not a joint type!' %spineJnt)
    else:
        parentJnt = cmds.listRelatives(legJoints[0], s=0, children=0, parent=1, type='joint')
        if parentJnt:
            spineJnt = parentJnt
        else:
            pass

    cmds.select(cl=1)

    rigModule = module.Module(prefix=prefix,
                              rigPartName=rigPartName,
                              baseObject=baseRig)

    hintFirstLength = cmds.getAttr(legJoints[2] + '.tx')
    hintSecondLength = cmds.getAttr(legJoints[1] + '.tx') + cmds.getAttr(legJoints[3] + '.tx')

    cmds.select(cl=1)

    # create IK_HintLeg
    hintJnt_List = []
    for i in xrange(3):
        hintJnt = cmds.joint(n=prefix + rigPartName + 'Hint_Jnt' + str(i))
        cmds.setAttr(hintJnt + '.drawStyle', 2)
        cmds.select(cl=1)
        hintJnt_List.append(hintJnt)

    for i in xrange(len(hintJnt_List)-1):
        cmds.parent(hintJnt_List[i+1], hintJnt_List[i])

    cmds.setAttr(hintJnt_List[1] + '.tx', hintFirstLength)
    cmds.setAttr(hintJnt_List[2] + '.tx', hintSecondLength)

    cmds.select(cl=1)

    cmds.setAttr(hintJnt_List[0] + '.rotateX', -90)
    cmds.setAttr(hintJnt_List[0] + '.rotateZ', 90)

    cmds.setAttr(hintJnt_List[1] + '.rotateZ', 90)

    cmds.makeIdentity(hintJnt_List[0], apply=1, t=1, r=1, s=1, n=0, pn=1)

    # hint leg ik
    IK_Hint_Part_List = cmds.ikHandle(n=prefix + rigPartName + 'hintLeg_IK', sj=hintJnt_List[0],
                                      ee=hintJnt_List[-1], sol='ikRPsolver')

    pc1 = cmds.pointConstraint(legJoints[0], hintJnt_List[0], mo=0)
    cmds.delete(pc1)
    pc2 = cmds.pointConstraint(legJoints[3], IK_Hint_Part_List[0], mo=0)
    cmds.delete(pc2)

    # create footCtrl and rev joints
    Foot_IK_Ctrl = control.Control(prefix=prefix,
                                   rigPartName=rigPartName,
                                   scale=rigScale*5,
                                   translateTo=legJoints[-2],
                                   rotateTo=legJoints[-2],
                                   shape='footControl',
                                   axis='y',
                                   lockChannels=['v'])
    cmds.select(cl=1)
    # flatten Ctrl and mirror the Ctrl action by plan YZ
    cmds.setAttr(Foot_IK_Ctrl.Off + '.rotateX', 90)
    cmds.setAttr(Foot_IK_Ctrl.Off + '.rotateY', 0)
    cmds.setAttr(Foot_IK_Ctrl.Off + '.rotateZ', cmds.getAttr(Foot_IK_Ctrl.Off + '.rotateZ') + 90)

    if prefix.startswith('R_'):
        cmds.setAttr(Foot_IK_Ctrl.Off + '.scaleZ', cmds.getAttr(Foot_IK_Ctrl.Off + '.scaleZ') * (-1))

    cmds.select(cl=1)

    revJntList = []
    for i in xrange(len(revJntlocList)):
        revJnt = cmds.joint(n=(name.removeSuffix(revJntlocList[i]) + '_Rev'))
        cmds.setAttr(revJnt + '.drawStyle', 2)
        cmds.select(cl=1)
        cmds.delete(cmds.pointConstraint(revJntlocList[i], revJnt, mo=0))
        cmds.delete(cmds.orientConstraint(Foot_IK_Ctrl.C, revJnt, mo=0))
        revJntList.append(revJnt)

    cmds.select(cl=1)

    for i in revJntlocList:
        cmds.delete(i)

    cmds.select(cl=1)

    legJoints_Rev = []
    for i in legJoints:
        legJoints_Rev.append(i)
    legJoints_Rev.reverse()

    cmds.select(cl=1)

    for i in xrange(len(legJoints_Rev[:3])):
        revJnt = cmds.joint(n=legJoints_Rev[i] + '_Rev')
        cmds.setAttr(revJnt + '.drawStyle', 2)
        cmds.select(cl=1)
        cmds.delete(cmds.pointConstraint(legJoints_Rev[i], revJnt, mo=0))
        cmds.delete(cmds.orientConstraint(Foot_IK_Ctrl.C, revJnt, mo=0))

        revJntList.append(revJnt)

    cmds.select(cl=1)

    # parenting
    for i in xrange(len(revJntList)-1):
        cmds.parent(revJntList[i+1], revJntList[i])
        cmds.select(cl=1)

    cmds.select(cl=1)

    cmds.makeIdentity(revJntList[0], apply=1, t=1, r=1, s=1, n=0, pn=1)

    # create BallRoll_Ctrl and RevJntRoll_Ctrl

    ballRoll_Ctrl = control.Control(prefix=prefix,
                                    rigPartName='BallRoll',
                                    scale=rigScale*3,
                                    translateTo=legJoints[-3],
                                    rotateTo=hintJnt_List[-1],
                                    shape='sphere',
                                    lockChannels=['t', 's', 'v'])
    cmds.orientConstraint(hintJnt_List[-1], ballRoll_Ctrl.Off, mo=0)

    cmds.select(cl=1)

    revJntRoll_Ctrl = control.Control(prefix=prefix,
                                      rigPartName='AnkleRoll',
                                      scale=rigScale * 7,
                                      translateTo=ankleRollLoc,
                                      rotateTo=Foot_IK_Ctrl.C,
                                      shape='rotationControl',
                                      axis='y',
                                      lockChannels=['t', 's', 'v'])
    cmds.delete(ankleRollLoc)
    cmds.select(cl=1)

    # revJntRoll_Ctrl connects attrs to revJntList
    cmds.addAttr(revJntRoll_Ctrl.C, ln='Ball2Toe', k=1, at="float", min=0, max=1, dv=0)

    # rotate Z

    condition1 = cmds.createNode('condition', n=prefix + 'Foot_CD#')
    cmds.setAttr(condition1 + '.colorIfFalseR', 0)

    cmds.setAttr(condition1 + '.operation', 2)

    cmds.connectAttr(revJntRoll_Ctrl.C + '.rotateZ', condition1 + '.firstTerm', f=1)
    cmds.connectAttr(revJntRoll_Ctrl.C + '.rotateZ', condition1 + '.colorIfTrueR', f=1)
    cmds.connectAttr(revJntRoll_Ctrl.C + '.rotateZ', condition1 + '.colorIfFalseG', f=1)

    cmds.connectAttr(condition1 + '.outColorR', revJntList[0] + '.rotateZ', f=1)
    cmds.connectAttr(condition1 + '.outColorG', revJntList[1] + '.rotateZ', f=1)

    # rotate Y

    cmds.connectAttr(revJntRoll_Ctrl.C + '.rotateY', revJntList[3] + '.rotateY', f=1)

    # rotate X
    condition2 = cmds.createNode('condition', n=prefix + 'Foot_CD#')
    cmds.setAttr(condition2 + '.colorIfFalseR', 0)
    cmds.setAttr(condition2 + '.operation', 2)

    cmds.connectAttr(revJntRoll_Ctrl.C + '.rotateX', condition2 + '.firstTerm', f=1)
    cmds.connectAttr(revJntRoll_Ctrl.C + '.rotateX', condition2 + '.colorIfTrueR', f=1)
    cmds.connectAttr(revJntRoll_Ctrl.C + '.rotateX', condition2 + '.colorIfFalseG', f=1)

    cmds.connectAttr(condition2 + '.outColorG', revJntList[2] + '.rotateX', f=1)

    blendColors = cmds.createNode('blendColors', n=prefix + 'Foot_BLC#')
    cmds.connectAttr(revJntRoll_Ctrl.C + '.Ball2Toe', blendColors + '.blender', f=1)
    cmds.connectAttr(condition2 + '.outColorR', blendColors + '.color1R', f=1)
    cmds.connectAttr(condition2 + '.outColorR', blendColors + '.color2G', f=1)

    cmds.connectAttr(blendColors + '.outputR', revJntList[4] + '.rotateX', f=1)
    cmds.connectAttr(blendColors + '.outputG', revJntList[5] + '.rotateX', f=1)

    cmds.select(cl=1)

    # Create IK for legJoints
    IK_Hip_Part_List = cmds.ikHandle(n=prefix + rigPartName + 'Hip_IK', sj=legJoints[0], ee=legJoints[2], sol='ikRPsolver')
    IK_Ball_List = cmds.ikHandle(n=prefix + rigPartName + 'Ball_IK', sj=legJoints[2], ee=legJoints[3], sol='ikSCsolver')
    IK_Toe_List = cmds.ikHandle(n=prefix + rigPartName + 'Toe_IK', sj=legJoints[3], ee=legJoints[4], sol='ikSCsolver')
    IK_ToeEnd_List = cmds.ikHandle(n=prefix + rigPartName + 'ToeEnd_IK', sj=legJoints[-2], ee=legJoints[-1], sol='ikSCsolver')
    cmds.select(cl=1)

    # pole vector Ctrl
    PV_Ctrl = control.Control(prefix=prefix,
                              rigPartName='Leg_PV',
                              scale=rigScale * 18,
                              translateTo=legJoints[1],
                              shape='diamond',
                              lockChannels=['r', 's', 'v'])
    cmds.select(cl=1)
    cmds.poleVectorConstraint(PV_Ctrl.C, IK_Hint_Part_List[0])
    cmds.setAttr(IK_Hint_Part_List[0] + '.twist', 180)
    cmds.poleVectorConstraint(PV_Ctrl.C, IK_Hip_Part_List[0])

    cmds.select(cl=1)

    # final parenting
    if spineJnt:
        cmds.parent(hintJnt_List[0], spineJnt)
    else:
        cmds.warning('No spine joint, IK system may not work as expected!')
        cmds.parent(hintJnt_List[0], rigModule.topGrp)

    cmds.parent(IK_Hip_Part_List[0], ballRoll_Ctrl.C)
    cmds.parent(IK_Ball_List[0], ballRoll_Ctrl.C)

    cmds.parent(ballRoll_Ctrl.Off, revJntList[-1])
    cmds.parent(IK_Hint_Part_List[0], revJntList[-1])

    cmds.parent(IK_Toe_List[0], revJntList[-2])
    cmds.parent(IK_ToeEnd_List[0], revJntList[-3])

    cmds.parent(revJntList[0], Foot_IK_Ctrl.C)
    cmds.parent(revJntRoll_Ctrl.Off, Foot_IK_Ctrl.C)

    cmds.parent(PV_Ctrl.Off, rigModule.topGrp)
    cmds.parent(Foot_IK_Ctrl.Off, rigModule.topGrp)

    # add Attr
    for joint in legJoints:
        if not cmds.attributeQuery('slaveJoint', node=joint, exists=1):
            cmds.addAttr(joint, longName='slaveJoint', at='message')

        if not cmds.attributeQuery('rigModule', node=joint, exists=1):
            cmds.addAttr(joint, longName='rigModule', at='message')

    # connect Attr
    for joint in legJoints:
        if cmds.attributeQuery('rigModule', node=joint, exists=1):
            cmds.connectAttr(rigModule.topGrp + '.' + prefix + rigPartName + '_Jnt',
                             joint + '.rigModule', f=1)

    cmds.select(cl=1)

    return rigModule
