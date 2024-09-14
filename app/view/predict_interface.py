from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QLabel
from qfluentwidgets import SegmentedWidget
from .loadfile_interface import LoadfileInterface
from .report_interface import ReportInterface
from .statistics_interface import StatisticsInterface


class PredictInterface(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置导航面板对象
        self.pivot = SegmentedWidget(self)

        # 设置页面名称-唯一值
        self.setObjectName("PredictInterface")
        # 创建导航条
        self.stackedWidget = QStackedWidget(self)
        # 垂直布局
        self.vBoxLayout = QVBoxLayout(self)

        # 设置标签页
        self.loadfileInterface = LoadfileInterface()
        self.statisticsInterface = StatisticsInterface()
        self.reportInterface = ReportInterface()
        self.loadfileInterface.filePathSignal.connect(self.statisticsInterface.GetFilePath)
        self.loadfileInterface.deletedInfoSignal.connect(self.statisticsInterface.clear_data)
        self.loadfileInterface.deletedInfoSignal.connect(self.reportInterface.clear_data)
        self.statisticsInterface.mappingDataReady.connect(self.reportInterface.Get_data)


        # 添加标签页
        self.addSubInterface(self.loadfileInterface, 'loadfileInterface', self.tr('① 导入数据'))
        self.addSubInterface(self.statisticsInterface, 'albumInterface', self.tr('② 配置并检查数据'))
        self.addSubInterface(self.reportInterface, 'reportInterface', self.tr('③ 预测报告'))

        # 连接信号
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        # 初始化当前标签页
        self.stackedWidget.setCurrentWidget(self.loadfileInterface)
        # 设置导航信息
        self.pivot.setCurrentItem(self.loadfileInterface.objectName())

        # 设置布局
        self.vBoxLayout.setContentsMargins(12, 18, 12, 12)
        # 添加控件到布局，不拉伸，居中
        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignHCenter)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.resize(400, 400)

        # 禁用 SegmentedWidget 的点击事件
        self.pivot.setEnabled(False)

    def addSubInterface(self, widget, objectName: str, text: str):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)

        # 使用全局唯一的 objectName 作为路由键
        self.pivot.addItem(
            routeKey=objectName,
            text=text,
            # onClick=lambda: self.stackedWidget.setCurrentWidget(widget)       # 禁用点击
        )

    # 点击导航事件
    def onCurrentIndexChanged(self, index):
        widget = self.stackedWidget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())

    # 切换到下一个界面
    def switchToNextInterface(self):
        current_index = self.stackedWidget.currentIndex()
        next_index = (current_index + 1) % self.stackedWidget.count()
        self.stackedWidget.setCurrentIndex(next_index)

    # 切换到上一个界面
    def switchToPreviousInterface(self):
        current_index = self.stackedWidget.currentIndex()
        previous_index = (current_index - 1) % self.stackedWidget.count()
        self.stackedWidget.setCurrentIndex(previous_index)
