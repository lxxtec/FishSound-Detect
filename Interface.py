from Ui_interface import Ui_mainWindow
from PyQt5.QtWidgets import QWidget, QApplication, QFileDialog, QMessageBox, QMainWindow
from PyQt5.QtCore import QStringListModel
from qt_material import apply_stylesheet
from Controller import Controller
from PyQt5.QtCore import QThread, QTimer
from PyQt5.QtGui import QPixmap
from MyPlot import static_fig
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from MyPlot import static_fig, dynamic_fig, MyFig
from DataSaver import Transform
import sys
from os.path import join, abspath
from encrypt import Encryption
plt.style.use('dark_background')
mpl.rcParams['font.sans-serif'] = ['KaiTi', 'SimHei']  # 汉字字体
# mpl.rcParams['font.size']=12#字体大小
mpl.rcParams['axes.unicode_minus'] = False  # 正常显示负号


def resource_path(relative_path):
    if getattr(sys, 'frozen', False):  # 是否Bundle Resource
        base_path = sys._MEIPASS  # 系统临时目录
    else:
        base_path = abspath(".")
    return join(base_path, relative_path)


class Interface(QMainWindow):
    def __init__(self):
        super(Interface, self).__init__()

        self.ui = Ui_mainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle('鲸鱼叫声检测软件V1.1 (已激活)')

        jpgName = resource_path(join("figs", "dophine.jpg"))
        jpg = QPixmap(jpgName).scaled(self.width(), self.height())
        self.ui.lbFig.setPixmap(jpg)

        self.ui.stackedWidget.setCurrentIndex(0)
        self.ctl = Controller(self)
        # self.resize(400,600)
        self.crypt = Encryption()
        if self.crypt.tryMode == True:
            self.setWindowTitle('鲸鱼叫声检测软件V1.1 (10天试用)')
        if self.crypt.outDated == True:
            self.setWindowTitle('鲸鱼叫声检测软件V1.1 (已过期)')
        self.ui.ldUuid.setText(self.crypt.localCode)

        self.figInit()
        self.timer = QTimer()
        self.timer.stop()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.do_timer_timeout)

        self.ui.cbSave.stateChanged.connect(self.do_save_status)
        self.ui.cbShow.stateChanged.connect(self.do_show_status)

    def figInit(self):
        self.fig = static_fig(width=6, height=3, dpi=80)
        self.ui.hLayout.addWidget(self.fig)

    def do_DataSaver(self):
        pass
        # self.saver=Transform('results.json',downRate=self.ctl.executor.down_rate)
        # self.saver.finished.connect(self.do_stop_status)
        # self.saver.status.connect(self.ui.pgSaver.setValue)
        # self.saver.start()

    def do_save_status(self):
        if self.ui.cbSave.isChecked():
            self.ctl.saveStatus = True
        else:
            self.ctl.saveStatus = False

    def do_stop_status(self):
        QMessageBox.information(self, '提示', '计算完成，结果已保存')

    def do_show_status(self):
        if self.ui.cbShow.isChecked():
            self.ctl.showStatus = True
        else:
            self.ctl.showStatus = False
        # print(self.ctl.showStatus)

    def on_btTry_pressed(self):
        if self.crypt.working == True:
            self.ui.stackedWidget.setCurrentIndex(2)

    def on_btReg_pressed(self):
        self.ui.stackedWidget.setCurrentIndex(1)
        self.ui.lbLastDate.setText(self.crypt.lastDate)
        # self.ui.ldUuid.setText(self.crypt.localCode)

    def on_btReg2_pressed(self):
        self.crypt.decrypt(self.ui.tdRegCode.toPlainText())
        if self.crypt.singleReg == True:
            QMessageBox.information(self, '提示', '注册成功！')
            self.ui.lbLastDate.setText(self.crypt.lastDate)
            self.crypt.singleReg = False
            self.ui.ldUuid.setText(self.crypt.localCode)
            self.setWindowTitle('鲸鱼叫声检测软件V1.1 (已激活)')

    def on_btRegBk_pressed(self):
        self.ui.stackedWidget.setCurrentIndex(0)
        self.crypt.checkRegStatus()

    def on_btMain_pressed(self):
        if self.crypt.working == True:
            self.ui.stackedWidget.setCurrentIndex(2)

    def on_btCheckFile_pressed(self):
        if self.ctl.isRunning():
            # self.figUpdate.setII(self.ctl.executor.II)
            # self.thread2.start()
            self.fig.axes.pcolormesh(self.ctl.executor.II)
            self.fig.draw()
        else:
            QMessageBox.information(self, '提示', '没有正在计算的数据')

    def do_timer_timeout(self):
        self.ui.pbCurlist.setValue(self.ctl.executor.generator.listPg())
        self.ui.pbCurfile.setValue(self.ctl.executor.generator.filePg())
        self.ui.lbFrame.setText(str(self.ctl.executor.sig+1))
        if self.ctl.executor.finished == True:
            self.ctl.executor.finished = False
            QMessageBox.information(self, '提示', '计算完毕，结果已保存')

        # print(self.ctl.executor.down_rate)
        # if self.ctl.isRunning():
        #     self.ui.lbStatus_2.setText(self.ctl.executor.curFileName)
        # else:
        #     self.ui.lbStatus_2.setText('')

    def on_btCalcu_pressed(self):
        if self.ui.cbBatchExec.isChecked():  # 批处理被选中
            print('start calculate batch file !')
            self.ctl.setCurList(self.ctl.getFileList())
        elif self.ui.lwFileList.currentItem() == None:  # 没有批处理，并且没有选文件
            reply = QMessageBox.information(self, '提示', '请至少选择一个文件后执行')
            return
        else:  # 没有批处理，有选中文件
            filename = self.ui.lwFileList.currentItem().text()
            print('start calculate single file !')
            self.ctl.setCurList([filename])
        print(self.ctl.getCurList())
        self.ctl.sample_rate = eval(self.ui.ldSampleRate.text())
        self.ctl.threshold = eval(self.ui.ldThresHold.text())
        self.ctl.width = eval(self.ui.ldWideThold.text())
        if self.ctl.saveStatus == True:
            self.ctl.finished.connect(self.do_DataSaver)
        if self.ctl.isRunning() == False:
            self.ctl.start()
            self.timer.start()
        else:
            QMessageBox.information(self, '提示', '已经有任务正在运行')

    def on_btStop_pressed(self):
        print('Stop!!!')
        self.ctl.terminate()
        QMessageBox.information(self, '提示', '任务已终止')

    def on_btPause_pressed(self):
        print('paused!!!')
        self.ctl.pause()

    def on_btOpenDir_pressed(self):
        # print('openDir')
        fileLists, urls = QFileDialog.getOpenFileNames(
            caption='请选择音频文件',
            directory='./',
            filter="music(*wav)")
        slm = QStringListModel(self)
        slm.setStringList(fileLists)
        self.ui.lwFileList.clear()
        self.ui.lwFileList.addItems(fileLists)
        self.ctl.setFileList(fileLists)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = Interface()
    # widget.setWindowTitle('鲸鱼叫声检测软件V1.1')
    widget.setFixedSize(widget.width(), widget.height())
    apply_stylesheet(app, theme='dark_blue.xml')
    widget.show()
    app.exec()
