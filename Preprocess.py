# %%
from math import degrees
from cv2 import getRotationMatrix2D,warpAffine,filter2D
import matplotlib.pyplot as plt

import numpy as np
from time import time
from scipy.signal import savgol_filter,butter,filtfilt
from scipy.io.wavfile import read
from scipy.signal import spectrogram
from scipy.io import savemat
# %%


def preprocessing(sr, s0):
    begin = time()
    time()
    #fs = sr//3+1
    fs=sr
    # y = librosa.resample(orig_data, orig_sr=sr, target_sr=fs)
    #s1 = signal.resample(s0, len(s0)//3)
    # 简陋版降采样
    #idx = np.arange(0, len(s0), step=3)
    #s1 = s0[idx]
    s1=s0
    #print('downsample done! {}s'.format(time()-start))
    start = time()
    # 高通截至频率
    fc = 4000
    b, a = butter(2, 2*fc/fs, 'highpass')
    s1 = filtfilt(b, a, s1)
    #print('filter done! {}s'.format(time()-start))
    #start = time()
    # 时域平滑
    #
    tmp1 = savgol_filter(np.abs(s1), 21, polyorder=1)
    #print('tmp1 done! {}s'.format(time()-start))
    start = time()
    tmp2 = savgol_filter(np.abs(s1), 5001, polyorder=1)
    #print('tmp2 done! {}s'.format(time()-start))
    start = time()
    Envlp = savgol_filter(tmp1/tmp2, 21, polyorder=1)
    #print('envlp done! {}s'.format(time()-start))
    # 小于1.2阈值的结果设置为1，然后用原始数据除以滤波后结果
    Envlp = np.array([1 if data < 1.2 else data for data in Envlp])
    s1 = s1/Envlp
    #print('时域平滑 done! {}s'.format(time()-start))
    start = time()
    SeqLgth = 2
    NbSeq = np.floor(len(s1)/(SeqLgth*fs))
    s1Mtx = np.reshape(s1[0:int(NbSeq*SeqLgth*fs)], (-1, SeqLgth*fs)).T
    s1Res = s1[s1Mtx.size+1:]
    s0Mtx = np.reshape(s0[0:int(NbSeq*SeqLgth*fs)], (-1, SeqLgth*fs)).T
    s0Res = s0[s0Mtx.size+1:]
    #print('processing done! {}s'.format(time()-begin))
    return (SeqLgth, NbSeq, s1Mtx, s1Res, s0Mtx, s0Res, fs)


def motion_blur(image, degree=12, angle=45):

    image = np.array(image)
    start = time()
    # 这里生成任意角度的运动模糊kernel的矩阵， degree越大，模糊程度越高
    M = getRotationMatrix2D((degree / 2, degree / 2), angle, 1)
    motion_blur_kernel = np.diag(np.ones(degree))
    motion_blur_kernel = warpAffine(
        motion_blur_kernel, M, (degree, degree))

    motion_blur_kernel = motion_blur_kernel / degree
    blurred = filter2D(image, -1, motion_blur_kernel)
    # print('filter cost: ', time()-start)
    # convert to uint8
    # cv2.normalize(blurred, blurred, 0, 255, cv2.NORM_MINMAX)
    # blurred = np.array(blurred, dtype=np.uint8)
    return blurred


# %%
if __name__ == '__main__':
    sr, s0 = read('./SBW1431_20160429_040400.wav')
    (SeqLgth, NbSeq, s1Mtx, s1Res, s0Mtx, s0Res, fs) = preprocessing(sr, s0)

# %%
# window = signal.get_window(window=('kaiser', 0.8), Nx=128)
# ff, tt, II = spectrogram(
#     s1Mtx[:, 2], fs=fs, window=window, noverlap=len(window)*0.98, nfft=680)
# II = 10*np.log10(II)
# II[II < -90] = -300
# II = motion_blur(II, degree=80, angle=45)
# II[II < 95] = -95
# confidence = Dophine_Sniffer(inputs, c1=200, c2=1000, c3=501)

#plt.pcolormesh(tt, ff, II)

# %%


# %%
# sr, s0 = read('./SBW1431_20160429_040400.wav')
# fs = sr//3+1
# s0max = np.max(s0)
# s0min = np.min(s0)
# ymax = 0.1872
# ymin = -0.2546
# s0 = (ymax-ymin)*(s0-s0min)/(s0max-s0min)+ymin
# # y = librosa.resample(orig_data, orig_sr=sr, target_sr=fs)
# #s1 = signal.resample(s0, len(s0)//3)
# # 简陋版降采样
# # %%
# idx = np.arange(0, len(s0), step=3)
# s1 = s0[idx]
# # %%
# #print('downsample done! {}s'.format(time()-start))
# #start = time()
# # 高通截至频率
# fc = 1000
# b, a = signal.butter(2, 2*fc/fs, 'highpass')
# s1 = signal.filtfilt(b, a, s1)
# #print('filter done! {}s'.format(time()-start))
# #start = time()
# # 时域平滑
# tmp1 = savgol_filter(np.abs(s1), 21, polyorder=1)
# #print('tmp1 done! {}s'.format(time()-start))
# start = time()
# tmp2 = savgol_filter(np.abs(s1), 5001, polyorder=1)
# #print('tmp2 done! {}s'.format(time()-start))
# start = time()
# Envlp = savgol_filter(tmp1/tmp2, 21, polyorder=1)
# #print('envlp done! {}s'.format(time()-start))
# # %%
# # 小于1.2阈值的结果设置为1，然后用原始数据除以滤波后结果
# Envlp = np.array([1 if data < 1.2 else data for data in Envlp])
# s1 = s1/Envlp
# # %%
# #print('时域平滑 done! {}s'.format(time()-start))
# #start = time()
# SeqLgth = 2
# NbSeq = np.floor(len(s1)/(SeqLgth*fs))
# s1Mtx = np.reshape(s1[0:int(NbSeq*SeqLgth*fs)], (-1, SeqLgth*fs)).T
# s1Res = s1[s1Mtx.size+1:]
# s0Mtx = np.reshape(s0[0:int(NbSeq*SeqLgth*fs)], (-1, SeqLgth*fs)).T
# s0Res = s0[s0Mtx.size+1:]
#
# # %%
# savemat('s1Mtx_py.mat', {'s1Mtx_py': s1Mtx, 's1_py': s1})
#
# # %%
