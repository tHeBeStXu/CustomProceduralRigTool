"""
module for making rig control
"""

import maya.cmds as cmds
import controlShape
reload(controlShape)


class Control():

    """
    class for building rig control
    """

    def __init__(self,
                 prefix='L_',
                 rigPartName='',
                 scale=1.0,
                 translateTo='',
                 rotateTo='',
                 parent='',
                 shape='circle',
                 axis='x',
                 lockChannels=['s', 'v']):
        """
        create rig control and rig offset group
        :param prefix: str, prefix to name new objects
        :param rigPartName: str, rig part name
        :param scale: float, scale value for size of control shapes
        :param translateTo: str, reference object for control position
        :param rotateTo: str,reference object for control orientation
        :param parent:str, object to be parent of new control
        :param shape: str, control shape type
        :param lockChannels: list(str), list of channels on control to be locked and non-keyable
        """

        circleNormal = [1, 0, 0]
        ctrlObject = None

        if shape in ['circle', 'circleX']:

            circleNormal = [1, 0, 0]

        elif shape == 'circleY':

            circleNormal = [0, 1, 0]

        elif shape == 'circleZ':

            circleNormal = [0, 0, 1]

        elif shape == 'sphere':
            ctrlObject = cmds.circle(n=prefix + rigPartName + '_Ctrl', ch=False, normal=[1, 0, 0], radius=scale)[0]
            addShape = cmds.circle(n=prefix + rigPartName + '_Ctrl2', ch=False, normal=[0, 0, 1], radius=scale)[0]
            cmds.parent(cmds.listRelatives(addShape, s=1), ctrlObject, r=1, s=1)
            cmds.delete(addShape)

        elif shape == 'crossControl':
            ctrlObject = controlShape.CrossControl.createShape(prefix=prefix + rigPartName + '_Ctrl')

        elif shape == 'arrowCurve':
            ctrlObject = controlShape.ArrowCurve.createShape(prefix=prefix + rigPartName + '_Ctrl')

        elif shape == 'crownCurve':
            ctrlObject = controlShape.CrownCurve.createShape(prefix=prefix + rigPartName + '_Ctrl')

        elif shape == 'cubeCurve':
            ctrlObject = controlShape.CubeCurve.createShape(prefix=prefix + rigPartName + '_Ctrl')

        elif shape == 'cubeOnBase':
            ctrlObject = controlShape.cubeOnBase.createShape(prefix=prefix + rigPartName + '_Ctrl')

        elif shape == 'diamond':
            ctrlObject = controlShape.Diamond.createShape(prefix=prefix + rigPartName + '_Ctrl')

        elif shape == 'fistCurve':
            ctrlObject = controlShape.FistCurve.createShape(prefix=prefix + rigPartName + '_Ctrl')

        elif shape == 'footControl':
            ctrlObject = controlShape.FootControl.createShape(prefix=prefix + rigPartName + '_Ctrl')

        elif shape == 'moveControl':
            ctrlObject = controlShape.MoveControl.createShape(prefix=prefix + rigPartName + '_Ctrl')

        elif shape == 'rotationControl':
            ctrlObject = controlShape.RotationControl.createShape(prefix=prefix + rigPartName + '_Ctrl')

        elif shape == 'singleRotateControl':
            ctrlObject = controlShape.singleRotateControl.createShape(prefix=prefix + rigPartName + '_Ctrl')

        elif shape == 'spikeCrossControl':
            ctrlObject = controlShape.SpikeCrossControl.createShape(prefix=prefix + rigPartName + '_Ctrl')

        elif shape == 'unitSliderControl':
            ctrlBox = controlShape.unitSliderControl.createShape(prefix=prefix + rigPartName)
            ctrlObject = cmds.listRelatives(ctrlBox, children=1, parent=0, s=0)
            ctrlObject = ctrlObject[1]

        elif shape == 'squareControl':
            ctrlObject = controlShape.squareControl.createShape(prefix=prefix + rigPartName + '_Ctrl')

        if not ctrlObject:
            ctrlObject = cmds.circle(n=prefix + rigPartName + '_Ctrl', ch=1,
                                     normal=circleNormal, radius=1.0)[0]

        # rotate the ctrlObject
        if shape in ['circle', 'circleX', 'circleY', 'circleZ']:
            pass
        else:
            self.rotate_Ctrl(ctrlObject=ctrlObject, shape=shape, axis=axis)

        # ctrl offset group
        ctrlOffset = cmds.group(n=prefix + rigPartName + '_CtrlGrp', em=1)
        if shape in ['unitSliderControl']:
            cmds.parent(ctrlBox, ctrlOffset)
        else:
            cmds.parent(ctrlObject, ctrlOffset)

        # scale the control grp
        cmds.setAttr(ctrlOffset + '.s', scale, scale, scale)

        # color control
        ctrlShapes = cmds.listRelatives(ctrlObject, s=1)

        [cmds.setAttr(s + '.ove', 1) for s in ctrlShapes]

        if prefix.startswith('L_'):
            [cmds.setAttr(s + '.ovc', 6) for s in ctrlShapes]

        elif prefix.startswith('R_'):
            [cmds.setAttr(s + '.ovc', 13) for s in ctrlShapes]

        else:
            [cmds.setAttr(s + '.ovc', 22) for s in ctrlShapes]

        # translate control

        if cmds.objExists(translateTo):
            cmds.delete(cmds.pointConstraint(translateTo, ctrlOffset, mo=0))

        # rotate control

        if cmds.objExists(rotateTo):
            cmds.delete(cmds.orientConstraint(rotateTo, ctrlOffset, mo=0))

        # parent control

        if cmds.objExists(parent):
            cmds.parent(ctrlOffset, parent)

        # lock control channels

        singleAttributeLockList = []
        for lockChannel in lockChannels:

            if lockChannel in ['t', 'r', 's']:

                for axis in ['x', 'y', 'z']:

                    at = lockChannel + axis
                    singleAttributeLockList.append(at)

            else:
                singleAttributeLockList.append(lockChannel)

        for at in singleAttributeLockList:
            cmds.setAttr(ctrlObject + '.' + at, l=1, k=0)

        # add public members

        self.C = ctrlObject
        self.Off = ctrlOffset

    def rotate_Ctrl(self, ctrlObject, shape, axis='x'):
        """
        not support for sliderControl and unitSliderControl
        :param ctrlObject: INSTANCE.C
        :param shape: control shape
        :param axis: forward axis
        :return: None
        """
        ctrlShape = cmds.listRelatives(ctrlObject, s=1, type='nurbsCurve')

        cls = cmds.cluster(ctrlShape)[1]

        if axis == 'x' and shape in ['crossControl', 'crownCurve', 'fistCurve',
                                     'footControl', 'moveControl', 'spikeCrossControl']:
            cmds.setAttr(cls + '.rz', 90)

        elif axis == 'x' and shape in ['rotationControl', 'singleRotateControl']:
            cmds.setAttr(cls + '.ry', 90)

        elif axis == 'z' and shape in ['arrowCurve', 'crossControl', 'crownCurve', 'cubeOnBase', 'fistCurve',
                                       'footControl', 'moveControl', 'spikeCrossControl']:
            cmds.setAttr(cls + '.rx', 90)

        elif axis == 'y' and shape in ['rotationControl', 'singleRotateControl']:
            cmds.setAttr(cls + '.rx', 90)

        elif axis == 'y' and shape in ['squareControl']:
            cmds.setAttr(cls + '.rz', 90)

        elif axis == 'z' and shape in ['squareControl']:
            cmds.setAttr(cls + '.ry', 90)

        elif axis == 'x' and shape in ['cubeOnBase']:
            cmds.move(0, 0, 0, [cls + '.scalePivot', cls + '.rotatePivot'], rpr=1)
            cmds.setAttr(cls + '.rz', -90)
        elif axis == 'x' and shape in ['arrowCurve']:
            cmds.move(0, 0, 0, [cls + '.scalePivot', cls + '.rotatePivot'], rpr=1)
            cmds.setAttr(cls + '.ry', -90)
            cmds.setAttr(cls + '.rx', -90)
        else:
            pass

        # delete the cluster
        cmds.delete(ctrlShape, ch=1)

        cmds.select(cl=1)
