import maya.cmds as cmds

from ..base import control
from ..base import module
reload(control)
reload(module)


def build(tailJoints,
          FK_Parent='',
          rigScale=1.0,
          prefix='C_',
          baseRig=None
          ):
    """
    Build the FK_Tail rig.
    :param tailJoints: list(str), tailJoints to the end. i.e.[tail_1, tail_2, tail_3, ... tail_x, tail_end]
    :param rigScale: float, rig scale of the FK_Tail rig module, 1.0 is used.
    :param FK_Parent: str, the joint which tailJoint[0] connects to.
    :param prefix: str, prefix of the tail rig.
    :param baseRig: str, base atttach of the rig, Base Class instance is used.
    :return: None
    """
    rigPartName = 'Tail'

    cmds.select(cl=1)
    rigModule = module.Module(prefix=prefix,
                              rigPartName=rigPartName,
                              baseObject=baseRig)

    ##########
    # FK Rig #
    ##########
    validTailJoints = []
    for i in tailJoints:
        if cmds.listRelatives(i, s=0, p=0, children=1):
            validTailJoints.append(i)

    FK_tailCtrl_List = []
    FK_tailCtrlGrp_List = []

    # FK Ctrl
    for i in xrange(len(validTailJoints)):
        FK_tailCtrl = control.Control(prefix=prefix + 'FK_',
                                      rigPartName=rigPartName + '_' + str(i),
                                      scale=rigScale * (len(validTailJoints) - i),
                                      translateTo=validTailJoints[i],
                                      rotateTo=validTailJoints[i],
                                      shape='circle')

        cmds.pointConstraint(FK_tailCtrl.C, validTailJoints[i], mo=0)
        cmds.orientConstraint(FK_tailCtrl.C, validTailJoints[i], mo=0)

        FK_tailCtrl_List.append(FK_tailCtrl.C)
        FK_tailCtrlGrp_List.append(FK_tailCtrl.Off)

    cmds.select(cl=1)

    # Parenting
    for i in xrange(len(FK_tailCtrlGrp_List)-1):
        cmds.parent(FK_tailCtrlGrp_List[i+1], FK_tailCtrl_List[i])

    cmds.select(cl=1)

    # add and set ctrl visibility
    cmds.addAttr(FK_tailCtrl_List[0], ln='Tail_Ctrl_Visibility', at='bool', dv=0, k=1)

    target_Ctrl_List = []
    for i in FK_tailCtrl_List[1::2]:
        target_Ctrl_List.append(i)

    ctrlShape_Input_List = []
    for i in xrange(len(target_Ctrl_List)):
        CtrlShape = cmds.listRelatives(target_Ctrl_List[i], s=1, children=0, parent=0)
        ctrlShape_Input = cmds.listConnections(CtrlShape[0] + '.create', source=1, destination=0, plugs=0)[0]
        ctrlShape_Input_List.append(ctrlShape_Input)

    cmds.setAttr(FK_tailCtrl_List[0] + '.Tail_Ctrl_Visibility', 0)
    for i in xrange(len(ctrlShape_Input_List)):
        cmds.setAttr(ctrlShape_Input_List[i] + '.sweep', 0)
        cmds.setDrivenKeyframe(ctrlShape_Input_List[i] + '.sweep', cd=FK_tailCtrl_List[0] + '.Tail_Ctrl_Visibility')

    cmds.setAttr(FK_tailCtrl_List[0] + '.Tail_Ctrl_Visibility', 1)
    for i in xrange(len(ctrlShape_Input_List)):
        cmds.setAttr(ctrlShape_Input_List[i] + '.sweep', 360)
        cmds.setDrivenKeyframe(ctrlShape_Input_List[i] + '.sweep', cd=FK_tailCtrl_List[0] + '.Tail_Ctrl_Visibility')

    # Clean the hierarchy
    if FK_Parent:
        FK_Loc = cmds.spaceLocator(n=prefix + 'Tail_Loc')
        FK_LocShape = cmds.listRelatives(FK_Loc, s=1)
        cmds.setAttr(FK_LocShape[0] + '.localScaleX', 0)
        cmds.setAttr(FK_LocShape[0] + '.localScaleY', 0)
        cmds.setAttr(FK_LocShape[0] + '.localScaleZ', 0)
        cmds.parentConstraint(FK_Parent, FK_Loc, mo=0)
        cmds.parent(FK_tailCtrlGrp_List[0], FK_Loc)
        cmds.parent(FK_Loc, rigModule.topGrp)
    else:
        cmds.parent(FK_tailCtrlGrp_List[0], rigModule.topGrp)
        cmds.warning('Warning: FK_Parent is None!')

    cmds.select(cl=1)

    # add attr
    for joint in tailJoints[:-1]:
        if not cmds.attributeQuery('slaveJoint', node=joint, exists=1):
            cmds.addAttr(joint, longName='slaveJoint', at='message')

        if not cmds.attributeQuery('rigModule', node=joint, exists=1):
            cmds.addAttr(joint, longName='rigModule', at='message')

    # connect attr
    for joint in tailJoints[:-1]:
        if cmds.attributeQuery('rigModule', node=joint, exists=1):
            cmds.connectAttr(rigModule.topGrp + '.' + prefix + 'Tail_Jnt',
                             joint + '.rigModule', f=1)

    cmds.select(cl=1)

    return rigModule
