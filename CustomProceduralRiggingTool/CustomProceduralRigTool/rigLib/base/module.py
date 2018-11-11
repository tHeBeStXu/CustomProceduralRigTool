"""
module for making top rig structure and rig module
"""

import maya.cmds as cmds
import control
reload(control)

sceneObjectType = 'rig'


class Base():
    """
    class for building top rig structure
    """

    @classmethod
    def addAttr(cls, group):
        if group:
            if not cmds.attributeQuery('MasterCtrl', node=group, exists=1):
                cmds.addAttr(group, ln='MasterCtrl', at='message')

            if not cmds.attributeQuery('MoveCtrl', node=group, exists=1):
                cmds.addAttr(group, ln='MoveCtrl', at='message')

            if not cmds.attributeQuery('rigModule', node=group, exists=1):
                cmds.addAttr(group, ln='rigModule', at='message')

    def __init__(self,
                 characterName='new',
                 scale=1.0,
                 mainCtrlAttachObj=''
                 ):
        """
        :param characterName: str, character name
        :param scale: float, general scale of the rig
        :return None
        """

        self.topGrp = cmds.group(n=characterName, em=1)

        characterNameAttr = 'characterName'
        sceneObjectTypeAttr = 'sceneObjectType'

        for attr in [characterNameAttr, sceneObjectTypeAttr]:

            cmds.addAttr(self.topGrp, ln=attr, dt='string')

        cmds.setAttr(self.topGrp + '.' + characterNameAttr,
                     characterName, type='string', l=1)
        cmds.setAttr(self.topGrp + '.' + sceneObjectTypeAttr,
                     sceneObjectType, type='string', l=1)

        # make global control

        self.Master_Ctrl = control.Control(prefix='C_',
                                           rigPartName='Master',
                                           shape='crownCurve',
                                           scale=scale * 10.0,
                                           parent=self.topGrp,
                                           axis='z',
                                           lockChannels=['v'])

        if not cmds.attributeQuery('MasterCtrl', node=self.Master_Ctrl.C, exists=1):
            cmds.addAttr(self.Master_Ctrl.C, ln='MasterCtrl', at='message')

        self.Move_Ctrl = control.Control(prefix='C_',
                                         rigPartName='Move',
                                         shape='moveControl',
                                         scale=scale * 15.0,
                                         parent=self.Master_Ctrl.C,
                                         axis='z',
                                         lockChannels=['s', 'v'])

        if not cmds.attributeQuery('MoveCtrl', node=self.Move_Ctrl.C, exists=1):
            cmds.addAttr(self.Move_Ctrl.C, ln='MoveCtrl', at='message')

        # add Attr
        if not cmds.attributeQuery('slaveJoint', node=self.Move_Ctrl.C, exists=1):
            cmds.addAttr(self.Move_Ctrl.C, ln='slaveJoint', at='message')

        if not cmds.attributeQuery('rootJoint', node=self.Move_Ctrl.C, exists=1):
            cmds.addAttr(self.Move_Ctrl.C, ln='rootJoint', at='message')

        for axis in ['y', 'z']:

            cmds.connectAttr(self.Master_Ctrl.C + '.sx', self.Master_Ctrl.C + '.s' + axis)
            cmds.setAttr(self.Master_Ctrl.C + '.s' + axis, k=0)

        cmds.aliasAttr('Global_Scale', self.Master_Ctrl.C + '.sx')

        # create a grp for objects are not influenced by rig moving
        self.dontTouchGrp = cmds.group(n='Dont_Touch_Grp', em=1, p=self.topGrp)
        # lock the inherits Transform attr
        cmds.setAttr(self.dontTouchGrp + '.it', 0, l=1)

        cmds.select(cl=1)

        # create setting group for further operation
        self.settingGrp = cmds.group(n=characterName + '_SettingGrp', em=1, p=self.dontTouchGrp)

        # add attrs to setting group
        Base.addAttr(group=self.settingGrp)

        # connect attr
        cmds.connectAttr(self.settingGrp + '.MasterCtrl',
                         self.Master_Ctrl.C + '.MasterCtrl', f=1)

        cmds.connectAttr(self.settingGrp + '.MoveCtrl',
                         self.Move_Ctrl.C + '.MoveCtrl', f=1)


class Module():

    """class for building module rig structure"""

    @classmethod
    def addAttr(cls, group):
        # query and add attribute
        if group:
            if not cmds.attributeQuery('slaveJoint', node=group, exists=1):
                cmds.addAttr(group, longName='slaveJoint', at='message')

            if not cmds.attributeQuery('settingGrp', node=group, exists=1):
                cmds.addAttr(group, longName='settingGrp', at='message')

    def __init__(self,
                 prefix='L_',
                 rigPartName='',
                 baseObject=None
                 ):

        """
        :param prefix:str, prefix to name new objects
        :param baseObject:instance of base.module.Base() class
        :return None
        """
        self.topGrp = cmds.group(n=prefix + rigPartName + '_Module_Grp', em=1)

        self.dontTouchGrp = cmds.group(n=prefix + rigPartName + '_Dont_Touch_Grp',
                                       em=1, p=self.topGrp)

        cmds.hide(self.dontTouchGrp)

        cmds.setAttr(self.dontTouchGrp + '.it', 0, l=1)

        Module.addAttr(group=self.topGrp)

        if not cmds.attributeQuery(prefix + rigPartName + '_Jnt', node=self.topGrp, exists=1):
            cmds.addAttr(self.topGrp, longName=prefix + rigPartName + '_Jnt', at='message')

        # parent module

        if baseObject:

            cmds.parent(self.topGrp, baseObject.Master_Ctrl.C)

        cmds.select(cl=1)
