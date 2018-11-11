import maya.cmds as cmds
from ..utils import name
from ..base import control
reload(name)
reload(control)


def createSplineIK(jointList, prefixName, curve=None):
    """
    create Spline IK whether curve is given or not
    :param jointList: list(str), list of joint chain
    :param curve: str, curve name
    :return: list(str), IK_Handle = [ikh, effector, crv]
    """
    if not curve:
        # create IK Spline
        IK_Handle = cmds.ikHandle(n=prefixName + '_ikh', sj=jointList[0],
                                  ee=jointList[-1], sol='ikSplineSolver', scv=0, pcv=0)
        IK_Handle[-1] = cmds.rename(IK_Handle[-1], prefixName + '_Crv_Input')

        # add input curve attr
        if not cmds.attributeQuery('inputCurve', node=IK_Handle[-1], exists=1):
            cmds.addAttr(IK_Handle[-1], longName='inputCurve', at='message')

    else:
        # add jointList to exists curve
        IK_Handle = cmds.ikHandle(n=prefixName + '_ikh', sj=jointList[0], ee=jointList[-1],
                                  sol='ikSplineSolver', c=curve, ccv=0, roc=0, pcv=0, snc=1)
        IK_Handle.append(curve)

    # add IK handle attr
    if not cmds.attributeQuery('IKHandle', node=IK_Handle[0], exists=1):
        cmds.addAttr(IK_Handle[0], longName='IKHandle', at='message')

    cmds.select(cl=1)

    return IK_Handle


def createCtrlSystem(jointList, prefixName, numCtrl, curve, upAxis='y'):
    """
    create FK Joints control system for controlling line shape
    :param jointList: list(str), joint chain list
    :param numCtrl: int, number of controls
    :param curve: str, controled curve
    :param upAxis: str, up Axis, y or z
    :return: dict, {'FK_CtrlGrp_List', 'FK_Ctrl_List'}
    """
    cmds.select(cl=1)

    if upAxis in ['y', 'Y']:
        worldUpVector = (0, 1, 0)
    elif upAxis in ['z', 'Z']:
        worldUpVector = (0, 0, 1)

    eachADD = 1.0 / (len(range(numCtrl)) - 1)

    fkJntList = []

    for i in range(numCtrl):
        fkJnt = cmds.joint(n=prefixName + '_' + str(i) + '_FK')

        cmds.delete(cmds.parentConstraint(jointList[0], fkJnt, mo=0))

        motionPath = cmds.pathAnimation(curve, fkJnt, n=fkJnt + '_motionPath', fractionMode=1, follow=1,
                                        followAxis='x', upAxis='y', worldUpType='Vector',
                                        worldUpVector=worldUpVector, inverseUp=0, inverseFront=0, bank=0)
        cmds.cutKey(motionPath + '.u', time=())
        cmds.setAttr(motionPath + '.uValue', eachADD * float(i))

        for attr in ['t', 'r']:
            for axis in ['x', 'y', 'z']:
                cmds.delete(fkJnt + '.%s%s' % (attr, axis), icn=1)

        cmds.delete(motionPath)

        cmds.select(cl=1)

        fkJntList.append(fkJnt)

    cmds.delete(cmds.parentConstraint(jointList[-1], fkJntList[-1], mo=0))

    fkJntList_rev = []

    for i in fkJntList:
        fkJntList_rev.append(i)

    fkJntList_rev.reverse()

    for i in xrange(len(fkJntList_rev)-1):
        cmds.delete(cmds.aimConstraint(fkJntList_rev[i], fkJntList_rev[i+1], mo=0, weight=1, aimVector=(1, 0, 0),
                                upVector=(0, 1, 0), worldUpType='vector', worldUpVector=worldUpVector))

    cmds.delete(cmds.orientConstraint(jointList[-1], fkJntList_rev[0], mo=0))

    for i in xrange(len(fkJntList_rev)-1):
        cmds.parent(fkJntList_rev[i], fkJntList_rev[i+1])

    for i in fkJntList:
        cmds.setAttr(i + '.drawStyle', 2)

    cmds.makeIdentity(fkJntList[0], apply=1)

    cmds.select(cl=1)

    # FK Ctrls and CtrlGrps

    FK_CtrlGrp_List = []
    FK_Ctrl_List = []

    for i in xrange(len(fkJntList)):
        FK_Ctrl = control.Control(prefix=prefixName,
                                  rigPartName='_' + str(i) + '_FK',
                                  scale=5,
                                  translateTo=fkJntList[i],
                                  rotateTo=fkJntList[i],
                                  shape='circle',
                                  lockChannels=['t', 's', 'v'])

        cmds.pointConstraint(FK_Ctrl.C, fkJntList[i], mo=0)
        cmds.orientConstraint(FK_Ctrl.C, fkJntList[i], mo=0)

        FK_CtrlGrp_List.append(FK_Ctrl.Off)
        FK_Ctrl_List.append(FK_Ctrl.C)

        # add fk control attr
        if not cmds.attributeQuery('FKCtrl', node=FK_Ctrl.C, exists=1):
            cmds.addAttr(FK_Ctrl.C, longName='FKCtrl', at='message')

    cmds.select(cl=1)

    for i in xrange(len(FK_Ctrl_List) - 1):
        cmds.parent(FK_CtrlGrp_List[i+1], FK_Ctrl_List[i])

    cmds.select(cl=1)

    # add fk control group attr
    if not cmds.attributeQuery('FKCtrlGrp', node=FK_CtrlGrp_List[0], exists=1):
        cmds.addAttr(FK_CtrlGrp_List[0], longName='FKCtrlGrp', at='message')

    cmds.select(cl=1)

    return {'FK_CtrlGrp_List': FK_CtrlGrp_List,
            'FK_Ctrl_List': FK_Ctrl_List,
            'fkJntList': fkJntList}


