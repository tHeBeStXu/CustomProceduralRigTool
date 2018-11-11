import maya.cmds as cmds


def build(inputJoints=None):
    """
    create Slave joints for given joints list.
    if inputJoints = None, create slave joints for all joints in the scene without end joint in the joint chain
    :param inputJoints: str list, target joints list for create Slave joints
    :return: None
    """

    if inputJoints:
        targetJoints = inputJoints
    else:
        targetJoints = []

        # list all selected inputJoints without end inputJoints
        allJoints = cmds.ls(type='joint')
        for joint in allJoints:
            if cmds.attributeQuery('slaveJoint', node=joint, exists=1):
                targetJoints.append(joint)

    cmds.select(cl=1)

    # 1. generate slave joint for each target joint

    if targetJoints:
        for joint in targetJoints:
            slaveJoint = cmds.joint(n='Slave_' + joint)
            cmds.select(cl=1)

            cmds.delete(cmds.parentConstraint(joint, slaveJoint, mo=0))
            cmds.makeIdentity(slaveJoint, apply=1, t=1, r=1, s=1)

            if not cmds.attributeQuery('slaveJoint', node=slaveJoint, exists=1):
                cmds.addAttr(slaveJoint, ln='slaveJoint', at='message')

                cmds.connectAttr(joint + '.slaveJoint', slaveJoint + '.slaveJoint', f=1)

    cmds.select(cl=1)

    # 2. parenting

    if targetJoints:
        for joint in targetJoints:
            slaveJoint = cmds.listConnections(joint + '.slaveJoint', destination=1, source=0, type='joint')[0]

            if cmds.attributeQuery('slaveParent', node=joint, exists=1):
                parent = cmds.getAttr(joint + '.slaveParent')

                if cmds.attributeQuery('slaveJoint', node=parent, exists=1):
                    parentSlave = cmds.listConnections(parent + '.slaveJoint', source=0, destination=1, type='joint')[0]

                    if parentSlave:
                        cmds.parent(slaveJoint, parentSlave)

            else:
                parent = cmds.listRelatives(joint, c=0, p=1, s=0, type='joint', path=1)
                if parent:
                    if cmds.attributeQuery('slaveJoint', node=parent[0], exists=1):
                        parentSlave = cmds.listConnections(parent[0] + '.slaveJoint',
                                                           source=0, destination=1, type='joint')

                        if parentSlave:
                            cmds.parent(slaveJoint, parentSlave[0])

    cmds.select(cl=1)

    # 3. Constraint slave joint

    if targetJoints:
        for joint in targetJoints:
            slaveJoint = cmds.listConnections(joint + '.slaveJoint', destination=1, source=0, type='joint')[0]

            if cmds.attributeQuery('slavePointConst', node=joint, exists=1):
                pointConst = cmds.getAttr(joint + '.slavePointConst')

                if pointConst:
                    cmds.pointConstraint(pointConst, slaveJoint, mo=0)
            else:
                cmds.pointConstraint(joint, slaveJoint, mo=0)

            cmds.orientConstraint(joint, slaveJoint, mo=0)
            cmds.scaleConstraint(joint, slaveJoint, mo=0)

    cmds.select(cl=1)

