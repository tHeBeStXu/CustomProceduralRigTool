import maya.cmds as cmds

from ..base import module
from ..base import control

from .. utils import name
from .. utils import IK_FK_Switch

reload(module)
reload(control)
reload(name)
reload(IK_FK_Switch)


def build(armJoints,
          prefix='L_',
          rigScale=1.0,
          FK_Parent='',
          switchCtrlPos='',
          baseRig=None):
    """
    Build the IK_FK_Arm rig.
    :param armJoints: list(str), armJoints list, [L_clavical, L_shoulder, L_elbow, L_wrist]
    :param prefix: str, prefix of the rig
    :param rigScale: float, rig scale of the IK_FK_Arm rig module.
    :param FK_Parent: str, the joint which armJoints[0] connects to.
    :param switchCtrlPos: str, position of the IK_FK_Blend_Ctrl position.
    :param baseRig: baseRig: str, base atttach of the rig. Base Class instance is used.
    :return: None
    """

    rigPartName = 'Arm'

    rigModule = module.Module(prefix=prefix,
                              rigPartName=rigPartName,
                              baseObject=baseRig)

    # create FK joints chain
    fk_preParent = armJoints[0]
    fk_Joint_List = []
    for i in xrange(len(armJoints)-1):
        newJnt = cmds.joint(n='FK_' + armJoints[i+1])
        cmds.delete(cmds.parentConstraint(armJoints[i+1], newJnt, mo=0))
        cmds.makeIdentity(newJnt, apply=1, t=1, r=1, s=1)
        cmds.parent(newJnt, fk_preParent)
        fk_Joint_List.append(newJnt)
        fk_preParent = newJnt
        cmds.select(cl=1)
    cmds.setAttr(fk_Joint_List[0] + '.v', 0)

    # create IK joints chain
    ik_preParent = armJoints[0]
    ik_Joint_List = []
    for i in xrange(len(armJoints)-1):
        newJnt = cmds.joint(n='IK_' + armJoints[i+1])
        cmds.delete(cmds.parentConstraint(armJoints[i+1], newJnt, mo=0))
        cmds.makeIdentity(newJnt, apply=1, t=1, r=1, s=1)
        cmds.parent(newJnt, ik_preParent)
        ik_Joint_List.append(newJnt)
        ik_preParent = newJnt
        cmds.select(cl=1)

    cmds.setAttr(ik_Joint_List[0] + '.v', 0)

    cmds.select(cl=1)

    ##############
    # Arm FK Rig #
    ##############
    FK_Arm_Ctrl_List = []
    FK_Arm_CtrlGrp_List = []
    for i in xrange(len(fk_Joint_List)):
        FK_Arm_Ctrl = control.Control(prefix=prefix + 'FK_',
                                      rigPartName=name.removePrefix(armJoints[i+1]),
                                      scale=rigScale*3.0,
                                      translateTo=fk_Joint_List[i],
                                      rotateTo=fk_Joint_List[i],
                                      shape='cubeOnBase',
                                      axis='x',
                                      lockChannels=['t', 's', 'v'])
        cmds.pointConstraint(FK_Arm_Ctrl.C, fk_Joint_List[i], mo=0)
        cmds.orientConstraint(FK_Arm_Ctrl.C, fk_Joint_List[i], mo=0)

        FK_Arm_Ctrl_List.append(FK_Arm_Ctrl.C)
        FK_Arm_CtrlGrp_List.append(FK_Arm_Ctrl.Off)
        cmds.select(cl=1)

    # lock the .rx and ry attribute of elbowCtrl
    # cmds.setAttr(FK_Arm_Ctrl_List[1] + '.rx', l=1, k=0)
    # cmds.setAttr(FK_Arm_Ctrl_List[1] + '.ry', l=1, k=0)

    # parent the CtrlGrps to the proper places
    for i in xrange(len(FK_Arm_Ctrl_List)-1):
        cmds.parent(FK_Arm_CtrlGrp_List[i+1], FK_Arm_Ctrl_List[i])

    # clavical Rig
    clavical_Ctrl = control.Control(prefix=prefix,
                                    rigPartName=name.removePrefix(armJoints[0]),
                                    scale=rigScale*3.0,
                                    translateTo=armJoints[0],
                                    rotateTo=armJoints[0],
                                    shape='rotationControl',
                                    axis='x',
                                    lockChannels=['t', 's', 'v'])

    cmds.orientConstraint(clavical_Ctrl.C, armJoints[0], mo=0)

    # Clavical local2World
    cmds.addAttr(clavical_Ctrl.C, ln='Local2World', at="float", min=0, max=1, dv=0, k=1)

    clavical_Local = cmds.spaceLocator(n=armJoints[0] + '_Local')
    clavical_Local_Shape = cmds.listRelatives(clavical_Local, s=1)
    cmds.setAttr(clavical_Local_Shape[0] + '.localScaleX', 0)
    cmds.setAttr(clavical_Local_Shape[0] + '.localScaleY', 0)
    cmds.setAttr(clavical_Local_Shape[0] + '.localScaleZ', 0)
    cmds.setAttr(clavical_Local_Shape[0] + '.template', 1)

    clavical_World = cmds.spaceLocator(n=armJoints[0] + '_World')
    clavical_World_Shape = cmds.listRelatives(clavical_World, s=1)
    cmds.setAttr(clavical_World_Shape[0] + '.localScaleX', 0)
    cmds.setAttr(clavical_World_Shape[0] + '.localScaleY', 0)
    cmds.setAttr(clavical_World_Shape[0] + '.localScaleZ', 0)
    cmds.setAttr(clavical_World_Shape[0] + '.template', 1)

    cmds.delete(cmds.parentConstraint(FK_Arm_Ctrl_List[0], clavical_Local, mo=0))
    cmds.delete(cmds.parentConstraint(FK_Arm_Ctrl_List[0], clavical_World, mo=0))

    cmds.pointConstraint(clavical_Local, FK_Arm_CtrlGrp_List[0], mo=0)
    clavical_OrientConstraint = cmds.orientConstraint(clavical_Local, clavical_World, FK_Arm_CtrlGrp_List[0], mo=0)

    cmds.setAttr(clavical_Ctrl.C + '.Local2World', 0)
    cmds.setAttr(clavical_OrientConstraint[0] + '.' + clavical_Local[0] + 'W0', 1)
    cmds.setAttr(clavical_OrientConstraint[0] + '.' + clavical_World[0] + 'W1', 0)

    cmds.setDrivenKeyframe(clavical_OrientConstraint[0] + '.' + clavical_Local[0] + 'W0',
                           cd=clavical_Ctrl.C + '.Local2World')
    cmds.setDrivenKeyframe(clavical_OrientConstraint[0] + '.' + clavical_World[0] + 'W1',
                           cd=clavical_Ctrl.C + '.Local2World')

    cmds.setAttr(clavical_Ctrl.C + '.Local2World', 1)
    cmds.setAttr(clavical_OrientConstraint[0] + '.' + clavical_Local[0] + 'W0', 0)
    cmds.setAttr(clavical_OrientConstraint[0] + '.' + clavical_World[0] + 'W1', 1)

    cmds.setDrivenKeyframe(clavical_OrientConstraint[0] + '.' + clavical_Local[0] + 'W0',
                           cd=clavical_Ctrl.C + '.Local2World')
    cmds.setDrivenKeyframe(clavical_OrientConstraint[0] + '.' + clavical_World[0] + 'W1',
                           cd=clavical_Ctrl.C + '.Local2World')

    cmds.parent(clavical_Local, armJoints[0])
    cmds.parent(clavical_World, rigModule.topGrp)

    ##############
    # Arm IK Rig #
    ##############
    IK_Arm_Ctrl = control.Control(prefix=prefix + 'IK_',
                                  rigPartName=rigPartName,
                                  scale=rigScale*3,
                                  translateTo=ik_Joint_List[-1],
                                  rotateTo=ik_Joint_List[-1],
                                  shape='circle')

    cmds.orientConstraint(IK_Arm_Ctrl.C, ik_Joint_List[-1], mo=0)

    IK_Arm_PV_Ctrl = control.Control(prefix=prefix + 'IK_',
                                     rigPartName=rigPartName + '_PV',
                                     scale=rigScale*3,
                                     translateTo=ik_Joint_List[1],
                                     shape='diamond',
                                     lockChannels=['r', 's', 'v'])

    ik_Part_List = cmds.ikHandle(n=prefix + rigPartName + '_IK', sj=ik_Joint_List[0],
                                 ee=ik_Joint_List[-1], sol='ikRPsolver')

    cmds.parent(ik_Part_List[0], IK_Arm_Ctrl.C)
    cmds.setAttr(ik_Part_List[0] + '.v', 0)
    cmds.poleVectorConstraint(IK_Arm_PV_Ctrl.C, ik_Part_List[0])

    ###############
    # FK Hand Rig #
    ###############

    # get finger joint list
    finger_Start_Joints_List = cmds.listRelatives(armJoints[-1], p=0, children=1, s=0, type='joint')

    finger_Joints_Dic = {}
    clean_Finger_Joints_Dic = {}
    for i in xrange(len(finger_Start_Joints_List)):
        finger_Joints_Dic[('Finger_' + str(i))] = cmds.listRelatives(finger_Start_Joints_List[i],
                                                                     p=0, allDescendents=1, s=0, type='joint')
        finger_Joints_Dic[('Finger_' + str(i))].append(finger_Start_Joints_List[i])
        # remove the end joint
        finger_Joints_Dic[('Finger_' + str(i))].reverse()
        clean_Finger_Joints_Dic[('Finger_' + str(i))] = finger_Joints_Dic[('Finger_' + str(i))][:-1]

    # create FK Ctrl
    finger_FK_Ctrl_Dic = {}
    finger_FK_CtrlGrp_Dic = {}
    for key in clean_Finger_Joints_Dic:
        finger_FK_Ctrl_Dic[key] = []
        finger_FK_CtrlGrp_Dic[key] = []
        for i in xrange(len(clean_Finger_Joints_Dic[key])):
            cleanRigPartName = name.removePrefix(name.removeSuffix(clean_Finger_Joints_Dic[key][i]))
            FK_Finger_Ctrl = control.Control(prefix=prefix + 'FK_',
                                             rigPartName=(cleanRigPartName + '_' + str(i)),
                                             scale=rigScale,
                                             translateTo=clean_Finger_Joints_Dic[key][i],
                                             rotateTo=clean_Finger_Joints_Dic[key][i],
                                             shape='circleZ',
                                             lockChannels=['t', 's', 'v']
                                             )
            cmds.pointConstraint(FK_Finger_Ctrl.C, clean_Finger_Joints_Dic[key][i], mo=0)
            cmds.orientConstraint(FK_Finger_Ctrl.C, clean_Finger_Joints_Dic[key][i], mo=0)

            finger_FK_Ctrl_Dic[key].append(FK_Finger_Ctrl.C)
            finger_FK_CtrlGrp_Dic[key].append(FK_Finger_Ctrl.Off)

    # clean the hierarchy
    for key in finger_FK_CtrlGrp_Dic:
        for i in xrange(len(finger_FK_CtrlGrp_Dic[key])-1):
            cmds.parent(finger_FK_CtrlGrp_Dic[key][i+1], finger_FK_Ctrl_Dic[key][i])

    # use locator as grp to control the handCtrl
    hand_Loc = cmds.spaceLocator(n=prefix + 'Wrist_Grp_Loc')
    hand_Loc_Shape = cmds.listRelatives(hand_Loc, s=1)
    cmds.setAttr(hand_Loc_Shape[0] + '.localScaleX', 0)
    cmds.setAttr(hand_Loc_Shape[0] + '.localScaleY', 0)
    cmds.setAttr(hand_Loc_Shape[0] + '.localScaleZ', 0)

    cmds.parentConstraint(armJoints[-1], hand_Loc, mo=0)

    for key in finger_FK_CtrlGrp_Dic:
        cmds.parent(finger_FK_CtrlGrp_Dic[key][0], hand_Loc)

    cmds.parent(hand_Loc, rigModule.topGrp)

    ###############
    # FK IK Blend #
    ###############

    IK_FK_Blend_Ctrl = control.Control(prefix=prefix,
                                       rigPartName=rigPartName + '_Blend',
                                       scale=rigScale * 3,
                                       translateTo=switchCtrlPos,
                                       shape='unitSliderControl',
                                       lockChannels=['tx', 'tz', 'r', 's', 'v'])
    # add enum attr for IK_FK seamless switch
    cmds.addAttr(IK_FK_Blend_Ctrl.C, ln='Mode', at='enum', en='IK:FK', k=1)

    cmds.rotate(0, 0, -90, IK_FK_Blend_Ctrl.Off, relative=1, objectSpace=1)

    for i in xrange(len(fk_Joint_List)):
        # create blendColors node
        blendNode = cmds.createNode('blendColors')
        # IK
        cmds.connectAttr(ik_Joint_List[i] + '.r', blendNode + '.color1', f=1)
        # FK
        cmds.connectAttr(fk_Joint_List[i] + '.r', blendNode + '.color2', f=1)
        # Skin
        cmds.connectAttr(blendNode + '.output', armJoints[i+1] + '.r', f=1)
        # blendNode
        cmds.connectAttr(IK_FK_Blend_Ctrl.C + '.ty', blendNode + '.blender')

    # visibility blend
    cmds.setAttr(IK_FK_Blend_Ctrl.C + '.ty', 0)
    cmds.setAttr(FK_Arm_CtrlGrp_List[0] + '.v', 1)
    cmds.setAttr(IK_Arm_Ctrl.Off + '.v', 0)
    cmds.setAttr(IK_Arm_PV_Ctrl.Off + '.v', 0)

    cmds.setDrivenKeyframe(FK_Arm_CtrlGrp_List[0] + '.v', cd=IK_FK_Blend_Ctrl.C + '.ty')
    cmds.setDrivenKeyframe(IK_Arm_Ctrl.Off + '.v', cd=IK_FK_Blend_Ctrl.C + '.ty')
    cmds.setDrivenKeyframe(IK_Arm_PV_Ctrl.Off + '.v', cd=IK_FK_Blend_Ctrl.C + '.ty')

    cmds.setAttr(IK_FK_Blend_Ctrl.C + '.ty', 1)
    cmds.setAttr(FK_Arm_CtrlGrp_List[0] + '.v', 0)
    cmds.setAttr(IK_Arm_Ctrl.Off + '.v', 1)
    cmds.setAttr(IK_Arm_PV_Ctrl.Off + '.v', 1)

    cmds.setDrivenKeyframe(FK_Arm_CtrlGrp_List[0] + '.v', cd=IK_FK_Blend_Ctrl.C + '.ty')
    cmds.setDrivenKeyframe(IK_Arm_Ctrl.Off + '.v', cd=IK_FK_Blend_Ctrl.C + '.ty')
    cmds.setDrivenKeyframe(IK_Arm_PV_Ctrl.Off + '.v', cd=IK_FK_Blend_Ctrl.C + '.ty')

    cmds.pointConstraint(switchCtrlPos, IK_FK_Blend_Ctrl.Off, mo=0)
    switchCtrlPos_Shape = cmds.listRelatives(switchCtrlPos, s=1)
    cmds.setAttr(switchCtrlPos_Shape[0] + '.localScaleX', 0)
    cmds.setAttr(switchCtrlPos_Shape[0] + '.localScaleY', 0)
    cmds.setAttr(switchCtrlPos_Shape[0] + '.localScaleZ', 0)
    cmds.setAttr(switchCtrlPos_Shape[0] + '.template', 1)
    switchCtrlLoc = cmds.spaceLocator(n=prefix + rigPartName + 'BlendCtrl_Loc')
    switchCtrlLoc_Shape = cmds.listRelatives(switchCtrlLoc, s=1)
    cmds.setAttr(switchCtrlLoc_Shape[0] + '.localScaleX', 0)
    cmds.setAttr(switchCtrlLoc_Shape[0] + '.localScaleY', 0)
    cmds.setAttr(switchCtrlLoc_Shape[0] + '.localScaleZ', 0)
    cmds.setAttr(switchCtrlLoc_Shape[0] + '.template', 1)

    cmds.pointConstraint(armJoints[-1], switchCtrlLoc, mo=0)
    cmds.parent(switchCtrlPos, switchCtrlLoc)

    # add attr
    for joint in armJoints:
        if not cmds.attributeQuery('rigModule', node=joint, exists=1):
            cmds.addAttr(joint, ln='rigModule', at='message')

        if not cmds.attributeQuery('slaveJoint', node=joint, exists=1):
            cmds.addAttr(joint, ln='slaveJoint', at='message')

    for key in clean_Finger_Joints_Dic.keys():
        for joint in clean_Finger_Joints_Dic[key]:
            if not cmds.attributeQuery(prefix + rigPartName + '_Jnt', node=joint, exists=1):
                cmds.addAttr(joint, ln=prefix + rigPartName + '_Jnt', at='message')

            if not cmds.attributeQuery('slaveJoint', node=joint, exists=1):
                cmds.addAttr(joint, ln='slaveJoint', at='message')

    # connect attr
    for joint in armJoints:
        if cmds.attributeQuery('rigModule', node=joint, exists=1):
            cmds.connectAttr(rigModule.topGrp + '.' + prefix + rigPartName + '_Jnt',
                             joint + '.rigModule', f=1)

    for key in clean_Finger_Joints_Dic.keys():
        for joint in clean_Finger_Joints_Dic[key]:
            if cmds.attributeQuery('rigModule', node=joint, exists=1):
                cmds.connectAttr(rigModule.topGrp + '.' + prefix + rigPartName + '_Jnt',
                                 joint + '.rigModule', f=1)

    # final cleaning
    cmds.parent(FK_Arm_CtrlGrp_List[0], clavical_Ctrl.C)

    if FK_Parent:
        FK_Loc = cmds.spaceLocator(n=prefix + rigPartName + '_Loc')
        FK_LocShape = cmds.listRelatives(FK_Loc, s=1)
        cmds.setAttr(FK_LocShape[0] + '.localScaleX', 0)
        cmds.setAttr(FK_LocShape[0] + '.localScaleY', 0)
        cmds.setAttr(FK_LocShape[0] + '.localScaleZ', 0)
        cmds.parentConstraint(FK_Parent, FK_Loc, mo=0)
        cmds.parent(clavical_Ctrl.Off, FK_Loc)
        cmds.parent(FK_Loc, rigModule.topGrp)
    else:
        cmds.warning('FK_Parent is None')
        cmds.parent(clavical_Ctrl.Off, rigModule.topGrp)

    cmds.parent(IK_Arm_PV_Ctrl.Off, rigModule.topGrp)
    cmds.parent(IK_Arm_Ctrl.Off, rigModule.topGrp)
    cmds.parent(switchCtrlLoc, rigModule.topGrp)
    cmds.parent(IK_FK_Blend_Ctrl.Off, rigModule.topGrp)

    cmds.select(cl=1)

    # IK_FK_seamless Switch by scriptJob and scriptNode
    IK_FK_Switch.IK_FK_Switch(prefix=prefix,
                              switchCtrl=IK_FK_Blend_Ctrl.C,
                              pvCtrl=IK_Arm_PV_Ctrl.C,
                              ikCtrl=IK_Arm_Ctrl.C,
                              skinJoints=armJoints[1:],
                              fkCtrlList=FK_Arm_Ctrl_List)

    cmds.select(cl=1)

    return rigModule
