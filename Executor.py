from DataGenerator import DataGenerator
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from scipy.signal import savgol_filter,spectrogram
from time import time
from concurrent.futures import ThreadPoolExecutor
from Preprocess import preprocessing,motion_blur
from PyQt5.QtCore import pyqtSignal,QObject
import json
from glob import glob

class Executor:
    def __init__(self,fileList,threshold=0.6,width=0.1,sample_rate=48000,time_sec=60):

        self.results={'':[]}
        self.threshold=threshold
        self.width=width
        self.II = 0
        self.sample_rate=sample_rate # 目标采样率
        self.sig=0
        self.generator = DataGenerator(fileList, time_sec=60)
        self.down_rate = self.cal_down_rate()

    def cal_down_rate(self):
        if int(self.generator.fs)%int(self.sample_rate)==0:
            return int(self.generator.fs)//int(self.sample_rate)
        else:
            return int(self.generator.fs)//int(self.sample_rate)+1

    def execute(self):
        print("starting executing!!!")
        while self.generator.isListEnd()==False:
            self.curFileName=self.generator.getFileName()
            (sr, s0) = self.generator.getData(self.down_rate)
            s0max = np.max(s0)
            s0min = np.min(s0)
            ymax = 0.1872
            ymin = -0.2546
            s0 = (ymax - ymin) * (s0 - s0min) / (s0max - s0min) + ymin
            (SeqLgth, NbSeq, s1Mtx, s1Res, s0Mtx, s0Res, fs) = preprocessing(sr, s0)
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
                res = self.getDuration(confidence, self.threshold,self.width*II.shape[1]/2)
                res += idxSeq * II.shape[1]
                res = res * 2 / II.shape[1] + (self.generator.prevMinutes-1)*60
                #res = res + (self.generator.prevMinutes)*II.shape[1]*30
                if len(res) != 0:
                    curMinuteResult.extend(res.tolist())
                print(idxSeq)
                self.sig=idxSeq
            self.saveResult(curMinuteResult)
            print(' 1 minutes cost: {} '.format(time() - start))
        #self.saveResult(curMinuteResult)
        print('calculate done!!!')

    def res2time(self,res):
        pass

    def getII(self):
        return self.II

    def saveResult(self,minuteRes):
        if self.curFileName in self.results:
            self.results[self.curFileName].extend(minuteRes)
        else:
            self.results[self.curFileName]=minuteRes
        if '' in self.results:
            self.results.pop('')
        with open('results.json','w') as f:
            json.dump(self.results,f)
            print('save done!!!')

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

    def getDuration(self, confidence, threshold,width):
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
                if np.mean(ax[head:tail]) > 0 and (tail-head)>width:
                    res.append([head, tail])
            elif head_ext == True and tail_ext == True:
                # 标志清空
                head = np.nan
                tail = np.nan
                head_ext = False
                tail_ext = False
        return np.array(res)

    # def concat(self,dat):
    #     if len(cat)<2:
    #         return dat
    #     for idx in range(len(dat)-1):
    #         if dat[idx+1][0]-dat[idx][1]<0.1:
    #







if __name__=='__main__':
    fileList=glob('.\\tempdata\\*.wav')
    executor=Executor(fileList,threshold=0.6,sample_rate=48000,time_sec=60)
    executor.execute()