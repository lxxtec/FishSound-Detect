import json
import numpy as np
from pprint import pprint
from scipy.io.wavfile import read
from scipy.signal import spectrogram
from scipy.signal.windows import hann
from scipy.signal import savgol_filter,butter,filtfilt
from Preprocess import motion_blur
import matplotlib.pyplot as plt
import matplotlib as mpl
from time import sleep,time
import os
from PyQt5.QtCore import pyqtSignal,QObject,QThread
mpl.use('Agg')
mpl.rcParams['font.sans-serif']=['KaiTi','SimHei']#汉字字体
#mpl.rcParams['font.size']=16#字体大小
mpl.rcParams['axes.unicode_minus']=False#正常显示负号
class Transform(QThread):
    status=pyqtSignal(int)
    def __init__(self,resultsFile,downRate=3):
        super(Transform, self).__init__()
        self.file=resultsFile
        self.timeResults=None
        self.fileDirs=None
        self.downRate=downRate
        self.total = 0
        self.cur=0

    def downSample(self,data):
        idx = np.arange(0, len(data), step=self.downRate)
        tmp = data[idx]
        return tmp

    def run(self):
        self.timeResults = json.load(open(self.file, 'r'))
        self.fileDirs = list(self.timeResults.keys())

        for dir in self.fileDirs:
            self.total+=len(self.timeResults[dir])


        for idx,dir in enumerate(self.fileDirs):
            # 导入数据，并降采样
            fs,data=read(dir)
            self.fs=fs//self.downRate
            self.data=self.downSample(data)
            del fs,data
            # 时间片段
            timePieces=self.timeResults[dir]
            print(idx,dir,self.fs,len(timePieces))
            for [start,end] in timePieces:
                idxS=int(start*self.fs-0.3)
                idxE=int(end*self.fs+0.3)
                onePiece=self.data[idxS:idxE]
                print(onePiece.shape)
                # 信号处理阶段
                (ff, tt, II)=self.signalProcess(onePiece)
                plt.cla()
                plt.pcolormesh(tt+start,ff,II)
                plt.xlabel('时间/s')
                plt.ylabel('频率/Hz')
                # 获取去除文件路径和后缀的文件名
                (filepath, filename) = os.path.split(dir)
                (name, suffix) = os.path.splitext(filename)
                if not os.path.exists('./results_figs'):
                    os.mkdir('./results_figs')
                figName='./results_figs/{}_{:.2f}_{:.2f}.jpg'.format(name,start,end)

                plt.savefig(figName)
                self.cur+=1
                self.status.emit(int(self.cur*100/self.total))


    def signalProcess(self,data):
        s0max = np.max(data)
        s0min = np.min(data)
        ymax = 0.1872
        ymin = -0.2546
        data = (ymax - ymin) * (data - s0min) / (s0max - s0min) + ymin

        fc = 4000
        b, a = butter(2, 2 * fc / self.fs, 'highpass')
        data = filtfilt(b, a, data)
        data1 = savgol_filter(np.abs(data), 21, polyorder=1)
        data2 = savgol_filter(np.abs(data), 1001, polyorder=1)
        evp = savgol_filter(data1 / data2, 21, polyorder=1)
        # 小于1.2阈值的结果设置为1，然后用原始数据除以滤波后结果
        evp = np.array([1 if data < 1.2 else data for data in evp])
        data = data / evp
        window = hann(128)
        ff, tt, II = spectrogram(
            data, fs=self.fs, window=window, noverlap=len(window) * 0.98, nfft=1024)
        II = 10 * np.log10(II)
        II[II < -90] = -200
        II = motion_blur(II, degree=100, angle=45)
        II[II < -90] = -95
        return (ff, tt, II)


if __name__=='__main__':
    task=Transform('results.json',downRate=12)
    task.run()