from Executor import Executor
from PyQt5.QtCore import QThread, QObject, pyqtSignal, QWaitCondition, QMutex
from glob import glob


class Controller(QThread):
    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        self.fileList = []
        self.curList = []
        self.saveStatus = False
        self.showStatus = False
        self.sample_rate = 48000
        self.threshold = 0.6
        self.width = 0.1

        self._isPause = False
        self.cond = QWaitCondition()
        self.mutex1 = QMutex()
        self.mutex2 = QMutex()

    def pause(self):
        print('线程休眠')
        self._isPause = True

    def resume(self):
        print('线程恢复')
        self.mutex2.lock()
        self._isPause = False
        self.cond.wakeAll()
        self.mutex2.unlock()

    def run(self):
        # self.mutex1.lock()
        if self._isPause:
            self.cond.wait(self.mutex2)
        if len(self.curList) != 0:
            self.executor = Executor(self.curList, threshold=self.threshold,
                                     width=self.width, sample_rate=self.sample_rate, time_sec=60)
            self.executor.execute()
        # self.mutex1.unlock()

    def setFileList(self, fileList):
        self.fileList = fileList

    def getFileList(self):
        return self.fileList

    def setCurList(self, curList):
        self.curList = curList

    def getCurList(self):
        return self.curList


if __name__ == '__main__':
    print('hello world')
    fileList = glob.glob('.\\tempdata\\*.wav')
    ctl = Controller()
    ctl.setCurList(fileList)
    ctl.run()