def createFollicle(curveShape, prefixName):
    """
    create a follicle node for curve
    :param curveShape: str, curve shape
    :param prefixName: str, prefix name of the original joint chain
    :return: dict, {'follicle': [follicleTransNode, follicleShape], 'curveOut': [curveTransNodeOut, curveShapeOut]}
    """

    # follicle
    follicleShape = cmds.createNode('follicle', n=prefixName + '_follicleShape')
    follicleTransNode = cmds.listRelatives(follicleShape, p=1, c=0, s=0)[0]
    follicleTransNode = cmds.rename(follicleTransNode, prefixName + '_follicleNode')
    follicleShape = cmds.listRelatives(follicleTransNode, c=1, p=0, s=1)[0]

    curveTransNode = cmds.listRelatives(curveShape, p=1, c=0, s=0)[0]

    cmds.connectAttr(curveTransNode + '.worldMatrix', follicleShape + '.startPositionMatrix', f=1)
    cmds.connectAttr(curveShape + '.local', follicleShape + '.startPosition', f=1)

    # create output curve
    curveShapeOut = cmds.createNode('nurbsCurve', n=prefixName + '_CrvShape_Output')
    curveTransNodeOut = cmds.listRelatives(curveShapeOut, p=1, c=0, s=0)[0]
    curveTransNodeOut = cmds.rename(curveTransNodeOut, prefixName + '_Crv_Output')
    curveShapeOut = cmds.listRelatives(curveTransNodeOut, c=1, p=0, s=1)[0]

    cmds.connectAttr(follicleTransNode + '.outCurve', curveShapeOut + '.create', f=0)

    cmds.select(cl=1)

    # add follicle attr
    if not cmds.attributeQuery('follicle', node=follicleShape, exists=1):
        cmds.addAttr(follicleShape, longName='follicle', at='message')

    # add output curve attr
    if not cmds.attributeQuery('outputCurve', node=curveTransNodeOut, exists=1):
        cmds.addAttr(curveTransNodeOut, longName='outputCurve', at='message')

    cmds.select(cl=1)

    return {'follicleTransNode': follicleTransNode,
            'follicleShape': follicleShape,
            'curveTransNodeOut': curveTransNodeOut,
            'curveShapeOut': curveShapeOut}


