import json
import numpy as np
from pprint import pprint
from scipy.io.wavfile import read
from scipy.signal import spectrogram
from scipy.signal.windows import hann
from scipy.signal import find_peaks
from scipy.signal import savgol_filter, butter, filtfilt
from Preprocess import motion_blur
import matplotlib.pyplot as plt
import matplotlib as mpl
from time import sleep, time
import pandas as pd
import os
from PyQt5.QtCore import pyqtSignal, QObject, QThread
mpl.use('Agg')
mpl.rcParams['font.sans-serif'] = ['KaiTi', 'SimHei']  # 汉字字体
# mpl.rcParams['font.size']=16#字体大小
mpl.rcParams['axes.unicode_minus'] = False  # 正常显示负号


class Transform(QThread):
    status = pyqtSignal(int)

    def __init__(self, resultsFile, downRate=3):
        super(Transform, self).__init__()
        self.file = resultsFile
        self.timeResults = None
        self.fileDirs = None
        self.downRate = downRate
        self.total = 0
        self.cur = 0

        self.results = {
            '持续时间': [],
            '起始时间': [],
            '终止时间': [],
            '起始频率': [],
            'F0.25': [],
            'F0.50': [],
            'F0.75': [],
            '结束频率': [],
            '基频最大值': [],
            '基频最小值': [],
            '频率变化范围': [],
            '平均频率': [],
            '开始扫向': [],
            '结束扫向': []
        }

    def update(self, st, ed, startF, f025, f050, f075, endF, maxF, minF, rangeF, meanF, chrpS, chrpE):
        self.results['持续时间'].append(ed-st)
        self.results['起始时间'].append(st)
        self.results['终止时间'].append(ed)
        self.results['起始频率'].append(int(startF))
        self.results['F0.25'].append(int(f025))
        self.results['F0.50'].append(int(f050))
        self.results['F0.75'].append(int(f075))
        self.results['结束频率'].append(int(endF))
        self.results['基频最大值'].append(int(maxF))
        self.results['基频最小值'].append(int(minF))
        self.results['频率变化范围'].append(int(rangeF))
        self.results['平均频率'].append(int(meanF))
        self.results['开始扫向'].append(chrpS)
        self.results['结束扫向'].append(chrpE)

    def downSample(self, data):
        idx = np.arange(0, len(data), step=self.downRate)
        tmp = data[idx]
        return tmp

    def run(self):
        self.timeResults = json.load(open(self.file, 'r'))
        self.fileDirs = list(self.timeResults.keys())

        for dir in self.fileDirs:
            self.total += len(self.timeResults[dir])

        for idx, dir in enumerate(self.fileDirs):
            # 导入数据，并降采样
            fs, data = read(dir)
            self.fs = fs//self.downRate
            self.data = self.downSample(data)
            del fs, data
            # 时间片段
            timePieces = self.timeResults[dir]
            print(idx, dir, self.fs, len(timePieces))
            for [start, end] in timePieces:
                idxS = int(start*self.fs)
                idxE = int(end*self.fs+0.1)
                onePiece = self.data[idxS:idxE]
                # print(onePiece.shape)
                # 信号处理阶段
                (ff, tt, II) = self.signalProcess(onePiece)
                print('II shape ', II.shape)
                # 脊线提取
                ridge = self.get_ridge(II)
                # 参数提取
                # 脊线头尾获取
                head, tail = self.get_start_end(ridge)
                piece = ridge[head:tail]
                print('piece shape ', piece.shape)
                # 得到信号真实起始时间
                st = tt[head]+start
                ed = tt[tail]+start
                (startF, f025, f050, f075, endF, maxF, minF, rangeF,
                 meanF, chrpS, chrpE) = self.get_params(piece, fs=self.fs)
                self.update(st, ed, startF, f025, f050, f075, endF,
                            maxF, minF, rangeF, meanF, chrpS, chrpE)

                plt.clf()
                plt.cla()
                plt.subplot(211)
                plt.pcolormesh(tt+start, ff, II)
                plt.xlabel('时间/s')
                plt.ylabel('频率/Hz')
                plt.subplot(212)
                deltaF = self.fs//2//512
                plt.scatter(tt+start, ridge*deltaF)
                # plt.plot(tt+start,ridge*deltaF)
                plt.ylim([0, self.fs//2])
                # plt.xlim([start,end])
                # 获取去除文件路径和后缀的文件名
                (filepath, filename) = os.path.split(dir)
                (name, suffix) = os.path.splitext(filename)
                if not os.path.exists('./results_figs'):
                    os.mkdir('./results_figs')
                figName = './results_figs/{}_{:.2f}_{:.2f}.jpg'.format(
                    name, start, end)

                plt.savefig(figName)
                self.cur += 1
                self.status.emit(int(self.cur*100/self.total))
            # saved_xl='./'+name+'.xlsx'
            # saved=pd.DataFrame(self.results).to_excel(saved_xl,index_label=name)

    def signalProcess(self, data):
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

    def get_ridge(self, input_II):
        tmp = input_II.T
        tmp = savgol_filter(input_II, 501, 1)
        tmp = tmp.T
        res = np.zeros(shape=(tmp.shape[0],))
        # 寻找最大值索引
        for idx in range(len(tmp)):
            # 如果第idx列最大值大于-60，就把第idx列的最大值保存到res的第idx个
            # find_peaks(tmp[idx],distance=30,threshold=0)
            if np.max(tmp[idx]) > -60:
                peaks, _ = find_peaks(
                    tmp[idx], height=-70, prominence=5, distance=10, width=5)
                # np.where(tmp[idx] == np.max(tmp[idx]))[0].item()
                res[idx] = peaks[0]
                # plt.plot(tmp[idx])
                # plt.plot(peaks[0], tmp[peaks[0]], "x")
                # plt.plot(np.zeros_like(tmp), "--", color="gray")
                # plt.show()
                # plt.imsave
            else:
                res[idx] = np.nan
        res = savgol_filter(res, 401, 1)
        return res
        # plt.plot(ff[thePeak], temp[thePeak], "x")
        #plt.plot(thePeak, temp[thePeak], "x")
        #plt.plot(np.zeros_like(temp), "--", color="gray")
        # plt.ioff()
        # plt.show()

        # def get_ridge(self, input_II):
        #     tmp = input_II.T
        #     res = np.zeros(shape=(tmp.shape[0],))
        #     # 寻找最大值索引
        #     for idx in range(len(tmp)):
        #         if np.max(tmp[idx]) > -60:
        #             res[idx] = np.where(tmp[idx] == np.max(tmp[idx]))[0].item()
        #         else:
        #             res[idx] = np.nan
        #     # 两次阶跃平滑
        #     for idx in range(1, len(res)):
        #         if abs(res[idx] - res[idx - 1]) > 100 and res[idx - 1] != 0:
        #             res[idx] = res[idx - 1]
        #     for idx in range(1, len(res)):
        #         if abs(res[idx] - res[idx - 1]) > 60 and res[idx - 1] != 0:
        #             res[idx] = res[idx - 1]
        #     # 最小二乘平滑
        #     res = savgol_filter(res, 401, 1)
        #     return res

    def get_start_end(self, res):
        head = np.nan
        tail = np.nan
        head_ext = False
        tail_ext = False
        res[np.isnan(res)] = -100
        for idx in range(0, len(res)-1):
            if head_ext == False and res[idx] > 0:
                head = idx
                head_ext = True
            elif head_ext == True and tail_ext == False and res[idx] > 0 and res[idx + 1] < 0:
                tail = idx-1
                tail_ext = True
            elif res[idx] > 0 and idx == len(res)-2:
                tail = len(res)-2
                tail_ext = True
        return head, tail

    # %%
    def get_params(self, res, fs=48000):
        lenth = len(res)
        deltaF = fs // 2 // 512
        startF = res[0] * deltaF
        f025 = res[lenth // 4] * deltaF
        f050 = res[lenth // 2] * deltaF
        f075 = res[lenth // 4 * 3] * deltaF
        endF = res[lenth - 1] * deltaF
        maxF = np.max(res) * deltaF
        minF = np.min(res) * deltaF
        rangeF = maxF - minF
        meanF = (maxF + minF + startF + endF) / 4

        chrpS = 0
        if (res[0] - res[100]) > 50:
            chrpS = -1
        elif (res[100] - res[0]) > 50:
            chrpS = 1

        chrpE = 0
        if (res[lenth - 1] - res[lenth - 100]) > 50:
            chrpE = -1
        elif (res[lenth - 100] - res[lenth - 1]) > 50:
            chrpE = 1
        return (startF, f025, f050, f075, endF, maxF, minF, rangeF, meanF, chrpS, chrpE)


if __name__ == '__main__':
    task = Transform('results.json', downRate=12)
    task.run()
