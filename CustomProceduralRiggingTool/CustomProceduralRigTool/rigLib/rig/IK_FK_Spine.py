import maya.cmds as cmds
from ..base import module
from ..base import control
reload(module)
reload(control)


def build(spineJoints,
          prefix='C_',
          rigScale=1.0,
          numFK_Jnt=3,
          spineBackUpAxis='y',
          mainSpineAttach=None,
          baseRig=None):
    """
    Build IK_FK_Spine rig.
    This IK_FK_Spine build module is used for spine joint chain which is placed in the 0 x-Axis position.
    :param spineJoints: list(str), original spine joints, from the C_Spine_0 to C_Spine_x, you need to make true that
                        the spine joints are at same directions, i.e. x-axis is main axis, and z-axis is point to the
                        -x axis of world space.
    :param prefix: str, prefix of the spine, usually, 'C_' is used.
    :param rigScale: float, rig scale of the IK_FK_Spine rig module.
    :param numFK_Jnt: int, number of FK spine joints, greater than 3.
    :param mainSpineAttach: str, main Spine Attach part name, if the spine is not the mainSpine, must set a attachJoint
                            name to it. Usually the last valid joint of attached part.
    :param baseRig: str, base atttach of the rig. Base Class instance is used.
    :return: dictionary, rigModule, chest_ctrl (used for upper body parts rig, IK_FK_Arm .etc)and pelvis_ctrl (used for FK_Tail rig)
    """
    # param check
    if numFK_Jnt < 3:
        raise RuntimeError('Param: numFK_Jnt must larger than 3!')
        return

    # local rigPartName
    rigPartName = 'Spine'

    rigModule = module.Module(prefix=prefix,
                              rigPartName=rigPartName,
                              baseObject=baseRig)

    if spineBackUpAxis in ['y', 'Y']:
        worldUpVector = (0, 1, 0)
    elif spineBackUpAxis in ['z', 'Z']:
        worldUpVector = (0, 0, 1)

    # fk skeleton chain
    # create FK crv
    ik_part_list = []
    ik_part_list = cmds.ikHandle(sj=spineJoints[0], ee=spineJoints[-1], parentCurve=1, sol='ikSplineSolver', numSpans=4,
                                 simplifyCurve=0)

    cmds.delete(ik_part_list[0])

    FK_Crv = ik_part_list[-1]

    fkJntList = []
    eachADD = 1.0 / (len(range(numFK_Jnt)) - 1)

    for i in range(numFK_Jnt):
        fkJnt = cmds.joint(n='FK_' + prefix + rigPartName + '_' + str(i))
        pc = cmds.parentConstraint(spineJoints[0], fkJnt, mo=0)
        cmds.delete(pc)

        motionPath = cmds.pathAnimation(FK_Crv, fkJnt, n=fkJnt + '_motionPath', fractionMode=1, follow=1,
                                        followAxis='x', upAxis='y', worldUpType='Vector',
                                        worldUpVector=worldUpVector, inverseUp=0, inverseFront=0, bank=0)

        # cmds.disconnectAttr(motionPath + '_uValue.output', motionPath + '.uValue')
        cmds.cutKey(motionPath + '.u', time=())

        cmds.setAttr(motionPath + '.uValue', eachADD * float(i))

        for attr in ['t', 'r']:
            for axis in ['x', 'y', 'z']:
                cmds.delete(fkJnt + '.%s%s' % (attr, axis), icn=1)

        cmds.delete(motionPath)

        cmds.select(cl=1)

        fkJntList.append(fkJnt)

    # delete the motionPath
    cmds.delete(FK_Crv)

    # move the last fk joint to the end of the spineJoints
    pc3 = cmds.pointConstraint(spineJoints[-1], fkJntList[-1], mo=0)
    cmds.delete(pc3)

    # aimConstraint all the fk_joints, the last joints must be same direction as the last joints of original joints list
    fkJntList_rev = []

    for i in fkJntList:
        fkJntList_rev.append(i)
    fkJntList_rev.reverse()

    for i in xrange(len(fkJntList_rev)-1):
        ac = cmds.aimConstraint(fkJntList_rev[i], fkJntList_rev[i+1], mo=0, weight=1, aimVector=(1, 0, 0),
                                upVector=(0, 1, 0), worldUpType='vector', worldUpVector=worldUpVector)
        cmds.delete(ac)

    # orientConstraint the last joint
    oc = cmds.orientConstraint(spineJoints[-1], fkJntList_rev[0], mo=0)
    cmds.delete(oc)

    # parent
    for i in xrange(len(fkJntList_rev)-1):
        cmds.parent(fkJntList_rev[i], fkJntList_rev[i+1])

    # set fk joints drawStyle to None and display to template

    for i in fkJntList:
        cmds.setAttr(i + '.drawStyle', 2)

    # freeze transformation
    cmds.makeIdentity(fkJntList[0], apply=1)


    ##########
    # FK rig #
    ##########
    FK_CtrlGrp_List = []
    FK_Ctrl_List = []

    for i in xrange(len(fkJntList)-2):
        FK_C_Spine_Ctrl = control.Control(prefix=prefix + 'FK_',
                                          rigPartName=rigPartName + '_' + str(i),
                                          scale=rigScale,
                                          translateTo=fkJntList[i+1],
                                          rotateTo=fkJntList[i+1],
                                          shape='circle',
                                          lockChannels=['t', 's', 'v'])

        cmds.orientConstraint(FK_C_Spine_Ctrl.C, fkJntList[i+1], mo=0)

        FK_CtrlGrp_List.append(FK_C_Spine_Ctrl.Off)
        FK_Ctrl_List.append(FK_C_Spine_Ctrl.C)

        cmds.select(cl=1)

    # parent the CtrlGrps to the proper places
    for i in xrange(len(FK_Ctrl_List)-1):
        cmds.parent(FK_CtrlGrp_List[i+1], FK_Ctrl_List[i])

    cmds.parent(FK_CtrlGrp_List[0], fkJntList[0])

    #############
    # Body Ctrl #
    #############

    if not mainSpineAttach:
        # create a square control shape for body ctrl
        body_Ctrl = control.Control(prefix=prefix,
                                    rigPartName='Body',
                                    scale=rigScale * 15,
                                    shape='squareControl',
                                    translateTo=spineJoints[0],
                                    axis='z')
    else:
        body_Loc = cmds.spaceLocator(n=prefix + rigPartName + '_Loc')
        body_LocShape = cmds.listRelatives(body_Loc, s=1)
        cmds.setAttr(body_LocShape[0] + '.localScaleX', 0)
        cmds.setAttr(body_LocShape[0] + '.localScaleY', 0)
        cmds.setAttr(body_LocShape[0] + '.localScaleZ', 0)
        cmds.parentConstraint(mainSpineAttach, body_Loc, mo=0)

    C_Pelvis_Ctrl = control.Control(prefix=prefix,
                                    rigPartName='Pelvis',
                                    scale=rigScale*2,
                                    translateTo=spineJoints[0],
                                    rotateTo=spineJoints[0],
                                    axis='x',
                                    shape='moveControl')

    C_Chest_Ctrl = control.Control(prefix=prefix,
                                   rigPartName='Chest',
                                   scale=rigScale*3,
                                   translateTo=spineJoints[-1],
                                   rotateTo=spineJoints[-1],
                                   axis='x',
                                   shape='moveControl')

    # create 2 joints for controlling ikHandle curve
    pelvis_Jnt = cmds.joint(n=prefix + 'Pelvis')
    cmds.select(cl=1)
    cmds.setAttr(pelvis_Jnt + '.v', 0)
    chest_Jnt = cmds.joint(n=prefix + 'Chest')
    cmds.select(cl=1)
    cmds.setAttr(chest_Jnt + '.v', 0)

    pc1 = cmds.parentConstraint(fkJntList[0], pelvis_Jnt, mo=0)
    cmds.delete(pc1)
    cmds.makeIdentity(pelvis_Jnt, apply=1)

    pc2 = cmds.parentConstraint(fkJntList[-1], chest_Jnt, mo=0)
    cmds.delete(pc2)
    cmds.makeIdentity(chest_Jnt, apply=1)

    ##########
    # IK rig #
    ##########

    IK_Part_List = cmds.ikHandle(n=prefix + rigPartName + '_IK',
                                 sj=spineJoints[0],
                                 ee=spineJoints[-1],
                                 parentCurve=0,
                                 numSpans=4,
                                 sol='ikSplineSolver')

    # bind ik curve with 2 joints
    cmds.select(cl=1)
    cmds.select(IK_Part_List[-1])
    cmds.select(chest_Jnt, add=1)
    cmds.select(pelvis_Jnt, add=1)
    cmds.skinCluster(chest_Jnt, pelvis_Jnt, IK_Part_List[-1], tsb=1)

    # setup IK Twist
    cmds.setAttr(IK_Part_List[0] + '.dTwistControlEnable', 1)
    cmds.setAttr(IK_Part_List[0] + '.dWorldUpType', 4)
    cmds.connectAttr(C_Pelvis_Ctrl.C + '.worldMatrix[0]', IK_Part_List[0] + '.dWorldUpMatrix')
    cmds.connectAttr(C_Chest_Ctrl.C + '.worldMatrix[0]', IK_Part_List[0] + '.dWorldUpMatrixEnd')

    # add attr
    for joint in spineJoints:
        if not cmds.attributeQuery('slaveJoint', node=joint, exists=1):
            cmds.addAttr(joint, ln='slaveJoint', at='message')

        if not cmds.attributeQuery('rigModule', node=joint, exists=1):
            cmds.addAttr(joint, ln='rigModule', at='message')

    # connect attr
    for joint in spineJoints:
        if cmds.attributeQuery('rigModule', node=joint, exists=1):
            cmds.connectAttr(rigModule.topGrp + '.' + prefix + rigPartName + "_Jnt",
                             joint + '.rigModule', f=1)

    # clean up the hierarchy
    cmds.parent(pelvis_Jnt, C_Pelvis_Ctrl.C)
    cmds.parent(chest_Jnt, C_Chest_Ctrl.C)

    # parent fk_jnt to body_Ctrl
    if not mainSpineAttach:
        cmds.parent(fkJntList[0], body_Ctrl.C)

        # parent pelvis_CtrlGrp to body_Ctrl
        cmds.parent(C_Pelvis_Ctrl.Off, body_Ctrl.C)
    else:
        cmds.parent(fkJntList[0], body_Loc)
        cmds.parent(C_Pelvis_Ctrl.Off, body_Loc)


    # parent chest_CtrlGrp to fkJntList[-1]
    cmds.parent(C_Chest_Ctrl.Off, fkJntList[-1])

    cmds.parent(IK_Part_List[-1], IK_Part_List[0], rigModule.dontTouchGrp)

    # parent body_CtrlGrp to rigmodule.topGrp
    if not mainSpineAttach:
        cmds.parent(body_Ctrl.Off, rigModule.topGrp)
    else:
        cmds.parent(body_Loc, rigModule.topGrp)

    cmds.select(cl=1)

    # rootJoint
    rootJnt = ''
    if not mainSpineAttach:
        rootJnt = cmds.listRelatives(spineJoints[0], p=1, c=0, s=0, type='joint')

        if rootJnt:

            if not cmds.attributeQuery('slaveJoint', node=rootJnt[0], exists=1):
                cmds.addAttr(rootJnt[0], ln='slaveJoint', at='message')

            if not cmds.attributeQuery('rootJoint', node=rootJnt[0], exists=1):
                cmds.addAttr(rootJnt[0], ln='rootJoint', at='message')


    # return
    return {'chest_Ctrl': C_Chest_Ctrl.C,
            'pelvis_Ctrl': C_Pelvis_Ctrl.C,
            'rootJnt': rootJnt[0],
            'rigModule': rigModule}
