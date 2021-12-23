from glob import glob
import numpy as np
import os
from scipy.io.wavfile import read
from scipy.signal import resample
class DataGenerator:
    def __init__(self, fileList,time_sec=60) -> None:
        self.fileList=fileList
        self.timeSec=time_sec
        self.fileProgress=0
        self.listProgress=0
        self.fileEnd=False
        self.listEnd=False
        self.fileIdx=0
        self.listIdx=0
        self.fs,self.data= read(self.fileList[self.listIdx])
        self.prevMinutes=0

    def getData(self,down_rate):
        if self.listEnd==True: # 列表已空，代表没有数据可读
            print('list over!!!')
            return 0,np.zeros(shape=(1,))
        # 还有数据可以读
        if self.fileIdx==0:
            self.prevMinutes=0
        if self.fileIdx+self.fs*self.timeSec<self.data.size:
            # 数据还够一帧
            temp=self.data[self.fileIdx:self.fileIdx+self.fs*self.timeSec]
            self.fileEnd=False
            self.fileIdx+=self.fs*self.timeSec
            self.prevMinutes+=1
            self.fileProgress=int(100*(self.fileIdx+1)//self.data.size)
        else: # 当前文件不够一帧，已到末尾
            temp = self.data[self.fileIdx:]
            self.prevMinutes +=1
            if len(self.fileList)==self.listIdx+1:# 若文件没有下一个了，列表遍历结束
                self.listEnd=True
            else: # 还有下一个文件
                self.listIdx+=1
                self.fileIdx=0
                self.fs,self.data=read(self.fileList[self.listIdx])

            self.fileProgress = 100
            self.fileEnd=True
        self.listProgress=int(100*(self.listIdx+1)//len(self.fileList))
        return self.fs//down_rate,self.downSample(temp,down_rate)

    def getFileName(self):
        return self.fileList[self.listIdx]

    def getFileIdx(self):
        return self.fileIdx

    def downSample(self, data, rate):
        if rate == 1:
            return data
        else:
            idx = np.arange(0, len(data), rate)
            tmp = data[idx]
            return tmp

    # def downSample(self, data, rate):
    #     if rate == 1:
    #         return data
    #     else:
    #         tmp = resample(data, len(data)//rate)
    #         return tmp

    def isListEnd(self):
        return self.listEnd

    def isFileEnd(self):
        return self.fileEnd

    def listPg(self):
        return self.listProgress

    def filePg(self):
        return self.fileProgress

if __name__ == '__main__':
    fileLists=glob('.\\tempdata\\*.wav')
    generator = DataGenerator(fileLists,60)
    for i in range(120):
        if generator.isListEnd() == False:
            print(i, generator.getFileName())
            fs, data = generator.getData(down_rate=12)
            print(fs, data.shape,generator.listPg(),' ',generator.filePg(),generator.isFileEnd(),generator.isListEnd(),generator.prevMinutes-1)