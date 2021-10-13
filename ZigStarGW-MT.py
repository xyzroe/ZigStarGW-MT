#!/usr/bin/python3
import sys

from PyQt5 import QtWidgets, QtCore, QtNetwork
from PyQt5.QtGui import QPixmap


import logging, webbrowser, functools, serial

# explicit import for py2exe - to fix "socket://" url issue
import serial.urlhandler.protocol_socket 

from ui import main, etc

#import resources_rc



#logging.basicConfig(level=logging.DEBUG)


#logger cc2538
class ccLogger(QtCore.QObject):
    emit_write = QtCore.pyqtSignal(str, int)

    class Severity:
        DEBUG = 0
        ERROR = 1

    def __init__(self, io_stream, severity):
        super().__init__()

        self.io_stream = io_stream
        self.severity = severity

    def write(self, text):
        self.io_stream.write(text)
        self.emit_write.emit(text, self.severity)

    def flush(self):
        self.io_stream.flush()


#OUTPUT_LOGGER_STDOUT = ccLogger(sys.stdout, ccLogger.Severity.DEBUG)
OUTPUT_LOGGER_STDERR = ccLogger(sys.stderr, ccLogger.Severity.ERROR)

#sys.stdout = OUTPUT_LOGGER_STDOUT
sys.stderr = OUTPUT_LOGGER_STDERR

#logger zigpy_znp
class znpLogger(logging.Handler):
    
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

    def emit(self, record):
        msg = self.format(record)
               
        self.parent.statusBar().showMessage(msg)
        if "Resetting" in msg:
            self.parent.updateProgress.emit(100)     
        else:    
            self.parent.msgs += 1
            if "nvram_reset" in msg:
                MagicNumber = 100/587
            else:
                MagicNumber = 100/581
            self.parent.updateProgress.emit(self.parent.msgs * MagicNumber)  




            
        

