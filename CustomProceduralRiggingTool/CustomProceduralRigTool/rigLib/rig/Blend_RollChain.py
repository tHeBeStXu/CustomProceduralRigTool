from maya import cmds


def build(rollStart,
          rollEnd,
          numRollJoints=1,
          rollWithSameDir=True
          ):
    """
    create a single bone roll joints chain with desired roll joints, blend rotation between rollStart and rollEnd joints
    :param rollStart: str, create roll joints from rollStart joint
    :param rollEnd: str, create roll joints ends at rollEnd joint
    :param roll_Parent: str, parent ik_roll_joints to roll_Parent joint.
                        If rollWithSameDir is True, roll_Parent is the joint above rollStart joint by 1 step
                        example: upper arm: Clavical; hip: body_pivot or c_spine_0
                        If rollWithSameDir is False, roll_Parent is the rollStart joint
                        example: lower arm: Elbow
    :param IK_Parent: str, parent ik handle to the IK_Parent joints
                        If rollWithSameDir is True, IK_Parent is the joint above rollStart joint by 1 step
                        example: upper arm: Clavical; hip: body_pivot or c_spine_0
                        If rollWithSameDir is False, IK_Parent is the rollStart joint
                        example: lower arm: Wrist
    :param numRollJoints: int, number of roll joints between rollStart joint and rollEnd joint
    :param rollWithSameDir: bool, whether the roll joints are the same generation direction
                            with the original joints chain direction
    :return: None
    """
    if numRollJoints < 1:
        raise RuntimeError('Param: numRollJoints must larger than 1, please input correct int number again!')
        return

    if rollWithSameDir:
        roll_Parent = cmds.listRelatives(rollStart, p=1, c=0, s=0, type='joint')[0]
        IK_Parent = cmds.listRelatives(rollStart, p=1, c=0, s=0, type='joint')[0]
    else:
        roll_Parent = rollStart
        IK_Parent = rollStart

    rollJointList = []

    # create the start and end roll joints
    rollStart_Jnt = cmds.joint(n=rollStart + '_Roll_Start')
    cmds.select(cl=1)
    rollEnd_Jnt = cmds.joint(n=rollStart + '_Roll_End')
    cmds.select(cl=1)

    # transform the joint
    pc1 = cmds.parentConstraint(rollStart, rollStart_Jnt, mo=0)
    cmds.delete(pc1)
    pc2 = cmds.parentConstraint(rollEnd, rollEnd_Jnt, mo=0)
    cmds.delete(pc2)

    # freeze transformation
    cmds.makeIdentity(rollStart_Jnt, apply=1, t=1, r=1, s=1)
    cmds.makeIdentity(rollEnd_Jnt, apply=1, t=1, r=1, s=1)

    # parent and get the .tx attribute
    cmds.parent(rollEnd_Jnt, rollStart_Jnt)
    totalLength = cmds.getAttr(rollEnd_Jnt + '.tx')

    eachLeagth = totalLength / (numRollJoints + 1)

    # create IK Handle
    ikHandle = cmds.ikHandle(n=rollStart + '_Roll_IK', sj=rollStart_Jnt, ee=rollEnd_Jnt, s='sticky', sol='ikSCsolver')
    cmds.parent(ikHandle[0], IK_Parent)
    cmds.pointConstraint(rollEnd, ikHandle[0], mo=0)

    rollJointList.append(rollStart_Jnt)

    if rollWithSameDir:
        rollDir = rollStart
        rollOrient = rollStart
        # create middle roll joints and transform it
        for i in range(0, numRollJoints):
            middleRoll_Jnt = cmds.duplicate(rollEnd_Jnt, n=rollStart + '_Roll_' + str(i + 1))
            cmds.setAttr(middleRoll_Jnt[0] + '.tx', eachLeagth * (int(i) + 1))
            cmds.parent(middleRoll_Jnt, rollDir)

            oc = cmds.orientConstraint(rollOrient, rollStart_Jnt, middleRoll_Jnt, mo=0)
            cmds.setAttr(oc[0] + '.' + rollStart_Jnt + 'W1', (len(range(0, numRollJoints)) - int(i)))
            cmds.setAttr(oc[0] + '.' + rollOrient + 'W0', (int(i) + 1))

            rollJointList.append(middleRoll_Jnt[0])

    else:
        rollDir = rollEnd
        rollOrient = rollEnd
        # create middle roll joints and transform it
        for i in range(0, numRollJoints):
            middleRoll_Jnt = cmds.duplicate(rollEnd_Jnt, n=rollStart + '_Roll_' + str(i + 1))
            cmds.setAttr(middleRoll_Jnt[0] + '.tx', eachLeagth * (int(i) + 1))
            cmds.parent(middleRoll_Jnt, rollDir)

            oc = cmds.orientConstraint(rollOrient, rollStart, middleRoll_Jnt, mo=0)
            cmds.setAttr(oc[0] + '.' + rollStart + 'W1', (len(range(0, numRollJoints)) - int(i)))
            cmds.setAttr(oc[0] + '.' + rollOrient + 'W0', (int(i) + 1))

            rollJointList.append(middleRoll_Jnt[0])

    # parent
    cmds.parent(rollStart_Jnt, roll_Parent)

    #############
    # attribute #
    #############
    if rollWithSameDir:
        # slave pointConstraint attr
        if not cmds.attributeQuery('slavePointConst', node=rollStart, exists=1):
            cmds.addAttr(rollStart, ln='slavePointConst', dt='string')

            cmds.setAttr(rollStart + '.slavePointConst', cmds.ls(rollEnd, long=1)[0], type='string', lock=1)

        if not cmds.attributeQuery('slaveParent', node=rollStart, exists=1):
            cmds.addAttr(rollStart, ln='slaveParent', dt='string')

            cmds.setAttr(rollStart + '.slaveParent', cmds.ls(rollJointList[-1], long=1)[0], type='string', lock=1)

        # slave parent attr
        for i in xrange(len(rollJointList) - 1):
            if not cmds.attributeQuery('slaveParent', node=rollJointList[i + 1], exists=1):
                cmds.addAttr(rollJointList[i + 1], ln='slaveParent', dt='string')
                cmds.setAttr(rollJointList[i + 1] + '.slaveParent', cmds.ls(rollJointList[i], long=1)[0], type='string',
                             lock=1)
    else:
        # add and set attr
        if not cmds.attributeQuery('slaveParent', node=rollStart, exists=1):
            cmds.addAttr(rollStart, ln='slaveParent', dt='string')
            cmds.setAttr(rollStart + '.slaveParent', cmds.ls(rollStart_Jnt, long=1)[0], type='string', lock=1)

        for i in xrange(len(rollJointList) - 1):
            if not cmds.attributeQuery('slaveParent', node=rollJointList[i], exists=1):
                cmds.addAttr(rollJointList[i], ln='slaveParent', dt='string')
                cmds.setAttr(rollJointList[i] + '.slaveParent', cmds.ls(rollJointList[i+1], long=1)[0], type='string',
                             lock=1)

    # add attr
    for joint in rollJointList:
        if not cmds.attributeQuery('rigModule', node=joint, exists=1):
            cmds.addAttr(joint, ln='rigModule', at='message')

        if not cmds.attributeQuery('slaveJoint', node=joint, exists=1):
            cmds.addAttr(joint, ln='slaveJoint', at='message')

        if not cmds.attributeQuery('rollJoint', node=joint, exists=1):
            cmds.addAttr(joint, ln='rollJoint', at='bool')
            cmds.setAttr(joint + '.rollJoint', 1, lock=1)

    rigModule = cmds.listConnections(rollStart + '.rigModule', source=1, destination=0, shapes=0)[0]

    if not cmds.attributeQuery('rollJoint', node=rigModule, exists=1):
        cmds.addAttr(rigModule, ln='rollJoint', at='message')

        for joint in rollJointList:
            cmds.connectAttr(rigModule + '.rollJoint', joint + '.rigModule', f=1)

    cmds.select(cl=1)
