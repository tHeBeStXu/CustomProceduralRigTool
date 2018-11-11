import maya.cmds as cmds


def IK_FK_Switch(prefix,
                 switchCtrl,
                 pvCtrl,
                 ikCtrl,
                 skinJoints,
                 fkCtrlList):
    """
    IK_FK seamless switch by scriptJob and scriptNode
    :param prefix: str, prefix of the scriptNode
    :param switchCtrl: str, switchCtrl Name, usually IK_FK_Blend_Ctrl.C
    :param pvCtrl: str, pole vector Ctrl name.
    :param ikCtrl: str, IK Ctrl name
    :param skinJoints: list(str), list of the skin joints[shoulder, elbow, wrist]
    :param fkCtrlList: list(str), list of the FK Ctrl[FK_shoulder, FK_elbow, FK_wrist]
    :return: None
    """
    codeStr = '''
import maya.cmds as cmds

def switch():
    switchCtrl = '{0}'
    pvCtrl = '{1}'
    ikCtrl = '{2}'
    skinJoints = {3}
    fkCtrlList = {4}

    objAttr = switchCtrl + '.Mode'
    objTy = switchCtrl + '.ty'
    # FK 2 IK
    if cmds.getAttr(objAttr) == 0:
        cmds.matchTransform(pvCtrl, skinJoints[1], pos=1, rot=0)
        cmds.matchTransform(ikCtrl, skinJoints[-1], pos=1, rot=1)
        cmds.setAttr(objTy, 1)
    # IK 2 FK
    elif cmds.getAttr(objAttr) == 1:
        for i in xrange(len(skinJoints)):
            cmds.matchTransform(fkCtrlList[i], skinJoints[i], pos=1, rot=1)
        cmds.setAttr(objTy, 0)

cmds.scriptJob(attributeChange=['{5}' + '.Mode', switch])
'''.format(switchCtrl,
           pvCtrl,
           ikCtrl,
           skinJoints,
           fkCtrlList,
           switchCtrl)
    nodeName = cmds.scriptNode(st=2, bs=codeStr.replace("'''", "''"), n=prefix + 'Arm_IKFK_Switch_Node_#', stp='python')
    cmds.scriptNode(nodeName, executeBefore=1)
