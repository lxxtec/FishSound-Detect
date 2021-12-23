import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from PyQt5 import QtCore, QtWidgets
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib
from PyQt5.QtCore import QObject,pyqtSignal
matplotlib.use("Qt5Agg")

class MyPlot(FigureCanvas):
    def __init__(self, parent=None, width=5, height=3, dpi=100):
        # normalized for 中文显示和负号
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False

        # new figure
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        # activate figure window
        # super(Plot_dynamic,self).__init__(self.fig)
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        #self.fig.canvas.mpl_connect('button_press_event', self)
        # sub plot by self.axes
        self.axes = self.fig.add_subplot(111)
        # initial figure
        self.compute_initial_figure()

        # size policy
        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass


# class for plotting a specific figure static or dynamic
class static_fig(MyPlot):
    def __init__(self, *args, **kwargs):
        MyPlot.__init__(self, *args, **kwargs)

    def compute_initial_figure(self):
        x = np.linspace(0, 2*np.pi, 100)
        y = x*np.sin(x)
        # self.axes.plot(x, y)
        # self.axes.set_title("signals")
        # self.axes.set_xlabel("delay(s)")
        # self.axes.set_ylabel("counts")

class MyFig(QObject):
    finished=pyqtSignal()
    def __init__(self,width=6, height=3, dpi=60):
        super(MyFig, self).__init__()
        self.fig=static_fig(width=width, height=height, dpi=dpi)
        self.II=0

    def setII(self,II):
        self.II=II

    def run(self):
        if self.II!=0:
            self.fig.axes.pcolormesh(II)
            self.fig.draw()
        print('no data')
        self.finished.emit()

class dynamic_fig(MyPlot):
    def __init__(self, *args, **kwargs):
        MyPlot.__init__(self, *args, **kwargs)

    def compute_initial_figure(self):
        counts = [1, 10]
        delay_t = [0, 1]
        self.axes.plot(delay_t, counts, '-ob')
        self.axes.set_title("signals")
        self.axes.set_xlabel("delay(s)")
        self.axes.set_ylabel("counts")
