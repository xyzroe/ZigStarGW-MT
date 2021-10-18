import sys
import traceback

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QPixmap

from ui import about, version

import asyncio, webbrowser, json, re

import cc2538_bsl

from zigpy_znp.api import ZNP
from zigpy_znp.tools import nvram_reset, nvram_read, nvram_write
from zigpy_znp.config import CONFIG_SCHEMA



class LabelClickable(QtWidgets.QLabel):

    clicked = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(LabelClickable, self).__init__(parent)

    def mouseReleaseEvent(self, event):
        self.clicked.emit("")


class About(QtWidgets.QDialog, about.Ui_Dialog):
    def __init__(self, parent=None):
        super(About, self).__init__(parent)
        self.setupUi(self)
        self.label_version.setText('v'+version.version)

        self.labelImagen1 = LabelClickable(self)
        self.labelImagen1.setGeometry(65, 230, 128, 35)
        self.labelImagen1.setToolTip("Buy me a coffee")
        self.labelImagen1.setCursor(QtCore.Qt.PointingHandCursor)                  
        self.pixmapImagen1 = QPixmap(':/ui/images/coffee.png').scaled(128, 35, QtCore.Qt.KeepAspectRatio,
                                     QtCore.Qt.SmoothTransformation)
        self.labelImagen1.setPixmap(self.pixmapImagen1)

        self.labelImagen1.clicked.connect(self.Clic1)


        self.labelImagen2 = LabelClickable(self)
        self.labelImagen2.setGeometry(330, 140, 90, 90)
        self.labelImagen2.setToolTip("t.me/xyzroe")
        self.labelImagen2.setCursor(QtCore.Qt.PointingHandCursor)                  
        self.pixmapImagen2 = QPixmap(':/ui/images/xyzroe.png').scaled(90, 90, QtCore.Qt.KeepAspectRatio,
                                     QtCore.Qt.SmoothTransformation)
        self.labelImagen2.setPixmap(self.pixmapImagen2)

        self.labelImagen2.clicked.connect(self.Clic2)

    def Clic1(self, accion):
        webbrowser.open('https://www.buymeacoffee.com/xyzroe')

    def Clic2(self, accion):
        webbrowser.open('https://github.com/xyzroe')



def checkDevicePort(port):
    domain = re.compile(r'^([^.:/@#]+)(\.[^.:/@#]+)+:(\d+)$')

    #ipv4 = re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b')

    #ipv6 = re.compile(r'(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))') 
    
    uart_win = re.compile(r'^COM(\d+)$')

    uart_unix = re.compile(r'^/(\w+)/(\S+)$')

    mode = ""

    if domain.match(port):
        mode = "ip"
    elif uart_win.match(port) or uart_unix.match(port):
        mode = "uart"
    else:
        port = ""


    return mode, port

def getIP(string):
        return string.split(':')[-2]



def workWithFWbtn(self):
    if (self.checkBox_fw_erase.isChecked() and not self.checkBox_fw_write.isChecked() and not self.checkBox_fw_verify.isChecked()):
        self.pushButton_fw_run.setText("Start")
        #self.pushButton_fw_run.setText("Erase")
        self.pushButton_fw_run.setEnabled(True)
    elif (self.checkBox_fw_erase.isChecked() and self.checkBox_fw_write.isChecked() and not self.checkBox_fw_verify.isChecked()):
        self.pushButton_fw_run.setText("Start")
        #self.pushButton_fw_run.setText("Erase and write")
        self.pushButton_fw_run.setEnabled(True)
    elif (not self.checkBox_fw_erase.isChecked() and self.checkBox_fw_write.isChecked() and self.checkBox_fw_verify.isChecked()):
        self.pushButton_fw_run.setText("Start")
        #self.pushButton_fw_run.setText("Write and verify")
        self.pushButton_fw_run.setEnabled(True)
    elif (self.checkBox_fw_erase.isChecked() and self.checkBox_fw_write.isChecked() and self.checkBox_fw_verify.isChecked()):
        self.pushButton_fw_run.setText("Start")
        #self.pushButton_fw_run.setText("Erase, write, verify")
        self.pushButton_fw_run.setEnabled(True)
    elif (not self.checkBox_fw_erase.isChecked() and self.checkBox_fw_write.isChecked() and not self.checkBox_fw_verify.isChecked()):
        self.pushButton_fw_run.setText("Start")
        #self.pushButton_fw_run.setText("Write")
        self.pushButton_fw_run.setEnabled(True)
    elif (not self.checkBox_fw_erase.isChecked() and not self.checkBox_fw_write.isChecked() and self.checkBox_fw_verify.isChecked()):
        self.pushButton_fw_run.setText("Start")
        #self.pushButton_fw_run.setText("Verify")
        self.pushButton_fw_run.setEnabled(True)
    else:
        self.pushButton_fw_run.setText("Select one")
        self.pushButton_fw_run.setEnabled(False)




