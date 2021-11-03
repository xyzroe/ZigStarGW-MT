#!/usr/bin/python3
import sys

from PyQt5 import QtWidgets, QtCore, QtNetwork, QtGui
from PyQt5.QtGui import QPixmap


import logging, webbrowser, functools, serial

# explicit import for py2exe - to fix "socket://" url issue
import serial.urlhandler.protocol_socket 

from ui import main, etc

#import resources_rc

import glob

from zeroconf import ServiceBrowser, Zeroconf
import socket

class ComboBox(QtWidgets.QComboBox):
    def addItem(self, item):
        if item not in self.get_set_items():
            super(ComboBox, self).addItem(item)

    def addItems(self, items):
        items = list(self.get_set_items() | set(items))
        super(ComboBox, self).addItems(items)

    def get_set_items(self):
        return set([self.itemText(i) for i in range(self.count())])


logging.basicConfig(level=logging.DEBUG)


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



class MyListener():
    def __init__(self, parent):
        self.parent = parent

    def update_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        self.parent.updateList.emit(socket.inet_ntoa(info.addresses[0]) + ":" + str(info.port))  

    def remove_service(self, zeroconf, type, name):
        print("Service %s removed" % (name,))
        info = zeroconf.get_service_info(type, name)
        print(socket.inet_ntoa(info.addresses[0]) + ":" + str(info.port))  

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        self.parent.updateList.emit(socket.inet_ntoa(info.addresses[0]) + ":" + str(info.port))  
            
        

class MainWindow(QtWidgets.QMainWindow, main.Ui_MainWindow):
    updateProgress = QtCore.pyqtSignal(int)
    updateList = QtCore.pyqtSignal(str)
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

        #self.pushButton_fw_run.setEnabled(False)
        self.pushButton_fw_run.setText("Read IEEE")
        self.pushButton_fw_run.clicked.connect(self.flashBtnClick)

        self.checkBox_fw_verify.setEnabled(False)
        self.checkBox_fw_write.setEnabled(False)
        self.checkBox_fw_erase.clicked.connect(self.clickChecks)
        self.checkBox_fw_verify.clicked.connect(self.clickChecks)
        self.checkBox_fw_write.clicked.connect(self.clickChecks)

        self.checkBox_ieee_write.clicked.connect(self.clickChecks)
        self.checkBox_ieee_write.setEnabled(False)
        self.lineEdit_ieee.textEdited.connect(self.editIEEE)

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
        self.progressBar.setProperty("value", 0)   

        self.comboBox = ComboBox(self.centralwidget)
        self.comboBox.setGeometry(QtCore.QRect(120, 190, 320, 35))
        font = QtGui.QFont()
        font.setPointSize(18)
        self.comboBox.setFont(font)
        self.comboBox.setEditable(True)

        self.updateList.connect(self.comboBox.addItem)
        self.onListChange("")
        self.comboBox.editTextChanged.connect(self.onListChange)

        zeroconf = Zeroconf()
        listener = MyListener(self)
        browser1 = ServiceBrowser(zeroconf, "_zig_star_gw._tcp.local.", listener)
        browser2 = ServiceBrowser(zeroconf, "_zigstar_gw._tcp.local.", listener)

        self.pushButton_update.clicked.connect(self.updateSerialPorts)


        self.pathFW = ''
        self.msgs = 0



        self.initMenu()

        #OUTPUT_LOGGER_STDOUT.emit_write.connect(self.print_cc_log)
        OUTPUT_LOGGER_STDERR.emit_write.connect(self.print_cc_log)

    def onListChange(self, text):
        mode, port = etc.checkDevicePort(text)
        #print (mode, port)
        if mode == "ip":
            self.pushButton_rst_esp.setEnabled(True)
            self.pushButton_rst_zigbee.setEnabled(True)
            self.checkBox_bsl.setEnabled(True)
            self.checkBox_bsl.setChecked(True)
        else:
            self.pushButton_rst_esp.setEnabled(False)
            self.pushButton_rst_zigbee.setEnabled(False)
            self.checkBox_bsl.setEnabled(False)
            self.checkBox_bsl.setChecked(False)
        if mode:
            self.mode = mode
            self.dev = port
            if self.mode == "ip":
                self.port = 'socket://' + self.dev
            else:
                self.port = self.dev
            self.pushButton_nv_erase.setEnabled(True)
            self.pushButton_nv_read.setEnabled(True)
            self.pushButton_nv_write.setEnabled(True)
        else:
            self.pushButton_nv_erase.setEnabled(False)
            self.pushButton_nv_read.setEnabled(False)
            self.pushButton_nv_write.setEnabled(False)


    def updateSerialPorts(self):

        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        #result = []
        #result.append("----------")
        for port in ports:
            try:
                if sys.platform.startswith('win'):
                    s = serial.Serial(port)
                    s.close()
                #result.append(port)
                self.comboBox.addItem(port)
            except (OSError, serial.SerialException):
                pass
        #return result

        #self.comboBox.addItems(serial_ports())


    def print_cc_log(self, text, severity):
        msg = text.lstrip()
        if 'Primary IEEE Address:' in msg: 
            self.lineEdit_ieee.setText(msg[int(msg.find(':')+1):])
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
        self.checkBox_ieee_write.setEnabled(False)
        self.lineEdit_ieee.setEnabled(False)


    def on_finished_CC(self):
        self.pushButton_fw_run.setEnabled(True)
        self.checkBox_fw_erase.setEnabled(True)
        if (self.file_name.text() != "select file"):
            self.checkBox_fw_verify.setEnabled(True)
            self.checkBox_fw_write.setEnabled(True)
        self.progressBar.setProperty("value", 100) 

        self.lineEdit_ieee.setEnabled(True)
        if (self.lineEdit_ieee.text() != ""):
            self.checkBox_ieee_write.setEnabled(True)

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
            #self.port = 'socket://' + self.lineEdit_ip.text() + ':' + self.lineEdit_port.text()
            self.action = 1
            self.zigpy_thread.start()  

    def showOpenNV(self):    
        options = QtWidgets.QFileDialog.Options()
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self,"Open NVRAM backup", "","NVRAM backup Files (*.json)", options=options)
        if fileName:
            self.file = fileName
            #self.port = 'socket://' + self.lineEdit_ip.text() + ':' + self.lineEdit_port.text()
            self.action = 2
            self.zigpy_thread.start() 

    def sendNVerase(self):
        #self.port = 'socket://' + self.lineEdit_ip.text() + ':' + self.lineEdit_port.text()
        self.action = 0
        self.zigpy_thread.start()  


    def editIEEE(self):
        etc.workWithIEEEline(self)

    def clickChecks(self):
        etc.workWithFWbtn(self)
    
    def flashBtnClick(self):
        if self.checkBox_bsl.isChecked():
            self.sendCmdGW('enableBSL')
        else: 
            QtCore.QTimer.singleShot(
                100,
                functools.partial(self.runBSL)
            )

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
        url = "http://" + etc.getIP(self.dev) + "/" + url
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
            'port': self.port,
            'file': self.pathFW,
            'erase': self.checkBox_fw_erase.isChecked(),
            'write': self.checkBox_fw_write.isChecked(),
            'verify': self.checkBox_fw_verify.isChecked(),
            'ieee_write': self.checkBox_ieee_write.isChecked(),
            'ieee': self.lineEdit_ieee.text()
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