def createHairSys(prefixName, nucleus=None):
    """
    create hair system
    :param prefixName: str, prefix_name of the original joint chain
    :param nucleus: str, whether specified nucleus
    :return: dict, {'hair_shape': hairShape, 'hairTransNode': hairTransNode}
    """

    nucleus = nucleus or createNucleus(prefixName=prefixName)
    # hair System
    hairShape = cmds.createNode('hairSystem', n=prefixName + '_hairSysShape')
    hairTransNode = cmds.listRelatives(hairShape, p=1, c=0, s=0)[0]
    hairTransNode = cmds.rename(hairTransNode, prefixName + '_hairSysNode_#')
    hairShape = cmds.listRelatives(hairTransNode, c=1, p=0, s=1)[0]
    cmds.select(cl=1)

    # connectAttr
    cmds.connectAttr('time1.outTime', hairShape + '.currentTime', f=1)
    index = cmds.getAttr(nucleus + '.inputActive', size=1)
    inputActive = '%s.inputActive[%s]' % (nucleus, index)
    inputStart = '%s.inputActiveStart[%s]' % (nucleus, index)
    output_object = '%s.outputObjects[%s]' % (nucleus, index)

    cmds.setAttr(hairShape + '.active', 1)

    cmds.connectAttr(hairShape + '.currentState', inputActive, f=1)
    cmds.connectAttr(hairShape + '.startState', inputStart, f=1)
    cmds.connectAttr(nucleus + '.startFrame', hairShape + '.startFrame', f=1)
    cmds.connectAttr(output_object, hairShape + '.nextState', f=1)

    # add hair attr
    if not cmds.attributeQuery('hair', node=hairShape, exists=1):
        cmds.addAttr(hairShape, longName='hair', at='message', multi=1)

    # add nucleus attr
    if not cmds.attributeQuery('nucleus', node=nucleus, exists=1):
        cmds.addAttr(nucleus, longName='nucleus', at='message', multi=1)

    cmds.select(cl=1)

    return {'hairShape': hairShape,
            'hairTransNode': hairTransNode,
            'nucleus': nucleus}


def createNucleus(prefixName):
    """
    create nucleus
    :param jointList: list(str), joint chain list.
    :return: nucleus
    """

    nucleus = cmds.createNode('nucleus', n=prefixName + '_nucleus_#')
    cmds.connectAttr('time1.outTime', nucleus + '.currentTime', f=1)

    # add nucleus attr
    if not cmds.attributeQuery('nucleus', node=nucleus, exists=1):
        cmds.addAttr(nucleus, longName='nucleus', at='message', multi=1)

    cmds.select(cl=1)

    return nucleus


def addFollicle(follicleShape, hairShape):
    """
    add existed follicle to hair system
    :param str, follicleShape: follicle shape node
    :param str, hairShape: hair system shape node
    :return: None
    """
    # find a available index number for connections
    hairIndex = 0

    while hairIndex < 10000:
        input_hair = '%s.inputHair[%s]' % (hairShape, hairIndex)
        output_hair = '%s.outputHair[%s]' % (hairShape, hairIndex)

        inputAttrs = cmds.listConnections(input_hair, plugs=1)
        outputAttrs = cmds.listConnections(output_hair, plugs=1)

        if not inputAttrs:
            if not outputAttrs:
                cmds.connectAttr(follicleShape + '.outHair', input_hair, f=1)
                cmds.connectAttr(output_hair, follicleShape + '.currentPosition', f=1)
                break
        hairIndex += 1

    cmds.select(cl=1)


def rigInputCrv(fkJointList, curveNode):
    """
    rig input crv with fk jointList
    :param fkJointList: list(str), fk joint control list
    :param curveNode: str, input curve of hair system
    :return: None
    """
    cmds.select(cl=1)
    cmds.skinCluster(fkJointList[:], curveNode, tsb=1)
    cmds.select(cl=1)