class MainWindow(QtWidgets.QMainWindow, main.Ui_MainWindow):
    updateProgress = QtCore.pyqtSignal(int)
    def __init__(self):
        super().__init__()

        self.setupUi(self)  

        self.labelLogo = etc.LabelClickable(self.centralwidget)
        self.labelLogo.setGeometry(260, 10, 140, 140)
        self.labelLogo.setToolTip("zig-star.com")
        self.labelLogo.setCursor(QtCore.Qt.PointingHandCursor)                 
        self.pixmapImagen = QPixmap(':/ui/images/zigstar.png').scaled(140, 140, QtCore.Qt.KeepAspectRatio,
                                     QtCore.Qt.SmoothTransformation)
        self.labelLogo.setPixmap(self.pixmapImagen)

        self.labelLogo.clicked.connect(self.Click)

        self.toolButton.clicked.connect(self.showOpenFW)

        self.pushButton_fw_run.setEnabled(False)
        self.pushButton_fw_run.clicked.connect(self.flashBtnClick)

        self.checkBox_fw_verify.setEnabled(False)
        self.checkBox_fw_write.setEnabled(False)
        self.checkBox_fw_erase.clicked.connect(self.clickChecks)
        self.checkBox_fw_verify.clicked.connect(self.clickChecks)
        self.checkBox_fw_write.clicked.connect(self.clickChecks)

        self.pushButton_rst_esp.clicked.connect(self.sendRestartESP)
        self.pushButton_rst_zigbee.clicked.connect(self.sendRestartZigbee)
        self.pushButton_nv_erase.clicked.connect(self.sendNVerase)
        self.pushButton_nv_read.clicked.connect(self.showSaveNV)
        self.pushButton_nv_write.clicked.connect(self.showOpenNV)


        self.zigpy_thread = etc.zigpy_NVRAM(parent=self)  
        self.zigpy_thread.started.connect(self.on_started_ZNP)
        self.zigpy_thread.finished.connect(self.on_finished_ZNP)
        self.zigpy_thread.mysignal.connect(self.on_change_ZNP, QtCore.Qt.QueuedConnection)

        self.cc2538_bsl_thread = etc.cc2538_bsl_run(parent=self)
        self.cc2538_bsl_thread.started.connect(self.on_started_CC)
        self.cc2538_bsl_thread.finished.connect(self.on_finished_CC)
        self.cc2538_bsl_thread.mysignal.connect(self.on_change_CC, QtCore.Qt.QueuedConnection)

        

        logTextBox = znpLogger(self)
        logTextBox.setFormatter(logging.Formatter('%(name)s - %(message)s'))
        logging.getLogger().addHandler(logTextBox) 
        logging.getLogger().setLevel(logging.INFO)

        self.updateProgress.connect(self.progressBar.setValue)

        self.pathFW = ''
        self.msgs = 0

        self.progressBar.setProperty("value", 0)   


        self.initMenu()

        #OUTPUT_LOGGER_STDOUT.emit_write.connect(self.print_cc_log)
        OUTPUT_LOGGER_STDERR.emit_write.connect(self.print_cc_log)



    def print_cc_log(self, text, severity):
        msg = text.lstrip()
        if not '\n' in msg:
            if len(text) > 3:
                self.statusBar().showMessage(msg)
        self.msgs += 1
        MagicNumber  = 0.069
        self.updateProgress.emit(self.msgs * MagicNumber)  

    def on_change_ZNP(self, s):
        self.statusBar().showMessage(s)

    def on_started_ZNP(self):
        self.pushButton_nv_read.setEnabled(False)
        self.pushButton_nv_write.setEnabled(False)
        self.pushButton_nv_erase.setEnabled(False)
        self.statusBar().showMessage('zigpy_znp.tools - Starting')
        self.msgs = 0
        self.progressBar.setProperty("value", 0)   

    def on_finished_ZNP(self):
        self.pushButton_nv_read.setEnabled(True)
        self.pushButton_nv_write.setEnabled(True)
        self.pushButton_nv_erase.setEnabled(True)

    def on_change_CC(self, s):
        self.statusBar().showMessage(s)

    def on_started_CC(self):
        self.statusBar().showMessage('cc2538-bsl.py - Starting')
        self.msgs = 0
        self.progressBar.setProperty("value", 0)   
        self.pushButton_fw_run.setEnabled(False)
        self.checkBox_fw_erase.setEnabled(False)
        self.checkBox_fw_verify.setEnabled(False)
        self.checkBox_fw_write.setEnabled(False)


    def on_finished_CC(self):
        self.pushButton_fw_run.setEnabled(True)
        self.checkBox_fw_erase.setEnabled(True)
        print(self.file_name.text())
        if (self.file_name.text() != "select file"):
            self.checkBox_fw_verify.setEnabled(True)
            self.checkBox_fw_write.setEnabled(True)
        self.progressBar.setProperty("value", 100) 

    def Click(self, accion):
        webbrowser.open('https://zig-star.com')

    def about_window(self):
        widget = etc.About()
        widget.exec_()

    def initMenu(self):
        exitAction = QtWidgets.QAction('&Exit', self)
        exitAction.setMenuRole(QtWidgets.QAction.NoRole)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(QtWidgets.qApp.quit)
        
        aboutAction = QtWidgets.QAction('&About', self)
        aboutAction.setMenuRole(QtWidgets.QAction.NoRole)
        aboutAction.setShortcut('Ctrl+Z')
        aboutAction.setStatusTip('About application')
        aboutAction.triggered.connect(self.about_window)
        
        menubar = self.menuBar()
        
        fileMenu = menubar.addMenu('&Menu')
        
        fileMenu.addAction(aboutAction)
        fileMenu.addAction(exitAction)

    def showOpenFW(self):
        options = QtWidgets.QFileDialog.Options()
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open firmware file', './', "Hex files (*.hex);; Bin files (*.bin)", options=options)
        if fileName:
            self.pathFW = fileName
            fname = (fileName.split('/'))[-1]
            self.file_name.setText(fname)
            self.checkBox_fw_verify.setEnabled(True)
            self.checkBox_fw_write.setEnabled(True)
            etc.workWithFWbtn(self)
        else:
            self.file_name.setText("select file")
            self.checkBox_fw_verify.setEnabled(False)
            self.checkBox_fw_write.setEnabled(False)
            self.checkBox_fw_verify.setChecked(False)
            self.checkBox_fw_write.setChecked(False)           
            etc.workWithFWbtn(self)
    
    def showSaveNV(self):
        options = QtWidgets.QFileDialog.Options()
        fileName, _ = QtWidgets.QFileDialog.getSaveFileName(self,"Save NVRAM backup","","NVRAM backup Files (*.json)", options=options)
        if fileName:
            self.file = fileName
            self.port = 'socket://' + self.lineEdit_ip.text() + ':' + self.lineEdit_port.text()
            self.action = 1
            self.zigpy_thread.start()  

    def showOpenNV(self):    
        options = QtWidgets.QFileDialog.Options()
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self,"Open NVRAM backup", "","NVRAM backup Files (*.json)", options=options)
        if fileName:
            self.file = fileName
            self.port = 'socket://' + self.lineEdit_ip.text() + ':' + self.lineEdit_port.text()
            self.action = 2
            self.zigpy_thread.start() 

    def sendNVerase(self):
        self.port = 'socket://' + self.lineEdit_ip.text() + ':' + self.lineEdit_port.text()
        self.action = 0
        self.zigpy_thread.start()  


    def clickChecks(self):
        etc.workWithFWbtn(self)
    
    def flashBtnClick(self):
        self.sendCmdGW('enableBSL')

    def sendRestartZigbee(self):
        self.sendCmdGW('rstZigbee')
        self.progressBar.setProperty("value", 0) 

    def sendRestartESP(self):
        self.sendCmdGW('rstESP')
        self.progressBar.setProperty("value", 0) 

    def sendCmdGW(self, cmd):
        url = {
                'rstESP': "reboot",
                'rstZigbee': "cmdZigRST",
                'enableBSL': "cmdZigBSL",#"switch/firmware_update/toggle"
        }[cmd]
        cmdName = {
                'rstESP': "restart ESP32",
                'rstZigbee': "restart Zigbee module",
                'enableBSL': "enable BSL mode",
        }[cmd]
        self.progressBar.setProperty("value", 0) 
        self.statusBar().showMessage("Try to " + cmdName)
        url = "http://" + self.lineEdit_ip.text() + "/" + url
        req = QtNetwork.QNetworkRequest(QtCore.QUrl(url))
        self.nam = QtNetwork.QNetworkAccessManager()
        self.nam.finished.connect(self.handleResponse)
        self.nam.get(req)    

    def handleResponse(self, reply):
        er = reply.error()
        cmd = (str(reply.url()).split('/'))[-1][:-2]
        cmdName = {
            'reboot': "restart ESP32",
            'cmdZigRST': "restart Zigbee module",
            'cmdZigBSL': "enable BSL mode",
        }[cmd]
        if er == QtNetwork.QNetworkReply.NoError:
            status = "Command to " + cmdName + " was send succesfull"
            if cmd == 'cmdZigBSL':
                status = status + ". Wait 5 seconds"
                self.statusBar().showMessage(status)
                self.on_started_CC()
                QtCore.QTimer.singleShot(
                    5000,
                    functools.partial(self.runBSL)
                )
            else:
                self.statusBar().showMessage(status)
        else:
            self.statusBar().showMessage("Error while trying to " + cmdName + " - check IP address")

    def runBSL(self):
        self.conf = {
            'port': 'socket://' + self.lineEdit_ip.text() + ':' + self.lineEdit_port.text(),
            'file': self.pathFW,
            'erase': self.checkBox_fw_erase.isChecked(),
            'write': self.checkBox_fw_write.isChecked(),
            'verify': self.checkBox_fw_verify.isChecked()
        }
        self.cc2538_bsl_thread.start()       

def main():
    QtWidgets.QApplication.setStyle('Fusion')
    app = QtWidgets.QApplication(sys.argv)  
    app.setApplicationName('ZigStarMultiTool')
    window = MainWindow() 
    window.show()  
    app.exec_()

if __name__ == '__main__': 
    main()  
