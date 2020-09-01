# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'settingsdialog.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_SettingsDialog(object):
    def setupUi(self, SettingsDialog):
        SettingsDialog.setObjectName("SettingsDialog")
        SettingsDialog.resize(426, 154)
        self.verticalLayout = QtWidgets.QVBoxLayout(SettingsDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label_2 = QtWidgets.QLabel(SettingsDialog)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.selectionColorButton = QgsColorButton(SettingsDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.selectionColorButton.sizePolicy().hasHeightForWidth())
        self.selectionColorButton.setSizePolicy(sizePolicy)
        self.selectionColorButton.setMinimumSize(QtCore.QSize(24, 20))
        self.selectionColorButton.setMaximumSize(QtCore.QSize(16777215, 20))
        self.selectionColorButton.setObjectName("selectionColorButton")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.selectionColorButton)
        self.activeLayerCheckBox = QtWidgets.QCheckBox(SettingsDialog)
        self.activeLayerCheckBox.setText("")
        self.activeLayerCheckBox.setChecked(True)
        self.activeLayerCheckBox.setObjectName("activeLayerCheckBox")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.activeLayerCheckBox)
        self.label = QtWidgets.QLabel(SettingsDialog)
        self.label.setObjectName("label")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label)
        self.label_3 = QtWidgets.QLabel(SettingsDialog)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_3)
        self.label_4 = QtWidgets.QLabel(SettingsDialog)
        self.label_4.setObjectName("label_4")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.label_4)
        self.replaceActionsCheckBox = QtWidgets.QCheckBox(SettingsDialog)
        self.replaceActionsCheckBox.setText("")
        self.replaceActionsCheckBox.setObjectName("replaceActionsCheckBox")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.replaceActionsCheckBox)
        self.showSettingsCheckBox = QtWidgets.QCheckBox(SettingsDialog)
        self.showSettingsCheckBox.setText("")
        self.showSettingsCheckBox.setChecked(True)
        self.showSettingsCheckBox.setObjectName("showSettingsCheckBox")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.showSettingsCheckBox)
        self.verticalLayout.addLayout(self.formLayout)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.okButton = QtWidgets.QPushButton(SettingsDialog)
        self.okButton.setObjectName("okButton")
        self.horizontalLayout.addWidget(self.okButton)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(SettingsDialog)
        self.okButton.clicked.connect(SettingsDialog.accept)
        QtCore.QMetaObject.connectSlotsByName(SettingsDialog)

    def retranslateUi(self, SettingsDialog):
        _translate = QtCore.QCoreApplication.translate
        SettingsDialog.setWindowTitle(_translate("SettingsDialog", "MultiLayer Select Settings"))
        self.label_2.setText(_translate("SettingsDialog", "Selection color"))
        self.label.setText(_translate("SettingsDialog", "Set active layer from selected feature"))
        self.label_3.setText(_translate("SettingsDialog", "Replace default selection actions (BETA)"))
        self.label_4.setText(_translate("SettingsDialog", "Display settings action on toolbar"))
        self.okButton.setText(_translate("SettingsDialog", "Ok"))

from qgscolorbutton import QgsColorButton