def createBakedCtrlSystem(jointList, prefixName):
    """
    create FK controls for FK_Joint chain list
    :param jointList: list(str), FK_Joint chain list
    :return: dict, {'Bake_FK_ctrlGrpList', 'Bake_FK_ctrlList'}
    """
    Bake_FK_ctrlList = []
    Bake_FK_ctrlGrpList = []

    cmds.select(cl=1)

    for i in xrange(len(jointList)-1):
        Bake_FK_Ctrl = control.Control(prefix=prefixName,
                                       rigPartName='_' + str(i) + '_Baked_FK',
                                       scale=7,
                                       translateTo=jointList[i],
                                       rotateTo=jointList[i],
                                       shape='squareControl',
                                       axis='z')

        cmds.pointConstraint(Bake_FK_Ctrl.C, jointList[i], mo=0)
        cmds.orientConstraint(Bake_FK_Ctrl.C, jointList[i], mo=0)

        Bake_FK_ctrlList.append(Bake_FK_Ctrl.C)
        Bake_FK_ctrlGrpList.append(Bake_FK_Ctrl.Off)

        # add bake fk control attr
        if not cmds.attributeQuery('BakeFKCtrl', node=Bake_FK_Ctrl.C, exists=1):
            cmds.addAttr(Bake_FK_Ctrl.C, longName='BakeFKCtrl', at='message')

        cmds.select(cl=1)

    for i in xrange(len(Bake_FK_ctrlList) - 1):
        cmds.parent(Bake_FK_ctrlGrpList[i+1], Bake_FK_ctrlList[i])

    cmds.select(cl=1)

    # add bake fk control group attr
    if not cmds.attributeQuery('BakeFKCtrlGrp', node=Bake_FK_ctrlGrpList[0], exists=1):
        cmds.addAttr(Bake_FK_ctrlGrpList[0], longName='BakeFKCtrlGrp', at='message')

    cmds.select(cl=1)

    return {'Bake_FK_ctrlGrpList': Bake_FK_ctrlGrpList, 'Bake_FK_ctrlList': Bake_FK_ctrlList}


def bakeDynamic2Ctrls(jointList, Bake_FK_ctrlList):
    """
    bake dynamic to the Baked_FK_controls
    :param jointList: list(str), joint chain list with dynamic
    :param Bake_FK_ctrlList: list(str)
    :return: None
    """
    animMinTime = cmds.playbackOptions(min=1, q=1)
    animMaxTime = cmds.playbackOptions(max=1, q=1)

    for i in xrange(int(animMaxTime-animMinTime) + 1):
        cmds.currentTime(animMinTime + i)

        for j in xrange(len(jointList) - 1):
            cmds.matchTransform(Bake_FK_ctrlList[j], jointList[j], pos=1, rot=1)
            for at in ['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ']:
                cmds.setKeyframe(Bake_FK_ctrlList[j], at=at, time=cmds.currentTime(q=1))

        print 'current time is: ' + str(animMinTime + i)

    cmds.select(cl=1)


def createIK_BakeJointChain(jointList):
    """
    create baked joint chain list
    :param jointList: list(str), original joint chain list
    :return:list(str), baked joint chain list
    """
    prefixName = name.removeSuffix(jointList[0])

    IKJointList = []
    bakeJointList = []
    for i in xrange(len(jointList)):
        # bake joint
        cmds.select(cl=1)
        bakedJnt = cmds.joint(n=prefixName + '_' + str(i) + '_Bake')
        cmds.delete(cmds.parentConstraint(jointList[i], bakedJnt, mo=0))
        bakeJointList.append(bakedJnt)
        if not cmds.attributeQuery('bakeJoint', node=bakedJnt, exists=1):
            cmds.addAttr(bakedJnt, longName='bakeJoint', at='message')
        cmds.select(cl=1)

        # ik joint
        IKJnt = cmds.joint(n=prefixName + '_' + str(i) + '_IK')
        cmds.delete(cmds.parentConstraint(jointList[i], IKJnt, mo=0))
        IKJointList.append(IKJnt)
        if not cmds.attributeQuery('IKJoint', node=IKJnt, exists=1):
            cmds.addAttr(IKJnt, longName='IKJoint', at='message')
        cmds.select(cl=1)

    for i in xrange(len(bakeJointList) - 1):

        cmds.parent(bakeJointList[i+1], bakeJointList[i])
        cmds.parent(IKJointList[i+1], IKJointList[i])

    cmds.makeIdentity(bakeJointList[0], apply=1)
    cmds.makeIdentity(IKJointList[0], apply=1)

    if cmds.listRelatives(jointList[0], p=1, c=0, s=0, type='joint'):
        cmds.parent(bakeJointList[0], cmds.listRelatives(jointList[0], p=1, c=0, s=0, type='joint')[0])
        cmds.parent(IKJointList[0], cmds.listRelatives(jointList[0], p=1, c=0, s=0, type='joint')[0])

    cmds.select(cl=1)

    return {'bakeJointList': bakeJointList,
            'IKJointList': IKJointList}


