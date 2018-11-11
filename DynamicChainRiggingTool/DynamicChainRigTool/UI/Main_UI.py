from PySide2 import QtCore, QtWidgets, QtGui
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui
import maya.cmds as cmds
import logging
import inspect
from ..rigLib import rig
from functools import partial
from ..rigLib import lib
reload(lib)
reload(rig)


logging.basicConfig()
logger = logging.getLogger('DynamicChainRigTool')
logger.setLevel(logging.DEBUG)


def getMayaWindow():
    """
    get the mayaMainWindow as parent
    :return: mayaMainWindow Ptr
    """
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(ptr), QtWidgets.QMainWindow)


class MainUI(QtWidgets.QDialog):
    def __init__(self):
        """
        Initialize and show the main window.
        """
        try:
            cmds.deleteUI('DynamicChainRigTool')
        except:
            logger.info('No previous UI exists!')

        super(MainUI, self).__init__(parent=getMayaWindow())

        self.setModal(False)
        self.setObjectName('DynamicChainRigTool')
        self.setWindowTitle('Dynamic Chain Rigging Tool')

        self.buildUI()
        self.setGrps = []
        self.currentSetGrp = None
        self.show()
        self.refreshListWidget()

    def refreshListWidget(self):
        """
        refresh listWidget with specified checked
        :return: None
        """
        self.listWidget.clear()

        joints = []
        hairs = []
        nucleus = []

        if self.jointCheck.isChecked():
            joints = cmds.ls(type='joint')

        if self.hairCheck.isChecked():
            hairs = cmds.ls(type='hairSystem')

        if self.nucleusCheck.isChecked():
            nucleus = cmds.ls(type='nucleus')

        returnList = joints + hairs + nucleus

        if returnList:
            if len(returnList) > 1:
                self.listWidget.addItems(returnList)
            else:
                self.listWidget.addItem(returnList[0])

    def buildUI(self):
        """
        Build the main UI
        :return: None
        """
        self.setFixedSize(380, 480)

        self.mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.mainLayout)

        self.mainWidget = QtWidgets.QTabWidget()

        self.mainLayout.addWidget(self.mainWidget)

        self.firstWidget = QtWidgets.QWidget()
        self.secondWidget = QtWidgets.QWidget()

        # add widget to TabWidget
        self.mainWidget.addTab(self.firstWidget, 'Create')
        self.mainWidget.addTab(self.secondWidget, 'Bake')

        self.mainWidget.currentChanged.connect(self.populateSettingGrp)

        #########################
        # build 'Create' widget #
        #########################
        self.firstLayout = QtWidgets.QVBoxLayout()
        self.firstWidget.setLayout(self.firstLayout)

        formWidget = QtWidgets.QWidget()
        formlayout = QtWidgets.QFormLayout()
        formWidget.setLayout(formlayout)

        self.rowItem = {}
        self.tupe = inspect.getargspec(func=rig.build)
        for i in self.tupe[0]:
            layout = QtWidgets.QHBoxLayout()
            self.rowItem[i] = QtWidgets.QLineEdit()
            button = QtWidgets.QPushButton('<<<')

            layout.addWidget(self.rowItem[i])
            layout.addWidget(button)

            button.clicked.connect(partial(self.setEditLine, self.rowItem[i]))

            formlayout.addRow(i, layout)

        self.firstLayout.addWidget(formWidget)

        # selection splitter
        self.listSplitter = Splitter()
        self.firstLayout.addWidget(self.listSplitter)

        # selection widget
        selectionWidget = QtWidgets.QWidget()
        selectionLayout = QtWidgets.QVBoxLayout()
        selectionWidget.setLayout(selectionLayout)

        filterWidget = QtWidgets.QWidget()
        filterLayout = QtWidgets.QHBoxLayout()
        filterWidget.setLayout(filterLayout)

        filterLable = QtWidgets.QLabel('Filter:    ')
        self.jointCheck = QtWidgets.QCheckBox('Joint')
        self.hairCheck = QtWidgets.QCheckBox('Hair')
        self.nucleusCheck = QtWidgets.QCheckBox('Nucleus')

        filterLayout.addWidget(filterLable)
        filterLayout.addWidget(self.jointCheck)
        filterLayout.addWidget(self.hairCheck)
        filterLayout.addWidget(self.nucleusCheck)

        self.jointCheck.stateChanged.connect(self.refreshListWidget)
        self.hairCheck.stateChanged.connect(self.refreshListWidget)
        self.nucleusCheck.stateChanged.connect(self.refreshListWidget)

        self.firstLayout.addWidget(selectionWidget)

        self.listWidget = QtWidgets.QListWidget()
        self.listWidget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        selectionLayout.addWidget(filterWidget)
        selectionLayout.addWidget(self.listWidget)

        # create rig splitter
        self.createRigSplitter = Splitter()
        self.firstLayout.addWidget(self.createRigSplitter)

        # create rig button
        self.createRigButton = QtWidgets.QPushButton('Create Dynamic Chain Rig!')
        self.createRigButton.clicked.connect(self.buildRig)
        self.firstLayout.addWidget(self.createRigButton)

        #######################
        # build 'Bake' widget #
        #######################
        self.secondLayout = QtWidgets.QVBoxLayout()
        self.secondWidget.setLayout(self.secondLayout)

        # setting group splitter
        self.settingSplitter = Splitter(text='SETTING GROUPS')
        self.secondLayout.addWidget(self.settingSplitter)

        # setting group comboBox
        self.setGrpComboBox = QtWidgets.QComboBox()
        self.setGrpComboBox.currentIndexChanged.connect(self.setCurrentSetGrp)
        self.secondLayout.addWidget(self.setGrpComboBox)

        # selection splitter
        self.selSplitter = Splitter(text='SELECTION')
        self.secondLayout.addWidget(self.selSplitter)

        # seleciton buttons
        self.selGridLayout = QtWidgets.QGridLayout()

        self.selHairBtn = QtWidgets.QPushButton('Select Hair System')
        self.selNucleusBtn = QtWidgets.QPushButton('Select Nucleus')
        self.selBakeCtrlBtn = QtWidgets.QPushButton('Select Bake Ctrls')
        self.selIKCtrlBtn = QtWidgets.QPushButton('Select IK Ctrls')
        self.selBakeJntBtn = QtWidgets.QPushButton('Select Bake Joints')
        self.selIKJntBtn = QtWidgets.QPushButton('Select IK Joints')
        self.selDynCrvBtn = QtWidgets.QPushButton('Select Dynamic Curve')
        self.selIKCrvBtn = QtWidgets.QPushButton('Select IK Curve')
        self.selOriginJntBtn = QtWidgets.QPushButton('Select Origin Joints')
        self.selFollicleBtn = QtWidgets.QPushButton('Select Follicle')
        self.selSetGrpBtn = QtWidgets.QPushButton('Select Setting Group')

        self.selGridLayout.addWidget(self.selHairBtn, 0, 0, 1, 2)
        self.selGridLayout.addWidget(self.selNucleusBtn, 0, 2, 1, 2)
        self.selGridLayout.addWidget(self.selBakeCtrlBtn, 1, 0, 1, 2)
        self.selGridLayout.addWidget(self.selIKCtrlBtn, 1, 2, 1, 2)
        self.selGridLayout.addWidget(self.selBakeJntBtn, 2, 0, 1, 2)
        self.selGridLayout.addWidget(self.selIKJntBtn, 2, 2, 1, 2)
        self.selGridLayout.addWidget(self.selDynCrvBtn, 3, 0, 1, 2)
        self.selGridLayout.addWidget(self.selIKCrvBtn, 3, 2, 1, 2)
        self.selGridLayout.addWidget(self.selOriginJntBtn, 4, 0, 1, 2)
        self.selGridLayout.addWidget(self.selFollicleBtn, 4, 2, 1, 2)
        self.selGridLayout.addWidget(self.selSetGrpBtn, 5, 1, 1, 2)

        self.selHairBtn.clicked.connect(partial(self.selectSpecifiedItem, 'hair'))
        self.selNucleusBtn.clicked.connect(partial(self.selectSpecifiedItem, 'nucleus'))
        self.selBakeCtrlBtn.clicked.connect(partial(self.selectSpecifiedItem, 'BakeFKCtrl'))
        self.selIKCtrlBtn.clicked.connect(partial(self.selectSpecifiedItem, 'FKCtrl'))
        self.selBakeJntBtn.clicked.connect(partial(self.selectSpecifiedItem, 'bakeJoint'))
        self.selIKJntBtn.clicked.connect(partial(self.selectSpecifiedItem, 'IKJoint'))
        self.selDynCrvBtn.clicked.connect(partial(self.selectSpecifiedItem, 'inputCurve'))
        self.selIKCrvBtn.clicked.connect(partial(self.selectSpecifiedItem, 'outputCurve'))
        self.selOriginJntBtn.clicked.connect(partial(self.selectSpecifiedItem, 'originJoint'))
        self.selFollicleBtn.clicked.connect(partial(self.selectSpecifiedItem, 'follicle'))
        self.selSetGrpBtn.clicked.connect(self.selectCurrentSetGrp)

        self.secondLayout.addLayout(self.selGridLayout)

        # bake splitter
        self.bakeSplitter = Splitter(text='BAKE')
        self.secondLayout.addWidget(self.bakeSplitter)

        # bake button
        self.bakeBtnLayout = QtWidgets.QHBoxLayout()
        self.bakeDynamicBtn = QtWidgets.QPushButton('Bake Dynamic on Bake Ctrls')
        self.bakeBtnLayout.addWidget(self.bakeDynamicBtn)
        self.bakeDynamicBtn.clicked.connect(self.bakeDynamic2Ctrls)

        self.secondLayout.addLayout(self.bakeBtnLayout)

        # replace splitter
        self.replaceSplitter = Splitter(text='REPLACE')
        self.secondLayout.addWidget(self.replaceSplitter)

        # replace layout
        self.replaceLayout = QtWidgets.QGridLayout()

        self.repHairComBox = QtWidgets.QComboBox()
        self.repHairBtn = QtWidgets.QPushButton('Replace')
        self.repHairBtn.clicked.connect(self.replaceHairSystem)
        self.repNecleusComBox = QtWidgets.QComboBox()
        self.repNecleusBtn = QtWidgets.QPushButton('Replace')
        self.repNecleusBtn.clicked.connect(self.replaceNucleus)

        self.replaceLayout.addWidget(self.repHairComBox, 0, 0, 1, 2)
        self.replaceLayout.addWidget(self.repHairBtn, 0, 2, 1, 1)
        self.replaceLayout.addWidget(self.repNecleusComBox, 1, 0, 1, 2)
        self.replaceLayout.addWidget(self.repNecleusBtn, 1, 2, 1, 1)

        self.secondLayout.addLayout(self.replaceLayout)

        # to be continued... splitter
        self.toBeContinuedSplitter = Splitter(text='TO BE CONTINUED...')
        self.secondLayout.addWidget(self.toBeContinuedSplitter)

    def setEditLine(self, editLine):
        """
        Set specified edit line for parameter
        :param editLine: dict, editLine
        :return: None
        """
        items = self.listWidget.selectedItems()

        itemStr = []
        for i in items:
            itemStr.append(self.listWidget.item(self.listWidget.row(i)).text())

        if itemStr:
            if len(itemStr) < 2:
                editLine.setText(itemStr[0])
            else:
                editLine.setText(str(itemStr))

    def buildRig(self):
        """
        Build dynamic chain rig
        :return: None
        """

        jointList = eval(self.rowItem['jointList'].text())
        numCtrl = eval(self.rowItem['numCtrl'].text())
        hairSystem = self.rowItem['hairSystem'].text()
        nucleus = self.rowItem['nucleus'].text()

        rig.build(jointList=jointList,
                  numCtrl=numCtrl,
                  hairSystem=hairSystem,
                  nucleus=nucleus)

    def populateSettingGrp(self):
        """
        Refresh setting group combo box.
        :return: None
        """
        self.setGrpComboBox.clear()
        self.setGrps = lib.findSettingGrp()
        self.setGrpComboBox.addItems(self.setGrps)

    def setCurrentSetGrp(self):
        """
        Set current setting group
        :return: None
        """
        self.currentSetGrp = self.setGrpComboBox.currentText()

        # hair
        self.repHairComBox.clear()

        hairSystemList = cmds.ls(type='hairSystem')
        connectedHair = cmds.listConnections(self.currentSetGrp + '.hair', source=0, destination=1,
                                             type='hairSystem', shapes=1)

        self.repHairComBox.addItems(connectedHair)

        for i in hairSystemList:
            if i not in connectedHair:
                self.repHairComBox.addItem(i)

        # add item new
        self.repHairComBox.addItem('New...')

        # necleus
        self.repNecleusComBox.clear()

        nucleusList = cmds.ls(type='nucleus')
        connectedNucleus = cmds.listConnections(self.currentSetGrp + '.nucleus', source=0, destination=1,
                                                type='nucleus')

        self.repNecleusComBox.addItems(connectedNucleus)

        for i in nucleusList:
            if i not in connectedNucleus:
                self.repNecleusComBox.addItem(i)

        # add item new
        self.repNecleusComBox.addItem('New...')

    def selectSpecifiedItem(self, item):
        """
        Select specified item
        :param item: str, specified item
        :return: None
        """
        if item not in ['hair', 'nucleus', 'follicle', 'inputCurve', 'outputCurve',
                        'FKCtrl', 'BakeFKCtrl', 'IKJoint', 'bakeJoint', 'originJoint']:
            cmds.warning('Unknown item, please check again!')

        if item in ['hair', 'follicle']:
            listConnection = cmds.listConnections(self.currentSetGrp + '.' + item, source=0, destination=1, shapes=1)
        else:
            listConnection = cmds.listConnections(self.currentSetGrp + '.' + item, source=0, destination=1)

        if listConnection:
            if len(listConnection) > 2:
                listConnection.sort()
                cmds.select(cl=1)
                for i in listConnection:
                    cmds.select(i, add=1)

            else:
                cmds.select(listConnection[0])

    def bakeDynamic2Ctrls(self):
        """
        Bake dynamic to the Baked_FK_controls
        :return: None
        """
        originJointList = cmds.listConnections(self.currentSetGrp + '.originJoint', source=0, destination=1)
        if originJointList:
            originJointList.sort()
        bakeFKCtrlList = cmds.listConnections(self.currentSetGrp + '.BakeFKCtrl', source=0, destination=1)
        if bakeFKCtrlList:
            bakeFKCtrlList.sort()

        animMinTime = cmds.playbackOptions(min=1, q=1)
        animMaxTime = cmds.playbackOptions(max=1, q=1)

        for i in xrange(int(animMaxTime - animMinTime) + 1):
            cmds.currentTime(animMinTime + i)

            for j in xrange(len(originJointList) - 1):
                cmds.matchTransform(bakeFKCtrlList[j], originJointList[j], pos=1, rot=1)
                for at in ['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ']:
                    cmds.setKeyframe(bakeFKCtrlList[j], at=at, time=cmds.currentTime(q=1))

            print 'current time is: ' + str(animMinTime + i)

        cmds.select(cl=1)

    def selectCurrentSetGrp(self):
        """
        Select current setting group
        :return: None
        """
        cmds.select(self.currentSetGrp)

    def replaceHairSystem(self):
        """
        Replace existed hair system with selected hair system or new hair system
        :return: None
        """
        # doesn't change
        currentHairSystem = cmds.listConnections(self.currentSetGrp + '.hair', source=0, destination=1, shapes=1)[0]

        if currentHairSystem == self.repHairComBox.currentText():
            return

        elif currentHairSystem != self.repHairComBox.currentText() and self.repHairComBox.currentText() != 'New...':
            # disconnect original hair system
            currentFollicle = cmds.listConnections(self.currentSetGrp + '.follicle',
                                                   source=0, destination=1, shapes=1)[0]

            curPosConnections = cmds.listConnections(currentFollicle + '.currentPosition',
                                                     source=1, destination=0, plugs=1)
            outHairConnections = cmds.listConnections(currentFollicle + '.outHair',
                                                      source=0, destination=1, plugs=1)

            if curPosConnections:
                for i in curPosConnections:
                    cmds.disconnectAttr(i, currentFollicle + '.currentPosition')

            if outHairConnections:
                for i in outHairConnections:
                    cmds.disconnectAttr(currentFollicle + '.outHair', i)

            currentHairSystemAttr = cmds.listConnections(self.currentSetGrp + '.hair',
                                                         source=0, destination=1, plugs=1)[0]
            currentNucleusAttr = cmds.listConnections(self.currentSetGrp + '.nucleus',
                                                      source=0, destination=1, plugs=1)[0]

            cmds.disconnectAttr(self.currentSetGrp + '.hair', currentHairSystemAttr)
            cmds.disconnectAttr(self.currentSetGrp + '.nucleus', currentNucleusAttr)

            # add current follicle to specified hair system

            lib.addFollicle(follicleShape=currentFollicle, hairShape=self.repHairComBox.currentText())

            # hairIndex = cmds.getAttr(self.repHairComBox.currentText() + '.hair', size=1)
            hairIndex = lib.findSingleAvailableIndex(attr=self.repHairComBox.currentText() + '.hair')
            targetNucleus = cmds.listConnections(self.repHairComBox.currentText() + '.currentState',
                                                 source=0, destination=1)[0]

            # nucleusIndex = cmds.getAttr(targetNucleus + '.nucleus', size=1)
            nucleusIndex = lib.findSingleAvailableIndex(attr=targetNucleus + '.nucleus')

            cmds.connectAttr(self.currentSetGrp + '.hair',
                             self.repHairComBox.currentText() + '.hair[%s]' % (str(hairIndex)), f=1)
            cmds.connectAttr(self.currentSetGrp + '.nucleus',
                             targetNucleus + '.nucleus[%s]' % (str(nucleusIndex)), f=1)

        # new...
        else:
            # disconnect from original hair system
            currentFollicle = cmds.listConnections(self.currentSetGrp + '.follicle',
                                                   source=0, destination=1, shapes=1)[0]

            curPosConnections = cmds.listConnections(currentFollicle + '.currentPosition',
                                                     source=1, destination=0, plugs=1)
            outHairConnections = cmds.listConnections(currentFollicle + '.outHair',
                                                      source=0, destination=1, plugs=1)

            if curPosConnections:
                for i in curPosConnections:
                    cmds.disconnectAttr(i, currentFollicle + '.currentPosition')

            if outHairConnections:
                for i in outHairConnections:
                    cmds.disconnectAttr(currentFollicle + '.outHair', i)

            currentHairSystemAttr = cmds.listConnections(self.currentSetGrp + '.hair',
                                                         source=0, destination=1, plugs=1)[0]

            cmds.disconnectAttr(self.currentSetGrp + '.hair', currentHairSystemAttr)

            currentNucleusAttr = cmds.listConnections(self.currentSetGrp + '.nucleus',
                                                      source=0, destination=1, plugs=1)[0]
            cmds.disconnectAttr(self.currentSetGrp + '.nucleus', currentNucleusAttr)

            # create new hair system with new nucleus
            hairNucleus = lib.createHairSys(prefixName='New')

            lib.addFollicle(follicleShape=currentFollicle, hairShape=hairNucleus['hairShape'])

            # hairIndex = cmds.getAttr(hairNucleus['hairShape'] + '.hair', size=1)
            hairIndex = lib.findSingleAvailableIndex(attr=hairNucleus['hairShape'] + '.hair')

            cmds.connectAttr(self.currentSetGrp + '.hair',
                             hairNucleus['hairShape'] + '.hair[%s]' % (str(hairIndex)), f=1)

            nucleusIndex = lib.findSingleAvailableIndex(attr=hairNucleus['nucleus'] + '.nucleus')
            cmds.connectAttr(self.currentSetGrp + '.nucleus',
                             hairNucleus['nucleus'] + '.nucleus[%s]' % (str(nucleusIndex)), f=1)

            # clean hierarchy
            follicleTransNode = cmds.listRelatives(currentFollicle, c=0, p=1, path=1)[0]
            targetParent = cmds.listRelatives(follicleTransNode, c=0, p=1, path=1)[0]
            cmds.parent(hairNucleus['hairTransNode'], targetParent)
            cmds.parent(hairNucleus['nucleus'], targetParent)

            cmds.select(cl=1)

        self.setCurrentSetGrp()

    def replaceNucleus(self):
        """
        Replace existed nucleus with selected nucleus or new nucleus
        :return: None
        """
        currentNucleus = cmds.listConnections(self.currentSetGrp + '.nucleus', source=0, destination=1)[0]

        if currentNucleus == self.repNecleusComBox.currentText():
            return

        elif currentNucleus != self.repNecleusComBox.currentText() and self.repNecleusComBox.currentText() != 'New...':
            # disconnect original nucleus
            currentHairSystem = cmds.listConnections(self.currentSetGrp + '.hair', source=0, destination=1, shapes=1)[0]

            inputActiveAttr = cmds.listConnections(currentHairSystem + '.currentState',
                                                   source=0, destination=1, plugs=1)[0]
            inputActiveStartAttr = cmds.listConnections(currentHairSystem + '.startState',
                                                        source=0, destination=1, plugs=1)[0]
            outputObjectAttr = cmds.listConnections(currentHairSystem + '.nextState',
                                                    source=1, destination=0, plugs=1)[0]

            cmds.disconnectAttr(currentHairSystem + '.currentState', inputActiveAttr)
            cmds.disconnectAttr(currentHairSystem + '.startState', inputActiveStartAttr)
            cmds.disconnectAttr(outputObjectAttr, currentHairSystem + '.nextState')
            cmds.disconnectAttr(currentNucleus + '.startFrame', currentHairSystem + '.startFrame')

            currentNucleusAttr = cmds.listConnections(self.currentSetGrp + '.nucleus',
                                                      source=0, destination=1, plugs=1)[0]
            cmds.disconnectAttr(self.currentSetGrp + '.nucleus', currentNucleusAttr)

            # connect specified nucleus
            index = lib.findTribleAvailableIndex(firstAttr=self.repNecleusComBox.currentText() + '.inputActive',
                                                 secondAttr=self.repNecleusComBox.currentText() + '.inputActiveStart',
                                                 thirdAttr=self.repNecleusComBox.currentText() + '.outputObjects')
            # inputActiveIndex = cmds.getAttr(self.repNecleusComBox.currentText() + '.inputActive', size=1)
            # inputActiveStartIndex = cmds.getAttr(self.repNecleusComBox.currentText() + '.inputActiveStart', size=1)
            # outputObjectIndex = cmds.getAttr(self.repNecleusComBox.currentText() + '.outputObjects', size=1)

            # nucleusIndex = cmds.getAttr(self.repNecleusComBox.currentText() + '.nucleus', size=1)
            nucleusIndex = lib.findSingleAvailableIndex(self.repNecleusComBox.currentText() + '.nucleus')

            cmds.connectAttr(self.repNecleusComBox.currentText() + '.outputObjects[%s]' % (str(index)),
                             currentHairSystem + '.nextState', f=1)
            cmds.connectAttr(self.repNecleusComBox.currentText() + '.startFrame',
                             currentHairSystem + '.startFrame', f=1)

            cmds.connectAttr(currentHairSystem + '.currentState',
                             self.repNecleusComBox.currentText() + '.inputActive[%s]' % (str(index)), f=1)
            cmds.connectAttr(currentHairSystem + '.startState',
                             self.repNecleusComBox.currentText() + '.inputActiveStart[%s]' % (str(index)),
                             f=1)

            cmds.connectAttr(self.currentSetGrp + '.nucleus',
                             self.repNecleusComBox.currentText() + '.nucleus[%s]' % (str(nucleusIndex)), f=1)

        else:
            # disconnect original nucleus
            currentHairSystem = cmds.listConnections(self.currentSetGrp + '.hair', source=0, destination=1, shapes=1)[0]

            inputActiveAttr = cmds.listConnections(currentHairSystem + '.currentState',
                                                   source=0, destination=1, plugs=1)[0]
            inputActiveStartAttr = cmds.listConnections(currentHairSystem + '.startState',
                                                        source=0, destination=1, plugs=1)[0]
            outputObjectAttr = cmds.listConnections(currentHairSystem + '.nextState',
                                                    source=1, destination=0, plugs=1)[0]

            cmds.disconnectAttr(currentHairSystem + '.currentState', inputActiveAttr)
            cmds.disconnectAttr(currentHairSystem + '.startState', inputActiveStartAttr)
            cmds.disconnectAttr(outputObjectAttr, currentHairSystem + '.nextState')
            cmds.disconnectAttr(currentNucleus + '.startFrame', currentHairSystem + '.startFrame')

            currentNucleusAttr = cmds.listConnections(self.currentSetGrp + '.nucleus',
                                                      source=0, destination=1, plugs=1)[0]
            cmds.disconnectAttr(self.currentSetGrp + '.nucleus', currentNucleusAttr)

            # create and connect
            createdNucleus = lib.createNucleus(prefixName='New')

            inputActiveIndex = cmds.getAttr(createdNucleus + '.inputActive', size=1)
            inputActiveStartIndex = cmds.getAttr(createdNucleus + '.inputActiveStart', size=1)
            outputObjectIndex = cmds.getAttr(createdNucleus + '.outputObjects', size=1)

            nucleusIndex = cmds.getAttr(createdNucleus + '.nucleus', size=1)

            cmds.connectAttr(createdNucleus + '.outputObjects[%s]' % (str(outputObjectIndex)),
                             currentHairSystem + '.nextState', f=1)
            cmds.connectAttr(createdNucleus + '.startFrame',
                             currentHairSystem + '.startFrame', f=1)

            cmds.connectAttr(currentHairSystem + '.currentState',
                             createdNucleus + '.inputActive[%s]' % (str(inputActiveIndex)), f=1)
            cmds.connectAttr(currentHairSystem + '.startState',
                             createdNucleus + '.inputActiveStart[%s]' % (str(inputActiveStartIndex)), f=1)

            cmds.connectAttr(self.currentSetGrp + '.nucleus',
                             createdNucleus + '.nucleus[%s]' % (str(nucleusIndex)), f=1)

            # clean hierarchy
            currentFollicle = cmds.listConnections(self.currentSetGrp + '.follicle',
                                                   source=0, destination=1, shapes=1)[0]
            follicleTransNode = cmds.listRelatives(currentFollicle, c=0, p=1, path=1)[0]
            targetParent = cmds.listRelatives(follicleTransNode, c=0, p=1, path=1)[0]

            cmds.parent(createdNucleus, targetParent)

            cmds.select(cl=1)

        self.setCurrentSetGrp()


class Splitter(QtWidgets.QWidget):
    def __init__(self, text=None):
        """
        Splitter class for create splitter widget
        :param text: text between splitter lines
        """
        super(Splitter, self).__init__()

        self.setMinimumHeight(2)
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.setLayout(self.mainLayout)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.setAlignment(QtCore.Qt.AlignVCenter)

        firstLine = QtWidgets.QFrame()
        firstLine.setFrameStyle(QtWidgets.QFrame.HLine)
        self.mainLayout.addWidget(firstLine)

        if not text:
            return

        font = QtGui.QFont()
        font.setBold(True)

        textWidth = QtGui.QFontMetrics(font)
        width = textWidth.width(text) + 10

        label = QtWidgets.QLabel()
        label.setText(text)
        label.setFont(font)
        label.setMaximumWidth(width)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)

        self.mainLayout.addWidget(label)

        secondLine = QtWidgets.QFrame()
        secondLine.setFrameStyle(QtWidgets.QFrame.HLine)
        self.mainLayout.addWidget(secondLine)
