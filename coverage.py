from PySide.QtCore import *
from PySide.QtGui import *
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backend_bases import key_press_handler
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.collections import LineCollection
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)

class CoverageView(QWidget):

    def __init__(self,dataDict):
        super().__init__()
        self.dataDict = dataDict
        self.chromosomes = self.dataDict['chromosomeList']
        self.subWindows = []
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.maxColumns = 2
        self.bpWindow = 50
        self.minCoverage = 0
        self.maxCoverage = 5
        self.createSettings()
        self.coverageNormLog = self.dataDict['coverageNormLog']
        self.coverageNorm = self.dataDict['coverageNorm']
        self.createChInfo()
        self.showChInfo()

    def returnActiveDataset(self):
        return self.dataDict

    #Adds a subwindow containing a matplotlib widget to the grid layout
    def addChromoPlot(self):
        addDialog = QDialog()
        addDialog.setWindowTitle("Add plot")
        applyButton = QPushButton('Ok', addDialog)
        applyButton.clicked.connect(addDialog.accept)
        chromoBox = QComboBox()
        chromoStrings = [chromo.name for chromo in self.chromosomes if not "GL" in chromo.name]
        chromoBox.addItems(chromoStrings)
        chrLabel = QLabel("Add plot for chromosome: ")
        typeBox = QComboBox()
        typeStrings = ["Line plot", "Scatter plot"]
        typeBox.addItems(typeStrings)
        typeLabel = QLabel("Plot method: ")
        addDialog.layout = QGridLayout(addDialog)
        addDialog.layout.addWidget(chrLabel,0,0)
        addDialog.layout.addWidget(chromoBox,0,1)
        addDialog.layout.addWidget(typeLabel,1,0)
        addDialog.layout.addWidget(typeBox,1,1)
        addDialog.layout.addWidget(applyButton,2,0)
        choice = addDialog.exec_()
        if choice == QDialog.Accepted:
            chromo = self.chromosomes[chromoBox.currentIndex()]
            chromoPlot = ChromoPlotWindow(chromo,typeBox.currentIndex(),self)
            self.subWindows.append(chromoPlot)
            self.arrangePlots()

    #Removes a plot and rearranges existing plots
    def removeChromoPlot(self,plot):
        self.subWindows.remove(plot)
        self.grid.removeWidget(plot)
        plot.destroy()
        self.arrangePlots()

    def arrangePlots(self):
        currentColumn = 0
        currentRow = 0
        for plot in self.subWindows:
            self.grid.addWidget(plot,currentRow,currentColumn)
            if currentColumn == self.maxColumns-1:
                currentRow += 1
                currentColumn = 0
            else:
                currentColumn += 1
        self.update()

    def createSettings(self):
        self.settingsModel = QStandardItemModel()
        #create header labels to distinguish different settings.
        verticalHeaders = ["bpWindow", "minCoverage", "maxCoverage"]
        self.settingsModel.setVerticalHeaderLabels(verticalHeaders)
        bpWinText = QStandardItem("BP Resolution (kb)")
        bpWinText.setEditable(False)
        bpWinText.setToolTip("Show each data point as the average of this value (x1000 bp)")
        bpWinData = QStandardItem()
        bpWinData.setData(self.bpWindow,0)
        bpWinData.setEditable(True)
        minCovLimitText = QStandardItem("Min.coverage value (%)")
        minCovLimitText.setEditable(False)
        minCovLimitText.setToolTip("Minimum coverage value,\nin percentage of average coverage value of genome.")
        minCovLimitData = QStandardItem()
        minCovLimitData.setData(self.minCoverage*100,0)
        minCovLimitData.setEditable(True)
        maxCovLimitText = QStandardItem("Max. coverage value (%)")
        maxCovLimitText.setEditable(False)
        maxCovLimitText.setToolTip("Maximum coverage value,\nin percentage of average coverage value of genome.")
        maxCovLimitData = QStandardItem()
        maxCovLimitData.setData(self.maxCoverage*100,0)
        maxCovLimitData.setEditable(True)
        maxColumnsText = QStandardItem("Number of columns")
        maxColumnsText.setEditable(False)
        maxColumnsText.setToolTip("Number of columns to arrange diagrams in")
        maxColumnsData = QStandardItem()
        maxColumnsData.setData(self.maxColumns,0)
        maxColumnsData.setEditable(True)
        self.settingsModel.setItem(0,0,bpWinText)
        self.settingsModel.setItem(0,1,bpWinData)
        self.settingsModel.setItem(1,0,minCovLimitText)
        self.settingsModel.setItem(1,1,minCovLimitData)
        self.settingsModel.setItem(2,0,maxCovLimitText)
        self.settingsModel.setItem(2,1,maxCovLimitData)
        self.settingsModel.setItem(3,0,maxColumnsText)
        self.settingsModel.setItem(3,1,maxColumnsData)
        self.settingsModel.itemChanged.connect(self.updateSettings)

    def viewSettings(self):
        self.settingsList = QTableView()
        self.settingsList.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.settingsList.setShowGrid(False)
        self.settingsList.horizontalHeader().hide()
        self.settingsList.verticalHeader().hide()
        self.settingsList.setModel(self.settingsModel)
        self.settingsList.setTextElideMode(Qt.ElideNone)
        self.settingsDia = QDialog(self)
        self.settingsDia.setWindowTitle("Settings")
        applyButton = QPushButton('Apply', self.settingsDia)
        applyButton.clicked.connect(self.settingsDia.accept)
        self.settingsDia.layout = QGridLayout(self.settingsDia)
        self.settingsDia.layout.addWidget(self.settingsList,0,0,1,3)
        self.settingsDia.layout.addWidget(applyButton,1,0,1,1)
        self.settingsDia.show()

    def updateSettings(self,item):
        if item.row() == 0:
            self.bpWindow = item.data(0)
        if item.row() == 1:
            self.minCoverage = item.data(0)/100
        if item.row() == 2:
            self.maxCoverage = item.data(0)/100
        if item.row() == 3:
            self.maxColumns = item.data(0)

    #Creates data model for info window
    def createChInfo(self):
        self.chModel = QStandardItemModel()
        topstring = ["Name","Length","No. of variants"]
        self.chModel.setHorizontalHeaderLabels(topstring)
        for chromo in self.chromosomes:
            infostring = [chromo.name,chromo.end,str(len(chromo.variants))]
            infoItems = [QStandardItem(string) for string in infostring]
            #only keep chromosomes up to MT (no. 24)
            if (self.chromosomes.index(chromo) <= 24):
                self.chModel.appendRow(infoItems)

    #Creates a window with chromosomes and toggles, info
    def showChInfo(self):
        #if any earlier window is open, close it
        try:
            self.chDia.close()
        except:
            pass
        self.chList = QTableView()
        self.chList.verticalHeader().hide()
        self.chList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.chList.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.chList.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.chList.setShowGrid(False)
        self.chList.setModel(self.chModel)
        self.chList.resizeColumnsToContents()
        #Give the length column some extra space..
        curWidth = self.chList.columnWidth(1)
        self.chList.setColumnWidth(1,curWidth+20)
        self.chDia = QDialog(self)
        self.chDia.setWindowTitle("Chromosome info")
        #Button for viewing selected chromosome variants
        viewVarButton = QPushButton('View variants', self.chDia)
        viewVarButton.clicked.connect(self.viewVariants)
        #Button for adding variants
        addVariantButton = QPushButton('Add variant', self.chDia)
        addVariantButton.clicked.connect(self.addVariant)
        self.chDia.layout = QGridLayout(self.chDia)
        self.chDia.layout.addWidget(self.chList,0,0,1,4)
        self.chDia.layout.addWidget(viewVarButton,1,0,1,1)
        self.chDia.layout.addWidget(addVariantButton,1,1,1,1)
        self.chDia.setMinimumSize(450,400)
        self.chDia.show()

    #Creates data model for variants in given chromosome
    def createVariantInfo(self, chromo):
        self.varModel = QStandardItemModel()
        topstring = ['TYPE', 'START', 'END', 'GENE(S)', 'CYTOBAND']
        self.varModel.setHorizontalHeaderLabels(topstring)
        #Adding variant info to a list
        for variant in chromo.variants:
            infoitem = []
            #this is event_type in the variant
            infoitem.append(QStandardItem(variant[4]))
            #this is posA in the variant
            startText = str(variant[1])
            infoitem.append(QStandardItem(startText))
            #this is posB or chrB: posB in the variant (if interchromosomal)
            if variant[0] is not variant[2]:
                endText = str(variant[2]) + ": " + str(variant[3])
            else:
                endText = str(variant[3])
            infoitem.append(QStandardItem(endText))
            #this is allGenes in the variant
            infoitem.append(QStandardItem(variant[7]))
            #this is cband in the variant
            infoitem.append(QStandardItem(variant[8]))
            self.varModel.appendRow(infoitem)

    #Creates a popup containing variant info in a table.
    #Could be implemented in a better way than multiple dialogues..
    def viewVariants(self):
        selectedIndexes = self.chList.selectedIndexes()
        selectedRows = [index.row() for index in selectedIndexes]
        selectedRows = set(selectedRows)
        for row in selectedRows:
            chromo = self.chromosomes[row]
            self.createVariantInfo(chromo)
            viewVarDia = QDialog(self)
            viewVarDia.setWindowTitle("Variants in contig " + chromo.name)
            varList = QTableView()
            varList.setMinimumSize(500,400)
            varList.verticalHeader().hide()
            varList.setEditTriggers(QAbstractItemView.NoEditTriggers)
            varList.setModel(self.varModel)
            varList.resizeColumnToContents(1)
            viewVarDia.layout = QGridLayout(viewVarDia)
            viewVarDia.layout.addWidget(varList,0,0)
            viewVarDia.show()

    def addVariant(self):
        #Adds a variant to selected chromosomes. Some models still have to be updated.
        #Not sure how to best handle input yet.
        selectedIndexes = self.chList.selectedIndexes()
        selectedRows = [index.row() for index in selectedIndexes]
        selectedRows = set(selectedRows)
        for row in selectedRows:
            chromo = self.chromosomes[row]
            addVariantDialog = QDialog()
            addVariantDialog.setWindowTitle("Add variant in contig " + chromo.name)
            applyButton = QPushButton('Ok', addVariantDialog)
            applyButton.clicked.connect(addVariantDialog.accept)
            cancelButton = QPushButton('Cancel', addVariantDialog)
            cancelButton.clicked.connect(addVariantDialog.reject)
            locBoxValidator = QIntValidator(self)
            locBoxValidator.setBottom(0)
            locABox = QLineEdit()
            locBBox = QLineEdit()
            locABox.setValidator(locBoxValidator)
            locBBox.setValidator(locBoxValidator)
            chromoBox = QComboBox()
            chromoStrings = [chromo.name for chromo in self.chromosomes if not "GL" in chromo.name]
            chromoBox.addItems(chromoStrings)
            altBox = QLineEdit()
            geneBox = QLineEdit()
            locALabel = QLabel("Position A: ")
            chromoLabel = QLabel("Chromosome B: ")
            locBLabel = QLabel("Position B: ")
            altLabel = QLabel("ALT: ")
            geneLabel = QLabel("GENE(S): ")
            addVariantDialog.layout = QGridLayout(addVariantDialog)
            addVariantDialog.layout.addWidget(locALabel,0,0)
            addVariantDialog.layout.addWidget(locABox,0,1)
            addVariantDialog.layout.addWidget(chromoLabel,1,0)
            addVariantDialog.layout.addWidget(chromoBox,1,1)
            addVariantDialog.layout.addWidget(locBLabel,2,0)
            addVariantDialog.layout.addWidget(locBBox,2,1)
            addVariantDialog.layout.addWidget(altLabel,3,0)
            addVariantDialog.layout.addWidget(altBox,3,1)
            addVariantDialog.layout.addWidget(geneLabel,4,0)
            addVariantDialog.layout.addWidget(geneBox,4,1)
            addVariantDialog.layout.addWidget(applyButton,5,0)
            addVariantDialog.layout.addWidget(cancelButton,5,1)
            choice = addVariantDialog.exec_()
            if choice == QDialog.Accepted:
                #END field should only be filled if chrB is the same
                if chromoBox.currentText() == chromo.name:
                    end = locBBox.text()
                else:
                    end = "."
                chromo.addVariant(locABox.text(),altBox.text(),"",end,geneBox.text(),"")