def createSettingGrp(prefixName):
    """
    create setting group for connections
    :param prefixName: str, prefix_name of the joint chain
    :return: str, setting group
    """
    settingGrp = cmds.group(n=prefixName + '_settingGrp', em=1)

    # set visibility to false
    cmds.setAttr(settingGrp + '.v', 0)

    for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v']:
        cmds.setAttr(settingGrp + '.' + attr, keyable=0, lock=1, channelBox=0)

    if not cmds.attributeQuery('IK2Bake', node=settingGrp, exists=1):
        cmds.addAttr(settingGrp, longName='IK2Bake', at="float", min=0, max=1, keyable=1)

    if not cmds.attributeQuery('hair', node=settingGrp, exists=1):
        cmds.addAttr(settingGrp, longName='hair', at='message')

    if not cmds.attributeQuery('follicle', node=settingGrp, exists=1):
        cmds.addAttr(settingGrp, longName='follicle', at='message')

    if not cmds.attributeQuery('nucleus', node=settingGrp, exists=1):
        cmds.addAttr(settingGrp, longName='nucleus', at='message')

    if not cmds.attributeQuery('inputCurve', node=settingGrp, exists=1):
        cmds.addAttr(settingGrp, longName='inputCurve', at='message')

    if not cmds.attributeQuery('outputCurve', node=settingGrp, exists=1):
        cmds.addAttr(settingGrp, longName='outputCurve', at='message')

    if not cmds.attributeQuery('FKCtrl', node=settingGrp, exists=1):
        cmds.addAttr(settingGrp, longName='FKCtrl', at='message')

    if not cmds.attributeQuery('FKCtrlGrp', node=settingGrp, exists=1):
        cmds.addAttr(settingGrp, longName='FKCtrlGrp', at='message')

    if not cmds.attributeQuery('IKHandle', node=settingGrp, exists=1):
        cmds.addAttr(settingGrp, longName='IKHandle', at='message')

    if not cmds.attributeQuery('BakeFKCtrl', node=settingGrp, exists=1):
        cmds.addAttr(settingGrp, longName='BakeFKCtrl', at='message')

    if not cmds.attributeQuery('BakeFKCtrlGrp', node=settingGrp, exists=1):
        cmds.addAttr(settingGrp, longName='BakeFKCtrlGrp', at='message')

    if not cmds.attributeQuery('IKJoint', node=settingGrp, exists=1):
        cmds.addAttr(settingGrp, longName='IKJoint', at='message')

    if not cmds.attributeQuery('bakeJoint', node=settingGrp, exists=1):
        cmds.addAttr(settingGrp, longName='bakeJoint', at='message')

    if not cmds.attributeQuery('originJoint', node=settingGrp, exists=1):
        cmds.addAttr(settingGrp, longName='originJoint', at='message')

    cmds.select(cl=1)

    return settingGrp


def connectAttr(setGrp, hair, follicle, nucleus, inputCrv, outputCrv, IK_Handle, FK_CtrlList,
                FK_CtrlGrp, Bake_FK_CtrlList, Bake_FK_CtrlGrp, IKJointList, bakeJointList, originJointList):
    """
    connect the specified attrs between setting group and the other objects
    :param setGrp: str, setting group
    :param hair: str, hair system shape
    :param follicle: str, follicle shape
    :param nucleus: str, nucleus
    :param inputCrv: str, input curve trans node
    :param outputCrv: str, output curve trans node
    :param IK_Handle: str, IK_handle of the spline IK system
    :param FK_CtrlList: list(str), FK control list
    :param FK_CtrlGrp: str, first FK control GRP of FK control group list
    :param Bake_FK_CtrlList: list(str), bake FK control list
    :param Bake_FK_CtrlGrp: str, first bake FK control GRP of bake FK control group list
    :param bakeJointList: list(str), bake_joint_list
    :param originJointList: list(str), origin_joint_list
    :return: None
    """
    # connect attrs
    hairIndex = cmds.getAttr(hair + '.hair', size=1)
    hairAttr = '%s.hair[%s]' % (hair, hairIndex)
    cmds.connectAttr(setGrp + '.hair', hairAttr, f=1)

    cmds.connectAttr(setGrp + '.follicle', follicle + '.follicle', f=1)

    nucleusIndex = cmds.getAttr(nucleus + '.nucleus', size=1)
    nucleusAttr = '%s.nucleus[%s]' % (nucleus, nucleusIndex)
    cmds.connectAttr(setGrp + '.nucleus', nucleusAttr, f=1)

    cmds.connectAttr(setGrp + '.inputCurve', inputCrv + '.inputCurve', f=1)
    cmds.connectAttr(setGrp + '.outputCurve', outputCrv + '.outputCurve', f=1)
    cmds.connectAttr(setGrp + '.IKHandle', IK_Handle + '.IKHandle', f=1)
    cmds.connectAttr(setGrp + '.FKCtrlGrp', FK_CtrlGrp + '.FKCtrlGrp', f=1)
    cmds.connectAttr(setGrp + '.BakeFKCtrlGrp', Bake_FK_CtrlGrp + '.BakeFKCtrlGrp', f=1)

    for i in FK_CtrlList:
        cmds.connectAttr(setGrp + '.FKCtrl', i + '.FKCtrl', f=1)

    for i in Bake_FK_CtrlList:
        cmds.connectAttr(setGrp + '.BakeFKCtrl', i + '.BakeFKCtrl', f=1)

    for i in bakeJointList:
        cmds.connectAttr(setGrp + '.bakeJoint', i + '.bakeJoint', f=1)

    for i in IKJointList:
        cmds.connectAttr(setGrp + '.IKJoint', i + '.IKJoint', f=1)

    for i in originJointList:
        cmds.connectAttr(setGrp + '.originJoint', i + '.originJoint', f=1)

    cmds.select(cl=1)


