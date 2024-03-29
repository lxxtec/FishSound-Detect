from DataGenerator import DataGenerator
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from scipy.signal import savgol_filter, spectrogram
from scipy.signal import find_peaks
from time import time
from concurrent.futures import ThreadPoolExecutor
from Preprocess import preprocessing, motion_blur
from DataSaver import Transform
from PyQt5.QtCore import pyqtSignal, QObject
import json
from glob import glob


class Executor:
    def __init__(self, fileList, threshold=0.6, width=0.1, sample_rate=48000, time_sec=60):
        self.results = {'': []}
        self.threshold = threshold
        self.width = width
        self.II = 0
        self.sample_rate = sample_rate  # 目标采样率
        self.sig = 0
        self.generator = DataGenerator(fileList, time_sec=60)
        self.down_rate = self.cal_down_rate()

        self.residual = False
        self.residualPoint = 0
        self.SeqLgth = 0
        self.finished = False

    def cal_down_rate(self):
        if int(self.generator.fs) % int(self.sample_rate) == 0:
            return int(self.generator.fs)//int(self.sample_rate)
        else:
            return int(self.generator.fs)//int(self.sample_rate)+1

    def execute(self):
        print("starting executing!!!")
        while self.generator.isListEnd() == False:
            self.curFileName = self.generator.getFileName()
            (sr, s0) = self.generator.getData(self.down_rate)
            s0max = np.max(s0)
            s0min = np.min(s0)
            ymax = 0.1872
            ymin = -0.2546
            s0 = (ymax - ymin) * (s0 - s0min) / (s0max - s0min) + ymin
            (SeqLgth, NbSeq, s1Mtx, s1Res, s0Mtx,
             s0Res, fs) = preprocessing(sr, s0)
            self.SeqLgth = SeqLgth
            start = time()
            window = signal.windows.hann(128)
            curMinuteResult = []
            for idxSeq in range(0, int(NbSeq)):
                ff, tt, II = spectrogram(
                    s1Mtx[:, idxSeq], fs=fs, window=window, noverlap=len(window) * 0.98, nfft=680)
                II = 10 * np.log10(II)
                II[II < -90] = -200
                II = motion_blur(II, degree=80, angle=45)
                II[II < -90] = -95
                self.II = II
                confidence = self.DophineSniffer(II, c1=200, c2=1000, c3=501)
                res = self.getDuration(
                    confidence, self.threshold, self.width*II.shape[1]/2)
                # res2 = res
                # if len(res) != 0:
                #     tmp = II.T[res2[0][0]:res2[0][1]]
                #     fin = np.zeros(shape=(tmp.shape[0],))
                #     for idx in range(len(tmp)):
                #         # 如果第idx列最大值大于-60，就把第idx列的最大值保存到res的第idx个
                #         # find_peaks(tmp[idx],distance=30,threshold=0)
                #         if np.max(tmp[idx]) > -60:
                #             fin[idx] = np.where(tmp[idx] == np.max(tmp[idx]))[0].item()
                #             temp = tmp[idx]
                #             # plt.ion()
                #             if idx > 2000 and idx<3000:
                #                 plt.clf()
                #                 # plt.plot(ff,temp)
                #                 plt.plot(temp)
                #                 peaks, _ = find_peaks(temp, height=-60,prominence=5,distance=10)
                #                 thePeak = peaks[0]
                #
                #                 # plt.plot(ff[thePeak], temp[thePeak], "x")
                #                 plt.plot(thePeak, temp[thePeak], "x")
                #                 plt.plot(np.zeros_like(temp), "--", color="gray")
                #                 #plt.ioff()
                #                 plt.show()

                res += idxSeq * II.shape[1]
                res = res * 2 / II.shape[1] + (self.generator.prevMinutes-1)*60
                if len(res) != 0:

                    curMinuteResult.extend(res.tolist())
                    tmp = II.T

                print(idxSeq)

                self.sig = idxSeq
            self.saveResult(curMinuteResult)
            print(' 1 minutes cost: {} '.format(time() - start))
        # self.saveResult(curMinuteResult)
        print('calculate done!!!')
        self.finished = True

    def res2time(self, res):
        pass

    def getII(self):
        return self.II

    def saveResult(self, minuteRes):
        if self.curFileName in self.results:
            self.results[self.curFileName].extend(minuteRes)
        else:
            self.results[self.curFileName] = minuteRes
        if '' in self.results:
            self.results.pop('')
        with open('results.json', 'w') as f:
            json.dump(self.results, f)
            print('save done!!!')
            # Lee337 :关闭生成记录功能
        self.saver = Transform('results.json', downRate=self.down_rate)
        self.results = {'': []}
        self.saver.run()

    def DophineSniffer(self, inputs, c1=200, c2=1000, c3=501):
        start = time()
        idxNb = np.floor(inputs.shape[1] / c2)
        AllCCavg = np.zeros(shape=(int(idxNb), int(c2 + c1)))

        for idx in range(0, int(idxNb)):
            indexs = np.arange(1, c2 + c1 + 1, 1, dtype=int) + int(idx * c2)
            ThisSec = inputs[:, indexs]
            # print(ThisSec.shape)
            ThisCC = np.corrcoef(ThisSec.T)
            # 上三角矩阵
            triu1 = np.triu(ThisCC, 1)
            triu2 = np.triu(ThisCC, c1 + 1)
            AllCCavg[idx, :] = np.sum(triu1 - triu2, 1)
        cc2 = inputs[:, int(idxNb * c2):]
        LastCC = np.corrcoef(cc2.T)
        LastCC_new = np.sum(np.triu(LastCC, 1) -
                            np.triu(LastCC, int(c1 + 1)), 1)
        output_temp = np.reshape(AllCCavg[:, 1:c2 + 1], (-1,))
        last_temp = LastCC_new[1:LastCC_new.shape[0] - c1 + 1]
        output = np.r_[output_temp, last_temp]
        output_smooth = savgol_filter(output, c3, 1)
        end = time()
        print("output_smooth shape: ", output_smooth.shape)
        print('computing Done!!! run time: ', end - start)
        return output_smooth / 200

    def getDuration(self, confidence, threshold, width):
        ax = confidence - threshold
        ax[np.isnan(ax)] = -2
        head = np.nan
        tail = np.nan
        head_ext = False
        tail_ext = False
        # 列表形式返回
        res = []
        for idx in range(len(ax)):
            if ax[idx] > -1.9 and head_ext == False:
                head = idx
                head_ext = True
            elif head_ext == True and tail_ext == False and ax[idx] < -1.9 and ax[idx - 2] > -1.9:
                tail = idx
                tail_ext = True
                if np.mean(ax[head:tail]) > 0 and (tail-head) > width:
                    res.append([head-int((0.15/self.SeqLgth)*len(ax)),
                               tail+int((0.15/self.SeqLgth)*len(ax))])
            elif head_ext == True and tail_ext == True:
                # 标志清空
                head = np.nan
                tail = np.nan
                head_ext = False
                tail_ext = False

        # Lee337 本帧处理完了，如果看到上一帧有保留，就把当前帧的第一个头提前
        if self.residual == True and len(res) != 0:
            if res[0][0] < 0.05*self.sample_rate:
                res[0][0] = self.residualPoint-len(ax)  # 当前时间减2s
            self.residual = False
            self.residualPoint = 0
        if head_ext == True and tail_ext == False:  # 如果当前帧存在有头无尾的情况，说明当前帧也有残余
            self.residual = True
            self.residualPoint = head-int((0.15/self.SeqLgth)*len(ax))
        return np.array(res)


if __name__ == '__main__':
    fileList = glob(
        'C:\\Users\\Lee337\\PycharmProjects\\FishSound_release\\figs\\*.wav')

    executor = Executor(fileList, threshold=0.6,
                        sample_rate=48000, time_sec=60)
    executor.execute()