class cc2538_bsl_run(QtCore.QThread):
    mysignal = QtCore.pyqtSignal(str)
    
    def  __init__(self, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.parent = parent

    def run(self):
        asyncio.run(workCC(self))
        
async def workCC(self):
        #print(self.parent.conf)
        defs = {
            'baud': 500000,
            'force_speed': 0,
            'bootloader_active_high': False,
            'bootloader_invert_lines': False,
        }
        cmd = cc2538_bsl.CommandInterface()
        try:
            cmd.open(self.parent.conf['port'], defs['baud'])
            cmd.invoke_bootloader(defs['bootloader_active_high'],
                                defs['bootloader_invert_lines'])
            cc2538_bsl.mdebug(5, "Opening port %(port)s, baud %(baud)d"
                    % {'port': self.parent.conf['port'], 'baud': defs['baud']})
                    
            if self.parent.conf['write'] or self.parent.conf['verify']:
                cc2538_bsl.mdebug(5, "Reading data from %s" % self.parent.conf['file'])
                firmware = cc2538_bsl.FirmwareFile(self.parent.conf['file'])

            cc2538_bsl.mdebug(5, "Connecting to target...")
        
            if not cmd.sendSynch():
                cc2538_bsl.mdebug(3, "Can't connect to target. Ensure boot loader "
                                    "is started. (no answer on synch sequence)")

            chip_id = cmd.cmdGetChipId()
            chip_id_str = cc2538_bsl.CHIP_ID_STRS.get(chip_id, None)

            if chip_id_str == None:
                cc2538_bsl.mdebug(10, "Unrecognized chip ID. Trying CC13xx/CC26xx")
                device = cc2538_bsl.CC26xx(cmd)
            else:
                cc2538_bsl.mdebug(10, "Target id 0x%x, %s" % (chip_id, chip_id_str))
                device = cc2538_bsl.CC2538(cmd)

            defs['address'] = device.flash_start_addr


            if defs['force_speed'] != 1 and device.has_cmd_set_xosc:
                if cmd.cmdSetXOsc():  
                    cmd.close()
                    defs['baud'] = 1000000
                    cmd.open(self.parent.conf['port'], defs['baud'])
                    cc2538_bsl.mdebug(6, "Opening port %(port)s, baud %(baud)d"
                            % {'port': self.parent.conf['port'], 'baud': defs['baud']})
                    cc2538_bsl.mdebug(6, "Reconnecting to target at higher speed...")
                    if (cmd.sendSynch() != 1):
                        cc2538_bsl.mdebug(3, "Can't connect to target after clock "
                                            "source switch. (Check external "
                                            "crystal)")
                else:
                    cc2538_bsl.mdebug(3, "Can't switch target to external clock "
                                        "source. (Try forcing speed)")

            if self.parent.conf['erase']:
                cc2538_bsl.mdebug(5, "Performing mass erase")
                if device.erase():
                    cc2538_bsl.mdebug(5, "Erase done")
                else:
                    cc2538_bsl.mdebug(3, "Erase failed")

            if self.parent.conf['write']:
                if cmd.writeMemory(defs['address'], firmware.bytes):
                    cc2538_bsl.mdebug(5, "Write done                                ")
                else:
                    cc2538_bsl.mdebug(3, "Write failed                       ")

            if self.parent.conf['verify']:
                cc2538_bsl.mdebug(5, "Verifying by comparing CRC32 calculations.")

                crc_local = firmware.crc32()
                crc_target = device.crc(defs['address'], len(firmware.bytes))

                if crc_local == crc_target:
                    cc2538_bsl.mdebug(5, "Verified (match: 0x%08x)" % crc_local)
                else:
                    cmd.cmdReset()
                    raise Exception("NO CRC32 match: Local = 0x%x, "
                                    "Target = 0x%x" % (crc_local, crc_target))
        except Exception:
            e = sys.exc_info()[1] 
            if (e.args):
                cc2538_bsl.mdebug(3, e.args[0])



class zigpy_NVRAM(QtCore.QThread):
    mysignal = QtCore.pyqtSignal(str)
    
    def  __init__(self, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.parent = parent

    def run(self):
        asyncio.run(workZNP(self))
        
async def workZNP(self):
        znp = ZNP(CONFIG_SCHEMA({"device": {"path": self.parent.port}}))
        try:
            await znp.connect()
            if self.parent.action == 0:
                await nvram_reset.nvram_reset(znp)
            if self.parent.action == 1:
                f = open(self.parent.file, 'w') 
                obj = await nvram_read.nvram_read(znp) 
                f.write(json.dumps(obj, indent=4) + "\n") 
            if self.parent.action == 2:
                f = open(self.parent.file, 'r')
                backup = json.load(f)
                await nvram_write.nvram_write(znp, backup)
            znp.close()
            self.mysignal.emit("zigpy_znp.tools - Finished")    
            self.parent.updateProgress.emit(100)   
        except Exception:
            e = sys.exc_info()[1] 
            f = traceback.format_exc()
            if (e.args):
                self.mysignal.emit(e.args[0])
            else: 
                if 'concurrent.futures._base.TimeoutError' in f:
                    self.mysignal.emit("zigpy_znp.tools - timeout error. Try to restart Zigbee module")  
                else:
                    self.mysignal.emit("zigpy_znp.tools - unknown error!")    