def createSwitchSystem(originJointList, IKJointList, bakeJointList, settingGrp):
    """
    create switch system between IKJointList and bakeJointList
    :param originJointList: list(str), original joint list
    :param IKJointList: list(str), IK joint list
    :param bakeJointList: list(str), bake joint list
    :param settingGrp: dynamic joint chain setting group
    :return: None
    """
    for i in xrange(len(originJointList)):

        # rotation
        rotBlendColor = cmds.createNode('blendColors')
        # bake
        cmds.connectAttr(bakeJointList[i] + '.r', rotBlendColor + '.color1', f=1)
        # ik
        cmds.connectAttr(IKJointList[i] + '.r', rotBlendColor + '.color2', f=1)
        # setting group
        cmds.connectAttr(settingGrp + '.IK2Bake', rotBlendColor + '.blender', f=1)
        # origin
        cmds.connectAttr(rotBlendColor + '.output', originJointList[i] + '.r', f=1)

    cmds.select(cl=1)


def addAttr2OriginJoints(originJoints):
    """
    add 'originJoint' attr to originJointList
    :param originJoints: origin joint list
    :return: None
    """
    for i in xrange(len(originJoints)):
        if not cmds.attributeQuery('originJoint', node=originJoints[i], exists=1):
            cmds.addAttr(originJoints[i], longName='originJoint', at='message')


def findSettingGrp():
    """
    find and return setting group for selection
    :return: list(str), setting groups
    """
    transformNodes = cmds.ls(type='transform')

    settingGrps = []
    for i in transformNodes:
        if cmds.attributeQuery('IK2Bake', node=i, exists=1):
            settingGrps.append(i)

    return settingGrps


def findSingleAvailableIndex(attr):
    """
    find the first free array index of multi-attribute
    :param attr: str, attribute without index
    :return: int, index of free array.
    """
    index = 0

    while index < 10000:
        fullAttr = attr + '[%s]' % (str(index))

        inputAttr = cmds.listConnections(fullAttr, plugs=1)

        if not inputAttr:
            return index

        index += 1


def findTribleAvailableIndex(firstAttr, secondAttr, thirdAttr):
    """
    find the common free array index of 3 multi-attributes.
    :param firstAttr: str, first attribute without index.
    :param secondAttr:str, second attribute without index.
    :param thirdAttr:str, third attribute without index.
    :return:int, index of free array.
    """
    index = 0

    while index < 10000:
        firstFullAttr = firstAttr + '[%s]' % (str(index))
        secondFullAttr = secondAttr + '[%s]' % (str(index))
        thirdFullAttr = thirdAttr + '[%s]' % (str(index))

        firstInputAttr = cmds.listConnections(firstFullAttr, plugs=1)
        secondInputAttr = cmds.listConnections(secondFullAttr, plugs=1)
        thirdInputAttr = cmds.listConnections(thirdFullAttr, plugs=1)

        if not firstInputAttr:
            if not secondInputAttr:
                if not thirdInputAttr:
                    return index

        index += 1
