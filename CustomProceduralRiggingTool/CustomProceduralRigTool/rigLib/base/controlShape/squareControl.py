import maya.cmds as cmds

def createShape(prefix='',
                scale=1.0):
    curve = cmds.curve(n=prefix, d=1, p=[(0, -0.5, 0.5), (0, -0.5, -0.5), (0, 0.5, -0.5), (0, 0.5, 0.5), (0, -0.5, 0.5)],
                       k=[0, 1, 2, 3, 4])
    cmds.setAttr(curve + '.s', scale, scale, scale)
    cmds.select(cl=1)

    return curve
