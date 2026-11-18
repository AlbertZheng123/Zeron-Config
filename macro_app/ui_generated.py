# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'macro_app.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame,
    QGroupBox, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMainWindow, QMenuBar, QPlainTextEdit,
    QPushButton, QRadioButton, QScrollArea, QSizePolicy,
    QStackedWidget, QStatusBar, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1176, 742)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.stackedWidget = QStackedWidget(self.centralwidget)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.stackedWidget.setGeometry(QRect(0, 0, 1221, 671))
        self.overlayPage = QWidget()
        self.overlayPage.setObjectName(u"overlayPage")
        self.overlayScrollArea = QScrollArea(self.overlayPage)
        self.overlayScrollArea.setObjectName(u"overlayScrollArea")
        self.overlayScrollArea.setGeometry(QRect(0, 0, 1470, 865))
        self.overlayScrollArea.setFrameShape(QFrame.NoFrame)
        self.overlayScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.overlayScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.overlayScrollArea.setWidgetResizable(False)
        self.overlayContent = QWidget()
        self.overlayContent.setObjectName(u"overlayContent")
        self.overlayContent.setGeometry(QRect(0, 0, 1468, 1320))
        self.overlayPageTitle = QLabel(self.overlayContent)
        self.overlayPageTitle.setObjectName(u"overlayPageTitle")
        self.overlayPageTitle.setGeometry(QRect(0, 12, 1470, 35))
        self.overlayPageTitle.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        self.overlaySubtitle = QLabel(self.overlayContent)
        self.overlaySubtitle.setObjectName(u"overlaySubtitle")
        self.overlaySubtitle.setGeometry(QRect(0, 44, 1470, 18))
        self.overlaySubtitle.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        self.overlayStatusLabel = QLabel(self.overlayContent)
        self.overlayStatusLabel.setObjectName(u"overlayStatusLabel")
        self.overlayStatusLabel.setGeometry(QRect(1300, 15, 150, 30))
        self.overlayStatusLabel.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.storyModeGroup = QGroupBox(self.overlayContent)
        self.storyModeGroup.setObjectName(u"storyModeGroup")
        self.storyModeGroup.setGeometry(QRect(26, 75, 455, 340))
        self.storyImageFrame = QFrame(self.storyModeGroup)
        self.storyImageFrame.setObjectName(u"storyImageFrame")
        self.storyImageFrame.setGeometry(QRect(0, 0, 455, 160))
        self.storyImageOverlay = QFrame(self.storyModeGroup)
        self.storyImageOverlay.setObjectName(u"storyImageOverlay")
        self.storyImageOverlay.setGeometry(QRect(0, 0, 455, 160))
        self.storyModeLabel = QLabel(self.storyModeGroup)
        self.storyModeLabel.setObjectName(u"storyModeLabel")
        self.storyModeLabel.setGeometry(QRect(14, 10, 80, 16))
        self.storyActiveLabel = QLabel(self.storyModeGroup)
        self.storyActiveLabel.setObjectName(u"storyActiveLabel")
        self.storyActiveLabel.setGeometry(QRect(360, 10, 80, 16))
        self.storyActiveLabel.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.storyMapLabel = QLabel(self.storyModeGroup)
        self.storyMapLabel.setObjectName(u"storyMapLabel")
        self.storyMapLabel.setGeometry(QRect(14, 180, 60, 14))
        self.storyMacroLabel = QLabel(self.storyModeGroup)
        self.storyMacroLabel.setObjectName(u"storyMacroLabel")
        self.storyMacroLabel.setGeometry(QRect(233, 180, 120, 14))
        self.storyMapCombo = QComboBox(self.storyModeGroup)
        self.storyMapCombo.setObjectName(u"storyMapCombo")
        self.storyMapCombo.setGeometry(QRect(14, 196, 209, 30))
        self.storyMacroCombo = QComboBox(self.storyModeGroup)
        self.storyMacroCombo.setObjectName(u"storyMacroCombo")
        self.storyMacroCombo.setGeometry(QRect(233, 196, 208, 30))
        self.storyRunsLabel = QLabel(self.storyModeGroup)
        self.storyRunsLabel.setObjectName(u"storyRunsLabel")
        self.storyRunsLabel.setGeometry(QRect(14, 240, 107, 40))
        self.storyRunsLabel.setTextFormat(Qt.RichText)
        self.storyTotalLabel = QLabel(self.storyModeGroup)
        self.storyTotalLabel.setObjectName(u"storyTotalLabel")
        self.storyTotalLabel.setGeometry(QRect(121, 240, 107, 40))
        self.storyTotalLabel.setTextFormat(Qt.RichText)
        self.storyTimeLabel = QLabel(self.storyModeGroup)
        self.storyTimeLabel.setObjectName(u"storyTimeLabel")
        self.storyTimeLabel.setGeometry(QRect(335, 240, 107, 40))
        self.storyTimeLabel.setTextFormat(Qt.RichText)
        self.storyCreateMacroButton = QPushButton(self.storyModeGroup)
        self.storyCreateMacroButton.setObjectName(u"storyCreateMacroButton")
        self.storyCreateMacroButton.setGeometry(QRect(14, 284, 209, 24))
        self.storyImportMacroButton = QPushButton(self.storyModeGroup)
        self.storyImportMacroButton.setObjectName(u"storyImportMacroButton")
        self.storyImportMacroButton.setGeometry(QRect(232, 284, 209, 24))
        self.storySelectMacroButton = QPushButton(self.storyModeGroup)
        self.storySelectMacroButton.setObjectName(u"storySelectMacroButton")
        self.storySelectMacroButton.setGeometry(QRect(14, 314, 427, 24))
        self.raidsModeGroup = QGroupBox(self.overlayContent)
        self.raidsModeGroup.setObjectName(u"raidsModeGroup")
        self.raidsModeGroup.setGeometry(QRect(507, 75, 455, 340))
        self.raidsImageFrame = QFrame(self.raidsModeGroup)
        self.raidsImageFrame.setObjectName(u"raidsImageFrame")
        self.raidsImageFrame.setGeometry(QRect(0, 0, 455, 160))
        self.raidsImageOverlay = QFrame(self.raidsModeGroup)
        self.raidsImageOverlay.setObjectName(u"raidsImageOverlay")
        self.raidsImageOverlay.setGeometry(QRect(0, 0, 455, 160))
        self.raidsModeLabel = QLabel(self.raidsModeGroup)
        self.raidsModeLabel.setObjectName(u"raidsModeLabel")
        self.raidsModeLabel.setGeometry(QRect(14, 10, 80, 16))
        self.raidsActiveLabel = QLabel(self.raidsModeGroup)
        self.raidsActiveLabel.setObjectName(u"raidsActiveLabel")
        self.raidsActiveLabel.setGeometry(QRect(360, 10, 80, 16))
        self.raidsActiveLabel.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.raidsMapLabel = QLabel(self.raidsModeGroup)
        self.raidsMapLabel.setObjectName(u"raidsMapLabel")
        self.raidsMapLabel.setGeometry(QRect(14, 180, 60, 14))
        self.raidsMacroLabel = QLabel(self.raidsModeGroup)
        self.raidsMacroLabel.setObjectName(u"raidsMacroLabel")
        self.raidsMacroLabel.setGeometry(QRect(233, 180, 120, 14))
        self.raidsMapCombo = QComboBox(self.raidsModeGroup)
        self.raidsMapCombo.setObjectName(u"raidsMapCombo")
        self.raidsMapCombo.setGeometry(QRect(14, 196, 209, 30))
        self.raidsMacroCombo = QComboBox(self.raidsModeGroup)
        self.raidsMacroCombo.setObjectName(u"raidsMacroCombo")
        self.raidsMacroCombo.setGeometry(QRect(233, 196, 208, 30))
        self.raidsRunsLabel = QLabel(self.raidsModeGroup)
        self.raidsRunsLabel.setObjectName(u"raidsRunsLabel")
        self.raidsRunsLabel.setGeometry(QRect(14, 240, 107, 40))
        self.raidsRunsLabel.setTextFormat(Qt.RichText)
        self.raidsTotalLabel = QLabel(self.raidsModeGroup)
        self.raidsTotalLabel.setObjectName(u"raidsTotalLabel")
        self.raidsTotalLabel.setGeometry(QRect(121, 240, 107, 40))
        self.raidsTotalLabel.setTextFormat(Qt.RichText)
        self.raidsTimeLabel = QLabel(self.raidsModeGroup)
        self.raidsTimeLabel.setObjectName(u"raidsTimeLabel")
        self.raidsTimeLabel.setGeometry(QRect(335, 240, 107, 40))
        self.raidsTimeLabel.setTextFormat(Qt.RichText)
        self.raidsCreateMacroButton = QPushButton(self.raidsModeGroup)
        self.raidsCreateMacroButton.setObjectName(u"raidsCreateMacroButton")
        self.raidsCreateMacroButton.setGeometry(QRect(14, 284, 209, 24))
        self.raidsImportMacroButton = QPushButton(self.raidsModeGroup)
        self.raidsImportMacroButton.setObjectName(u"raidsImportMacroButton")
        self.raidsImportMacroButton.setGeometry(QRect(232, 284, 209, 24))
        self.raidsSelectMacroButton = QPushButton(self.raidsModeGroup)
        self.raidsSelectMacroButton.setObjectName(u"raidsSelectMacroButton")
        self.raidsSelectMacroButton.setGeometry(QRect(14, 314, 427, 24))
        self.legendModeGroup = QGroupBox(self.overlayContent)
        self.legendModeGroup.setObjectName(u"legendModeGroup")
        self.legendModeGroup.setGeometry(QRect(988, 75, 455, 340))
        self.legendImageFrame = QFrame(self.legendModeGroup)
        self.legendImageFrame.setObjectName(u"legendImageFrame")
        self.legendImageFrame.setGeometry(QRect(0, 0, 455, 160))
        self.legendImageOverlay = QFrame(self.legendModeGroup)
        self.legendImageOverlay.setObjectName(u"legendImageOverlay")
        self.legendImageOverlay.setGeometry(QRect(0, 0, 455, 160))
        self.legendModeLabel = QLabel(self.legendModeGroup)
        self.legendModeLabel.setObjectName(u"legendModeLabel")
        self.legendModeLabel.setGeometry(QRect(14, 10, 120, 16))
        self.legendActiveLabel = QLabel(self.legendModeGroup)
        self.legendActiveLabel.setObjectName(u"legendActiveLabel")
        self.legendActiveLabel.setGeometry(QRect(360, 10, 80, 16))
        self.legendActiveLabel.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.legendMapLabel = QLabel(self.legendModeGroup)
        self.legendMapLabel.setObjectName(u"legendMapLabel")
        self.legendMapLabel.setGeometry(QRect(14, 180, 60, 14))
        self.legendMacroLabel = QLabel(self.legendModeGroup)
        self.legendMacroLabel.setObjectName(u"legendMacroLabel")
        self.legendMacroLabel.setGeometry(QRect(233, 180, 120, 14))
        self.legendMapCombo = QComboBox(self.legendModeGroup)
        self.legendMapCombo.setObjectName(u"legendMapCombo")
        self.legendMapCombo.setGeometry(QRect(14, 196, 209, 30))
        self.legendMacroCombo = QComboBox(self.legendModeGroup)
        self.legendMacroCombo.setObjectName(u"legendMacroCombo")
        self.legendMacroCombo.setGeometry(QRect(233, 196, 208, 30))
        self.legendRunsLabel = QLabel(self.legendModeGroup)
        self.legendRunsLabel.setObjectName(u"legendRunsLabel")
        self.legendRunsLabel.setGeometry(QRect(14, 240, 107, 40))
        self.legendRunsLabel.setTextFormat(Qt.RichText)
        self.legendTotalLabel = QLabel(self.legendModeGroup)
        self.legendTotalLabel.setObjectName(u"legendTotalLabel")
        self.legendTotalLabel.setGeometry(QRect(121, 240, 107, 40))
        self.legendTotalLabel.setTextFormat(Qt.RichText)
        self.legendTimeLabel = QLabel(self.legendModeGroup)
        self.legendTimeLabel.setObjectName(u"legendTimeLabel")
        self.legendTimeLabel.setGeometry(QRect(335, 240, 107, 40))
        self.legendTimeLabel.setTextFormat(Qt.RichText)
        self.legendCreateMacroButton = QPushButton(self.legendModeGroup)
        self.legendCreateMacroButton.setObjectName(u"legendCreateMacroButton")
        self.legendCreateMacroButton.setGeometry(QRect(14, 284, 209, 24))
        self.legendImportMacroButton = QPushButton(self.legendModeGroup)
        self.legendImportMacroButton.setObjectName(u"legendImportMacroButton")
        self.legendImportMacroButton.setGeometry(QRect(232, 284, 209, 24))
        self.legendSelectMacroButton = QPushButton(self.legendModeGroup)
        self.legendSelectMacroButton.setObjectName(u"legendSelectMacroButton")
        self.legendSelectMacroButton.setGeometry(QRect(14, 314, 427, 24))
        self.bossRushModeGroup = QGroupBox(self.overlayContent)
        self.bossRushModeGroup.setObjectName(u"bossRushModeGroup")
        self.bossRushModeGroup.setGeometry(QRect(26, 430, 455, 340))
        self.bossRushImageFrame = QFrame(self.bossRushModeGroup)
        self.bossRushImageFrame.setObjectName(u"bossRushImageFrame")
        self.bossRushImageFrame.setGeometry(QRect(0, 0, 455, 160))
        self.bossRushImageOverlay = QFrame(self.bossRushModeGroup)
        self.bossRushImageOverlay.setObjectName(u"bossRushImageOverlay")
        self.bossRushImageOverlay.setGeometry(QRect(0, 0, 455, 160))
        self.bossRushModeLabel = QLabel(self.bossRushModeGroup)
        self.bossRushModeLabel.setObjectName(u"bossRushModeLabel")
        self.bossRushModeLabel.setGeometry(QRect(14, 10, 100, 16))
        self.bossRushActiveLabel = QLabel(self.bossRushModeGroup)
        self.bossRushActiveLabel.setObjectName(u"bossRushActiveLabel")
        self.bossRushActiveLabel.setGeometry(QRect(360, 10, 80, 16))
        self.bossRushActiveLabel.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.bossRushMapLabel = QLabel(self.bossRushModeGroup)
        self.bossRushMapLabel.setObjectName(u"bossRushMapLabel")
        self.bossRushMapLabel.setGeometry(QRect(14, 180, 60, 14))
        self.bossRushMacroLabel = QLabel(self.bossRushModeGroup)
        self.bossRushMacroLabel.setObjectName(u"bossRushMacroLabel")
        self.bossRushMacroLabel.setGeometry(QRect(233, 180, 120, 14))
        self.bossRushMapCombo = QComboBox(self.bossRushModeGroup)
        self.bossRushMapCombo.setObjectName(u"bossRushMapCombo")
        self.bossRushMapCombo.setGeometry(QRect(14, 196, 209, 30))
        self.bossRushMacroCombo = QComboBox(self.bossRushModeGroup)
        self.bossRushMacroCombo.setObjectName(u"bossRushMacroCombo")
        self.bossRushMacroCombo.setGeometry(QRect(233, 196, 208, 30))
        self.bossRushRunsLabel = QLabel(self.bossRushModeGroup)
        self.bossRushRunsLabel.setObjectName(u"bossRushRunsLabel")
        self.bossRushRunsLabel.setGeometry(QRect(14, 240, 107, 40))
        self.bossRushRunsLabel.setTextFormat(Qt.RichText)
        self.bossRushTotalLabel = QLabel(self.bossRushModeGroup)
        self.bossRushTotalLabel.setObjectName(u"bossRushTotalLabel")
        self.bossRushTotalLabel.setGeometry(QRect(121, 240, 107, 40))
        self.bossRushTotalLabel.setTextFormat(Qt.RichText)
        self.bossRushTimeLabel = QLabel(self.bossRushModeGroup)
        self.bossRushTimeLabel.setObjectName(u"bossRushTimeLabel")
        self.bossRushTimeLabel.setGeometry(QRect(335, 240, 107, 40))
        self.bossRushTimeLabel.setTextFormat(Qt.RichText)
        self.bossRushCreateMacroButton = QPushButton(self.bossRushModeGroup)
        self.bossRushCreateMacroButton.setObjectName(u"bossRushCreateMacroButton")
        self.bossRushCreateMacroButton.setGeometry(QRect(14, 284, 209, 24))
        self.bossRushImportMacroButton = QPushButton(self.bossRushModeGroup)
        self.bossRushImportMacroButton.setObjectName(u"bossRushImportMacroButton")
        self.bossRushImportMacroButton.setGeometry(QRect(232, 284, 209, 24))
        self.bossRushSelectMacroButton = QPushButton(self.bossRushModeGroup)
        self.bossRushSelectMacroButton.setObjectName(u"bossRushSelectMacroButton")
        self.bossRushSelectMacroButton.setGeometry(QRect(14, 314, 427, 24))
        self.eventsModeGroup = QGroupBox(self.overlayContent)
        self.eventsModeGroup.setObjectName(u"eventsModeGroup")
        self.eventsModeGroup.setGeometry(QRect(507, 430, 455, 340))
        self.eventsImageFrame = QFrame(self.eventsModeGroup)
        self.eventsImageFrame.setObjectName(u"eventsImageFrame")
        self.eventsImageFrame.setGeometry(QRect(0, 0, 455, 160))
        self.eventsImageOverlay = QFrame(self.eventsModeGroup)
        self.eventsImageOverlay.setObjectName(u"eventsImageOverlay")
        self.eventsImageOverlay.setGeometry(QRect(0, 0, 455, 160))
        self.eventsModeLabel = QLabel(self.eventsModeGroup)
        self.eventsModeLabel.setObjectName(u"eventsModeLabel")
        self.eventsModeLabel.setGeometry(QRect(14, 10, 80, 16))
        self.eventsActiveLabel = QLabel(self.eventsModeGroup)
        self.eventsActiveLabel.setObjectName(u"eventsActiveLabel")
        self.eventsActiveLabel.setGeometry(QRect(360, 10, 80, 16))
        self.eventsActiveLabel.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.eventsMapLabel = QLabel(self.eventsModeGroup)
        self.eventsMapLabel.setObjectName(u"eventsMapLabel")
        self.eventsMapLabel.setGeometry(QRect(14, 180, 60, 14))
        self.eventsMacroLabel = QLabel(self.eventsModeGroup)
        self.eventsMacroLabel.setObjectName(u"eventsMacroLabel")
        self.eventsMacroLabel.setGeometry(QRect(233, 180, 120, 14))
        self.eventsMapCombo = QComboBox(self.eventsModeGroup)
        self.eventsMapCombo.setObjectName(u"eventsMapCombo")
        self.eventsMapCombo.setGeometry(QRect(14, 196, 209, 30))
        self.eventsMacroCombo = QComboBox(self.eventsModeGroup)
        self.eventsMacroCombo.setObjectName(u"eventsMacroCombo")
        self.eventsMacroCombo.setGeometry(QRect(233, 196, 208, 30))
        self.eventsRunsLabel = QLabel(self.eventsModeGroup)
        self.eventsRunsLabel.setObjectName(u"eventsRunsLabel")
        self.eventsRunsLabel.setGeometry(QRect(14, 240, 107, 40))
        self.eventsRunsLabel.setTextFormat(Qt.RichText)
        self.eventsTotalLabel = QLabel(self.eventsModeGroup)
        self.eventsTotalLabel.setObjectName(u"eventsTotalLabel")
        self.eventsTotalLabel.setGeometry(QRect(121, 240, 107, 40))
        self.eventsTotalLabel.setTextFormat(Qt.RichText)
        self.eventsTimeLabel = QLabel(self.eventsModeGroup)
        self.eventsTimeLabel.setObjectName(u"eventsTimeLabel")
        self.eventsTimeLabel.setGeometry(QRect(335, 240, 107, 40))
        self.eventsTimeLabel.setTextFormat(Qt.RichText)
        self.eventsCreateMacroButton = QPushButton(self.eventsModeGroup)
        self.eventsCreateMacroButton.setObjectName(u"eventsCreateMacroButton")
        self.eventsCreateMacroButton.setGeometry(QRect(14, 284, 209, 24))
        self.eventsImportMacroButton = QPushButton(self.eventsModeGroup)
        self.eventsImportMacroButton.setObjectName(u"eventsImportMacroButton")
        self.eventsImportMacroButton.setGeometry(QRect(232, 284, 209, 24))
        self.eventsSelectMacroButton = QPushButton(self.eventsModeGroup)
        self.eventsSelectMacroButton.setObjectName(u"eventsSelectMacroButton")
        self.eventsSelectMacroButton.setGeometry(QRect(14, 314, 427, 24))
        self.dungeonModeGroup = QGroupBox(self.overlayContent)
        self.dungeonModeGroup.setObjectName(u"dungeonModeGroup")
        self.dungeonModeGroup.setGeometry(QRect(988, 430, 455, 340))
        self.dungeonImageFrame = QFrame(self.dungeonModeGroup)
        self.dungeonImageFrame.setObjectName(u"dungeonImageFrame")
        self.dungeonImageFrame.setGeometry(QRect(0, 0, 455, 160))
        self.dungeonImageOverlay = QFrame(self.dungeonModeGroup)
        self.dungeonImageOverlay.setObjectName(u"dungeonImageOverlay")
        self.dungeonImageOverlay.setGeometry(QRect(0, 0, 455, 160))
        self.dungeonModeLabel = QLabel(self.dungeonModeGroup)
        self.dungeonModeLabel.setObjectName(u"dungeonModeLabel")
        self.dungeonModeLabel.setGeometry(QRect(14, 10, 100, 16))
        self.dungeonActiveLabel = QLabel(self.dungeonModeGroup)
        self.dungeonActiveLabel.setObjectName(u"dungeonActiveLabel")
        self.dungeonActiveLabel.setGeometry(QRect(360, 10, 80, 16))
        self.dungeonActiveLabel.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.dungeonMapLabel = QLabel(self.dungeonModeGroup)
        self.dungeonMapLabel.setObjectName(u"dungeonMapLabel")
        self.dungeonMapLabel.setGeometry(QRect(14, 180, 60, 14))
        self.dungeonMacroLabel = QLabel(self.dungeonModeGroup)
        self.dungeonMacroLabel.setObjectName(u"dungeonMacroLabel")
        self.dungeonMacroLabel.setGeometry(QRect(233, 180, 120, 14))
        self.dungeonMapCombo = QComboBox(self.dungeonModeGroup)
        self.dungeonMapCombo.setObjectName(u"dungeonMapCombo")
        self.dungeonMapCombo.setGeometry(QRect(14, 196, 209, 30))
        self.dungeonMacroCombo = QComboBox(self.dungeonModeGroup)
        self.dungeonMacroCombo.setObjectName(u"dungeonMacroCombo")
        self.dungeonMacroCombo.setGeometry(QRect(233, 196, 208, 30))
        self.dungeonRunsLabel = QLabel(self.dungeonModeGroup)
        self.dungeonRunsLabel.setObjectName(u"dungeonRunsLabel")
        self.dungeonRunsLabel.setGeometry(QRect(14, 240, 107, 40))
        self.dungeonRunsLabel.setTextFormat(Qt.RichText)
        self.dungeonTotalLabel = QLabel(self.dungeonModeGroup)
        self.dungeonTotalLabel.setObjectName(u"dungeonTotalLabel")
        self.dungeonTotalLabel.setGeometry(QRect(121, 240, 107, 40))
        self.dungeonTotalLabel.setTextFormat(Qt.RichText)
        self.dungeonTimeLabel = QLabel(self.dungeonModeGroup)
        self.dungeonTimeLabel.setObjectName(u"dungeonTimeLabel")
        self.dungeonTimeLabel.setGeometry(QRect(335, 240, 107, 40))
        self.dungeonTimeLabel.setTextFormat(Qt.RichText)
        self.dungeonCreateMacroButton = QPushButton(self.dungeonModeGroup)
        self.dungeonCreateMacroButton.setObjectName(u"dungeonCreateMacroButton")
        self.dungeonCreateMacroButton.setGeometry(QRect(14, 284, 209, 24))
        self.dungeonImportMacroButton = QPushButton(self.dungeonModeGroup)
        self.dungeonImportMacroButton.setObjectName(u"dungeonImportMacroButton")
        self.dungeonImportMacroButton.setGeometry(QRect(232, 284, 209, 24))
        self.dungeonSelectMacroButton = QPushButton(self.dungeonModeGroup)
        self.dungeonSelectMacroButton.setObjectName(u"dungeonSelectMacroButton")
        self.dungeonSelectMacroButton.setGeometry(QRect(14, 314, 427, 24))
        self.overlayWebhookGroup = QGroupBox(self.overlayContent)
        self.overlayWebhookGroup.setObjectName(u"overlayWebhookGroup")
        self.overlayWebhookGroup.setGeometry(QRect(26, 785, 1418, 55))
        self.overlayWebhookLabel = QLabel(self.overlayWebhookGroup)
        self.overlayWebhookLabel.setObjectName(u"overlayWebhookLabel")
        self.overlayWebhookLabel.setGeometry(QRect(14, 14, 90, 26))
        self.overlayWebhookLabel.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.overlayWebhookToggleButton = QPushButton(self.overlayWebhookGroup)
        self.overlayWebhookToggleButton.setObjectName(u"overlayWebhookToggleButton")
        self.overlayWebhookToggleButton.setGeometry(QRect(110, 14, 80, 26))
        self.overlayWebhookUrlInput = QLineEdit(self.overlayWebhookGroup)
        self.overlayWebhookUrlInput.setObjectName(u"overlayWebhookUrlInput")
        self.overlayWebhookUrlInput.setGeometry(QRect(200, 14, 1100, 26))
        self.overlayWebhookTestButton = QPushButton(self.overlayWebhookGroup)
        self.overlayWebhookTestButton.setObjectName(u"overlayWebhookTestButton")
        self.overlayWebhookTestButton.setGeometry(QRect(1310, 14, 96, 26))
        self.overlayScrollArea.setWidget(self.overlayContent)
        self.stackedWidget.addWidget(self.overlayPage)
        self.page = QWidget()
        self.page.setObjectName(u"page")
        self.mainPageTitle = QLabel(self.page)
        self.mainPageTitle.setObjectName(u"mainPageTitle")
        self.mainPageTitle.setGeometry(QRect(50, 10, 200, 30))
        font = QFont()
        font.setBold(True)
        self.mainPageTitle.setFont(font)
        self.mainStatusLabel = QLabel(self.page)
        self.mainStatusLabel.setObjectName(u"mainStatusLabel")
        self.mainStatusLabel.setGeometry(QRect(580, 10, 160, 30))
        self.mainStatusLabel.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.macroList = QListWidget(self.page)
        self.macroList.setObjectName(u"macroList")
        self.macroList.setGeometry(QRect(50, 50, 300, 400))
        self.stopMacroButton = QPushButton(self.page)
        self.stopMacroButton.setObjectName(u"stopMacroButton")
        self.stopMacroButton.setGeometry(QRect(500, 420, 180, 50))
        self.advancedCreateButton = QPushButton(self.page)
        self.advancedCreateButton.setObjectName(u"advancedCreateButton")
        self.advancedCreateButton.setGeometry(QRect(500, 50, 180, 40))
        self.editAdvancedButton = QPushButton(self.page)
        self.editAdvancedButton.setObjectName(u"editAdvancedButton")
        self.editAdvancedButton.setGeometry(QRect(500, 100, 180, 40))
        self.webhookGroup = QGroupBox(self.page)
        self.webhookGroup.setObjectName(u"webhookGroup")
        self.webhookGroup.setGeometry(QRect(50, 470, 630, 70))
        self.webhookToggleButton = QPushButton(self.webhookGroup)
        self.webhookToggleButton.setObjectName(u"webhookToggleButton")
        self.webhookToggleButton.setGeometry(QRect(10, 28, 100, 30))
        self.webhookUrlInput = QLineEdit(self.webhookGroup)
        self.webhookUrlInput.setObjectName(u"webhookUrlInput")
        self.webhookUrlInput.setGeometry(QRect(120, 28, 420, 30))
        self.webhookTestButton = QPushButton(self.webhookGroup)
        self.webhookTestButton.setObjectName(u"webhookTestButton")
        self.webhookTestButton.setGeometry(QRect(550, 28, 70, 30))
        self.stackedWidget.addWidget(self.page)
        self.advancedCreatePage = QWidget()
        self.advancedCreatePage.setObjectName(u"advancedCreatePage")
        self.rightPanelBackground = QFrame(self.advancedCreatePage)
        self.rightPanelBackground.setObjectName(u"rightPanelBackground")
        self.rightPanelBackground.setGeometry(QRect(1200, 0, 270, 630))
        self.rightPanelBackground.setFrameShape(QFrame.NoFrame)
        self.advTrafficLightBar = QWidget(self.advancedCreatePage)
        self.advTrafficLightBar.setObjectName(u"advTrafficLightBar")
        self.advTrafficLightBar.setGeometry(QRect(1200, 0, 68, 25))
        self.advancedStepsLabel = QLabel(self.advancedCreatePage)
        self.advancedStepsLabel.setObjectName(u"advancedStepsLabel")
        self.advancedStepsLabel.setGeometry(QRect(1200, 0, 249, 35))
        self.advancedStepsLabel.setAlignment(Qt.AlignCenter)
        self.advCloseButton = QPushButton(self.advancedCreatePage)
        self.advCloseButton.setObjectName(u"advCloseButton")
        self.advCloseButton.setGeometry(QRect(1452, 11, 13, 13))
        self.advancedStepsScrollArea = QScrollArea(self.advancedCreatePage)
        self.advancedStepsScrollArea.setObjectName(u"advancedStepsScrollArea")
        self.advancedStepsScrollArea.setGeometry(QRect(1200, 35, 269, 510))
        self.advancedStepsScrollArea.setWidgetResizable(True)
        self.advancedStepsScrollContent = QWidget()
        self.advancedStepsScrollContent.setObjectName(u"advancedStepsScrollContent")
        self.advancedStepsScrollContent.setGeometry(QRect(0, 0, 267, 558))
        self.advancedStepsScrollArea.setWidget(self.advancedStepsScrollContent)
        self.tabContentBackground = QWidget(self.advancedCreatePage)
        self.tabContentBackground.setObjectName(u"tabContentBackground")
        self.tabContentBackground.setGeometry(QRect(0, 628, 820, 242))
        self.unitSelectionGroup = QGroupBox(self.advancedCreatePage)
        self.unitSelectionGroup.setObjectName(u"unitSelectionGroup")
        self.unitSelectionGroup.setGeometry(QRect(10, 668, 788, 160))
        self.unitSelectionHeaderLabel = QLabel(self.unitSelectionGroup)
        self.unitSelectionHeaderLabel.setObjectName(u"unitSelectionHeaderLabel")
        self.unitSelectionHeaderLabel.setGeometry(QRect(0, 0, 788, 30))
        self.unit1Group = QGroupBox(self.unitSelectionGroup)
        self.unit1Group.setObjectName(u"unit1Group")
        self.unit1Group.setGeometry(QRect(15, 38, 245, 52))
        self.unit1HeaderLabel = QLabel(self.unit1Group)
        self.unit1HeaderLabel.setObjectName(u"unit1HeaderLabel")
        self.unit1HeaderLabel.setGeometry(QRect(0, 5, 55, 22))
        self.unit1HeaderLabel.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.unit1NameInput = QLineEdit(self.unit1Group)
        self.unit1NameInput.setObjectName(u"unit1NameInput")
        self.unit1NameInput.setGeometry(QRect(55, 3, 185, 26))
        self.unit1NameInput.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.unit1CoordsLabel = QLabel(self.unit1Group)
        self.unit1CoordsLabel.setObjectName(u"unit1CoordsLabel")
        self.unit1CoordsLabel.setGeometry(QRect(55, 32, 150, 16))
        self.unit1CoordsLabel.setStyleSheet(u"color: #555555; font-family: \"Menlo\", \"SF Mono\", monospace; font-size: 10px; font-weight: 500; background-color: transparent;")
        self.unit1CoordsLabel.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.unit1SavedLabel = QLabel(self.unit1Group)
        self.unit1SavedLabel.setObjectName(u"unit1SavedLabel")
        self.unit1SavedLabel.setGeometry(QRect(180, 32, 50, 16))
        self.unit1SavedLabel.setStyleSheet(u"color: #22C55E; font-size: 9px; background-color: transparent;")
        self.unit2Group = QGroupBox(self.unitSelectionGroup)
        self.unit2Group.setObjectName(u"unit2Group")
        self.unit2Group.setGeometry(QRect(270, 38, 245, 52))
        self.unit2HeaderLabel = QLabel(self.unit2Group)
        self.unit2HeaderLabel.setObjectName(u"unit2HeaderLabel")
        self.unit2HeaderLabel.setGeometry(QRect(0, 5, 55, 22))
        self.unit2HeaderLabel.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.unit2NameInput = QLineEdit(self.unit2Group)
        self.unit2NameInput.setObjectName(u"unit2NameInput")
        self.unit2NameInput.setGeometry(QRect(55, 3, 185, 26))
        self.unit2NameInput.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.unit2CoordsLabel = QLabel(self.unit2Group)
        self.unit2CoordsLabel.setObjectName(u"unit2CoordsLabel")
        self.unit2CoordsLabel.setGeometry(QRect(55, 32, 150, 16))
        self.unit2CoordsLabel.setStyleSheet(u"color: #555555; font-family: \"Menlo\", \"SF Mono\", monospace; font-size: 10px; font-weight: 500; background-color: transparent;")
        self.unit2CoordsLabel.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.unit2SavedLabel = QLabel(self.unit2Group)
        self.unit2SavedLabel.setObjectName(u"unit2SavedLabel")
        self.unit2SavedLabel.setGeometry(QRect(180, 32, 50, 16))
        self.unit2SavedLabel.setStyleSheet(u"color: #22C55E; font-size: 9px; background-color: transparent;")
        self.unit3Group = QGroupBox(self.unitSelectionGroup)
        self.unit3Group.setObjectName(u"unit3Group")
        self.unit3Group.setGeometry(QRect(525, 38, 245, 52))
        self.unit3HeaderLabel = QLabel(self.unit3Group)
        self.unit3HeaderLabel.setObjectName(u"unit3HeaderLabel")
        self.unit3HeaderLabel.setGeometry(QRect(0, 5, 55, 22))
        self.unit3HeaderLabel.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.unit3NameInput = QLineEdit(self.unit3Group)
        self.unit3NameInput.setObjectName(u"unit3NameInput")
        self.unit3NameInput.setGeometry(QRect(55, 3, 185, 26))
        self.unit3NameInput.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.unit3CoordsLabel = QLabel(self.unit3Group)
        self.unit3CoordsLabel.setObjectName(u"unit3CoordsLabel")
        self.unit3CoordsLabel.setGeometry(QRect(55, 32, 150, 16))
        self.unit3CoordsLabel.setStyleSheet(u"color: #555555; font-family: \"Menlo\", \"SF Mono\", monospace; font-size: 10px; font-weight: 500; background-color: transparent;")
        self.unit3CoordsLabel.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.unit3SavedLabel = QLabel(self.unit3Group)
        self.unit3SavedLabel.setObjectName(u"unit3SavedLabel")
        self.unit3SavedLabel.setGeometry(QRect(180, 32, 50, 16))
        self.unit3SavedLabel.setStyleSheet(u"color: #22C55E; font-size: 9px; background-color: transparent;")
        self.unit4Group = QGroupBox(self.unitSelectionGroup)
        self.unit4Group.setObjectName(u"unit4Group")
        self.unit4Group.setGeometry(QRect(15, 98, 245, 52))
        self.unit4HeaderLabel = QLabel(self.unit4Group)
        self.unit4HeaderLabel.setObjectName(u"unit4HeaderLabel")
        self.unit4HeaderLabel.setGeometry(QRect(0, 5, 55, 22))
        self.unit4HeaderLabel.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.unit4NameInput = QLineEdit(self.unit4Group)
        self.unit4NameInput.setObjectName(u"unit4NameInput")
        self.unit4NameInput.setGeometry(QRect(55, 3, 185, 26))
        self.unit4NameInput.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.unit4CoordsLabel = QLabel(self.unit4Group)
        self.unit4CoordsLabel.setObjectName(u"unit4CoordsLabel")
        self.unit4CoordsLabel.setGeometry(QRect(55, 32, 150, 16))
        self.unit4CoordsLabel.setStyleSheet(u"color: #555555; font-family: \"Menlo\", \"SF Mono\", monospace; font-size: 10px; font-weight: 500; background-color: transparent;")
        self.unit4CoordsLabel.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.unit4SavedLabel = QLabel(self.unit4Group)
        self.unit4SavedLabel.setObjectName(u"unit4SavedLabel")
        self.unit4SavedLabel.setGeometry(QRect(180, 32, 50, 16))
        self.unit4SavedLabel.setStyleSheet(u"color: #22C55E; font-size: 9px; background-color: transparent;")
        self.unit5Group = QGroupBox(self.unitSelectionGroup)
        self.unit5Group.setObjectName(u"unit5Group")
        self.unit5Group.setGeometry(QRect(270, 98, 245, 52))
        self.unit5HeaderLabel = QLabel(self.unit5Group)
        self.unit5HeaderLabel.setObjectName(u"unit5HeaderLabel")
        self.unit5HeaderLabel.setGeometry(QRect(0, 5, 55, 22))
        self.unit5HeaderLabel.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.unit5NameInput = QLineEdit(self.unit5Group)
        self.unit5NameInput.setObjectName(u"unit5NameInput")
        self.unit5NameInput.setGeometry(QRect(55, 3, 185, 26))
        self.unit5NameInput.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.unit5CoordsLabel = QLabel(self.unit5Group)
        self.unit5CoordsLabel.setObjectName(u"unit5CoordsLabel")
        self.unit5CoordsLabel.setGeometry(QRect(55, 32, 150, 16))
        self.unit5CoordsLabel.setStyleSheet(u"color: #555555; font-family: \"Menlo\", \"SF Mono\", monospace; font-size: 10px; font-weight: 500; background-color: transparent;")
        self.unit5CoordsLabel.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.unit5SavedLabel = QLabel(self.unit5Group)
        self.unit5SavedLabel.setObjectName(u"unit5SavedLabel")
        self.unit5SavedLabel.setGeometry(QRect(180, 32, 50, 16))
        self.unit5SavedLabel.setStyleSheet(u"color: #22C55E; font-size: 9px; background-color: transparent;")
        self.unit6Group = QGroupBox(self.unitSelectionGroup)
        self.unit6Group.setObjectName(u"unit6Group")
        self.unit6Group.setGeometry(QRect(525, 98, 245, 52))
        self.unit6HeaderLabel = QLabel(self.unit6Group)
        self.unit6HeaderLabel.setObjectName(u"unit6HeaderLabel")
        self.unit6HeaderLabel.setGeometry(QRect(0, 5, 55, 22))
        self.unit6HeaderLabel.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.unit6NameInput = QLineEdit(self.unit6Group)
        self.unit6NameInput.setObjectName(u"unit6NameInput")
        self.unit6NameInput.setGeometry(QRect(55, 3, 185, 26))
        self.unit6NameInput.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.unit6CoordsLabel = QLabel(self.unit6Group)
        self.unit6CoordsLabel.setObjectName(u"unit6CoordsLabel")
        self.unit6CoordsLabel.setGeometry(QRect(55, 32, 150, 16))
        self.unit6CoordsLabel.setStyleSheet(u"color: #555555; font-family: \"Menlo\", \"SF Mono\", monospace; font-size: 10px; font-weight: 500; background-color: transparent;")
        self.unit6CoordsLabel.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.unit6SavedLabel = QLabel(self.unit6Group)
        self.unit6SavedLabel.setObjectName(u"unit6SavedLabel")
        self.unit6SavedLabel.setGeometry(QRect(180, 32, 50, 16))
        self.unit6SavedLabel.setStyleSheet(u"color: #22C55E; font-size: 9px; background-color: transparent;")
        self.upgradeGroup = QGroupBox(self.advancedCreatePage)
        self.upgradeGroup.setObjectName(u"upgradeGroup")
        self.upgradeGroup.setGeometry(QRect(10, 668, 336, 152))
        self.upgradeHeaderLabel = QLabel(self.upgradeGroup)
        self.upgradeHeaderLabel.setObjectName(u"upgradeHeaderLabel")
        self.upgradeHeaderLabel.setGeometry(QRect(0, 0, 336, 30))
        self.upgradeUnitLabel = QLabel(self.upgradeGroup)
        self.upgradeUnitLabel.setObjectName(u"upgradeUnitLabel")
        self.upgradeUnitLabel.setGeometry(QRect(12, 38, 150, 12))
        self.upgradeUnitCombo = QComboBox(self.upgradeGroup)
        self.upgradeUnitCombo.setObjectName(u"upgradeUnitCombo")
        self.upgradeUnitCombo.setGeometry(QRect(12, 52, 150, 20))
        self.upgradePlacementLabel = QLabel(self.upgradeGroup)
        self.upgradePlacementLabel.setObjectName(u"upgradePlacementLabel")
        self.upgradePlacementLabel.setGeometry(QRect(168, 38, 155, 12))
        self.upgradePlacementCombo = QComboBox(self.upgradeGroup)
        self.upgradePlacementCombo.setObjectName(u"upgradePlacementCombo")
        self.upgradePlacementCombo.setGeometry(QRect(168, 52, 155, 20))
        self.upgradeCountLabel = QLabel(self.upgradeGroup)
        self.upgradeCountLabel.setObjectName(u"upgradeCountLabel")
        self.upgradeCountLabel.setGeometry(QRect(12, 78, 60, 12))
        self.upgradeCountInput = QLineEdit(self.upgradeGroup)
        self.upgradeCountInput.setObjectName(u"upgradeCountInput")
        self.upgradeCountInput.setGeometry(QRect(12, 90, 60, 20))
        self.autoUpgradeCheckBox = QCheckBox(self.upgradeGroup)
        self.autoUpgradeCheckBox.setObjectName(u"autoUpgradeCheckBox")
        self.autoUpgradeCheckBox.setGeometry(QRect(80, 92, 110, 16))
        self.upgradeNoPlacementsLabel = QLabel(self.upgradeGroup)
        self.upgradeNoPlacementsLabel.setObjectName(u"upgradeNoPlacementsLabel")
        self.upgradeNoPlacementsLabel.setGeometry(QRect(195, 92, 125, 16))
        self.addUpgradeStepButton = QPushButton(self.upgradeGroup)
        self.addUpgradeStepButton.setObjectName(u"addUpgradeStepButton")
        self.addUpgradeStepButton.setGeometry(QRect(12, 114, 312, 28))
        self.placeGroup = QGroupBox(self.advancedCreatePage)
        self.placeGroup.setObjectName(u"placeGroup")
        self.placeGroup.setGeometry(QRect(361, 668, 435, 152))
        self.placeHeaderLabel = QLabel(self.placeGroup)
        self.placeHeaderLabel.setObjectName(u"placeHeaderLabel")
        self.placeHeaderLabel.setGeometry(QRect(0, 0, 435, 30))
        self.placeUnitLabel = QLabel(self.placeGroup)
        self.placeUnitLabel.setObjectName(u"placeUnitLabel")
        self.placeUnitLabel.setGeometry(QRect(12, 38, 100, 12))
        self.placeUnitCombo = QComboBox(self.placeGroup)
        self.placeUnitCombo.setObjectName(u"placeUnitCombo")
        self.placeUnitCombo.setGeometry(QRect(12, 52, 100, 20))
        self.placementColHeaderLabel = QLabel(self.placeGroup)
        self.placementColHeaderLabel.setObjectName(u"placementColHeaderLabel")
        self.placementColHeaderLabel.setGeometry(QRect(118, 38, 90, 12))
        self.placementCounterLabel = QLabel(self.placeGroup)
        self.placementCounterLabel.setObjectName(u"placementCounterLabel")
        self.placementCounterLabel.setGeometry(QRect(118, 52, 90, 20))
        self.placementCounterLabel.setStyleSheet(u"color: #AAAAAA; font-family: \"Menlo\", \"SF Mono\", monospace; font-size: 14px; font-weight: 600; background-color: transparent; qproperty-alignment: AlignCenter;")
        self.placeXLabel = QLabel(self.placeGroup)
        self.placeXLabel.setObjectName(u"placeXLabel")
        self.placeXLabel.setGeometry(QRect(214, 38, 75, 12))
        self.placeXInput = QLineEdit(self.placeGroup)
        self.placeXInput.setObjectName(u"placeXInput")
        self.placeXInput.setGeometry(QRect(214, 52, 75, 20))
        self.placeYLabel = QLabel(self.placeGroup)
        self.placeYLabel.setObjectName(u"placeYLabel")
        self.placeYLabel.setGeometry(QRect(295, 38, 75, 12))
        self.placeYInput = QLineEdit(self.placeGroup)
        self.placeYInput.setObjectName(u"placeYInput")
        self.placeYInput.setGeometry(QRect(295, 52, 75, 20))
        self.placeUntilEmptyCheckbox = QCheckBox(self.placeGroup)
        self.placeUntilEmptyCheckbox.setObjectName(u"placeUntilEmptyCheckbox")
        self.placeUntilEmptyCheckbox.setGeometry(QRect(12, 84, 130, 16))
        self.addPlaceStepButton = QPushButton(self.placeGroup)
        self.addPlaceStepButton.setObjectName(u"addPlaceStepButton")
        self.addPlaceStepButton.setGeometry(QRect(12, 112, 197, 28))
        self.recordPlaceClickButton = QPushButton(self.placeGroup)
        self.recordPlaceClickButton.setObjectName(u"recordPlaceClickButton")
        self.recordPlaceClickButton.setGeometry(QRect(215, 112, 198, 28))
        self.advancedWaitGroup = QGroupBox(self.advancedCreatePage)
        self.advancedWaitGroup.setObjectName(u"advancedWaitGroup")
        self.advancedWaitGroup.setGeometry(QRect(10, 668, 500, 138))
        self.waitHeaderLabel = QLabel(self.advancedWaitGroup)
        self.waitHeaderLabel.setObjectName(u"waitHeaderLabel")
        self.waitHeaderLabel.setGeometry(QRect(0, 0, 500, 30))
        self.advancedWaitSecondsRadio = QRadioButton(self.advancedWaitGroup)
        self.advancedWaitSecondsRadio.setObjectName(u"advancedWaitSecondsRadio")
        self.advancedWaitSecondsRadio.setGeometry(QRect(12, 40, 120, 20))
        self.advancedWaitSecondsRadio.setChecked(True)
        self.advancedWaitSecondsInput = QLineEdit(self.advancedWaitGroup)
        self.advancedWaitSecondsInput.setObjectName(u"advancedWaitSecondsInput")
        self.advancedWaitSecondsInput.setGeometry(QRect(135, 40, 50, 20))
        self.advancedWaitSecondsLabel = QLabel(self.advancedWaitGroup)
        self.advancedWaitSecondsLabel.setObjectName(u"advancedWaitSecondsLabel")
        self.advancedWaitSecondsLabel.setGeometry(QRect(190, 42, 25, 16))
        self.advancedWaitSecondsLabel.setStyleSheet(u"font-family: \"Inter\", sans-serif; font-size: 10px; color: #555555; background-color: transparent;")
        self.advancedWaitRoundRadio = QRadioButton(self.advancedWaitGroup)
        self.advancedWaitRoundRadio.setObjectName(u"advancedWaitRoundRadio")
        self.advancedWaitRoundRadio.setGeometry(QRect(250, 40, 125, 20))
        self.advancedWaveLabel = QLabel(self.advancedWaitGroup)
        self.advancedWaveLabel.setObjectName(u"advancedWaveLabel")
        self.advancedWaveLabel.setGeometry(QRect(380, 42, 35, 16))
        self.advancedWaveLabel.setStyleSheet(u"font-family: \"Inter\", sans-serif; font-size: 10px; color: #555555; background-color: transparent;")
        self.advancedWaveInput = QLineEdit(self.advancedWaitGroup)
        self.advancedWaveInput.setObjectName(u"advancedWaveInput")
        self.advancedWaveInput.setGeometry(QRect(418, 40, 50, 20))
        self.advancedWaitYenRadio = QRadioButton(self.advancedWaitGroup)
        self.advancedWaitYenRadio.setObjectName(u"advancedWaitYenRadio")
        self.advancedWaitYenRadio.setGeometry(QRect(12, 70, 120, 20))
        self.advancedWaitYenInput = QLineEdit(self.advancedWaitGroup)
        self.advancedWaitYenInput.setObjectName(u"advancedWaitYenInput")
        self.advancedWaitYenInput.setGeometry(QRect(135, 70, 50, 20))
        self.advancedWaitGameRadio = QRadioButton(self.advancedWaitGroup)
        self.advancedWaitGameRadio.setObjectName(u"advancedWaitGameRadio")
        self.advancedWaitGameRadio.setGeometry(QRect(250, 70, 160, 20))
        self.addAdvancedWaitButton = QPushButton(self.advancedWaitGroup)
        self.addAdvancedWaitButton.setObjectName(u"addAdvancedWaitButton")
        self.addAdvancedWaitButton.setGeometry(QRect(12, 100, 476, 28))
        self.advancedSaveButton = QPushButton(self.advancedCreatePage)
        self.advancedSaveButton.setObjectName(u"advancedSaveButton")
        self.advancedSaveButton.setGeometry(QRect(1207, 550, 255, 36))
        self.advancedClearButton = QPushButton(self.advancedCreatePage)
        self.advancedClearButton.setObjectName(u"advancedClearButton")
        self.advancedClearButton.setGeometry(QRect(1207, 592, 123, 30))
        self.advBackButton = QPushButton(self.advancedCreatePage)
        self.advBackButton.setObjectName(u"advBackButton")
        self.advBackButton.setGeometry(QRect(1338, 592, 124, 30))
        self.tabUnitsButton = QPushButton(self.advancedCreatePage)
        self.tabUnitsButton.setObjectName(u"tabUnitsButton")
        self.tabUnitsButton.setGeometry(QRect(0, 630, 164, 28))
        self.tabPlaceUpgradeButton = QPushButton(self.advancedCreatePage)
        self.tabPlaceUpgradeButton.setObjectName(u"tabPlaceUpgradeButton")
        self.tabPlaceUpgradeButton.setGeometry(QRect(164, 630, 164, 28))
        self.tabWaitButton = QPushButton(self.advancedCreatePage)
        self.tabWaitButton.setObjectName(u"tabWaitButton")
        self.tabWaitButton.setGeometry(QRect(328, 630, 164, 28))
        self.tabRawStepsButton = QPushButton(self.advancedCreatePage)
        self.tabRawStepsButton.setObjectName(u"tabRawStepsButton")
        self.tabRawStepsButton.setGeometry(QRect(492, 630, 164, 28))
        self.tabSettingsButton = QPushButton(self.advancedCreatePage)
        self.tabSettingsButton.setObjectName(u"tabSettingsButton")
        self.tabSettingsButton.setGeometry(QRect(656, 630, 164, 28))
        self.runStopBackground = QFrame(self.advancedCreatePage)
        self.runStopBackground.setObjectName(u"runStopBackground")
        self.runStopBackground.setGeometry(QRect(820, 630, 380, 204))
        self.runStopBackground.setFrameShape(QFrame.NoFrame)
        self.advRunMacroButton = QPushButton(self.advancedCreatePage)
        self.advRunMacroButton.setObjectName(u"advRunMacroButton")
        self.advRunMacroButton.setGeometry(QRect(828, 639, 176, 34))
        self.advStopMacroButton = QPushButton(self.advancedCreatePage)
        self.advStopMacroButton.setObjectName(u"advStopMacroButton")
        self.advStopMacroButton.setGeometry(QRect(1012, 639, 180, 34))
        self.advLogTextArea = QPlainTextEdit(self.advancedCreatePage)
        self.advLogTextArea.setObjectName(u"advLogTextArea")
        self.advLogTextArea.setGeometry(QRect(828, 679, 364, 151))
        self.advLogTextArea.setReadOnly(True)
        self.reservedBottomRight = QFrame(self.advancedCreatePage)
        self.reservedBottomRight.setObjectName(u"reservedBottomRight")
        self.reservedBottomRight.setGeometry(QRect(1200, 630, 270, 230))
        self.reservedBottomRight.setFrameShape(QFrame.NoFrame)
        self.advancedClickGroup = QGroupBox(self.advancedCreatePage)
        self.advancedClickGroup.setObjectName(u"advancedClickGroup")
        self.advancedClickGroup.setGeometry(QRect(10, 668, 390, 152))
        self.advancedClickGroup.setVisible(False)
        self.clickHeaderLabel = QLabel(self.advancedClickGroup)
        self.clickHeaderLabel.setObjectName(u"clickHeaderLabel")
        self.clickHeaderLabel.setGeometry(QRect(0, 0, 390, 30))
        self.advClickXLabel = QLabel(self.advancedClickGroup)
        self.advClickXLabel.setObjectName(u"advClickXLabel")
        self.advClickXLabel.setGeometry(QRect(12, 38, 14, 14))
        self.advClickXLabel.setStyleSheet(u"color: #555555; font-family: \"Inter\", sans-serif; font-size: 9px; font-weight: 700; letter-spacing: 1; background-color: transparent;")
        self.advClickXInput = QLineEdit(self.advancedClickGroup)
        self.advClickXInput.setObjectName(u"advClickXInput")
        self.advClickXInput.setGeometry(QRect(12, 54, 180, 24))
        self.advClickYLabel = QLabel(self.advancedClickGroup)
        self.advClickYLabel.setObjectName(u"advClickYLabel")
        self.advClickYLabel.setGeometry(QRect(200, 38, 14, 14))
        self.advClickYLabel.setStyleSheet(u"color: #555555; font-family: \"Inter\", sans-serif; font-size: 9px; font-weight: 700; letter-spacing: 1; background-color: transparent;")
        self.advClickYInput = QLineEdit(self.advancedClickGroup)
        self.advClickYInput.setObjectName(u"advClickYInput")
        self.advClickYInput.setGeometry(QRect(200, 54, 178, 24))
        self.advRecordClickButton = QPushButton(self.advancedClickGroup)
        self.advRecordClickButton.setObjectName(u"advRecordClickButton")
        self.advRecordClickButton.setGeometry(QRect(12, 90, 180, 28))
        self.addAdvancedClickButton = QPushButton(self.advancedClickGroup)
        self.addAdvancedClickButton.setObjectName(u"addAdvancedClickButton")
        self.addAdvancedClickButton.setGeometry(QRect(200, 90, 178, 28))
        self.advancedKeyGroup = QGroupBox(self.advancedCreatePage)
        self.advancedKeyGroup.setObjectName(u"advancedKeyGroup")
        self.advancedKeyGroup.setGeometry(QRect(410, 668, 390, 152))
        self.advancedKeyGroup.setVisible(False)
        self.keyHeaderLabel = QLabel(self.advancedKeyGroup)
        self.keyHeaderLabel.setObjectName(u"keyHeaderLabel")
        self.keyHeaderLabel.setGeometry(QRect(0, 0, 390, 30))
        self.advKeyPressRadio = QRadioButton(self.advancedKeyGroup)
        self.advKeyPressRadio.setObjectName(u"advKeyPressRadio")
        self.advKeyPressRadio.setGeometry(QRect(12, 46, 90, 20))
        self.advKeyPressRadio.setChecked(True)
        self.advKeyTimesLabel = QLabel(self.advancedKeyGroup)
        self.advKeyTimesLabel.setObjectName(u"advKeyTimesLabel")
        self.advKeyTimesLabel.setGeometry(QRect(200, 34, 40, 12))
        self.advKeyTimesLabel.setStyleSheet(u"color: #555555; font-family: \"Inter\", sans-serif; font-size: 9px; font-weight: 700; letter-spacing: 1; background-color: transparent;")
        self.advKeyTimesInput = QLineEdit(self.advancedKeyGroup)
        self.advKeyTimesInput.setObjectName(u"advKeyTimesInput")
        self.advKeyTimesInput.setGeometry(QRect(200, 46, 80, 20))
        self.advKeyPressKeyLabel = QLabel(self.advancedKeyGroup)
        self.advKeyPressKeyLabel.setObjectName(u"advKeyPressKeyLabel")
        self.advKeyPressKeyLabel.setGeometry(QRect(295, 34, 28, 12))
        self.advKeyPressKeyLabel.setStyleSheet(u"color: #555555; font-family: \"Inter\", sans-serif; font-size: 9px; font-weight: 700; letter-spacing: 1; background-color: transparent;")
        self.advKeyInput = QLineEdit(self.advancedKeyGroup)
        self.advKeyInput.setObjectName(u"advKeyInput")
        self.advKeyInput.setGeometry(QRect(295, 46, 80, 20))
        self.advKeyHoldRadio = QRadioButton(self.advancedKeyGroup)
        self.advKeyHoldRadio.setObjectName(u"advKeyHoldRadio")
        self.advKeyHoldRadio.setGeometry(QRect(12, 82, 100, 20))
        self.advKeyHoldSecLabel = QLabel(self.advancedKeyGroup)
        self.advKeyHoldSecLabel.setObjectName(u"advKeyHoldSecLabel")
        self.advKeyHoldSecLabel.setGeometry(QRect(200, 70, 28, 12))
        self.advKeyHoldSecLabel.setStyleSheet(u"color: #555555; font-family: \"Inter\", sans-serif; font-size: 9px; font-weight: 700; letter-spacing: 1; background-color: transparent;")
        self.advKeyHoldInput = QLineEdit(self.advancedKeyGroup)
        self.advKeyHoldInput.setObjectName(u"advKeyHoldInput")
        self.advKeyHoldInput.setGeometry(QRect(200, 82, 80, 20))
        self.advKeyHoldKeyLabel = QLabel(self.advancedKeyGroup)
        self.advKeyHoldKeyLabel.setObjectName(u"advKeyHoldKeyLabel")
        self.advKeyHoldKeyLabel.setGeometry(QRect(295, 70, 28, 12))
        self.advKeyHoldKeyLabel.setStyleSheet(u"color: #555555; font-family: \"Inter\", sans-serif; font-size: 9px; font-weight: 700; letter-spacing: 1; background-color: transparent;")
        self.advKeyHoldKeyInput = QLineEdit(self.advancedKeyGroup)
        self.advKeyHoldKeyInput.setObjectName(u"advKeyHoldKeyInput")
        self.advKeyHoldKeyInput.setGeometry(QRect(295, 82, 80, 20))
        self.addAdvancedKeyButton = QPushButton(self.advancedKeyGroup)
        self.addAdvancedKeyButton.setObjectName(u"addAdvancedKeyButton")
        self.addAdvancedKeyButton.setGeometry(QRect(12, 112, 366, 28))
        self.stackedWidget.addWidget(self.advancedCreatePage)
        self.licensePage = QWidget()
        self.licensePage.setObjectName(u"licensePage")
        self.licenseTitleLabel = QLabel(self.licensePage)
        self.licenseTitleLabel.setObjectName(u"licenseTitleLabel")
        self.licenseTitleLabel.setGeometry(QRect(0, 180, 800, 30))
        self.licenseTitleLabel.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        self.licenseKeyInput = QLineEdit(self.licensePage)
        self.licenseKeyInput.setObjectName(u"licenseKeyInput")
        self.licenseKeyInput.setGeometry(QRect(250, 236, 300, 42))
        self.licenseKeyInput.setAlignment(Qt.AlignCenter)
        self.licenseErrorLabel = QLabel(self.licensePage)
        self.licenseErrorLabel.setObjectName(u"licenseErrorLabel")
        self.licenseErrorLabel.setGeometry(QRect(200, 288, 400, 20))
        self.licenseErrorLabel.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        self.licenseValidateButton = QPushButton(self.licensePage)
        self.licenseValidateButton.setObjectName(u"licenseValidateButton")
        self.licenseValidateButton.setGeometry(QRect(250, 324, 300, 40))
        self.stackedWidget.addWidget(self.licensePage)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1176, 37))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.stackedWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Zeron Config", None))
        MainWindow.setStyleSheet(QCoreApplication.translate("MainWindow", u"\n"
"/* ============================================\n"
"   Modern Dark Theme \u2014 Single Accent\n"
"   ============================================ */\n"
"\n"
"/* === Base === */\n"
"QMainWindow, QWidget {\n"
"    background-color: #121212;\n"
"    color: #E0E0E0;\n"
"    font-family: \"IBM Plex Sans\", \"Helvetica Neue\", \"Segoe UI\", sans-serif;\n"
"    font-size: 13px;\n"
"}\n"
"\n"
"/* === Typography === */\n"
"QLabel {\n"
"    color: #E0E0E0;\n"
"    font-size: 13px;\n"
"    background-color: transparent;\n"
"}\n"
"\n"
"QLabel#mainPageTitle {\n"
"    color: #ffffff;\n"
"    font-size: 22px;\n"
"    font-weight: 600;\n"
"    font-family: \"Rajdhani\", \"IBM Plex Sans\", sans-serif;\n"
"}\n"
"\n"
"/* === List Widget === */\n"
"QListWidget {\n"
"    background-color: #1A1A1A;\n"
"    color: #E0E0E0;\n"
"    border: 1px solid #2A2A2A;\n"
"    border-radius: 8px;\n"
"    padding: 6px;\n"
"    font-size: 13px;\n"
"}\n"
"\n"
"QListWidget::item {\n"
"    padding: 10px 8px;\n"
"    border-radius: 6px;\n"
"    "
                        "margin: 2px;\n"
"}\n"
"\n"
"QListWidget::item:selected {\n"
"    background-color: rgba(255, 255, 255, 0.06);\n"
"    color: #ffffff;\n"
"}\n"
"\n"
"QListWidget::item:hover {\n"
"    background-color: #232323;\n"
"}\n"
"\n"
"/* === Buttons (Secondary Default) === */\n"
"QPushButton {\n"
"    background-color: #2A2A2A;\n"
"    color: #E0E0E0;\n"
"    border: 1px solid #333333;\n"
"    border-radius: 6px;\n"
"    padding: 8px 16px;\n"
"    font-size: 13px;\n"
"    font-weight: 500;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #363636;\n"
"    border-color: #444444;\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #1E1E1E;\n"
"}\n"
"\n"
"/* Danger \u2014 Stop Buttons */\n"
"QPushButton#stopMacroButton {\n"
"    background-color: #2A2A2A;\n"
"    color: #E0E0E0;\n"
"    border: 1px solid #333333;\n"
"}\n"
"\n"
"QPushButton#stopMacroButton:hover {\n"
"    background-color: #363636;\n"
"}\n"
"\n"
"/* Webhook Toggle \u2014 disabled */\n"
"QPushButton#webhookToggleButton {\n"
"    backgro"
                        "und-color: #2A2A2A;\n"
"    color: #999999;\n"
"    border: 1px solid #333333;\n"
"}\n"
"\n"
"QPushButton#webhookToggleButton:hover {\n"
"    background-color: #363636;\n"
"}\n"
"\n"
"/* Webhook Toggle \u2014 enabled */\n"
"QPushButton#webhookToggleButton[enabled_state=\"true\"] {\n"
"    background-color: #E0E0E0;\n"
"    color: #ffffff;\n"
"    border: none;\n"
"}\n"
"\n"
"QPushButton#webhookToggleButton[enabled_state=\"true\"]:hover {\n"
"    background-color: #34D76F;\n"
"}\n"
"\n"
"/* Webhook Test */\n"
"QPushButton#webhookTestButton {\n"
"    background-color: #2A2A2A;\n"
"    color: #E0E0E0;\n"
"    border: 1px solid #333333;\n"
"}\n"
"\n"
"QPushButton#webhookTestButton:hover {\n"
"    background-color: #363636;\n"
"}\n"
"\n"
"/* Overlay Webhook Toggle \u2014 disabled */\n"
"QPushButton#overlayWebhookToggleButton {\n"
"    background-color: #2A2A2A;\n"
"    color: #999999;\n"
"    border: 1px solid #333333;\n"
"}\n"
"\n"
"QPushButton#overlayWebhookToggleButton:hover {\n"
"    background-color: #363636;\n"
""
                        "}\n"
"\n"
"/* Overlay Webhook Toggle \u2014 enabled */\n"
"QPushButton#overlayWebhookToggleButton[enabled_state=\"true\"] {\n"
"    background-color: #E0E0E0;\n"
"    color: #ffffff;\n"
"    border: none;\n"
"}\n"
"\n"
"QPushButton#overlayWebhookToggleButton[enabled_state=\"true\"]:hover {\n"
"    background-color: #34D76F;\n"
"}\n"
"\n"
"/* Overlay Webhook Test */\n"
"QPushButton#overlayWebhookTestButton {\n"
"    background-color: #2A2A2A;\n"
"    color: #E0E0E0;\n"
"    border: 1px solid #333333;\n"
"}\n"
"\n"
"QPushButton#overlayWebhookTestButton:hover {\n"
"    background-color: #363636;\n"
"}\n"
"\n"
"/* === Standard Group Box === */\n"
"QGroupBox {\n"
"    background-color: #1A1A1A;\n"
"    border: 1px solid #2A2A2A;\n"
"    border-top: 2px solid #3A3A3A;\n"
"    border-radius: 8px;\n"
"    margin-top: 16px;\n"
"    padding: 12px;\n"
"    padding-top: 14px;\n"
"    font-weight: 500;\n"
"    color: #E0E0E0;\n"
"}\n"
"\n"
"QGroupBox::title {\n"
"    subcontrol-origin: margin;\n"
"    subcontrol-position: "
                        "top left;\n"
"    left: 12px;\n"
"    padding: 2px 8px;\n"
"    color: #E0E0E0;\n"
"    font-size: 13px;\n"
"    font-weight: 600;\n"
"    background-color: transparent;\n"
"}\n"
"\n"
"/* Widgets inside group boxes */\n"
"QGroupBox QLabel,\n"
"QGroupBox QRadioButton,\n"
"QGroupBox QCheckBox {\n"
"    background-color: transparent;\n"
"}\n"
"\n"
"/* === Overlay Page Background === */\n"
"QWidget#overlayPage {\n"
"    background-color: #0d0d0d;\n"
"    font-family: \"Inter\", sans-serif;\n"
"}\n"
"\n"
"/* === Overlay Mode Cards === */\n"
"QGroupBox#storyModeGroup, QGroupBox#raidsModeGroup, QGroupBox#legendModeGroup,\n"
"QGroupBox#bossRushModeGroup, QGroupBox#eventsModeGroup,\n"
"QGroupBox#dungeonModeGroup {\n"
"    background-color: #111111;\n"
"    border: none;\n"
"    border-radius: 0px;\n"
"    margin-top: 0px;\n"
"    padding: 0px;\n"
"}\n"
"QGroupBox#storyModeGroup:hover, QGroupBox#raidsModeGroup:hover, QGroupBox#legendModeGroup:hover,\n"
"QGroupBox#bossRushModeGroup:hover, QGroupBox#eventsModeGroup:hover,"
                        "\n"
"QGroupBox#dungeonModeGroup:hover {\n"
"    border: none;\n"
"}\n"
"QGroupBox#storyModeGroup::title, QGroupBox#raidsModeGroup::title, QGroupBox#legendModeGroup::title,\n"
"QGroupBox#bossRushModeGroup::title, QGroupBox#eventsModeGroup::title,\n"
"QGroupBox#dungeonModeGroup::title {\n"
"    width: 0px; height: 0px; padding: 0px; margin: 0px;\n"
"}\n"
"\n"
"/* Overlay card combos */\n"
"QGroupBox#storyModeGroup QComboBox, QGroupBox#raidsModeGroup QComboBox,\n"
"QGroupBox#legendModeGroup QComboBox, QGroupBox#bossRushModeGroup QComboBox,\n"
"QGroupBox#eventsModeGroup QComboBox,\n"
"QGroupBox#dungeonModeGroup QComboBox {\n"
"    background-color: #0a0a0a;\n"
"    border: 1px solid #2a2a2a;\n"
"    border-radius: 0px;\n"
"    color: #ccc;\n"
"    padding: 4px 10px;\n"
"    font-size: 12px;\n"
"    combobox-popup: 0;\n"
"}\n"
"QGroupBox#storyModeGroup QComboBox QAbstractItemView,\n"
"QGroupBox#raidsModeGroup QComboBox QAbstractItemView,\n"
"QGroupBox#legendModeGroup QComboBox QAbstractItemView,\n"
"QGroupBox#bossR"
                        "ushModeGroup QComboBox QAbstractItemView,\n"
"QGroupBox#eventsModeGroup QComboBox QAbstractItemView,\n"
"QGroupBox#dungeonModeGroup QComboBox QAbstractItemView {\n"
"    background-color: #0a0a0a;\n"
"    color: #E0E0E0;\n"
"    selection-background-color: #1a1a1a;\n"
"    selection-color: #ffffff;\n"
"    border: 1px solid #2a2a2a;\n"
"    border-radius: 0px;\n"
"    font-size: 12px;\n"
"    padding: 2px;\n"
"    outline: 0;\n"
"}\n"
"QGroupBox#storyModeGroup QComboBox QAbstractItemView::item,\n"
"QGroupBox#raidsModeGroup QComboBox QAbstractItemView::item,\n"
"QGroupBox#legendModeGroup QComboBox QAbstractItemView::item,\n"
"QGroupBox#bossRushModeGroup QComboBox QAbstractItemView::item,\n"
"QGroupBox#eventsModeGroup QComboBox QAbstractItemView::item,\n"
"QGroupBox#dungeonModeGroup QComboBox QAbstractItemView::item {\n"
"    padding: 3px 6px;\n"
"    min-height: 16px;\n"
"    background-color: #0a0a0a;\n"
"    color: #E0E0E0;\n"
"}\n"
"QGroupBox#storyModeGroup QComboBox QAbstractItemView::item:selected,\n"
"QGr"
                        "oupBox#raidsModeGroup QComboBox QAbstractItemView::item:selected,\n"
"QGroupBox#legendModeGroup QComboBox QAbstractItemView::item:selected,\n"
"QGroupBox#bossRushModeGroup QComboBox QAbstractItemView::item:selected,\n"
"QGroupBox#eventsModeGroup QComboBox QAbstractItemView::item:selected,\n"
"QGroupBox#dungeonModeGroup QComboBox QAbstractItemView::item:selected {\n"
"    background-color: #1a1a1a;\n"
"    color: #ffffff;\n"
"}\n"
"QGroupBox#storyModeGroup QComboBox QFrame,\n"
"QGroupBox#raidsModeGroup QComboBox QFrame,\n"
"QGroupBox#legendModeGroup QComboBox QFrame,\n"
"QGroupBox#bossRushModeGroup QComboBox QFrame,\n"
"QGroupBox#eventsModeGroup QComboBox QFrame,\n"
"QGroupBox#dungeonModeGroup QComboBox QFrame {\n"
"    border: 1px solid #2a2a2a;\n"
"    border-radius: 0px;\n"
"    background-color: #0a0a0a;\n"
"}\n"
"\n"
"/* Overlay webhook group */\n"
"QGroupBox#overlayWebhookGroup {\n"
"    background-color: #111111;\n"
"    border: 1px solid #1e1e1e;\n"
"    border-radius: 0px;\n"
"    margin-top: 0px;\n"
""
                        "    padding: 0px;\n"
"}\n"
"QGroupBox#overlayWebhookGroup::title {\n"
"    width: 0px; height: 0px; padding: 0px; margin: 0px;\n"
"}\n"
"\n"
"/* Overlay webhook input */\n"
"QGroupBox#overlayWebhookGroup QLineEdit {\n"
"    background-color: #0a0a0a;\n"
"    border: 1px solid #2a2a2a;\n"
"    border-radius: 0px;\n"
"}\n"
"\n"
"/* === Inputs === */\n"
"QLineEdit {\n"
"    background-color: #1E1E1E;\n"
"    color: #E0E0E0;\n"
"    border: 1px solid #2A2A2A;\n"
"    border-radius: 8px;\n"
"    padding: 6px 10px;\n"
"    font-size: 13px;\n"
"}\n"
"\n"
"QLineEdit:focus {\n"
"    border: 1px solid #808080;\n"
"}\n"
"\n"
"QLineEdit:hover {\n"
"    border: 1px solid #3A3A3A;\n"
"}\n"
"\n"
"/* === Radio Buttons === */\n"
"QRadioButton {\n"
"    color: #E0E0E0;\n"
"    font-size: 13px;\n"
"    background-color: transparent;\n"
"    spacing: 8px;\n"
"}\n"
"\n"
"QRadioButton::indicator {\n"
"    width: 16px;\n"
"    height: 16px;\n"
"}\n"
"\n"
"QRadioButton::indicator:unchecked {\n"
"    border: 2px solid #3A3A3A;\n"
"   "
                        " border-radius: 8px;\n"
"    background-color: #1E1E1E;\n"
"}\n"
"\n"
"QRadioButton::indicator:unchecked:hover {\n"
"    border-color: #E0E0E0;\n"
"}\n"
"\n"
"QRadioButton::indicator:checked {\n"
"    border: 2px solid #E0E0E0;\n"
"    border-radius: 8px;\n"
"    background-color: #E0E0E0;\n"
"}\n"
"\n"
"/* === Checkboxes === */\n"
"QCheckBox {\n"
"    color: #E0E0E0;\n"
"    font-size: 13px;\n"
"    background-color: transparent;\n"
"    spacing: 8px;\n"
"}\n"
"\n"
"QCheckBox::indicator {\n"
"    width: 16px;\n"
"    height: 16px;\n"
"}\n"
"\n"
"QCheckBox::indicator:unchecked {\n"
"    border: 2px solid #3A3A3A;\n"
"    border-radius: 4px;\n"
"    background-color: #1E1E1E;\n"
"}\n"
"\n"
"QCheckBox::indicator:unchecked:hover {\n"
"    border-color: #E0E0E0;\n"
"}\n"
"\n"
"QCheckBox::indicator:checked {\n"
"    border: 2px solid #E0E0E0;\n"
"    border-radius: 4px;\n"
"    background-color: #E0E0E0;\n"
"}\n"
"\n"
"/* === Separator Insert Buttons === */\n"
"QPushButton#insertButton {\n"
"    background-color: t"
                        "ransparent;\n"
"    color: #444444;\n"
"    border: none;\n"
"    font-weight: 600;\n"
"    font-size: 10px;\n"
"    padding: 0px;\n"
"    border-radius: 3px;\n"
"}\n"
"\n"
"QPushButton#insertButton:hover {\n"
"    color: #E0E0E0;\n"
"    background-color: #3A3A3A;\n"
"}\n"
"\n"
"QPushButton#insertButton:pressed {\n"
"    color: #22C55E;\n"
"    background-color: #2A2A2A;\n"
"}\n"
"\n"
"/* Cancel Insert */\n"
"QPushButton#cancelInsertButton {\n"
"    background-color: #FF4D4F;\n"
"    color: #ffffff;\n"
"    border: none;\n"
"    border-radius: 6px;\n"
"    font-weight: 600;\n"
"    font-size: 12px;\n"
"}\n"
"\n"
"QPushButton#cancelInsertButton:hover {\n"
"    background-color: #FF6B6B;\n"
"}\n"
"\n"
"\n"
"/* === Step Rows === */\n"
"QWidget#stepRow {\n"
"    background-color: transparent;\n"
"    border: none;\n"
"}\n"
"\n"
"/* Number badge */\n"
"QLabel#stepNumBadge {\n"
"    background-color: #0a0a0a;\n"
"    color: #666666;\n"
"    border: 1px solid #2a2a2a;\n"
"    border-radius: 0px;\n"
"    font-family:"
                        " \"Inter\", sans-serif;\n"
"    font-size: 11px;\n"
"    font-weight: 400;\n"
"}\n"
"\n"
"/* Card container */\n"
"QWidget#stepCard {\n"
"    background-color: #1a1a1a;\n"
"    border: 1px solid #2a2a2a;\n"
"    border-radius: 0px;\n"
"}\n"
"\n"
"/* Step type label \u2014 bold tracked caps */\n"
"QLabel#stepTypeLabel {\n"
"    background-color: transparent;\n"
"    color: #FFFFFF;\n"
"    font-family: \"Inter\", sans-serif;\n"
"    font-size: 11px;\n"
"    font-weight: 700;\n"
"    letter-spacing: 2;\n"
"}\n"
"\n"
"/* Detail / descriptor */\n"
"QLabel#stepDetailLabel {\n"
"    background-color: transparent;\n"
"    color: #888888;\n"
"    font-family: \"Inter\", sans-serif;\n"
"    font-size: 10px;\n"
"    font-weight: 400;\n"
"}\n"
"\n"
"/* Value chip */\n"
"QLabel#stepValueLabel {\n"
"    background-color: transparent;\n"
"    color: #4EC9B0;\n"
"    font-family: \"Inter\", sans-serif;\n"
"    font-size: 11px;\n"
"    font-weight: 700;\n"
"    letter-spacing: 1;\n"
"}\n"
"\n"
"QPushButton#inlineAddButton {\n"
""
                        "    background-color: transparent;\n"
"    color: #666666;\n"
"    border: 1px solid #2a2a2a;\n"
"    border-radius: 0px;\n"
"    font-size: 16px;\n"
"    font-weight: 300;\n"
"    padding: 0px;\n"
"    padding-bottom: 2px;\n"
"    margin: 0px;\n"
"}\n"
"QPushButton#inlineAddButton:hover {\n"
"    color: #10b981;\n"
"    border-color: #10b981;\n"
"}\n"
"\n"
"QPushButton#editStepButton {\n"
"    background-color: transparent;\n"
"    color: #666666;\n"
"    border: 1px solid #2a2a2a;\n"
"    border-radius: 0px;\n"
"    font-weight: 600;\n"
"    font-size: 12px;\n"
"    padding: 0px;\n"
"    padding-bottom: 1px;\n"
"    margin: 0px;\n"
"}\n"
"QPushButton#editStepButton:hover {\n"
"    color: #E0E0E0;\n"
"    border-color: #555555;\n"
"}\n"
"\n"
"QPushButton#deleteStepButton {\n"
"    background-color: transparent;\n"
"    color: #c72e2e;\n"
"    border: 1px solid #c72e2e;\n"
"    border-radius: 0px;\n"
"    font-weight: 600;\n"
"    font-size: 15px;\n"
"    padding: 0px;\n"
"    padding-bottom: 2px;\n"
"    marg"
                        "in: 0px;\n"
"}\n"
"QPushButton#deleteStepButton:hover {\n"
"    color: #FF4D4F;\n"
"    border-color: #FF4D4F;\n"
"    background-color: rgba(199, 46, 46, 0.1);\n"
"}\n"
"\n"
"/* === Separator Widget States === */\n"
"QWidget#separator {\n"
"    background-color: transparent;\n"
"}\n"
"\n"
"QWidget#separator[active=\"true\"] {\n"
"    background-color: rgba(255, 255, 255, 0.04);\n"
"    border: 1px solid #808080;\n"
"    border-radius: 4px;\n"
"}\n"
"\n"
"/* === Group Box Highlight (Edit Mode) === */\n"
"QGroupBox[highlighted=\"true\"] {\n"
"    border: 2px solid #E0E0E0;\n"
"}\n"
"\n"
"/* === Scroll Area === */\n"
"QScrollArea {\n"
"    background-color: #1A1A1A;\n"
"    border: 1px solid #2A2A2A;\n"
"    border-radius: 8px;\n"
"}\n"
"\n"
"QScrollArea > QWidget > QWidget {\n"
"    background-color: #1A1A1A;\n"
"}\n"
"\n"
"QScrollBar:vertical {\n"
"    background-color: #1A1A1A;\n"
"    width: 8px;\n"
"    border-radius: 4px;\n"
"}\n"
"\n"
"QScrollBar::handle:vertical {\n"
"    background-color: #333333;\n"
" "
                        "   border-radius: 4px;\n"
"    min-height: 20px;\n"
"}\n"
"\n"
"QScrollBar::handle:vertical:hover {\n"
"    background-color: #444444;\n"
"}\n"
"\n"
"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {\n"
"    height: 0px;\n"
"}\n"
"\n"
"/* === Status Bar === */\n"
"QStatusBar {\n"
"    background-color: #000000;\n"
"    color: #999999;\n"
"    border-top: 1px solid #2A2A2A;\n"
"    font-size: 12px;\n"
"}\n"
"\n"
"/* === Menu Bar === */\n"
"QMenuBar {\n"
"    background-color: #1A1A1A;\n"
"    color: #E0E0E0;\n"
"}\n"
"\n"
"/* === Combo Box === */\n"
"QComboBox {\n"
"    background-color: #1E1E1E;\n"
"    color: #E0E0E0;\n"
"    border: 1px solid #2A2A2A;\n"
"    border-radius: 8px;\n"
"    padding: 8px 12px;\n"
"    font-size: 13px;\n"
"}\n"
"\n"
"QComboBox:hover {\n"
"    border-color: #3A3A3A;\n"
"}\n"
"\n"
"QComboBox:focus {\n"
"    border-color: #E0E0E0;\n"
"}\n"
"\n"
"QComboBox::drop-down {\n"
"    border: none;\n"
"    background-color: transparent;\n"
"    width: 25px;\n"
"}\n"
"\n"
"QComboB"
                        "ox::down-arrow {\n"
"    image: url(references/down_arrow.svg);\n"
"    width: 10px;\n"
"    height: 6px;\n"
"}\n"
"\n"
"QComboBox QAbstractItemView {\n"
"    background-color: #1A1A1A;\n"
"    color: #E0E0E0;\n"
"    selection-background-color: rgba(255, 255, 255, 0.06);\n"
"    selection-color: #ffffff;\n"
"    border: 1px solid #2A2A2A;\n"
"    border-radius: 0px;\n"
"    font-size: 10px;\n"
"    padding: 2px;\n"
"    outline: 0;\n"
"}\n"
"\n"
"QComboBox QAbstractItemView::item {\n"
"    padding: 3px 6px;\n"
"    min-height: 16px;\n"
"    background-color: #1A1A1A;\n"
"    color: #E0E0E0;\n"
"}\n"
"\n"
"QComboBox QAbstractItemView::item:selected {\n"
"    background-color: #2A2A2A;\n"
"    color: #ffffff;\n"
"}\n"
"\n"
"/* Remove white frame around combo popup */\n"
"QComboBox QFrame {\n"
"    border: 1px solid #2A2A2A;\n"
"    border-radius: 0px;\n"
"    background-color: #1A1A1A;\n"
"}\n"
"\n"
"/* === Advanced section compact combos/inputs === */\n"
"QGroupBox#upgradeGroup QComboBox {\n"
"    font-family:"
                        " \"Inter\", sans-serif;\n"
"    font-size: 10px;\n"
"    padding: 1px 4px;\n"
"    border-radius: 0px;\n"
"    background-color: #0a0a0a;\n"
"    border: 1px solid #1a1a1a;\n"
"    color: #E0E0E0;\n"
"    combobox-popup: 0;\n"
"}\n"
"QGroupBox#placeGroup QComboBox {\n"
"    font-size: 10px;\n"
"    padding: 1px 4px;\n"
"    border-radius: 0px;\n"
"    background-color: #0a0a0a;\n"
"    border: 1px solid #1a1a1a;\n"
"    color: #E0E0E0;\n"
"    combobox-popup: 0;\n"
"}\n"
"\n"
"QGroupBox#upgradeGroup QComboBox QAbstractItemView,\n"
"QGroupBox#placeGroup QComboBox QAbstractItemView {\n"
"    background-color: #0a0a0a;\n"
"    color: #E0E0E0;\n"
"    selection-background-color: #1a1a1a;\n"
"    selection-color: #ffffff;\n"
"    border: 1px solid #2a2a2a;\n"
"    border-radius: 0px;\n"
"    font-size: 10px;\n"
"    padding: 2px;\n"
"    outline: 0;\n"
"}\n"
"\n"
"QGroupBox#advancedClickGroup QComboBox,\n"
"QGroupBox#advancedKeyGroup QComboBox {\n"
"    font-size: 10px;\n"
"    padding: 1px 4px;\n"
"    border-radi"
                        "us: 4px;\n"
"}\n"
"\n"
"QGroupBox#upgradeGroup QLineEdit,\n"
"QGroupBox#placeGroup QLineEdit {\n"
"    font-family: \"Menlo\", \"SF Mono\", monospace;\n"
"    font-size: 10px;\n"
"    padding: 1px 4px;\n"
"    border-radius: 0px;\n"
"    background-color: #0a0a0a;\n"
"    border: 1px solid #1a1a1a;\n"
"    color: #E0E0E0;\n"
"}\n"
"\n"
"QGroupBox#advancedWaitGroup QLineEdit {\n"
"    font-family: \"Menlo\", \"SF Mono\", monospace;\n"
"    font-size: 10px;\n"
"    padding: 1px 4px;\n"
"    border-radius: 0px;\n"
"    background-color: #0a0a0a;\n"
"    border: 1px solid #1a1a1a;\n"
"    color: #E0E0E0;\n"
"}\n"
"\n"
"QGroupBox#advancedClickGroup QLineEdit,\n"
"QGroupBox#advancedKeyGroup QLineEdit {\n"
"    font-family: \"Menlo\", \"SF Mono\", monospace;\n"
"    font-size: 10px;\n"
"    padding: 1px 4px;\n"
"    border-radius: 0px;\n"
"    background-color: #0a0a0a;\n"
"    border: 1px solid #1a1a1a;\n"
"    color: #E0E0E0;\n"
"}\n"
"\n"
"QGroupBox#advancedKeyGroup QRadioButton,\n"
"QGroupBox#advancedClickGroup Q"
                        "RadioButton {\n"
"    font-family: \"Inter\", sans-serif;\n"
"    font-size: 10px;\n"
"    spacing: 6px;\n"
"}\n"
"QGroupBox#advancedKeyGroup QRadioButton::indicator,\n"
"QGroupBox#advancedClickGroup QRadioButton::indicator {\n"
"    width: 12px;\n"
"    height: 12px;\n"
"}\n"
"QGroupBox#advancedKeyGroup QRadioButton::indicator:unchecked,\n"
"QGroupBox#advancedClickGroup QRadioButton::indicator:unchecked {\n"
"    border: 1px solid #3A3A3A;\n"
"    border-radius: 0px;\n"
"    background-color: #0a0a0a;\n"
"}\n"
"QGroupBox#advancedKeyGroup QRadioButton::indicator:unchecked:hover,\n"
"QGroupBox#advancedClickGroup QRadioButton::indicator:unchecked:hover {\n"
"    border-color: #10b981;\n"
"}\n"
"QGroupBox#advancedKeyGroup QRadioButton::indicator:checked,\n"
"QGroupBox#advancedClickGroup QRadioButton::indicator:checked {\n"
"    border: 1px solid #10b981;\n"
"    border-radius: 0px;\n"
"    background-color: #10b981;\n"
"    image: url(references/checkmark.svg);\n"
"}\n"
"\n"
"/* === Wait group radio buttons (rede"
                        "signed) === */\n"
"QGroupBox#advancedWaitGroup QRadioButton {\n"
"    font-family: \"Inter\", sans-serif;\n"
"    font-size: 10px;\n"
"    spacing: 6px;\n"
"}\n"
"\n"
"QGroupBox#advancedWaitGroup QRadioButton::indicator {\n"
"    width: 12px;\n"
"    height: 12px;\n"
"}\n"
"\n"
"QGroupBox#advancedWaitGroup QRadioButton::indicator:unchecked {\n"
"    border: 1px solid #3A3A3A;\n"
"    border-radius: 0px;\n"
"    background-color: #0a0a0a;\n"
"}\n"
"\n"
"QGroupBox#advancedWaitGroup QRadioButton::indicator:unchecked:hover {\n"
"    border-color: #10b981;\n"
"}\n"
"\n"
"QGroupBox#advancedWaitGroup QRadioButton::indicator:checked {\n"
"    border: 1px solid #10b981;\n"
"    border-radius: 0px;\n"
"    background-color: #10b981;\n"
"    image: url(references/checkmark.svg);\n"
"}\n"
"\n"
"\n"
"QGroupBox#unitSelectionGroup QLineEdit {\n"
"    font-family: \"Inter\", sans-serif;\n"
"    font-size: 12px;\n"
"    padding: 4px 8px;\n"
"    border-radius: 0px;\n"
"    background-color: #0a0a0a;\n"
"    border: 1px solid #"
                        "2a2a2a;\n"
"    color: #E0E0E0;\n"
"}\n"
"\n"
"QGroupBox#upgradeGroup QCheckBox {\n"
"    font-family: \"Inter\", sans-serif;\n"
"    font-size: 10px;\n"
"    spacing: 6px;\n"
"}\n"
"QGroupBox#placeGroup QCheckBox {\n"
"    font-size: 10px;\n"
"    spacing: 6px;\n"
"}\n"
"\n"
"QGroupBox#upgradeGroup QCheckBox::indicator,\n"
"QGroupBox#placeGroup QCheckBox::indicator {\n"
"    width: 12px;\n"
"    height: 12px;\n"
"}\n"
"\n"
"QGroupBox#upgradeGroup QCheckBox::indicator:unchecked,\n"
"QGroupBox#placeGroup QCheckBox::indicator:unchecked {\n"
"    border: 1px solid #3A3A3A;\n"
"    border-radius: 0px;\n"
"    background-color: #0a0a0a;\n"
"}\n"
"\n"
"QGroupBox#upgradeGroup QCheckBox::indicator:unchecked:hover,\n"
"QGroupBox#placeGroup QCheckBox::indicator:unchecked:hover {\n"
"    border-color: #10b981;\n"
"}\n"
"\n"
"QGroupBox#upgradeGroup QCheckBox::indicator:checked,\n"
"QGroupBox#placeGroup QCheckBox::indicator:checked {\n"
"    border: 1px solid #10b981;\n"
"    border-radius: 0px;\n"
"    background-color: #"
                        "10b981;\n"
"    image: url(references/checkmark.svg);\n"
"}\n"
"\n"
"/* === Unit Group Boxes === */\n"
"QGroupBox#unit1Group, QGroupBox#unit2Group, QGroupBox#unit3Group,\n"
"QGroupBox#unit4Group, QGroupBox#unit5Group, QGroupBox#unit6Group {\n"
"    background-color: transparent;\n"
"    border: none;\n"
"    border-radius: 0px;\n"
"    margin-top: 0px;\n"
"    padding: 0px;\n"
"}\n"
"\n"
"QGroupBox#unit1Group::title, QGroupBox#unit2Group::title, QGroupBox#unit3Group::title,\n"
"QGroupBox#unit4Group::title, QGroupBox#unit5Group::title, QGroupBox#unit6Group::title {\n"
"    width: 0px;\n"
"    height: 0px;\n"
"}\n"
"\n"
"/* === Upgrade Section === */\n"
"QGroupBox#upgradeGroup {\n"
"    background-color: #000000;\n"
"    border: 1px solid #2a2a2a;\n"
"    border-radius: 0px;\n"
"    margin-top: 0px;\n"
"    padding: 0px;\n"
"}\n"
"\n"
"QGroupBox#upgradeGroup::title {\n"
"    width: 0px;\n"
"    height: 0px;\n"
"}\n"
"\n"
"/* === Place Section === */\n"
"QGroupBox#placeGroup {\n"
"    background-color: #000000;\n"
""
                        "    border: 1px solid #2a2a2a;\n"
"    border-radius: 0px;\n"
"    margin-top: 0px;\n"
"    padding: 0px;\n"
"}\n"
"\n"
"QGroupBox#placeGroup::title {\n"
"    width: 0px;\n"
"    height: 0px;\n"
"}\n"
"\n"
"/* === Group Header Labels === */\n"
"QLabel#clickHeaderLabel,\n"
"QLabel#keyHeaderLabel {\n"
"    background-color: transparent;\n"
"    color: #888888;\n"
"    font-family: \"Inter\", sans-serif;\n"
"    font-size: 10px;\n"
"    font-weight: 700;\n"
"    letter-spacing: 2;\n"
"    padding-left: 10px;\n"
"    border-bottom: 1px solid #2a2a2a;\n"
"    border-radius: 0px;\n"
"}\n"
"QLabel#settingsHeaderLabel {\n"
"    background-color: transparent;\n"
"    color: #888888;\n"
"    font-family: \"Inter\", sans-serif;\n"
"    font-size: 10px;\n"
"    font-weight: 700;\n"
"    letter-spacing: 2;\n"
"    padding-left: 10px;\n"
"    border-bottom: 1px solid #2a2a2a;\n"
"    border-radius: 0px;\n"
"}\n"
"\n"
"QLabel#waitHeaderLabel {\n"
"    background-color: transparent;\n"
"    color: #888888;\n"
"    font-family"
                        ": \"Inter\", sans-serif;\n"
"    font-size: 10px;\n"
"    font-weight: 700;\n"
"    letter-spacing: 2;\n"
"    padding-left: 10px;\n"
"    border-bottom: 1px solid #2a2a2a;\n"
"    border-radius: 0px;\n"
"}\n"
"\n"
"/* === Upgrade/Place/Units Header Labels (dark redesign) === */\n"
"QLabel#upgradeHeaderLabel,\n"
"QLabel#unitSelectionHeaderLabel {\n"
"    background-color: transparent;\n"
"    color: #888888;\n"
"    font-family: \"Inter\", sans-serif;\n"
"    font-size: 10px;\n"
"    font-weight: 700;\n"
"    letter-spacing: 2;\n"
"    padding-left: 10px;\n"
"    border-bottom: 1px solid #2a2a2a;\n"
"    border-radius: 0px;\n"
"}\n"
"QLabel#placeHeaderLabel {\n"
"    background-color: transparent;\n"
"    color: #888888;\n"
"    font-size: 10px;\n"
"    font-weight: 700;\n"
"    letter-spacing: 2;\n"
"    padding-left: 10px;\n"
"    border-bottom: 1px solid #2a2a2a;\n"
"    border-radius: 0px;\n"
"}\n"
"\n"
"/* === Unit N: labels (inline with inputs) === */\n"
"QLabel#unit1HeaderLabel, QLabel#unit2HeaderLabel,"
                        " QLabel#unit3HeaderLabel,\n"
"QLabel#unit4HeaderLabel, QLabel#unit5HeaderLabel, QLabel#unit6HeaderLabel {\n"
"    background-color: transparent;\n"
"    color: #888888;\n"
"    font-family: \"Inter\", sans-serif;\n"
"    font-size: 11px;\n"
"    font-weight: 600;\n"
"    letter-spacing: 0;\n"
"    padding-left: 0px;\n"
"    border-radius: 0px;\n"
"}\n"
"\n"
"/* === All labels in upgrade group use Inter === */\n"
"QGroupBox#upgradeGroup QLabel {\n"
"    font-family: \"Inter\", sans-serif;\n"
"}\n"
"\n"
"/* === Column header labels in upgrade/place groups === */\n"
"QLabel#upgradeUnitLabel,\n"
"QLabel#upgradePlacementLabel,\n"
"QLabel#upgradeCountLabel {\n"
"    color: #555555;\n"
"    font-family: \"Inter\", sans-serif;\n"
"    font-size: 9px;\n"
"    font-weight: 700;\n"
"    letter-spacing: 1;\n"
"    background-color: transparent;\n"
"}\n"
"QLabel#placeUnitLabel,\n"
"QLabel#placeXLabel,\n"
"QLabel#placeYLabel,\n"
"QLabel#placementColHeaderLabel {\n"
"    color: #555555;\n"
"    font-size: 9px;\n"
"    font-w"
                        "eight: 700;\n"
"    letter-spacing: 1;\n"
"    background-color: transparent;\n"
"}\n"
"\n"
"/* === Add Upgrade Step button (green, full-width) === */\n"
"QPushButton#addUpgradeStepButton {\n"
"    background-color: #10b981;\n"
"    color: #000000;\n"
"    font-family: \"Inter\", sans-serif;\n"
"    font-size: 11px;\n"
"    font-weight: 700;\n"
"    letter-spacing: 2;\n"
"    border: none;\n"
"    border-radius: 0px;\n"
"}\n"
"QPushButton#addUpgradeStepButton:hover {\n"
"    background-color: #0ea472;\n"
"}\n"
"QPushButton#addUpgradeStepButton:pressed {\n"
"    background-color: #0d9668;\n"
"}\n"
"\n"
"/* === Add Place Step button (green) === */\n"
"QPushButton#addPlaceStepButton {\n"
"    background-color: #10b981;\n"
"    color: #000000;\n"
"    font-size: 10px;\n"
"    font-weight: 600;\n"
"    letter-spacing: 1;\n"
"    border: none;\n"
"    border-radius: 0px;\n"
"}\n"
"QPushButton#addPlaceStepButton:hover {\n"
"    background-color: #0ea472;\n"
"}\n"
"\n"
"/* === Record Place Click button (dark secondary"
                        ") === */\n"
"QPushButton#recordPlaceClickButton {\n"
"    background-color: #0a0a0a;\n"
"    color: #C0C0C0;\n"
"    font-size: 10px;\n"
"    font-weight: 600;\n"
"    letter-spacing: 1;\n"
"    border: 1px solid #333333;\n"
"    border-radius: 0px;\n"
"}\n"
"QPushButton#recordPlaceClickButton:hover {\n"
"    background-color: #2E2E2E;\n"
"    color: #E0E0E0;\n"
"    border-color: #444444;\n"
"}\n"
"\n"
"/* === Add Wait Step button (green, redesigned) === */\n"
"QPushButton#addAdvancedWaitButton {\n"
"    background-color: #10b981;\n"
"    color: #000000;\n"
"    font-family: \"Inter\", sans-serif;\n"
"    font-size: 11px;\n"
"    font-weight: 700;\n"
"    letter-spacing: 2;\n"
"    border: none;\n"
"    border-radius: 0px;\n"
"}\n"
"QPushButton#addAdvancedWaitButton:hover {\n"
"    background-color: #0ea472;\n"
"}\n"
"QPushButton#addAdvancedWaitButton:pressed {\n"
"    background-color: #0d9668;\n"
"}\n"
"\n"
"/* === Click / Key add buttons (green) === */\n"
"QPushButton#addAdvancedClickButton,\n"
"QPushButto"
                        "n#addAdvancedKeyButton {\n"
"    background-color: #10b981;\n"
"    color: #000000;\n"
"    font-family: \"Inter\", \"IBM Plex Sans\", sans-serif;\n"
"    font-size: 10px;\n"
"    font-weight: 700;\n"
"    letter-spacing: 2;\n"
"    border: none;\n"
"    border-radius: 0px;\n"
"}\n"
"QPushButton#addAdvancedClickButton:hover,\n"
"QPushButton#addAdvancedKeyButton:hover {\n"
"    background-color: #0ea472;\n"
"}\n"
"QPushButton#addAdvancedClickButton:pressed,\n"
"QPushButton#addAdvancedKeyButton:pressed {\n"
"    background-color: #0d9668;\n"
"}\n"
"/* === Record Click button (dark) === */\n"
"QPushButton#advRecordClickButton {\n"
"    background-color: #1a1a1a;\n"
"    color: #C0C0C0;\n"
"    font-family: \"Inter\", \"IBM Plex Sans\", sans-serif;\n"
"    font-size: 10px;\n"
"    font-weight: 600;\n"
"    letter-spacing: 1;\n"
"    border: 1px solid #333333;\n"
"    border-radius: 0px;\n"
"}\n"
"QPushButton#advRecordClickButton:hover {\n"
"    background-color: #2E2E2E;\n"
"    color: #E0E0E0;\n"
"    border-colo"
                        "r: #444444;\n"
"}\n"
"\n"
"/* === Save / Clear / Back buttons (Advanced Create) === */\n"
"QPushButton#advancedSaveButton {\n"
"    background-color: #10b981;\n"
"    color: #000000;\n"
"    font-family: \"Inter\", sans-serif;\n"
"    font-size: 11px;\n"
"    font-weight: 700;\n"
"    letter-spacing: 2;\n"
"    border: none;\n"
"    border-radius: 0px;\n"
"}\n"
"QPushButton#advancedSaveButton:hover {\n"
"    background-color: #0ea472;\n"
"}\n"
"QPushButton#advancedSaveButton:pressed {\n"
"    background-color: #0d9668;\n"
"}\n"
"QPushButton#advancedClearButton {\n"
"    background-color: #0a0a0a;\n"
"    color: #888888;\n"
"    font-family: \"Inter\", sans-serif;\n"
"    font-size: 11px;\n"
"    font-weight: 700;\n"
"    letter-spacing: 2;\n"
"    border: 1px solid #2a2a2a;\n"
"    border-radius: 0px;\n"
"}\n"
"QPushButton#advancedClearButton:hover {\n"
"    background-color: #1a1a1a;\n"
"    color: #CCCCCC;\n"
"    border-color: #444444;\n"
"}\n"
"QPushButton#advBackButton {\n"
"    background-color: #0a0a0a;"
                        "\n"
"    color: #888888;\n"
"    font-family: \"Inter\", sans-serif;\n"
"    font-size: 11px;\n"
"    font-weight: 700;\n"
"    letter-spacing: 2;\n"
"    border: 1px solid #2a2a2a;\n"
"    border-radius: 0px;\n"
"}\n"
"QPushButton#advBackButton:hover {\n"
"    background-color: #1a1a1a;\n"
"    color: #CCCCCC;\n"
"    border-color: #444444;\n"
"}\n"
"\n"
"/* === Unit Selection === */\n"
"QGroupBox#unitSelectionGroup {\n"
"    background-color: #000000;\n"
"    border: 1px solid #2a2a2a;\n"
"    border-radius: 0px;\n"
"    margin-top: 0px;\n"
"    padding: 0px;\n"
"}\n"
"QGroupBox#unitSelectionGroup::title { width: 0px; height: 0px; }\n"
"\n"
"/* === Advanced Steps Scroll Area === */\n"
"QScrollArea#advancedStepsScrollArea {\n"
"    background-color: #0a0a0a;\n"
"    border: 1px solid #2a2a2a;\n"
"    border-radius: 0px;\n"
"}\n"
"\n"
"/* === Wait Section === */\n"
"QGroupBox#advancedWaitGroup {\n"
"    background-color: #000000;\n"
"    border: 1px solid #2a2a2a;\n"
"    border-radius: 0px;\n"
"    margin-top"
                        ": 0px;\n"
"    padding: 0px;\n"
"}\n"
"QGroupBox#advancedWaitGroup::title { width: 0px; height: 0px; }\n"
"\n"
"/* === Click Group (Raw Steps) === */\n"
"QGroupBox#advancedClickGroup {\n"
"    background-color: #000000;\n"
"    border: 1px solid #2a2a2a;\n"
"    border-radius: 0px;\n"
"    margin-top: 0px;\n"
"    padding: 0px;\n"
"}\n"
"QGroupBox#advancedClickGroup::title { width: 0px; height: 0px; }\n"
"\n"
"/* === Key Group (Raw Steps) === */\n"
"QGroupBox#advancedKeyGroup {\n"
"    background-color: #000000;\n"
"    border: 1px solid #2a2a2a;\n"
"    border-radius: 0px;\n"
"    margin-top: 0px;\n"
"    padding: 0px;\n"
"}\n"
"QGroupBox#advancedKeyGroup::title { width: 0px; height: 0px; }\n"
"\n"
"   ", None))
        self.overlayScrollArea.setStyleSheet(QCoreApplication.translate("MainWindow", u"QScrollArea { background-color: #0d0d0d; border: none; } QWidget#overlayContent { background-color: #0d0d0d; }", None))
        self.overlayPageTitle.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size: 28px; font-weight: 700; color: #ffffff; font-family: \"Inter\", sans-serif; background: transparent;", None))
        self.overlayPageTitle.setText(QCoreApplication.translate("MainWindow", u"Zeron Config", None))
        self.overlaySubtitle.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size: 11px; color: #444444; letter-spacing: 2px; font-weight: 600; background: transparent; font-family: \"Inter\", sans-serif;", None))
        self.overlaySubtitle.setText(QCoreApplication.translate("MainWindow", u"0 OF 6 MACROS CONFIGURED", None))
        self.overlayStatusLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #666666; font-size: 15px; font-weight: 700; background: transparent; font-family: \"Rajdhani\", \"Inter\", sans-serif; letter-spacing: 0.5px;", None))
        self.overlayStatusLabel.setText("")
        self.storyModeGroup.setTitle("")
        self.storyImageFrame.setStyleSheet(QCoreApplication.translate("MainWindow", u"border: none; background-repeat: no-repeat; background-position: center;", None))
        self.storyImageOverlay.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(17,17,17,0), stop:0.4 rgba(17,17,17,30), stop:0.7 rgba(17,17,17,160), stop:1 rgba(17,17,17,255)); border: none;", None))
        self.storyModeLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #999; font-size: 10px; font-weight: 700; letter-spacing: 2px; background: transparent;", None))
        self.storyModeLabel.setText(QCoreApplication.translate("MainWindow", u"STORY", None))
        self.storyActiveLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #10b981; font-size: 10px; font-weight: 700; letter-spacing: 1px; background: transparent;", None))
        self.storyActiveLabel.setText(QCoreApplication.translate("MainWindow", u"ACTIVE", None))
        self.storyMapLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #555; font-size: 9px; font-weight: 600; letter-spacing: 1px; background: transparent;", None))
        self.storyMapLabel.setText(QCoreApplication.translate("MainWindow", u"MAP", None))
        self.storyMacroLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #555; font-size: 9px; font-weight: 600; letter-spacing: 1px; background: transparent;", None))
        self.storyMacroLabel.setText(QCoreApplication.translate("MainWindow", u"ACTIVE MACRO", None))
        self.storyRunsLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: transparent;", None))
        self.storyRunsLabel.setText(QCoreApplication.translate("MainWindow", u"<span style=\"color:#555;font-size:9px;font-weight:600;letter-spacing:1px;\">RUNS</span><br><span style=\"color:#fff;font-size:14px;font-weight:600;font-family:'Menlo','SF Mono',monospace;\">0</span>", None))
        self.storyTotalLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: transparent;", None))
        self.storyTotalLabel.setText(QCoreApplication.translate("MainWindow", u"<span style=\"color:#555;font-size:9px;font-weight:600;letter-spacing:1px;\">TOTAL</span><br><span style=\"color:#fff;font-size:14px;font-weight:600;font-family:'Menlo','SF Mono',monospace;\">0</span>", None))
        self.storyTimeLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: transparent;", None))
        self.storyTimeLabel.setText(QCoreApplication.translate("MainWindow", u"<span style=\"color:#555;font-size:9px;font-weight:600;letter-spacing:1px;\">TIME</span><br><span style=\"color:#fff;font-size:14px;font-weight:600;font-family:'Menlo','SF Mono',monospace;\">0m 0s</span>", None))
        self.storyCreateMacroButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: #10b981; color: #000; font-weight: 700; font-size: 11px; border: none; border-radius: 0px; letter-spacing: 1px;", None))
        self.storyCreateMacroButton.setText(QCoreApplication.translate("MainWindow", u"CREATE MACRO", None))
        self.storyImportMacroButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: #0a0a0a; color: #999; font-size: 11px; border: 1px solid #2a2a2a; border-radius: 0px;", None))
        self.storyImportMacroButton.setText(QCoreApplication.translate("MainWindow", u"IMPORT MACRO", None))
        self.storySelectMacroButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: #0a0a0a; color: #999; font-size: 11px; border: 1px solid #2a2a2a; border-radius: 0px;", None))
        self.storySelectMacroButton.setText(QCoreApplication.translate("MainWindow", u"SELECT MACRO", None))
        self.raidsModeGroup.setTitle("")
        self.raidsImageFrame.setStyleSheet(QCoreApplication.translate("MainWindow", u"border: none; background-repeat: no-repeat; background-position: center;", None))
        self.raidsImageOverlay.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(17,17,17,0), stop:0.4 rgba(17,17,17,30), stop:0.7 rgba(17,17,17,160), stop:1 rgba(17,17,17,255)); border: none;", None))
        self.raidsModeLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #999; font-size: 10px; font-weight: 700; letter-spacing: 2px; background: transparent;", None))
        self.raidsModeLabel.setText(QCoreApplication.translate("MainWindow", u"RAIDS", None))
        self.raidsActiveLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #10b981; font-size: 10px; font-weight: 700; letter-spacing: 1px; background: transparent;", None))
        self.raidsActiveLabel.setText(QCoreApplication.translate("MainWindow", u"ACTIVE", None))
        self.raidsMapLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #555; font-size: 9px; font-weight: 600; letter-spacing: 1px; background: transparent;", None))
        self.raidsMapLabel.setText(QCoreApplication.translate("MainWindow", u"MAP", None))
        self.raidsMacroLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #555; font-size: 9px; font-weight: 600; letter-spacing: 1px; background: transparent;", None))
        self.raidsMacroLabel.setText(QCoreApplication.translate("MainWindow", u"ACTIVE MACRO", None))
        self.raidsRunsLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: transparent;", None))
        self.raidsRunsLabel.setText(QCoreApplication.translate("MainWindow", u"<span style=\"color:#555;font-size:9px;font-weight:600;letter-spacing:1px;\">RUNS</span><br><span style=\"color:#fff;font-size:14px;font-weight:600;font-family:'Menlo','SF Mono',monospace;\">0</span>", None))
        self.raidsTotalLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: transparent;", None))
        self.raidsTotalLabel.setText(QCoreApplication.translate("MainWindow", u"<span style=\"color:#555;font-size:9px;font-weight:600;letter-spacing:1px;\">TOTAL</span><br><span style=\"color:#fff;font-size:14px;font-weight:600;font-family:'Menlo','SF Mono',monospace;\">0</span>", None))
        self.raidsTimeLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: transparent;", None))
        self.raidsTimeLabel.setText(QCoreApplication.translate("MainWindow", u"<span style=\"color:#555;font-size:9px;font-weight:600;letter-spacing:1px;\">TIME</span><br><span style=\"color:#fff;font-size:14px;font-weight:600;font-family:'Menlo','SF Mono',monospace;\">0m 0s</span>", None))
        self.raidsCreateMacroButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: #10b981; color: #000; font-weight: 700; font-size: 11px; border: none; border-radius: 0px; letter-spacing: 1px;", None))
        self.raidsCreateMacroButton.setText(QCoreApplication.translate("MainWindow", u"CREATE MACRO", None))
        self.raidsImportMacroButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: #0a0a0a; color: #999; font-size: 11px; border: 1px solid #2a2a2a; border-radius: 0px;", None))
        self.raidsImportMacroButton.setText(QCoreApplication.translate("MainWindow", u"IMPORT MACRO", None))
        self.raidsSelectMacroButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: #0a0a0a; color: #999; font-size: 11px; border: 1px solid #2a2a2a; border-radius: 0px;", None))
        self.raidsSelectMacroButton.setText(QCoreApplication.translate("MainWindow", u"SELECT MACRO", None))
        self.legendModeGroup.setTitle("")
        self.legendImageFrame.setStyleSheet(QCoreApplication.translate("MainWindow", u"border: none; background-repeat: no-repeat; background-position: center;", None))
        self.legendImageOverlay.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(17,17,17,0), stop:0.4 rgba(17,17,17,30), stop:0.7 rgba(17,17,17,160), stop:1 rgba(17,17,17,255)); border: none;", None))
        self.legendModeLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #999; font-size: 10px; font-weight: 700; letter-spacing: 2px; background: transparent;", None))
        self.legendModeLabel.setText(QCoreApplication.translate("MainWindow", u"LEGEND STAGE", None))
        self.legendActiveLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #10b981; font-size: 10px; font-weight: 700; letter-spacing: 1px; background: transparent;", None))
        self.legendActiveLabel.setText(QCoreApplication.translate("MainWindow", u"ACTIVE", None))
        self.legendMapLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #555; font-size: 9px; font-weight: 600; letter-spacing: 1px; background: transparent;", None))
        self.legendMapLabel.setText(QCoreApplication.translate("MainWindow", u"MAP", None))
        self.legendMacroLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #555; font-size: 9px; font-weight: 600; letter-spacing: 1px; background: transparent;", None))
        self.legendMacroLabel.setText(QCoreApplication.translate("MainWindow", u"ACTIVE MACRO", None))
        self.legendRunsLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: transparent;", None))
        self.legendRunsLabel.setText(QCoreApplication.translate("MainWindow", u"<span style=\"color:#555;font-size:9px;font-weight:600;letter-spacing:1px;\">RUNS</span><br><span style=\"color:#fff;font-size:14px;font-weight:600;font-family:'Menlo','SF Mono',monospace;\">0</span>", None))
        self.legendTotalLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: transparent;", None))
        self.legendTotalLabel.setText(QCoreApplication.translate("MainWindow", u"<span style=\"color:#555;font-size:9px;font-weight:600;letter-spacing:1px;\">TOTAL</span><br><span style=\"color:#fff;font-size:14px;font-weight:600;font-family:'Menlo','SF Mono',monospace;\">0</span>", None))
        self.legendTimeLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: transparent;", None))
        self.legendTimeLabel.setText(QCoreApplication.translate("MainWindow", u"<span style=\"color:#555;font-size:9px;font-weight:600;letter-spacing:1px;\">TIME</span><br><span style=\"color:#fff;font-size:14px;font-weight:600;font-family:'Menlo','SF Mono',monospace;\">0m 0s</span>", None))
        self.legendCreateMacroButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: #10b981; color: #000; font-weight: 700; font-size: 11px; border: none; border-radius: 0px; letter-spacing: 1px;", None))
        self.legendCreateMacroButton.setText(QCoreApplication.translate("MainWindow", u"CREATE MACRO", None))
        self.legendImportMacroButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: #0a0a0a; color: #999; font-size: 11px; border: 1px solid #2a2a2a; border-radius: 0px;", None))
        self.legendImportMacroButton.setText(QCoreApplication.translate("MainWindow", u"IMPORT MACRO", None))
        self.legendSelectMacroButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: #0a0a0a; color: #999; font-size: 11px; border: 1px solid #2a2a2a; border-radius: 0px;", None))
        self.legendSelectMacroButton.setText(QCoreApplication.translate("MainWindow", u"SELECT MACRO", None))
        self.bossRushModeGroup.setTitle("")
        self.bossRushImageFrame.setStyleSheet(QCoreApplication.translate("MainWindow", u"border: none; background-repeat: no-repeat; background-position: center;", None))
        self.bossRushImageOverlay.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(17,17,17,0), stop:0.4 rgba(17,17,17,30), stop:0.7 rgba(17,17,17,160), stop:1 rgba(17,17,17,255)); border: none;", None))
        self.bossRushModeLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #999; font-size: 10px; font-weight: 700; letter-spacing: 2px; background: transparent;", None))
        self.bossRushModeLabel.setText(QCoreApplication.translate("MainWindow", u"BOSS RUSH", None))
        self.bossRushActiveLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #10b981; font-size: 10px; font-weight: 700; letter-spacing: 1px; background: transparent;", None))
        self.bossRushActiveLabel.setText(QCoreApplication.translate("MainWindow", u"ACTIVE", None))
        self.bossRushMapLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #555; font-size: 9px; font-weight: 600; letter-spacing: 1px; background: transparent;", None))
        self.bossRushMapLabel.setText(QCoreApplication.translate("MainWindow", u"MAP", None))
        self.bossRushMacroLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #555; font-size: 9px; font-weight: 600; letter-spacing: 1px; background: transparent;", None))
        self.bossRushMacroLabel.setText(QCoreApplication.translate("MainWindow", u"ACTIVE MACRO", None))
        self.bossRushRunsLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: transparent;", None))
        self.bossRushRunsLabel.setText(QCoreApplication.translate("MainWindow", u"<span style=\"color:#555;font-size:9px;font-weight:600;letter-spacing:1px;\">RUNS</span><br><span style=\"color:#fff;font-size:14px;font-weight:600;font-family:'Menlo','SF Mono',monospace;\">0</span>", None))
        self.bossRushTotalLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: transparent;", None))
        self.bossRushTotalLabel.setText(QCoreApplication.translate("MainWindow", u"<span style=\"color:#555;font-size:9px;font-weight:600;letter-spacing:1px;\">TOTAL</span><br><span style=\"color:#fff;font-size:14px;font-weight:600;font-family:'Menlo','SF Mono',monospace;\">0</span>", None))
        self.bossRushTimeLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: transparent;", None))
        self.bossRushTimeLabel.setText(QCoreApplication.translate("MainWindow", u"<span style=\"color:#555;font-size:9px;font-weight:600;letter-spacing:1px;\">TIME</span><br><span style=\"color:#fff;font-size:14px;font-weight:600;font-family:'Menlo','SF Mono',monospace;\">0m 0s</span>", None))
        self.bossRushCreateMacroButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: #10b981; color: #000; font-weight: 700; font-size: 11px; border: none; border-radius: 0px; letter-spacing: 1px;", None))
        self.bossRushCreateMacroButton.setText(QCoreApplication.translate("MainWindow", u"CREATE MACRO", None))
        self.bossRushImportMacroButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: #0a0a0a; color: #999; font-size: 11px; border: 1px solid #2a2a2a; border-radius: 0px;", None))
        self.bossRushImportMacroButton.setText(QCoreApplication.translate("MainWindow", u"IMPORT MACRO", None))
        self.bossRushSelectMacroButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: #0a0a0a; color: #999; font-size: 11px; border: 1px solid #2a2a2a; border-radius: 0px;", None))
        self.bossRushSelectMacroButton.setText(QCoreApplication.translate("MainWindow", u"SELECT MACRO", None))
        self.eventsModeGroup.setTitle("")
        self.eventsImageFrame.setStyleSheet(QCoreApplication.translate("MainWindow", u"border: none; background-repeat: no-repeat; background-position: center;", None))
        self.eventsImageOverlay.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(17,17,17,0), stop:0.4 rgba(17,17,17,30), stop:0.7 rgba(17,17,17,160), stop:1 rgba(17,17,17,255)); border: none;", None))
        self.eventsModeLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #999; font-size: 10px; font-weight: 700; letter-spacing: 2px; background: transparent;", None))
        self.eventsModeLabel.setText(QCoreApplication.translate("MainWindow", u"EVENTS", None))
        self.eventsActiveLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #10b981; font-size: 10px; font-weight: 700; letter-spacing: 1px; background: transparent;", None))
        self.eventsActiveLabel.setText(QCoreApplication.translate("MainWindow", u"ACTIVE", None))
        self.eventsMapLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #555; font-size: 9px; font-weight: 600; letter-spacing: 1px; background: transparent;", None))
        self.eventsMapLabel.setText(QCoreApplication.translate("MainWindow", u"MAP", None))
        self.eventsMacroLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #555; font-size: 9px; font-weight: 600; letter-spacing: 1px; background: transparent;", None))
        self.eventsMacroLabel.setText(QCoreApplication.translate("MainWindow", u"ACTIVE MACRO", None))
        self.eventsRunsLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: transparent;", None))
        self.eventsRunsLabel.setText(QCoreApplication.translate("MainWindow", u"<span style=\"color:#555;font-size:9px;font-weight:600;letter-spacing:1px;\">RUNS</span><br><span style=\"color:#fff;font-size:14px;font-weight:600;font-family:'Menlo','SF Mono',monospace;\">0</span>", None))
        self.eventsTotalLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: transparent;", None))
        self.eventsTotalLabel.setText(QCoreApplication.translate("MainWindow", u"<span style=\"color:#555;font-size:9px;font-weight:600;letter-spacing:1px;\">TOTAL</span><br><span style=\"color:#fff;font-size:14px;font-weight:600;font-family:'Menlo','SF Mono',monospace;\">0</span>", None))
        self.eventsTimeLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: transparent;", None))
        self.eventsTimeLabel.setText(QCoreApplication.translate("MainWindow", u"<span style=\"color:#555;font-size:9px;font-weight:600;letter-spacing:1px;\">TIME</span><br><span style=\"color:#fff;font-size:14px;font-weight:600;font-family:'Menlo','SF Mono',monospace;\">0m 0s</span>", None))
        self.eventsCreateMacroButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: #10b981; color: #000; font-weight: 700; font-size: 11px; border: none; border-radius: 0px; letter-spacing: 1px;", None))
        self.eventsCreateMacroButton.setText(QCoreApplication.translate("MainWindow", u"CREATE MACRO", None))
        self.eventsImportMacroButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: #0a0a0a; color: #999; font-size: 11px; border: 1px solid #2a2a2a; border-radius: 0px;", None))
        self.eventsImportMacroButton.setText(QCoreApplication.translate("MainWindow", u"IMPORT MACRO", None))
        self.eventsSelectMacroButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: #0a0a0a; color: #999; font-size: 11px; border: 1px solid #2a2a2a; border-radius: 0px;", None))
        self.eventsSelectMacroButton.setText(QCoreApplication.translate("MainWindow", u"SELECT MACRO", None))
        self.dungeonModeGroup.setTitle("")
        self.dungeonImageFrame.setStyleSheet(QCoreApplication.translate("MainWindow", u"border: none; background-repeat: no-repeat; background-position: center;", None))
        self.dungeonImageOverlay.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(17,17,17,0), stop:0.4 rgba(17,17,17,30), stop:0.7 rgba(17,17,17,160), stop:1 rgba(17,17,17,255)); border: none;", None))
        self.dungeonModeLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #999; font-size: 10px; font-weight: 700; letter-spacing: 2px; background: transparent;", None))
        self.dungeonModeLabel.setText(QCoreApplication.translate("MainWindow", u"DUNGEONS", None))
        self.dungeonActiveLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #10b981; font-size: 10px; font-weight: 700; letter-spacing: 1px; background: transparent;", None))
        self.dungeonActiveLabel.setText(QCoreApplication.translate("MainWindow", u"ACTIVE", None))
        self.dungeonMapLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #555; font-size: 9px; font-weight: 600; letter-spacing: 1px; background: transparent;", None))
        self.dungeonMapLabel.setText(QCoreApplication.translate("MainWindow", u"MAP", None))
        self.dungeonMacroLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #555; font-size: 9px; font-weight: 600; letter-spacing: 1px; background: transparent;", None))
        self.dungeonMacroLabel.setText(QCoreApplication.translate("MainWindow", u"ACTIVE MACRO", None))
        self.dungeonRunsLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: transparent;", None))
        self.dungeonRunsLabel.setText(QCoreApplication.translate("MainWindow", u"<span style=\"color:#555;font-size:9px;font-weight:600;letter-spacing:1px;\">RUNS</span><br><span style=\"color:#fff;font-size:14px;font-weight:600;font-family:'Menlo','SF Mono',monospace;\">0</span>", None))
        self.dungeonTotalLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: transparent;", None))
        self.dungeonTotalLabel.setText(QCoreApplication.translate("MainWindow", u"<span style=\"color:#555;font-size:9px;font-weight:600;letter-spacing:1px;\">TOTAL</span><br><span style=\"color:#fff;font-size:14px;font-weight:600;font-family:'Menlo','SF Mono',monospace;\">0</span>", None))
        self.dungeonTimeLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: transparent;", None))
        self.dungeonTimeLabel.setText(QCoreApplication.translate("MainWindow", u"<span style=\"color:#555;font-size:9px;font-weight:600;letter-spacing:1px;\">TIME</span><br><span style=\"color:#fff;font-size:14px;font-weight:600;font-family:'Menlo','SF Mono',monospace;\">0m 0s</span>", None))
        self.dungeonCreateMacroButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: #10b981; color: #000; font-weight: 700; font-size: 11px; border: none; border-radius: 0px; letter-spacing: 1px;", None))
        self.dungeonCreateMacroButton.setText(QCoreApplication.translate("MainWindow", u"CREATE MACRO", None))
        self.dungeonImportMacroButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: #0a0a0a; color: #999; font-size: 11px; border: 1px solid #2a2a2a; border-radius: 0px;", None))
        self.dungeonImportMacroButton.setText(QCoreApplication.translate("MainWindow", u"IMPORT MACRO", None))
        self.dungeonSelectMacroButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: #0a0a0a; color: #999; font-size: 11px; border: 1px solid #2a2a2a; border-radius: 0px;", None))
        self.dungeonSelectMacroButton.setText(QCoreApplication.translate("MainWindow", u"SELECT MACRO", None))
        self.overlayWebhookGroup.setTitle("")
        self.overlayWebhookLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #555; font-size: 10px; font-weight: 700; letter-spacing: 2px; background: transparent;", None))
        self.overlayWebhookLabel.setText(QCoreApplication.translate("MainWindow", u"WEBHOOK", None))
        self.overlayWebhookToggleButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: #0a0a0a; color: #999; border: 1px solid #2a2a2a; border-radius: 0px; font-size: 11px;", None))
        self.overlayWebhookToggleButton.setText(QCoreApplication.translate("MainWindow", u"Disabled", None))
        self.overlayWebhookUrlInput.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: #0a0a0a; color: #ccc; border: 1px solid #2a2a2a; border-radius: 0px; padding: 4px 10px; font-size: 11px;", None))
        self.overlayWebhookUrlInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Enter Discord webhook URL...", None))
        self.overlayWebhookTestButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: #0a0a0a; color: #999; border: 1px solid #2a2a2a; border-radius: 0px; font-size: 11px;", None))
        self.overlayWebhookTestButton.setText(QCoreApplication.translate("MainWindow", u"Test", None))
        self.mainPageTitle.setText(QCoreApplication.translate("MainWindow", u"Saved Macros", None))
        self.mainStatusLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #666666; font-size: 15px; font-weight: 700; background: transparent; font-family: \"Space Mono\", \"Menlo\", monospace; letter-spacing: 0.5px;", None))
        self.mainStatusLabel.setText("")
        self.stopMacroButton.setText(QCoreApplication.translate("MainWindow", u"Stop Macro", None))
        self.advancedCreateButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"background-color: #2A2A2A; color: #E0E0E0; border: 1px solid #333333;", None))
        self.advancedCreateButton.setText(QCoreApplication.translate("MainWindow", u"Advanced Create", None))
        self.editAdvancedButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"background-color: #2A2A2A; color: #E0E0E0; border: 1px solid #333333;", None))
        self.editAdvancedButton.setText(QCoreApplication.translate("MainWindow", u"Edit Advanced Macro", None))
        self.webhookGroup.setTitle(QCoreApplication.translate("MainWindow", u"Discord Webhook", None))
        self.webhookToggleButton.setText(QCoreApplication.translate("MainWindow", u"Disabled", None))
        self.webhookUrlInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Enter Discord webhook URL...", None))
        self.webhookTestButton.setText(QCoreApplication.translate("MainWindow", u"Test", None))
        self.rightPanelBackground.setStyleSheet(QCoreApplication.translate("MainWindow", u"background-color: #000000; border: none;", None))
        self.advTrafficLightBar.setStyleSheet(QCoreApplication.translate("MainWindow", u"background-color: #000000;", None))
        self.advancedStepsLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #888888; font-family: \"Inter\", sans-serif; font-size: 11px; font-weight: 700; letter-spacing: 2; background-color: #000000; border-bottom: 1px solid #2a2a2a;", None))
        self.advancedStepsLabel.setText(QCoreApplication.translate("MainWindow", u"MACRO STEPS", None))
        self.advCloseButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"background-color: #FF5F57; border-radius: 6px; border: none; padding: 0px;", None))
        self.advCloseButton.setText("")
        self.tabContentBackground.setStyleSheet(QCoreApplication.translate("MainWindow", u"background-color: #0a0a0a;", None))
        self.unitSelectionGroup.setTitle("")
        self.unitSelectionHeaderLabel.setText(QCoreApplication.translate("MainWindow", u"UNITS", None))
        self.unit1Group.setTitle("")
        self.unit1HeaderLabel.setText(QCoreApplication.translate("MainWindow", u"Unit 1:", None))
        self.unit1NameInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Enter Unit", None))
        self.unit1CoordsLabel.setText(QCoreApplication.translate("MainWindow", u"X: 512  Y: 822", None))
        self.unit1SavedLabel.setText("")
        self.unit2Group.setTitle("")
        self.unit2HeaderLabel.setText(QCoreApplication.translate("MainWindow", u"Unit 2:", None))
        self.unit2NameInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Enter Unit", None))
        self.unit2CoordsLabel.setText(QCoreApplication.translate("MainWindow", u"X: 602  Y: 825", None))
        self.unit2SavedLabel.setText("")
        self.unit3Group.setTitle("")
        self.unit3HeaderLabel.setText(QCoreApplication.translate("MainWindow", u"Unit 3:", None))
        self.unit3NameInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Enter Unit", None))
        self.unit3CoordsLabel.setText(QCoreApplication.translate("MainWindow", u"X: 681  Y: 821", None))
        self.unit3SavedLabel.setText("")
        self.unit4Group.setTitle("")
        self.unit4HeaderLabel.setText(QCoreApplication.translate("MainWindow", u"Unit 4:", None))
        self.unit4NameInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Enter Unit", None))
        self.unit4CoordsLabel.setText(QCoreApplication.translate("MainWindow", u"X: 782  Y: 825", None))
        self.unit4SavedLabel.setText("")
        self.unit5Group.setTitle("")
        self.unit5HeaderLabel.setText(QCoreApplication.translate("MainWindow", u"Unit 5:", None))
        self.unit5NameInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Enter Unit", None))
        self.unit5CoordsLabel.setText(QCoreApplication.translate("MainWindow", u"X: 868  Y: 821", None))
        self.unit5SavedLabel.setText("")
        self.unit6Group.setTitle("")
        self.unit6HeaderLabel.setText(QCoreApplication.translate("MainWindow", u"Unit 6:", None))
        self.unit6NameInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Enter Unit", None))
        self.unit6CoordsLabel.setText(QCoreApplication.translate("MainWindow", u"X: 953  Y: 825", None))
        self.unit6SavedLabel.setText("")
        self.upgradeGroup.setTitle("")
        self.upgradeHeaderLabel.setText(QCoreApplication.translate("MainWindow", u"\u21bb  UNIT UPGRADE", None))
        self.upgradeUnitLabel.setText(QCoreApplication.translate("MainWindow", u"UNIT", None))
        self.upgradePlacementLabel.setText(QCoreApplication.translate("MainWindow", u"PLACEMENT", None))
        self.upgradeCountLabel.setText(QCoreApplication.translate("MainWindow", u"UPGRADES", None))
        self.upgradeCountInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"1", None))
        self.autoUpgradeCheckBox.setText(QCoreApplication.translate("MainWindow", u"Auto Upgrade", None))
        self.upgradeNoPlacementsLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #FF4D4F; font-size: 10px; background-color: transparent;", None))
        self.upgradeNoPlacementsLabel.setText("")
        self.addUpgradeStepButton.setStyleSheet("")
        self.addUpgradeStepButton.setText(QCoreApplication.translate("MainWindow", u"Add Upgrade Step", None))
        self.placeGroup.setTitle("")
        self.placeHeaderLabel.setText(QCoreApplication.translate("MainWindow", u"+  UNIT PLACE", None))
        self.placeUnitLabel.setText(QCoreApplication.translate("MainWindow", u"UNIT", None))
        self.placementColHeaderLabel.setText(QCoreApplication.translate("MainWindow", u"PLACEMENT", None))
        self.placementCounterLabel.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.placeXLabel.setText(QCoreApplication.translate("MainWindow", u"X", None))
        self.placeXInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"0", None))
        self.placeYLabel.setText(QCoreApplication.translate("MainWindow", u"Y", None))
        self.placeYInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"0", None))
        self.placeUntilEmptyCheckbox.setText(QCoreApplication.translate("MainWindow", u"Place until empty", None))
        self.addPlaceStepButton.setStyleSheet("")
        self.addPlaceStepButton.setText(QCoreApplication.translate("MainWindow", u"Add Place Step", None))
        self.recordPlaceClickButton.setStyleSheet("")
        self.recordPlaceClickButton.setText(QCoreApplication.translate("MainWindow", u"Record Click", None))
        self.advancedWaitGroup.setTitle("")
        self.waitHeaderLabel.setText(QCoreApplication.translate("MainWindow", u"WAIT", None))
        self.advancedWaitSecondsRadio.setText(QCoreApplication.translate("MainWindow", u"Wait for Seconds", None))
        self.advancedWaitSecondsInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"1.0", None))
        self.advancedWaitSecondsLabel.setText(QCoreApplication.translate("MainWindow", u"SEC", None))
        self.advancedWaitRoundRadio.setText(QCoreApplication.translate("MainWindow", u"Round Completed", None))
        self.advancedWaveLabel.setText(QCoreApplication.translate("MainWindow", u"Wave", None))
        self.advancedWaveInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"0", None))
        self.advancedWaitYenRadio.setText(QCoreApplication.translate("MainWindow", u"Wait for Yen >=", None))
        self.advancedWaitYenInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"1000", None))
        self.advancedWaitGameRadio.setText(QCoreApplication.translate("MainWindow", u"Wait for Game Start", None))
        self.addAdvancedWaitButton.setText(QCoreApplication.translate("MainWindow", u"Add Wait Step", None))
        self.advancedSaveButton.setStyleSheet("")
        self.advancedSaveButton.setText(QCoreApplication.translate("MainWindow", u"\u2b21   SAVE MACRO", None))
        self.advancedClearButton.setStyleSheet("")
        self.advancedClearButton.setText(QCoreApplication.translate("MainWindow", u"\u21ba   CLEAR STEPS", None))
        self.advBackButton.setText(QCoreApplication.translate("MainWindow", u"\u2190   BACK", None))
        self.tabUnitsButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"background-color: transparent; color: #E0E0E0; border: none; border-bottom: 2px solid #5B8DEF; border-radius: 0px; font-size: 11px; font-weight: bold; letter-spacing: 1;", None))
        self.tabUnitsButton.setText(QCoreApplication.translate("MainWindow", u"UNITS", None))
        self.tabPlaceUpgradeButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"background-color: transparent; color: #666666; border: none; border-bottom: 2px solid transparent; border-radius: 0px; font-size: 11px; font-weight: bold; letter-spacing: 1;", None))
        self.tabPlaceUpgradeButton.setText(QCoreApplication.translate("MainWindow", u"PLACE / UPGRADE", None))
        self.tabWaitButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"background-color: transparent; color: #666666; border: none; border-bottom: 2px solid transparent; border-radius: 0px; font-size: 11px; font-weight: bold; letter-spacing: 1;", None))
        self.tabWaitButton.setText(QCoreApplication.translate("MainWindow", u"WAIT", None))
        self.tabRawStepsButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"background-color: transparent; color: #666666; border: none; border-bottom: 2px solid transparent; border-radius: 0px; font-size: 11px; font-weight: bold; letter-spacing: 1;", None))
        self.tabRawStepsButton.setText(QCoreApplication.translate("MainWindow", u"RAW STEPS", None))
        self.tabSettingsButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"background-color: transparent; color: #666666; border: none; border-bottom: 2px solid transparent; border-radius: 0px; font-size: 11px; font-weight: bold; letter-spacing: 1;", None))
        self.tabSettingsButton.setText(QCoreApplication.translate("MainWindow", u"SETTINGS", None))
        self.runStopBackground.setStyleSheet(QCoreApplication.translate("MainWindow", u"background-color: #0a0a0a; border: none;", None))
        self.advRunMacroButton.setText(QCoreApplication.translate("MainWindow", u"Start Macro (Ctrl+S)", None))
        self.advStopMacroButton.setText(QCoreApplication.translate("MainWindow", u"Stop Macro (Ctrl+P)", None))
        self.reservedBottomRight.setStyleSheet(QCoreApplication.translate("MainWindow", u"background-color: #0a0a0a; border: 1px solid #2a2a2a; border-radius: 0px;", None))
        self.advancedClickGroup.setTitle("")
        self.clickHeaderLabel.setText(QCoreApplication.translate("MainWindow", u"CLICK", None))
        self.advClickXLabel.setText(QCoreApplication.translate("MainWindow", u"X", None))
        self.advClickXInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"0", None))
        self.advClickYLabel.setText(QCoreApplication.translate("MainWindow", u"Y", None))
        self.advClickYInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"0", None))
        self.advRecordClickButton.setText(QCoreApplication.translate("MainWindow", u"RECORD CLICK", None))
        self.addAdvancedClickButton.setText(QCoreApplication.translate("MainWindow", u"ADD CLICK STEP", None))
        self.advancedKeyGroup.setTitle("")
        self.keyHeaderLabel.setText(QCoreApplication.translate("MainWindow", u"KEY PRESS", None))
        self.advKeyPressRadio.setText(QCoreApplication.translate("MainWindow", u"Press Key", None))
        self.advKeyTimesLabel.setText(QCoreApplication.translate("MainWindow", u"TIMES", None))
        self.advKeyTimesInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"1", None))
        self.advKeyPressKeyLabel.setText(QCoreApplication.translate("MainWindow", u"KEY", None))
        self.advKeyInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"t", None))
        self.advKeyHoldRadio.setText(QCoreApplication.translate("MainWindow", u"Hold Key for:", None))
        self.advKeyHoldSecLabel.setText(QCoreApplication.translate("MainWindow", u"SEC", None))
        self.advKeyHoldInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"1", None))
        self.advKeyHoldKeyLabel.setText(QCoreApplication.translate("MainWindow", u"KEY", None))
        self.advKeyHoldKeyInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"t", None))
        self.addAdvancedKeyButton.setText(QCoreApplication.translate("MainWindow", u"ADD KEY STEP", None))
        self.licenseTitleLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #E0E0E0; font-size: 18px; font-weight: 600; font-family: \"Inter\", sans-serif; background: transparent;", None))
        self.licenseTitleLabel.setText(QCoreApplication.translate("MainWindow", u"Enter License Key", None))
        self.licenseKeyInput.setStyleSheet(QCoreApplication.translate("MainWindow", u"background-color: #1A1A1A; color: #E0E0E0; border: 1px solid #2A2A2A; border-radius: 6px; padding: 10px; font-size: 14px; font-family: \"Menlo\", \"SF Mono\", monospace;", None))
        self.licenseKeyInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"AV-XXXX-XXXX-XXXX", None))
        self.licenseErrorLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"color: #FF4D4F; font-size: 12px; font-family: \"Inter\", sans-serif; background: transparent;", None))
        self.licenseErrorLabel.setText("")
        self.licenseValidateButton.setStyleSheet(QCoreApplication.translate("MainWindow", u"QPushButton { background-color: #22C55E; color: #ffffff; border: none; border-radius: 6px; padding: 10px; font-size: 14px; font-weight: 600; font-family: \"Inter\", sans-serif; } QPushButton:hover { background-color: #16A34A; } QPushButton:pressed { background-color: #15803D; }", None))
        self.licenseValidateButton.setText(QCoreApplication.translate("MainWindow", u"Validate Key", None))
    # retranslateUi
