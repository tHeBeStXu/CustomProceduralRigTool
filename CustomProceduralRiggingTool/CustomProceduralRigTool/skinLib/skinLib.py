import os
import cPickle as pickle
import maya.cmds as cmds
import maya.OpenMaya as openmaya
import maya.OpenMayaUI as openmayaui
import maya.OpenMayaAnim as openmayaanim
from functools import partial


from PySide2 import QtGui, QtWidgets, QtCore
from shiboken2 import wrapInstance


def show():
    """
    Show Export and Import dialog UI
    :return:
    """
    dialog = SkinIODialog(getMayaWindow())
    dialog.show()


def getMayaWindow():
    """
    Get the mayaMainWindow as parent
    :return: mayaMainWindow Ptr
    """
    ptr = openmayaui.MQtUtil.mainWindow()
    return wrapInstance(long(ptr), QtWidgets.QMainWindow)


def getShape(node, intermediate=False):
    """
    Get the shape from specified node.

    :param node: node Name of a transform or shape node.
    :param intermediate: intermediate True to get the intermediate shape, False to get the visible shape
    :return: the name of the desired shape node
    """
    if cmds.nodeType(node) == 'transform':
        shapes = cmds.listRelatives(node, shapes=1, path=1)

        # from transform node to get the shape node
        if not shapes:
            shapes = []
        for shape in shapes:
            isIntermediate = cmds.getAttr('%s.intermediateObject' % shape)
            # Sometimes there are left over intermediate shapes that are not used to(the duplicated deformed shape)
            # check the connections to make sure we get the one that is used
            # return intermediate shape which has incoming objects
            if intermediate and isIntermediate and cmds.listConnections(shape, source=0, destination=1):
                return shape

            # return visible shape
            elif not intermediate and not isIntermediate:
                return shape

        if shapes:
            return shapes[0]
    # return the shape which just is a Shape Node
    elif cmds.nodeType(node) in ['mesh', 'nurbsCurve', 'nurbsSurface']:
        return node

    return None


