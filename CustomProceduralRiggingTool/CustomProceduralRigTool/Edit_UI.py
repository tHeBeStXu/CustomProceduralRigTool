from PySide2 import QtWidgets
import maya.cmds as cmds
import logging
import inspect
from functools import partial
import Splitter_UI


class EditWidget(QtWidgets.QDialog):
    def __init__(self, instance, uiName, functionName):

        logging.basicConfig()
        logger = logging.getLogger('%s' % uiName)
        logger.setLevel(logging.INFO)

        try:
            cmds.deleteUI('%s' % uiName)
        except:
            logger.info('No %s exists!' % uiName)

        super(EditWidget, self).__init__(parent=instance)
        self.setObjectName('%s' % uiName)
        self.setWindowTitle('%s' % uiName)
        self.setModal(False)

        self.instance = instance
        self.functionName = functionName

        # Turn on track selection order for selecting vertices and lines 1 by 1
        self.TSO_Type = cmds.selectPref(q=1, tso=1)
        cmds.selectPref(tso=1)

        self.buildUI()
        self.populate()
        self.show()
        self.refreshListWidget()

    def buildUI(self):
        """
        Build the Edit UI
        :return: None
        """
        # Main layout
        self.mainLayout = QtWidgets.QGridLayout()
        self.setLayout(self.mainLayout)

        # parameters part
        self.paramSplitterWidget = Splitter_UI.Splitter('Parameters')

        self.formWidget = QtWidgets.QFrame()
        self.formWidget.setFrameStyle(QtWidgets.QFrame.StyledPanel)
        self.formWidget.setFrameShadow(QtWidgets.QFrame.Plain)
        self.formLayout = QtWidgets.QFormLayout()
        self.formWidget.setLayout(self.formLayout)

        # Selection part
        self.selSplitterWidget = Splitter_UI.Splitter('Check & Select')

        selectionWidget = QtWidgets.QFrame()
        selectionWidget.setFrameStyle(QtWidgets.QFrame.StyledPanel)
        selectionWidget.setFrameShadow(QtWidgets.QFrame.Plain)

        selectionLayout = QtWidgets.QVBoxLayout()
        selectionWidget.setLayout(selectionLayout)

        # filter part
        filterWidget = QtWidgets.QWidget()
        filterLayout = QtWidgets.QHBoxLayout()
        filterWidget.setLayout(filterLayout)
        filterLabel = QtWidgets.QLabel('Filter:    ')
        self.jointCheck = QtWidgets.QCheckBox('joint')
        self.locatorCheck = QtWidgets.QCheckBox('locator')

        filterLayout.addWidget(filterLabel)
        filterLayout.addWidget(self.jointCheck)
        filterLayout.addWidget(self.locatorCheck)

        self.jointCheck.stateChanged.connect(self.refreshListWidget)
        self.locatorCheck.stateChanged.connect(self.refreshListWidget)

        # arrangement
        self.mainLayout.addWidget(self.paramSplitterWidget, 0, 0, 1, 1)
        self.mainLayout.addWidget(self.formWidget, 1, 0, 1, 1)
        self.mainLayout.addWidget(self.selSplitterWidget, 0, 1, 1, 1)
        self.mainLayout.addWidget(selectionWidget, 1, 1, 1, 1)

        self.listWidget = QtWidgets.QListWidget()
        self.listWidget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.rowItem = {}
        self.tupe = inspect.getargspec(func=self.functionName)
        for i in self.tupe[0]:
            layout = QtWidgets.QHBoxLayout()

            self.rowItem[i] = QtWidgets.QLineEdit()
            button = QtWidgets.QPushButton('<<<')

            layout.addWidget(self.rowItem[i])
            layout.addWidget(button)

            button.clicked.connect(partial(self.setEditLine, self.rowItem[i]))

            self.formLayout.addRow(i, layout)

        selectionLayout.addWidget(filterWidget)
        selectionLayout.addWidget(self.listWidget)

        # selectionWidget.setMaximumHeight(self.formWidget.height())

        self.createGeneralButton(self.mainLayout)

    def setEditLine(self, editLine):
        """
        set specified editLine text
        :param editLine: specified editLine
        :return: None
        """
        # listWidget selected items
        listItems = self.listWidget.selectedItems()
        itemStr = []
        for i in listItems:
            itemStr.append(self.listWidget.item(self.listWidget.row(i)).text())

        # vertices or lines
        selList = cmds.ls(os=1)

        finalList = itemStr + selList

        if finalList:
            if len(finalList) < 2:
                editLine.setText(finalList[0])
            else:
                editLine.setText(str(finalList))

    def saveData(self):
        """
        Save the args info to the specified rig widget's rigArgs dictionary
        :return: None
        """
        tupe = inspect.getargspec(self.functionName)
        for i in tupe[0]:
            self.instance.rigArgs[i] = self.rowItem[i].text()

    def setData(self):
        """
        Save the rigArgs info and close the rigArgs dialog
        :return: None
        """
        self.saveData()

        self.close()

        cmds.selectPref(tso=self.TSO_Type)

    def cancel(self):
        """
        Cancel button action -> close the rigArgs dialog
        :return: None
        """
        self.close()
        cmds.selectPref(tso=self.TSO_Type)

    def populate(self):
        """
        Refresh and populate the rigArgs info for each arg
        :return: None
        """
        for arg in self.instance.rigArgs.keys():
            if arg in self.rowItem.keys():
                self.rowItem[arg].setText(str(self.instance.rigArgs[arg]))
            else:
                raise RuntimeWarning('No specified properties!')

    def createGeneralButton(self, layout):
        """
        Create the Cancel and OK button for each widget
        :param layout: the edit window main widget
        :return: None
        """
        btnWidget = QtWidgets.QWidget()
        btnLayout = QtWidgets.QHBoxLayout(btnWidget)
        layout.addWidget(btnWidget, 2, 0, 1, 2)

        cancel_Btn = QtWidgets.QPushButton('Cancel')
        OK_Btn = QtWidgets.QPushButton('OK')

        btnLayout.addWidget(cancel_Btn)
        btnLayout.addWidget(OK_Btn)

        OK_Btn.clicked.connect(self.setData)
        cancel_Btn.clicked.connect(self.cancel)

    def refreshListWidget(self):
        """
        refresh listWidget with specified checked
        :return: None
        """

        self.listWidget.clear()

        joints = []
        locators = []
        if self.jointCheck.isChecked():
            joints = cmds.ls(type='joint')

        locaterShapes = []
        if self.locatorCheck.isChecked():
            locaterShapes = cmds.ls(type='locator')

        for loc in locaterShapes:
            locators.append(cmds.listRelatives(loc, p=1)[0])

        returnList = joints + locators

        if returnList:
            if len(returnList) > 1:
                self.listWidget.addItems(returnList)
            else:
                self.listWidget.addItem(returnList[0])