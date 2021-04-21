#!/usr/bin/env python
"""
The galvo voltage control UI

Aditya Venkatramani 04/21 --> Adapted from zStage.py
"""
import os

from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.sc_library.parameters as params

import storm_control.hal4000.halLib.halDialog as halDialog
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule

import storm_control.hal4000.qtdesigner.galvo1D_ui as galvoUi


class GalvoView(halDialog.HalDialog):
    """
    Manages the galvo1D GUI.
    """
    def __init__(self, configuration = None, **kwds):
        super().__init__(**kwds)
        self.parameters = params.StormXMLObject()
        self.galvo_fn = None

        # Load UI
        self.ui = galvoUi.Ui_Dialog()
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

        self.ui.zeroButton.clicked.connect(self.handleZeroButton)

        self.ui.goButton.clicked.connect(self.handleGoButton)
        
        # Set to minimum size & fix.
        self.adjustSize()
        self.setFixedSize(self.width(), self.height())

        # Add parameters.
        self.parameters.add(params.ParameterRangeFloat(description ="Galvo large step size",
                                                       name = "volt_large_step",
                                                       value = configuration.get("large_step"),
                                                       min_value = 0.0,
                                                       max_value = 1000.0))        
        self.parameters.add(params.ParameterRangeFloat(description ="Galvo small step size",
                                                       name = "volt_small_step",
                                                       value = configuration.get("small_step"),
                                                       min_value = 0.0,
                                                       max_value = 1000.0))
        
        self.setEnabled(False)

    def getParameters(self):
        return self.parameters

    def handleDownLButton(self, boolean):
        self.galvo_fn.goRelative(-1.0*self.parameters.get("volt_large_step"))

    def handleDownSButton(self, boolean):
        self.galvo_fn.goRelative(-1.0*self.parameters.get("volt_small_step"))

    def handleGoButton(self, boolean):
        self.galvo_fn.goAbsolute(self.ui.goSpinBox.value())
        

    def handleUpLButton(self, boolean):
        self.galvo_fn.goRelative(self.parameters.get("volt_large_step"))

    def handleUpSButton(self, boolean):
        self.galvo_fn.goRelative(self.parameters.get("volt_small_step"))        

    def handleZeroButton(self, boolean):
        self.galvo_fn.zero()

    def handleGalvoVoltage(self, volt):
        self.ui.galvoVoltLabel.setText("{0:.2f}".format(volt))
        
    def newParameters(self, parameters):
        self.parameters.setv("volt_large_step", parameters.get("volt_large_step"))
        self.parameters.setv("volt_small_step", parameters.get("volt_small_step"))

    def setFunctionality(self, galvo_fn):
        self.galvo_fn = galvo_fn
        self.galvo_fn.galvoVoltage.connect(self.handleGalvoVoltage)
        self.ui.goSpinBox.setMinimum(self.galvo_fn.getMinimum())
        self.ui.goSpinBox.setMaximum(self.galvo_fn.getMaximum())
        self.setEnabled(True)


class Galvo(halModule.HalModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.configuration = module_params.get("configuration")

        self.view = GalvoView(module_name = self.module_name,
                               configuration = module_params.get("configuration"))
        self.view.halDialogInit(qt_settings,
                                module_params.get("setup_name") + " galvo")

    def cleanUp(self, qt_settings):
        self.view.cleanUp(qt_settings)

    def handleResponse(self, message, response):
        if message.isType("get functionality"):
            self.view.setFunctionality(response.getData()["functionality"])

    def processMessage(self, message):

        if message.isType("configure1"):
            self.sendMessage(halMessage.HalMessage(m_type = "add to menu",
                                                   data = {"item name" : "Galvo",
                                                           "item data" : "galvoview"}))

            self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                   data = {"name" : self.configuration.get("galvo_fn")}))

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
            if (message.getData()["show"] == "galvoview"):
                self.view.show()

        elif message.isType("start"):
            if message.getData()["show_gui"]:
                self.view.showIfVisible()