#Widget containing a pyplot, plotting coverage data from given chromosome
class ChromoPlotWindow(QWidget):

    def __init__(self,chromo,plotType,parent):
        super().__init__(parent)
        self.chromo = chromo
        self.setMinimumSize(500,500)
        self.figure = Figure(figsize=(5,2),dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setParent(self)
        self.canvas.setFocusPolicy( Qt.ClickFocus )
        self.canvas.setFocus()
        #Set true/false on toolbar to toggle coordinate display
        self.mpl_toolbar = NavigationToolbar(self.canvas, self, False)
        minLabel = QLabel("X min: ")
        maxLabel = QLabel("X max: ")
        self.minXSet = QLineEdit(self)
        self.maxXSet = QLineEdit(self)
        self.mpl_toolbar.addWidget(minLabel)
        self.mpl_toolbar.addWidget(self.minXSet)
        self.mpl_toolbar.addWidget(maxLabel)
        self.mpl_toolbar.addWidget(self.maxXSet)
        self.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.canvas.mpl_connect('draw_event', self.updateSetLimits)
        self.canvas.mpl_connect('button_release_event', self.onClick)

        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        self.setLayout(vbox)
        self.ax = self.figure.add_subplot(111)

        normValue = self.parentWidget().coverageNorm
        minCov = normValue*self.parentWidget().minCoverage
        maxCov = normValue*self.parentWidget().maxCoverage
        coverageChunks = [chromo.coverage[i:i+self.parentWidget().bpWindow] for i in range(0,len(chromo.coverage),self.parentWidget().bpWindow)]
        self.coverageData = []
        for chunk in coverageChunks:
            val = sum(chunk) / len(chunk)
            if val > maxCov:
                val = maxCov
            if val < minCov:
                val = minCov
            self.coverageData.append(val/normValue)

        #Maps colors to coverage values as follows: green: [0,0.75], blue: [0.75,1.25], red: [1.25,5]
        colorMap = ListedColormap(['g', 'black', 'r'])
        colorNorm = BoundaryNorm([0, 0.75, 1.25, 5], 3)
        #See the following example code for explanation http://matplotlib.org/examples/pylab_examples/multicolored_line.html
        points = np.array([range(len(self.coverageData)), self.coverageData]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        #converting the coverageData list into a numpy array needed for the LineCollection
        numpyArrayCData = np.array(self.coverageData)
        lc = LineCollection(segments, cmap=colorMap, norm=colorNorm)
        lc.set_array(numpyArrayCData)
        if plotType == 0:
            self.ax.add_collection(lc)
        elif plotType == 1:
            self.ax.scatter(range(len(self.coverageData)),self.coverageData, c=self.coverageData, cmap= colorMap, norm=colorNorm)

        #Create an input validator for the manual x range input boxes, range is no of bins
        self.xRangeValidator = QIntValidator(0,len(self.coverageData),self)
        self.minXSet.setValidator(self.xRangeValidator)
        self.maxXSet.setValidator(self.xRangeValidator)
        self.minXSet.setText("0")
        self.maxXSet.setText(str(len(self.coverageData)))
        self.minXSet.returnPressed.connect(self.updateXRange)
        self.maxXSet.returnPressed.connect(self.updateXRange)
        self.ax.set_xlim(0,len(self.coverageData))
        self.ax.set_ylim(minCov/normValue,maxCov/normValue)
        self.ax.set_title("Contig " + chromo.name)
        self.ax.set_xlabel("Position (x" + str(self.parentWidget().bpWindow) + " kb)")
        self.ax.set_ylabel("Coverage")
        self.canvas.updateGeometry()
        self.canvas.draw()

    def on_key_press(self, event):
        key_press_handler(event, self.canvas, self.mpl_toolbar)

    def updateXRange(self):
        self.ax.set_xlim(int(self.minXSet.text()),int(self.maxXSet.text()))
        self.canvas.draw()

    def updateSetLimits(self,event):
        xmin,xmax = self.ax.get_xlim()
        if xmin < 0:
            xmin = 0
        if xmax > len(self.coverageData):
            xmax = len(self.coverageData)
        self.ax.set_xlim(xmin,xmax)
        self.minXSet.setText(str(int(xmin)))
        self.maxXSet.setText(str(int(xmax)))

    #Opens a context menu on ctrl+right click on a plot
    def onClick(self, event):
        if event.button == 3 and event.key == 'control':
           menu = QMenu()
           self.clickX = event.xdata
           self.clickY = event.ydata
           addPlotTextAct = QAction('Insert text',self)
           addPlotTextAct.triggered.connect(self.addPlotText)
           deletePlotAct = QAction('Delete plot',self)
           deletePlotAct.triggered.connect(self.deletePlot)
           menu.addAction(addPlotTextAct)
           menu.addAction(deletePlotAct)
           canvasHeight = int(self.figure.get_figheight()*self.figure.dpi)
           menu.exec_(self.mapToGlobal(QPoint(event.x,canvasHeight-event.y)))

    #Adds a given text to the clicked location (in data coordinates) to the plot
    def addPlotText(self):
        (text, ok) = QInputDialog.getText(None, 'Insert text', 'Text:')
        if ok and text:
            self.ax.text(self.clickX, self.clickY, text)
            self.canvas.draw()

    def deletePlot(self):
        self.hide()
        self.parentWidget().removeChromoPlot(self)