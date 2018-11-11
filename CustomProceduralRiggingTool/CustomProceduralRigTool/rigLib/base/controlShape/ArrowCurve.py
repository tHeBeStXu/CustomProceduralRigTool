import maya.cmds as cmds
def createShape(prefix='', scale=1.0):
    
    List = []
    List.append(cmds.curve(n=prefix, p=[(-1.0, 0.0, 0.0), (-1.0, 0.0, 2.0), (1.0, 0.0, 2.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.0, 0.0, -2.0), (-2.0, 0.0, 0.0), (-1.0, 0.0, 0.0)],per = False, d=1, k=[0, 1, 2, 3, 4, 5, 6, 7]))
    for x in range(len(List)-1):
        cmds.makeIdentity(List[x+1], apply=True, t=1, r=1, s=1, n=0)
        shapeNode = cmds.ListRelatives(List[x+1], shapes=True)
        cmds.parent(shapeNode, List[0], add=True, s=True)
        cmds.delete(List[x+1])

    sel = List[0]

    cmds.setAttr(sel + '.s', scale, scale, scale)

    cmds.makeIdentity(sel, apply=1, t=1, r=1, s=1, n=0)

    return sel

