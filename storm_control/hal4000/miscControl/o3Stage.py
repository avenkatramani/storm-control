#!/usr/bin/env python
"""
The o3 stage UI.

Aditya 08/21
"""
import os

from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.sc_library.parameters as params

import storm_control.hal4000.halLib.halDialog as halDialog
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule

import storm_control.hal4000.qtdesigner.o3_stage_ui as o3StageUi


class o3StageView(halDialog.HalDialog):
    """
    Manages the o3 stage GUI.
    """
    def __init__(self, configuration = None, **kwds):
        super().__init__(**kwds)
        self.parameters = params.StormXMLObject()
        self.retracted_o3 = configuration.get("retracted_o3")
        self.o3_stage_fn = None

        # Load UI
        self.ui = o3StageUi.Ui_Dialog()
        self.ui.setupUi(self)

        icon_path = os.path.join(os.path.dirname(__file__),"../icons/")
        self.ui.upLButton.setIcon(QtGui.QIcon(os.path.join(icon_path, "2uparrow-128.png")))
        self.ui.upLButton.clicked.connect(self.handleUpLButton)
        self.ui.upSButton.setIcon(QtGui.QIcon(os.path.join(icon_path, "1uparrow-128.png")))
        self.ui.upSButton.clicked.connect(self.handleUpSButton)
        self.ui.downSButton.setIcon(QtGui.QIcon(os.path.join(icon_path, "1downarrow-128.png")))
        self.ui.downSButton.clicked.connect(self.handleDownSButton)                
        self.ui.downLButton.setIcon(QtGui.QIcon(os.path.join(icon_path, "2downarrow-128.png")))
        self.ui.downLButton.clicked.connect(self.handleDownLButton)

        self.ui.homeButton.clicked.connect(self.handleHomeButton)
        self.ui.retractButton.clicked.connect(self.handleRetractButton)
        self.ui.zeroButton.clicked.connect(self.handleZeroButton)

        self.ui.goButton.clicked.connect(self.handleGoButton)
        
        # Set to minimum size & fix.
        self.adjustSize()
        self.setFixedSize(self.width(), self.height())

        # Add parameters.
        self.parameters.add(params.ParameterRangeFloat(description ="o3 Stage large step size",
                                                       name = "o3_large_step",
                                                       value = configuration.get("large_step"),
                                                       min_value = 0.001,
                                                       max_value = 100.0))        
        self.parameters.add(params.ParameterRangeFloat(description ="o3 Stage small step size",
                                                       name = "o3_small_step",
                                                       value = configuration.get("small_step"),
                                                       min_value = 0.001,
                                                       max_value = 10.0))
        
        self.setEnabled(False)

    def getParameters(self):
        return self.parameters

    def handleDownLButton(self, boolean):
        self.o3_stage_fn.goRelative(-1.0*self.parameters.get("o3_large_step"))

    def handleDownSButton(self, boolean):
        self.o3_stage_fn.goRelative(-1.0*self.parameters.get("o3_small_step"))

    def handleGoButton(self, boolean):
        self.o3_stage_fn.goAbsolute(self.ui.goSpinBox.value())
        
    def handleHomeButton(self, boolean):
        self.o3_stage_fn.goAbsolute(0.0)

    def handleRetractButton(self, boolean):
        self.o3_stage_fn.goAbsolute(self.retracted_o3)

    def handleUpLButton(self, boolean):
        self.o3_stage_fn.goRelative(self.parameters.get("o3_large_step"))

    def handleUpSButton(self, boolean):
        self.o3_stage_fn.goRelative(self.parameters.get("o3_small_step"))        

    def handleZeroButton(self, boolean):
        self.o3_stage_fn.zero()

    def handleo3StagePosition(self, o3_value):
        self.ui.zPosLabel.setText("{0:.2f}".format(o3_value))
        

    def newParameters(self, parameters):
        self.parameters.setv("o3_large_step", parameters.get("o3_large_step"))
        self.parameters.setv("o3_small_step", parameters.get("o3_small_step"))

    def setFunctionality(self, o3_stage_fn):
        self.o3_stage_fn = o3_stage_fn
        self.o3_stage_fn.o3StagePosition.connect(self.handleo3StagePosition)
        self.setEnabled(True)


class o3Stage(halModule.HalModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.configuration = module_params.get("configuration")

        self.view = o3StageView(module_name = self.module_name,
                               configuration = module_params.get("configuration"))
        self.view.halDialogInit(qt_settings,
                                module_params.get("setup_name") + " o3 stage")

    def cleanUp(self, qt_settings):
        self.view.cleanUp(qt_settings)

    def handleResponse(self, message, response):
        if message.isType("get functionality"):
            self.view.setFunctionality(response.getData()["functionality"])

    def processMessage(self, message):

        if message.isType("configure1"):
            self.sendMessage(halMessage.HalMessage(m_type = "add to menu",
                                                   data = {"item name" : "o3 Stage",
                                                           "item data" : "o3 stage"}))

            self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                   data = {"name" : self.configuration.get("o3_stage_fn")}))

            self.sendMessage(halMessage.HalMessage(m_type = "initial parameters",
                                                   data = {"parameters" : self.view.getParameters()}))            

        elif message.isType("new parameters"):
            p = message.getData()["parameters"]
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"old parameters" : self.view.getParameters().copy()}))
            self.view.newParameters(p.get(self.module_name))
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"new parameters" : self.view.getParameters()}))

        elif message.isType("show"):
            if (message.getData()["show"] == "o3 stage"):
                self.view.show()

        elif message.isType("start"):
            if message.getData()["show_gui"]:
                self.view.showIfVisible()