class SkinCluster(object):
    # global variable extension
    kFileExtension = '.skin'

    @classmethod
    def export(cls, filePath=None, shape=None):
        skin = SkinCluster(shape)
        skin.exportSkin(filePath)

    @classmethod
    def createAndImport(cls, filePath=None, shape=None):
        """
        Create a skinCluster on the specified shape if one does not already exist
        and then import the weight data.
        :param filePath: filePath of the skinWeights
        :param shape: mesh shape which skinCluster deforms
        :return:
        """

        if not shape:
            try:
                shape = cmds.ls(sl=1)[0]

            except:
                raise RuntimeError('No shape selected')

        if filePath == None:
            startDir = cmds.workspace(q=1, rootDirectory=1)
            filePath = cmds.fileDialog2(dialogStyle=2, fileMode=1, startingDirectory=startDir,
                                        fileFilter='Skin Files (*%s)' % SkinCluster.kFileExtension)

        if not filePath:
            return
        if not isinstance(filePath, basestring):
            filePath = filePath[0]

        # Read the data from the file
        fh = open(filePath, 'rb')
        data = pickle.load(fh)
        fh.close()

        # Make sure the vertex count is the same
        meshVertices = cmds.polyEvaluate(shape, vertex=1)

        importedVertices = len(data['blendWeights'])
        if meshVertices != importedVertices:
            raise RuntimeError('Vertex counts do not match. %d != %d' % (meshVertices, importedVertices))


        # check if the shape already has a skinCluster
        if SkinCluster.getSkinCluster(shape):
            skinCluster = SkinCluster(shape)
        else:
            # create a new skinCluster
            joints = data['weights'].keys()

            # Make sure all the joints exist

            unusedImports = []
            # Create a set for get which joint in the scene doesn't have weights
            noMatch = set([SkinCluster.removeNamespaceFromString(x) for x in cmds.ls(type='joint')])

            for j in joints:
                if j in noMatch:
                    noMatch.remove(j)
                else:
                    unusedImports.append(j)

            # Remapping the joints
            # if there were unmapped influences ask the user to map them
            if unusedImports and noMatch:

                mappingDialog = WeightRemapDialog(getMayaWindow())
                mappingDialog.setInfluences(unusedImports, noMatch)
                mappingDialog.exec_()

                for src, dst in mappingDialog.mapping.items():
                    # swap the mapping
                    data['weights'][dst] = data['weights'][src]
                    del data['weights'][src]

            # Create the skinCluster with post normalization so setting the weights does not
            # normalize all weights
            joints = data['weights'].keys()

            skinCluster = cmds.skinCluster(joints, shape, tsb=1, nw=2, n=data['name'])
            skinCluster = SkinCluster(shape)

        skinCluster.setData(data)
        print "Imported %s" % filePath

    @classmethod
    def getSkinCluster(cls, shape):
        """
        Get the skinCluster node attached to the specified shape.
        :param shape: Shape node name
        :return: The attached skinCluster name or None if no skinCluster is attached
        """
        shape = getShape(shape)
        history = cmds.listHistory(shape, pruneDagObjects=1, interestLevel=2)

        if not history:
            return None
        skins = [x for x in history if cmds.nodeType(x) == 'skinCluster']

        if skins:
            return skins[0]
        return None

    @classmethod
    def removeNamespaceFromString(cls, influenceName):
        """
        Remove namespaces from a string
        CHANGES NAMESPACE:  joint1 | NAMESAPCE:joint2 -> joint1 | joint2
        :param influenceName: string, name with a namespace
        :return: string ,name without a namespace
        """
        tokens = influenceName.split('|')
        result = ''

        for i, tokens in enumerate(tokens):
            if i > 0:
                result += '|'

            result += tokens.split(':')[-1]

        return result

    def __init__(self, shape=None):
        if not shape:
            try:
                shape = cmds.ls(sl=1)[0]

            except:
                raise RuntimeError('No shape selected')

        self.shape = getShape(shape)
        if not self.shape:
            raise RuntimeError('No shape connected to %s' % shape)

        # Get the skinCluster node attached to the shape
        self.node = SkinCluster.getSkinCluster(self.shape)
        if not self.node:
            raise ValueError('No skinCluster attached to %s' % self.shape)

        # Get the skinCluster MObject
        selectionList = openmaya.MSelectionList()
        selectionList.add(self.node)
        self.mobj = openmaya.MObject()
        selectionList.getDependNode(0, self.mobj)
        self.fn = openmayaanim.MFnSkinCluster(self.mobj)
        self.data = {'weights': {},
                     'blendWeights': [],
                     'name': self.node}

    def gatherData(self):
        """
        get and store the skinningMethod and normalizeWeights attributes in data dictionary
        :return: None
        """
        dagPath, components = self.__getGeometryComponents()
        self.gatherInfluenceWeights(dagPath, components)
        self.gatherBlendWeights(dagPath, components)

        for attr in ['skinningMethod', 'normalizeWeights']:
            self.data[attr] = cmds.getAttr('%s.%s' % (self.node, attr))

    def __getGeometryComponents(self):
        """
        get the dagPath of influence object(joint) and Geometry components(vertex)
        :return: dagPath, componnets
        """
        # get dagPath and member components of skined shape
        # the deformerSet pretty controls which vertex is deformed by the skinCluster
        # the deformerSet will allows us to pull out that components(vertex) mobject that we need
        fnSet = openmaya.MFnSet(self.fn.deformerSet())
        members = openmaya.MSelectionList()
        # the MSelectionList contains the vertex information in the deformerSet above
        fnSet.getMembers(members, False)

        dagPath = openmaya.MDagPath()
        components = openmaya.MObject()

        # dagPath: dagPath of influence objects(joint)
        # components: mesh components(vertex)
        members.getDagPath(0, dagPath, components)

        return dagPath, components

    def gatherInfluenceWeights(self, dagPath, components):
        """
        get and store the weights of each influence object for same ordered components(vertex) in data['weights'] dictionary
        :param dagPath:
        :param components: mesh components(vertex)
        :return: None
        """
        # Gathers all the influence weights
        weights = self.__getCurrentWeights(dagPath, components)

        influencePaths = openmaya.MDagPathArray()
        # influencePaths is the fullPath of the object(joint)
        numInfluences = self.fn.influenceObjects(influencePaths)
        # weight size = number of components(vertex) * number of influenceObjects(joints)
        numComponentsPerInfluence = weights.length() / numInfluences

        for ii in range(influencePaths.length()):
            influenceName = influencePaths[ii].partialPathName()
            # we want to store the weights by influence without the namespace so it is easier
            # to import if the namespace is different
            influenceNameWithoutNamespace = SkinCluster.removeNamespaceFromString(influenceName)
            # store the weight of each influence object(joint) for same ordered components(vertex)
            self.data['weights'][influenceNameWithoutNamespace] = [weights[jj * numInfluences + ii] for jj in range(numComponentsPerInfluence)]

    def gatherBlendWeights(self, dagPath, components):
        """
        Gather the BlendWeights
        :param dagPath: dagPath of influence objects(joint)
        :param components: mesh components(vertex)
        :return: None
        """
        weights = openmaya.MDoubleArray()
        self.fn.getBlendWeights(dagPath, components, weights)
        self.data['blendWeights'] = [weights[i] for i in range(weights.length())]

    def __getCurrentWeights(self, dagPath, components):
        """
        Get the current weights array. Be careful about the weight array, it is a giant single array.
        The order of the weights array is dependent on the indices of the joint
        :param dagPath: path to object deformed by the skinCluster
        :param components: Components to return weight for, every single vertex in the mesh
        :return: Weights
        """
        weights = openmaya.MDoubleArray()
        util = openmaya.MScriptUtil()

        util.createFromInt(0)

        pUInt = util.asUintPtr()
        # Gets the skinCluster weights for ALL influenceObjects(joints) for the specified components of the object whose dagPath is specified.
        # More details see: https://download.autodesk.com/us/maya/2011help/API/class_m_fn_skin_cluster.html#82e83fc5ab653aa15c5431710b3ac86a
        self.fn.getWeights(dagPath, components, weights, pUInt)
        # weights is a giant single Double Array
        # size = number of components(vertex) * number of influenceObjects(joints)
        return weights

    def exportSkin(self, filePath=None):
        """
        Export the skinCluster data to disk
        :param filePath: File Path
        :return:
        """
        if filePath == None:
            startDir = cmds.workspace(q=1, rootDirectory=1)
            filePath = cmds.fileDialog2(dialogStyle=2, fileMode=0, startingDirectory=startDir,
                                        fileFilter='Skin Files(*%s)' % SkinCluster.kFileExtension)

        if not filePath:
            return

        filePath = filePath[0]

        if not filePath.endswith(SkinCluster.kFileExtension):
            filePath += SkinCluster.kFileExtension

        self.gatherData()

        fh = open(filePath, 'wb')
        pickle.dump(self.data, fh, pickle.HIGHEST_PROTOCOL)

        fh.close()
        print "Exported skinCluster (%d influences, %d vertices) %s" % (len(self.data['weights'].keys()), len(self.data['blendWeights']), filePath)

    def setData(self, data):
        """
        Sets the data and stores it in the Maya skinCluster node.
        :return:
        """
        self.data = data
        dagPath, components = self.__getGeometryComponents()
        self.setInfluenceWeights(dagPath, components)
        self.setBlendWeights(dagPath, components)

        for attr in ['skinningMethod', 'normalizeWeights']:
            cmds.setAttr('%s.%s' % (self.node, attr), self.data[attr])

    def setInfluenceWeights(self, dagPath, components):
        """

        :param dagPath:
        :param components:
        :return:
        """
        # get the existing weights and fill in the new weights
        weights = self.__getCurrentWeights(dagPath, components)
        influencePaths = openmaya.MDagPathArray()
        numInfluences = self.fn.influenceObjects(influencePaths)
        numComponentsPerInfluence = weights.length() / numInfluences

        # Keep track of which imported influences aren't used
        unusedImports = []
        # Keep track of which existing influences don't get anything imported
        noMatch = [influencePaths[ii].partialPathName() for ii in xrange(influencePaths.length())]

        for importedInfluence, importedWeights in self.data['weights'].items():
            for inf_count in xrange(influencePaths.length()):
                # partialPathName used to return exclusive partial path name of the object
                influenceName = influencePaths[inf_count].partialPathName()
                influenceWithoutNamespace = SkinCluster.removeNamespaceFromString(influenceName)

                if influenceWithoutNamespace == importedInfluence:
                    # Store the imported weights into the MDoubeArray
                    for jj in xrange(numComponentsPerInfluence):
                        weights.set(importedWeights[jj], jj * numInfluences + inf_count)

                    noMatch.remove(influenceName)
                    break
            else:
                unusedImports.append(importedInfluence)

        if unusedImports and noMatch:
            mappingDialog = WeightRemapDialog(getMayaWindow())
            mappingDialog.setInfluences(unusedImports, noMatch)
            mappingDialog.exec_()
            for src, dst in mappingDialog.mapping.items():
                for ii in range(influencePaths.length()):
                    if influencePaths[ii].partialPathName() == dst:
                        for jj in range(numComponentsPerInfluence):
                            weights.set(self.data['weights'][src][jj], jj*numInfluences+ii)
                        break

        influenceIndics = openmaya.MIntArray(numInfluences)
        for ii in range(numInfluences):
            influenceIndics.set(ii, ii)
        self.fn.setWeights(dagPath, components, influenceIndics, weights, False)

    def setBlendWeights(self, dagPath, components):
        """
        Set BlendWeights
        :param dagPath:
        :param components:
        :return:
        """
        blendWeights = openmaya.MDoubleArray(len(self.data['blendWeights']))
        for i, w in enumerate(self.data['blendWeights']):
            blendWeights.set(w, i)

        self.fn.setBlendWeights(dagPath, components, blendWeights)


class WeightRemapDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(WeightRemapDialog, self).__init__(parent)

        self.setWindowTitle('Remap Weights')
        self.setObjectName('remapWeightUI')

        self.setModal(True)
        self.resize(600, 400)
        self.mapping = {}

        self.mainVbox = QtWidgets.QVBoxLayout()

        self.setLayout(self.mainVbox)

        label = QtWidgets.QLabel('The following influences have no corresponding influence from the import file. '
                                 'You can either remap the influences or skip them')

        label.setWordWrap(True)

        self.mainVbox.addWidget(label)

        self.HBox = QtWidgets.QHBoxLayout()
        self.mainVbox.addLayout(self.HBox)


        self.VBox = QtWidgets.QVBoxLayout()
        self.HBox.addLayout(self.VBox)

        self.VBox.addWidget(QtWidgets.QLabel('Unmapped influences'))

        self.existingInfluences = QtWidgets.QListWidget()
        self.VBox.addWidget(self.existingInfluences)

        vbox = QtWidgets.QVBoxLayout()
        self.HBox.addLayout(vbox)
        vbox.addWidget(QtWidgets.QLabel('Available imported influence'))
        self.scrollArea = QtWidgets.QScrollArea()
        self.widget = QtWidgets.QScrollArea()
        self.importedInfluenceLayout = QtWidgets.QVBoxLayout(self.widget)
        vbox.addWidget(self.widget)

        hbox = QtWidgets.QHBoxLayout()
        self.mainVbox.addLayout(hbox)
        hbox.addStretch()
        self.btn = QtWidgets.QPushButton('OK')
        self.btn.released.connect(self.accept)
        hbox.addWidget(self.btn)

    def setInfluences(self, importedInfluences, existingInfluences):
        infs = list(existingInfluences)
        infs.sort()
        self.existingInfluences.addItems(infs)

        width = 200
        for inf in importedInfluences:
            row = QtWidgets.QHBoxLayout()
            self.importedInfluenceLayout.addLayout(row)

            label = QtWidgets.QLabel(inf)
            row.addWidget(label)

            toggleBtn = QtWidgets.QPushButton('->')
            toggleBtn.setMaximumWidth(30)
            row.addWidget(toggleBtn)

            label = QtWidgets.QLabel('')
            label.setMaximumWidth(width)
            label.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            row.addWidget(label)

            toggleBtn.released.connect(partial(self.setInfluencesMapping, src=inf, label=label))

        self.importedInfluenceLayout.addStretch()


    def setInfluencesMapping(self, src, label):
        selectedInfluence = self.existingInfluences.selectedItems()

        if not selectedInfluence:
            return

        dst = selectedInfluence[0].text()

        label.setText(dst)

        self.mapping[src] = dst

        index = self.existingInfluences.indexFromItem(selectedInfluence[0])

        item = self.existingInfluences.takeItem(index.row())

        del item


class SkinIODialog(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super(SkinIODialog, self).__init__(parent)

        self.setWindowTitle('Skin IO')
        self.setObjectName('skinioWidget')
        self.setModal(False)
        self.setFixedSize(200, 80)

        self.vbox = QtWidgets.QVBoxLayout()
        self.setLayout(self.vbox)

        self.exportBtn = QtWidgets.QPushButton("Export")
        self.vbox.addWidget(self.exportBtn)
        self.exportBtn.clicked.connect(SkinCluster.export)

        self.importBtn = QtWidgets.QPushButton("Import")
        self.vbox.addWidget(self.importBtn)
        self.importBtn.clicked.connect(SkinCluster.createAndImport)
