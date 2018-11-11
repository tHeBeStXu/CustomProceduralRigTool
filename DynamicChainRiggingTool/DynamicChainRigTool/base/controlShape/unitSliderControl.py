import maya.cmds as cmds


def createShape(prefix='',
                scale=1.0):
    """
    create a unit slider for blend operation
    :param prefix: str, prefix of the control
    :param scale: float, scale of the control
    :return: str, ctrlBox of the unitSliderControl
    """
    Ctrl = cmds.circle(radius=0.2, nr=(1, 0, 0), n=prefix + '_Ctrl')[0]
    cmds.transformLimits(Ctrl, tx=(0, 0), ty=(0, 1), tz=(0, 0), etx=(1, 1), ety=(1, 1), etz=(1, 1))

    CtrlBox = cmds.curve(d=1, p=[(0, 0, 0), (0, 1, 0)], k=[0, 1], n=prefix + '_CtrlBox')
    parentCrvShape = cmds.listRelatives(CtrlBox, s=1)
    cmds.setAttr(parentCrvShape[0] + '.template', 1)

    cmds.parent(Ctrl, CtrlBox)
    cmds.setAttr(CtrlBox + '.s', scale, scale, scale)
    cmds.makeIdentity(CtrlBox, apply=1, t=1, r=1, s=1, n=0)
    cmds.select(cl=1)

    return CtrlBox
