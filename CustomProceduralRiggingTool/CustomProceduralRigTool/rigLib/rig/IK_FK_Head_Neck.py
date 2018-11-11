import maya.cmds as cmds
from ..base import module
from ..base import control
reload(module)
reload(control)


def build(neckJoints,
          Neck_Parent='',
          rigScale=1.0,
          prefix='C_',
          blendCtrl_Pos='',
          baseRig=None
          ):
    """
    Build the IK_FK_Neck rig.
    :param neckJoints: list(str), neck joints and head joint list, [neck_0, neck_1, ... neck_#, head, head_end]
    :param Neck_Parent: str, Neck parent joint, it's usually the last valid joint of the spine joints(i.e. Spine_#)
    :param rigScale: float, rig scale of the control
    :param prefix: str, 'C_', 'L_' or 'R_'
    :param blendCtrl_Pos: str, space locator
    :param baseRig: str, base atttach of the rig, Base Class instance is used.
    :return: None
    """
    if Neck_Parent:
        try:
            cmds.objectType(Neck_Parent) == 'joint'
            pass
        except:
            cmds.error('%s is not a joint, please check again' % Neck_Parent)

    else:
        parentJnt = cmds.listRelatives(neckJoints[0], s=0, c=0, parent=1, type='joint')
        if parentJnt:
            Neck_Parent = parentJnt
        else:
            cmds.warning('No parent jnt of %s, IK may not work as expected!' % neckJoints[0])

    cmds.select(cl=1)

    rigPartName = 'Head'

    rigModule = module.Module(prefix=prefix,
                              rigPartName=rigPartName,
                              baseObject=baseRig)

    cmds.select(cl=1)

    # duplicate the specified joints
    # create fk joints list
    fk_Joints_List = []
    fkHeadJnts_Dirty_Start = cmds.duplicate(neckJoints[0], n='FK_' + neckJoints[0], renameChildren=1)
    fk_Joints_List.append(fkHeadJnts_Dirty_Start[0])
    fkHeadJnts_Dirty_Children = cmds.listRelatives(fkHeadJnts_Dirty_Start, s=0, parent=0, children=1, type='joint')

    for i in range(len(fkHeadJnts_Dirty_Children)):
        rename_Jnt = cmds.rename(fkHeadJnts_Dirty_Children[i], 'FK_' + neckJoints[i+1])
        fk_Joints_List.append(rename_Jnt)

    cmds.setAttr(fk_Joints_List[0] + '.v', 0)
    cmds.select(cl=1)

    # create ik joints list
    ik_Joints_List = []
    ikHeadJnts_Dirty_Start = cmds.duplicate(neckJoints[0], n='IK_' + neckJoints[0], renameChildren=1)
    ik_Joints_List.append(ikHeadJnts_Dirty_Start[0])
    ikHeadJnts_Dirty_Children = cmds.listRelatives(ikHeadJnts_Dirty_Start, s=0, parent=0, children=1, type='joint')

    for i in range(len(ikHeadJnts_Dirty_Children)):
        rename_Jnt = cmds.rename(ikHeadJnts_Dirty_Children[i], 'IK_' + neckJoints[i+1])
        ik_Joints_List.append(rename_Jnt)

    cmds.setAttr(ik_Joints_List[0] + '.v', 0)
    cmds.select(cl=1)

    ##########
    # FK Rig #
    ##########

    FK_Neck_CtrlGrp_List = []
    FK_Neck_Ctrl_List = []

    for i in xrange(len(fk_Joints_List)-2):
        FK_Neck_Ctrl = control.Control(prefix=prefix + 'FK_',
                                       rigPartName='Neck_' + str(i),
                                       scale=rigScale,
                                       translateTo=fk_Joints_List[i],
                                       rotateTo=fk_Joints_List[i],
                                       shape='arrowCurve',
                                       axis='x',
                                       lockChannels=['t', 's', 'v']
                                       )
        cmds.orientConstraint(FK_Neck_Ctrl.C, fk_Joints_List[i], mo=0)

        FK_Neck_CtrlGrp_List.append(FK_Neck_Ctrl.Off)
        FK_Neck_Ctrl_List.append(FK_Neck_Ctrl.C)

        cmds.select(cl=1)

    # parent the CtrlGrps to the proper places
    for i in xrange(len(FK_Neck_Ctrl_List)-1):
        cmds.parent(FK_Neck_CtrlGrp_List[i+1], FK_Neck_Ctrl_List[i])

    FK_Head_Ctrl = control.Control(prefix=prefix + 'FK_',
                                   rigPartName=rigPartName,
                                   scale=rigScale,
                                   translateTo=fk_Joints_List[-2],
                                   rotateTo=fk_Joints_List[-2],
                                   shape='cubeOnBase',
                                   axis='x',
                                   lockChannels=['t', 's', 'v'])

    # Local LOC
    fk_headLocal = cmds.spaceLocator(n='FK_' + prefix + rigPartName + '_Local')
    fk_headLocal_Shape = cmds.listRelatives(fk_headLocal, s=1)
    cmds.setAttr(fk_headLocal_Shape[0] + '.localScaleX', 0)
    cmds.setAttr(fk_headLocal_Shape[0] + '.localScaleY', 0)
    cmds.setAttr(fk_headLocal_Shape[0] + '.localScaleZ', 0)
    cmds.setAttr(fk_headLocal_Shape[0] + '.template', 1)

    # World LOC
    fk_headWorld = cmds.spaceLocator(n='FK_' + prefix + rigPartName + '_World')
    fk_headWorld_Shape = cmds.listRelatives(fk_headWorld, s=1)
    cmds.setAttr(fk_headWorld_Shape[0] + '.localScaleX', 0)
    cmds.setAttr(fk_headWorld_Shape[0] + '.localScaleY', 0)
    cmds.setAttr(fk_headWorld_Shape[0] + '.localScaleZ', 0)
    cmds.setAttr(fk_headWorld_Shape[0] + '.template', 1)

    cmds.delete(cmds.parentConstraint(fk_Joints_List[-2], fk_headLocal, mo=0))
    cmds.delete(cmds.parentConstraint(fk_Joints_List[-2], fk_headWorld, mo=0))

    FK_Head_OrientConstraint = cmds.orientConstraint(fk_headLocal, fk_headWorld, FK_Head_Ctrl.Off, mo=0)
    cmds.pointConstraint(fk_headLocal, FK_Head_Ctrl.Off, mo=0)

    # create attr and setDrivenKey
    cmds.addAttr(FK_Head_Ctrl.C, ln='Local2World', at="float", min=0, max=1, dv=0, k=1)
    cmds.setAttr(FK_Head_Ctrl.C + '.Local2World', 0)
    cmds.setAttr(FK_Head_OrientConstraint[0] + '.' + fk_headLocal[0] + 'W0', 1)
    cmds.setAttr(FK_Head_OrientConstraint[0] + '.' + fk_headWorld[0] + 'W1', 0)

    cmds.setDrivenKeyframe(FK_Head_OrientConstraint[0] + '.' + fk_headLocal[0] + 'W0',
                           cd=FK_Head_Ctrl.C + '.Local2World')
    cmds.setDrivenKeyframe(FK_Head_OrientConstraint[0] + '.' + fk_headWorld[0] + 'W1',
                           cd=FK_Head_Ctrl.C + '.Local2World')

    cmds.setAttr(FK_Head_Ctrl.C + '.Local2World', 1)
    cmds.setAttr(FK_Head_OrientConstraint[0] + '.' + fk_headLocal[0] + 'W0', 0)
    cmds.setAttr(FK_Head_OrientConstraint[0] + '.' + fk_headWorld[0] + 'W1', 1)

    cmds.setDrivenKeyframe(FK_Head_OrientConstraint[0] + '.' + fk_headLocal[0] + 'W0',
                           cd=FK_Head_Ctrl.C + '.Local2World')
    cmds.setDrivenKeyframe(FK_Head_OrientConstraint[0] + '.' + fk_headWorld[0] + 'W1',
                           cd=FK_Head_Ctrl.C + '.Local2World')

    # point and orient constriant the fk head joint
    cmds.pointConstraint(FK_Head_Ctrl.C, fk_Joints_List[-2], mo=0)
    cmds.orientConstraint(FK_Head_Ctrl.C, fk_Joints_List[-2], mo=1)

    ##########
    # IK Rig #
    ##########
    IK_Head_Ctrl = control.Control(prefix=prefix + 'IK_',
                                   rigPartName=rigPartName,
                                   scale=rigScale,
                                   translateTo=ik_Joints_List[-2],
                                   rotateTo=ik_Joints_List[-2],
                                   shape='moveControl',
                                   axis='x')

    IK_Start_Jnt = cmds.joint(n='IK_' + prefix + rigPartName + '_StartJnt')
    cmds.select(cl=1)
    IK_End_Jnt = cmds.joint(n='IK_' + prefix + rigPartName + '_EndJnt')
    cmds.select(cl=1)
    cmds.delete(cmds.parentConstraint(neckJoints[0], IK_Start_Jnt, mo=0))
    cmds.delete(cmds.parentConstraint(neckJoints[-2], IK_End_Jnt, mo=0))

    cmds.makeIdentity(IK_Start_Jnt, apply=1, t=1, r=1, s=1, n=0, pn=1)
    cmds.makeIdentity(IK_End_Jnt, apply=1, t=1, r=1, s=1, n=0, pn=1)

    cmds.select(cl=1)
    cmds.parent(IK_End_Jnt, IK_Head_Ctrl.C)

    if Neck_Parent:
        cmds.parent(IK_Start_Jnt, Neck_Parent)
    else:
        cmds.parent(IK_Start_Jnt, rigModule.topGrp)

    cmds.setAttr(IK_Start_Jnt + '.v', 0)
    cmds.setAttr(IK_End_Jnt + '.v', 0)

    # ik handle
    IK_Part_List = cmds.ikHandle(n=prefix + rigPartName + '_IK',
                                 sj=ik_Joints_List[0],
                                 ee=ik_Joints_List[-2],
                                 sol='ikSplineSolver',
                                 pcv=0,
                                 numSpans=4)

    cmds.select(cl=1)
    cmds.select(IK_Part_List[-1])
    cmds.select(IK_Start_Jnt, add=1)
    cmds.select(IK_End_Jnt, add=1)
    cmds.skinCluster(IK_Start_Jnt, IK_End_Jnt, IK_Part_List[-1], tsb=1)
    cmds.select(cl=1)

    # setup IK Twist
    cmds.setAttr(IK_Part_List[0] + '.dTwistControlEnable', 1)
    cmds.setAttr(IK_Part_List[0] + '.dWorldUpType', 4)
    cmds.connectAttr(IK_Start_Jnt + '.worldMatrix[0]', IK_Part_List[0] + '.dWorldUpMatrix')
    cmds.connectAttr(IK_End_Jnt + '.worldMatrix[0]', IK_Part_List[0] + '.dWorldUpMatrixEnd')

    # create ik_head_local and ik_head_world
    ik_headLocal = cmds.spaceLocator(n='IK_' + prefix + rigPartName + '_Local')
    ik_headLocal_Shape = cmds.listRelatives(ik_headLocal, s=1)
    cmds.setAttr(ik_headLocal_Shape[0] + '.localScaleX', 0)
    cmds.setAttr(ik_headLocal_Shape[0] + '.localScaleY', 0)
    cmds.setAttr(ik_headLocal_Shape[0] + '.localScaleZ', 0)
    cmds.setAttr(ik_headLocal_Shape[0] + '.template', 1)

    ik_headWorld = cmds.spaceLocator(n='IK_' + prefix + rigPartName + '_World')
    ik_headWorld_Shape = cmds.listRelatives(ik_headWorld, s=1)
    cmds.setAttr(ik_headWorld_Shape[0] + '.localScaleX', 0)
    cmds.setAttr(ik_headWorld_Shape[0] + '.localScaleY', 0)
    cmds.setAttr(ik_headWorld_Shape[0] + '.localScaleZ', 0)
    cmds.setAttr(ik_headWorld_Shape[0] + '.template', 1)

    cmds.delete(cmds.parentConstraint(ik_Joints_List[-2], ik_headLocal, mo=0))
    cmds.delete(cmds.parentConstraint(ik_Joints_List[-2], ik_headWorld, mo=0))

    IK_Head_OrientConstraint = cmds.orientConstraint(ik_headLocal, ik_headWorld, IK_Head_Ctrl.Off, mo=0)

    # create attr and setDrivenKey
    cmds.addAttr(IK_Head_Ctrl.C, ln='Local2World', at="float", min=0, max=1, dv=0, k=1)

    cmds.setAttr(IK_Head_Ctrl.C + '.Local2World', 0)
    cmds.setAttr(IK_Head_OrientConstraint[0] + '.' + ik_headLocal[0] + 'W0', 1)
    cmds.setAttr(IK_Head_OrientConstraint[0] + '.' + ik_headWorld[0] + 'W1', 0)

    cmds.setDrivenKeyframe(IK_Head_OrientConstraint[0] + '.' + ik_headLocal[0] + 'W0',
                           cd=IK_Head_Ctrl.C + '.Local2World')
    cmds.setDrivenKeyframe(IK_Head_OrientConstraint[0] + '.' + ik_headWorld[0] + 'W1',
                           cd=IK_Head_Ctrl.C + '.Local2World')

    cmds.setAttr(IK_Head_Ctrl.C + '.Local2World', 1)
    cmds.setAttr(IK_Head_OrientConstraint[0] + '.' + ik_headLocal[0] + 'W0', 0)
    cmds.setAttr(IK_Head_OrientConstraint[0] + '.' + ik_headWorld[0] + 'W1', 1)

    cmds.setDrivenKeyframe(IK_Head_OrientConstraint[0] + '.' + ik_headLocal[0] + 'W0',
                           cd=IK_Head_Ctrl.C + '.Local2World')
    cmds.setDrivenKeyframe(IK_Head_OrientConstraint[0] + '.' + ik_headWorld[0] + 'W1',
                           cd=IK_Head_Ctrl.C + '.Local2World')

    # IK FK BLEND
    IK_FK_BlendCtrl = control.Control(prefix=prefix,
                                      rigPartName=rigPartName + '_Blend',
                                      scale=rigScale*5,
                                      translateTo=blendCtrl_Pos,
                                      rotateTo=blendCtrl_Pos,
                                      shape='unitSliderControl',
                                      lockChannels=['tx', 'tz', 'r', 's', 'v'])

    for i in range(len(fk_Joints_List)):
        # blend node
        blend = cmds.createNode('blendColors')
        # ik
        cmds.connectAttr(ik_Joints_List[i] + '.r', blend + '.color1', f=1)
        # fk
        cmds.connectAttr(fk_Joints_List[i] + '.r', blend + '.color2', f=1)
        # output to origin neckJoints
        cmds.connectAttr(blend + '.output', neckJoints[i] + '.r', f=1)
        # IK_FK_BlendCtrl
        cmds.connectAttr(IK_FK_BlendCtrl.C + '.ty', blend + '.blender')

    # visibility blend
    cmds.setAttr(IK_FK_BlendCtrl.C + '.ty', 0)
    cmds.setAttr(FK_Neck_CtrlGrp_List[0] + '.v', 1)
    cmds.setAttr(FK_Head_Ctrl.Off + '.v', 1)
    cmds.setAttr(IK_Head_Ctrl.Off + '.v', 0)

    cmds.setDrivenKeyframe(FK_Neck_CtrlGrp_List[0] + '.v', cd=IK_FK_BlendCtrl.C + '.ty')
    cmds.setDrivenKeyframe(FK_Head_Ctrl.Off + '.v', cd=IK_FK_BlendCtrl.C + '.ty')
    cmds.setDrivenKeyframe(IK_Head_Ctrl.Off + '.v', cd=IK_FK_BlendCtrl.C + '.ty')

    cmds.setAttr(IK_FK_BlendCtrl.C + '.ty', 1)
    cmds.setAttr(FK_Neck_CtrlGrp_List[0] + '.v', 0)
    cmds.setAttr(FK_Head_Ctrl.Off + '.v', 0)
    cmds.setAttr(IK_Head_Ctrl.Off + '.v', 1)

    cmds.setDrivenKeyframe(FK_Neck_CtrlGrp_List[0] + '.v', cd=IK_FK_BlendCtrl.C + '.ty')
    cmds.setDrivenKeyframe(FK_Head_Ctrl.Off + '.v', cd=IK_FK_BlendCtrl.C + '.ty')
    cmds.setDrivenKeyframe(IK_Head_Ctrl.Off + '.v', cd=IK_FK_BlendCtrl.C + '.ty')

    neckLoc = cmds.spaceLocator(n=prefix + 'Neck_Loc')

    if Neck_Parent:
        cmds.parentConstraint(Neck_Parent, neckLoc, mo=0)

    cmds.parent(FK_Neck_CtrlGrp_List[0], neckLoc)
    cmds.parent(IK_Head_Ctrl.Off, neckLoc)

    # fk_headLocal and fk_headWorld
    cmds.parent(fk_headLocal, FK_Neck_Ctrl_List[-1])
    cmds.parent(fk_headWorld, rigModule.topGrp)
    # ik_headLocal and ik_headWorld
    cmds.parent(ik_headLocal, neckLoc)
    cmds.parent(ik_headWorld, rigModule.topGrp)

    # ik parts
    cmds.parent(IK_Part_List[0], rigModule.dontTouchGrp)
    cmds.parent(IK_Part_List[-1], rigModule.dontTouchGrp)

    # blend ctrl
    cmds.pointConstraint(blendCtrl_Pos, IK_FK_BlendCtrl.Off, mo=0)
    blendCtrl_Pos_Shape = cmds.listRelatives(blendCtrl_Pos, s=1)
    cmds.setAttr(blendCtrl_Pos_Shape[0] + '.localScaleX', 0)
    cmds.setAttr(blendCtrl_Pos_Shape[0] + '.localScaleY', 0)
    cmds.setAttr(blendCtrl_Pos_Shape[0] + '.localScaleZ', 0)
    cmds.setAttr(blendCtrl_Pos_Shape[0] + '.template', 1)
    headBlendLoc = cmds.spaceLocator(n=prefix + rigPartName + '_Blend_Loc')
    headBlendLoc_Shape = cmds.listRelatives(headBlendLoc, s=1)
    cmds.setAttr(headBlendLoc_Shape[0] + '.localScaleX', 0)
    cmds.setAttr(headBlendLoc_Shape[0] + '.localScaleY', 0)
    cmds.setAttr(headBlendLoc_Shape[0] + '.localScaleZ', 0)
    cmds.setAttr(headBlendLoc_Shape[0] + '.template', 1)
    cmds.pointConstraint(neckJoints[-2], headBlendLoc, mo=0)
    cmds.parent(blendCtrl_Pos, headBlendLoc)
    cmds.parent(IK_FK_BlendCtrl.Off, rigModule.topGrp)
    cmds.parent(headBlendLoc, rigModule.topGrp)

    # clean rigModule
    cmds.parent(FK_Head_Ctrl.Off, rigModule.topGrp)
    cmds.parent(neckLoc, rigModule.topGrp)

    # add attr
    for joint in neckJoints[:-1]:
        if not cmds.attributeQuery('slaveJoint', node=joint, exists=1):
            cmds.addAttr(joint, ln='slaveJoint', at='message')

        if not cmds.attributeQuery('rigModule', node=joint, exists=1):
            cmds.addAttr(joint, ln='rigModule', at='message')

    # connect attr
    for joint in neckJoints[:-1]:
        if cmds.attributeQuery('rigModule', node=joint, exists=1):
            cmds.connectAttr(rigModule.topGrp + '.' + prefix + rigPartName + '_Jnt',
                             joint + '.rigModule', f=1)

    cmds.select(cl=1)

    return rigModule
