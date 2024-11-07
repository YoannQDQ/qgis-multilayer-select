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
        SettingsDialog.resize(279, 359)
        self.verticalLayout = QtWidgets.QVBoxLayout(SettingsDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label_2 = QtWidgets.QLabel(SettingsDialog)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.selectionColorButton = QgsColorButton(SettingsDialog)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.selectionColorButton.sizePolicy().hasHeightForWidth()
        )
        self.selectionColorButton.setSizePolicy(sizePolicy)
        self.selectionColorButton.setMinimumSize(QtCore.QSize(60, 20))
        self.selectionColorButton.setMaximumSize(QtCore.QSize(16777215, 20))
        self.selectionColorButton.setObjectName("selectionColorButton")
        self.formLayout.setWidget(
            0, QtWidgets.QFormLayout.FieldRole, self.selectionColorButton
        )
        self.activeLayerCheckBox = QtWidgets.QCheckBox(SettingsDialog)
        self.activeLayerCheckBox.setText("")
        self.activeLayerCheckBox.setChecked(True)
        self.activeLayerCheckBox.setObjectName("activeLayerCheckBox")
        self.formLayout.setWidget(
            1, QtWidgets.QFormLayout.FieldRole, self.activeLayerCheckBox
        )
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
        self.formLayout.setWidget(
            2, QtWidgets.QFormLayout.FieldRole, self.replaceActionsCheckBox
        )
        self.showSettingsCheckBox = QtWidgets.QCheckBox(SettingsDialog)
        self.showSettingsCheckBox.setText("")
        self.showSettingsCheckBox.setChecked(True)
        self.showSettingsCheckBox.setObjectName("showSettingsCheckBox")
        self.formLayout.setWidget(
            3, QtWidgets.QFormLayout.FieldRole, self.showSettingsCheckBox
        )
        self.verticalLayout.addLayout(self.formLayout)
        self.groupBox = QtWidgets.QGroupBox(SettingsDialog)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.onlyVisibleCheckBox = QtWidgets.QCheckBox(self.groupBox)
        self.onlyVisibleCheckBox.setObjectName("onlyVisibleCheckBox")
        self.verticalLayout_2.addWidget(self.onlyVisibleCheckBox)
        self.includeActiveLayerCheckBox = QtWidgets.QCheckBox(self.groupBox)
        self.includeActiveLayerCheckBox.setObjectName("includeActiveLayerCheckBox")
        self.verticalLayout_2.addWidget(self.includeActiveLayerCheckBox)
        self.ignoreScaleCheckBox = QtWidgets.QCheckBox(self.groupBox)
        self.ignoreScaleCheckBox.setObjectName("ignoreScaleCheckBox")
        self.verticalLayout_2.addWidget(self.ignoreScaleCheckBox)
        self.view = QtWidgets.QListView(self.groupBox)
        self.view.setObjectName("view")
        self.verticalLayout_2.addWidget(self.view)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.includeButton = QtWidgets.QPushButton(self.groupBox)
        self.includeButton.setObjectName("includeButton")
        self.horizontalLayout_2.addWidget(self.includeButton)
        self.excludeButton = QtWidgets.QPushButton(self.groupBox)
        self.excludeButton.setObjectName("excludeButton")
        self.horizontalLayout_2.addWidget(self.excludeButton)
        spacerItem = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        self.horizontalLayout_2.addItem(spacerItem)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.verticalLayout.addWidget(self.groupBox)
        spacerItem1 = QtWidgets.QSpacerItem(
            20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
        )
        self.verticalLayout.addItem(spacerItem1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem2 = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        self.horizontalLayout.addItem(spacerItem2)
        self.okButton = QtWidgets.QPushButton(SettingsDialog)
        self.okButton.setObjectName("okButton")
        self.horizontalLayout.addWidget(self.okButton)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(SettingsDialog)
        self.okButton.clicked.connect(SettingsDialog.accept)
        QtCore.QMetaObject.connectSlotsByName(SettingsDialog)

    def retranslateUi(self, SettingsDialog):
        _translate = QtCore.QCoreApplication.translate
        SettingsDialog.setWindowTitle(
            _translate("SettingsDialog", "MultiLayer Select Settings")
        )
        self.label_2.setText(_translate("SettingsDialog", "Selection color"))
        self.label.setText(
            _translate("SettingsDialog", "Set active layer from selected feature")
        )
        self.label_3.setText(
            _translate("SettingsDialog", "Replace default selection actions (BETA)")
        )
        self.label_4.setText(
            _translate("SettingsDialog", "Display settings action on toolbar")
        )
        self.groupBox.setToolTip(
            _translate(
                "SettingsDialog",
                "Allow to define layers that will not be considered by the multiselection tools (i.e. vector basemaps)",
            )
        )
        self.groupBox.setTitle(_translate("SettingsDialog", "Included Layers"))
        self.onlyVisibleCheckBox.setToolTip(
            _translate(
                "SettingsDialog",
                "If checked, the active layer will be handled by the selection tools even if it is unchecked in the list below",
            )
        )
        self.onlyVisibleCheckBox.setText(
            _translate("SettingsDialog", "Exlude hidden layers")
        )
        self.includeActiveLayerCheckBox.setToolTip(
            _translate(
                "SettingsDialog",
                "If checked, the active layer will be handled by the selection tools even if it is unchecked in the list below",
            )
        )
        self.includeActiveLayerCheckBox.setText(
            _translate("SettingsDialog", "Always include active layer")
        )
        self.ignoreScaleCheckBox.setToolTip(
            _translate(
                "SettingsDialog",
                "If checked, the scale based visibility will be disabled by the selection tools",
            )
        )
        self.ignoreScaleCheckBox.setText(
            _translate("SettingsDialog", "Include hidden entities according to scale")
        )
        self.includeButton.setText(_translate("SettingsDialog", "Include All"))
        self.excludeButton.setText(_translate("SettingsDialog", "Exclude All"))
        self.okButton.setText(_translate("SettingsDialog", "Ok"))


from qgscolorbutton import QgsColorButton
