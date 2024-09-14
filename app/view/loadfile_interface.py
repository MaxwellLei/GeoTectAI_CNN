from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFileDialog, QFrame, QFormLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from qfluentwidgets import (isDarkTheme, QColor, PushButton, ComboBox, GroupHeaderCardWidget,
                            IconWidget, InfoBarIcon, BodyLabel, PrimaryPushButton,
                            FluentIcon, HeaderCardWidget, InfoBar, InfoBarPosition)
from qfluentwidgets import FluentIcon as FIF
import os
from PyQt5.QtCore import pyqtSignal

# 全局变量
file_path_G = None


# 左上角-文件选择器
class FileDropWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setAcceptDrops(True)
        self.setFixedSize(280, 320)  # 固定大小

        layout = QVBoxLayout()
        self.label = BodyLabel(self.tr("拖动并释放或者点击选择\nXLS, XLSX 或者 CSV 类型的文件"))
        self.label.setAlignment(Qt.AlignCenter)
        if isDarkTheme():
            tintColor = QColor(50, 50, 50, 160)
            textColor = "white"
        else:
            tintColor = QColor(252, 253, 254, 200)
            textColor = "black"

        self.setStyleSheet(f"""
                    QWidget {{
                        background-color: {tintColor.name(QColor.HexArgb)};
                        border-radius: 5px;
                    }}
                    QLabel {{
                        border: 2px dashed #aaa;
                        border-radius: 5px;
                        padding: 20px;
                        color: {textColor};
                    }}
                """)
        layout.addWidget(self.label)

        self.setLayout(layout)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        self.process_file(files[0])

    def mousePressEvent(self, event):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Select File", "",
                                                   "Excel Files (*.xlsx *.xls);;CSV Files (*.csv)")
        if file_path:
            self.process_file(file_path)

    def process_file(self, file_path):
        global file_path_G
        if file_path.lower().endswith(('.xls', '.xlsx', '.csv')):
            self.label.setText(f"File selected:\n{file_path.split('/')[-1]}")
            file_path_G = file_path
            InfoBar.success(
                title=self.tr('成功'),
                content=self.tr(f"导入文件 {file_path} 成功"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM,
                duration=2000,
                parent=self.parent()
            )
        else:
            file_path_G = None
            self.label.setText(self.tr("无效的文件类型\n请选择 XLS,XLSX或者CSV格式的文件Please select a XLS, XLSX or CSV file."))
            InfoBar.error(
                title=self.tr('警告'),
                content=self.tr("选择文件类型错误"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM,
                duration=2000,
                parent=self.parent()
            )


# 右上角-导入文件设置
class SettingsCard(GroupHeaderCardWidget):
    nextClicked = pyqtSignal(int, int)  # 新增信号
    deleteClicked = pyqtSignal()  # 新增信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("基本设置"))
        self.setBorderRadius(8)
        self.setMaximumHeight(400)  # 设置最大高度

        self.comboBox = ComboBox()  # 标题行选项
        self.comboBox_ = ComboBox()  # 自动匹配选项

        self.hintIcon = IconWidget(InfoBarIcon.INFORMATION)
        self.hintLabel = BodyLabel(self.tr("点击下一步进行数据检查和映射配置👉"))
        self.nextButton = PrimaryPushButton(FluentIcon.PLAY_SOLID, self.tr("下一步"))
        self.deleteButton = PrimaryPushButton(FluentIcon.DELETE, self.tr("清除选择"))
        self.openButton = PushButton(FluentIcon.VIEW, self.tr("打开文件所在位置"))
        self.bottomLayout = QHBoxLayout()

        self.comboBox.setFixedWidth(150)
        self.comboBox.addItems([self.tr("是"), self.tr("否")])
        self.comboBox_.setFixedWidth(150)
        self.comboBox_.addItems([self.tr("模糊匹配"), self.tr("精确匹配")])

        # 连接信号
        self.openButton.clicked.connect(self.open_file_location)
        self.nextButton.clicked.connect(self.next_step)
        self.deleteButton.clicked.connect(self.delete_file)

        # 设置底部工具栏布局
        self.hintIcon.setFixedSize(16, 16)
        self.bottomLayout.setSpacing(10)
        self.bottomLayout.setContentsMargins(24, 8, 24, 15)
        self.bottomLayout.addWidget(self.hintIcon, 0, Qt.AlignLeft)
        self.bottomLayout.addWidget(self.hintLabel, 0, Qt.AlignLeft)
        self.bottomLayout.addStretch(1)
        self.bottomLayout.addWidget(self.openButton, 0, Qt.AlignRight)
        self.bottomLayout.addWidget(self.nextButton, 0, Qt.AlignRight)

        # 添加组件到分组中
        self.addGroup(FIF.BOOK_SHELF, self.tr("标题行"), self.tr("数据首行是标题行"), self.comboBox)
        self.addGroup(FIF.TILES, self.tr("标题匹配"), self.tr("选择标题特征元素的匹配模型（仅当存在标题行有效）"), self.comboBox_)
        group = self.addGroup(FIF.DELETE, self.tr("重置选择"), self.tr("清除选择的文件"), self.deleteButton)
        group.setSeparatorVisible(True)

        # 添加底部工具栏
        self.vBoxLayout.addLayout(self.bottomLayout)

    # 根据文件路径，打开文件所在位置
    def open_file_location(self):
        global file_path_G
        if file_path_G:
            InfoBar.success(
                title=self.tr('成功'),
                content=self.tr("已打开文件所在文件夹"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM,
                duration=2000,
                parent=self.parent()
            )
            os.startfile(os.path.dirname(file_path_G))
        else:
            InfoBar.warning(
                title=self.tr('警告'),
                content=self.tr("文件类型错误或文件不存在"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM,
                duration=2000,
                parent=self.parent()
            )

    # 点击下一步，传递信号
    def next_step(self):
        if file_path_G:
            # 传递两个信号参数，分别是两个设置，0-是，1-否；0-模糊匹配，1-精确匹配
            self.nextClicked.emit(self.comboBox.currentIndex(),self.comboBox_.currentIndex())  # 发射信号
        else:
            InfoBar.error(
                title=self.tr('错误'),
                content=self.tr("请选择文件"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM,
                duration=2000,
                parent=self.parent()
            )

    # 情况加载
    def delete_file(self):
        global file_path_G
        file_path_G = None
        self.parent().file_drop_widget.label.setText(self.tr("拖动并释放或者点击选择\nXLS, XLSX 或者 CSV 类型的文件"))
        self.deleteClicked.emit()  # 发射信号
        InfoBar.success(
            title=self.tr('成功'),
            content=self.tr("重置数据成功"),
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM,
            duration=2000,
            parent=self.parent()
        )


# 最下面的卡片
class SystemRequirementCard(HeaderCardWidget):
    """ System requirements card """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr('格式说明'))

        self.infoLabel1 = BodyLabel(self.tr('1. 确保你的输入是否含有标题行，并检查你的数据输入不存在非法格式'), self)
        self.infoLabel1.setWordWrap(True)
        self.infoLabel2 = BodyLabel(self.tr('2. 确保你的文件含有地球化学数据，并选择合适的匹配模式'), self)
        self.infoLabel2.setWordWrap(True)
        self.infoLabel3 = BodyLabel(self.tr('3. 模糊匹配会根据默认需要的地球化学元素来不区分大小写匹配你的数据标题列是否含有地球化学元素名称'), self)
        self.infoLabel3.setWordWrap(True)
        self.infoLabel4 = BodyLabel(self.tr('4. 精确匹配会根据默认需要的地球化学元素来不区分大小写匹配你的数据标题列'), self)
        self.infoLabel4.setWordWrap(True)
        self.infoLabel5 = BodyLabel(self.tr('5. 匹配模式不一定正确，请注意在下一步检查数据匹配结果'), self)
        self.infoLabel5.setWordWrap(True)

        self.vBoxLayout = QVBoxLayout()

        self.vBoxLayout.setSpacing(10)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.vBoxLayout.addWidget(self.infoLabel1)
        self.vBoxLayout.addWidget(self.infoLabel2)
        self.vBoxLayout.addWidget(self.infoLabel3)
        self.vBoxLayout.addWidget(self.infoLabel4)
        self.vBoxLayout.addWidget(self.infoLabel5)

        self.viewLayout.addLayout(self.vBoxLayout)


# 主页面
class LoadfileInterface(QWidget):
    filePathSignal = pyqtSignal(str, int, int)
    deletedInfoSignal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()

        # 上部布局（左右布局）
        top_layout = QHBoxLayout()

        # 左侧：文件拖放控件
        self.file_drop_widget = FileDropWidget()
        top_layout.addWidget(self.file_drop_widget, alignment=Qt.AlignCenter)

        # 右侧：SettingsCard
        settings_card = SettingsCard(self)
        # 设置信号
        settings_card.nextClicked.connect(self.onNextClicked)
        settings_card.deleteClicked.connect(self.onDeleteClicked)
        top_layout.addWidget(settings_card)

        # 将上部布局添加到主布局
        main_layout.addLayout(top_layout)

        # 添加 SystemRequirementCard
        system_requirement_card = SystemRequirementCard(self)
        main_layout.addWidget(system_requirement_card)

        # 下部布局（标题和内容）
        bottom_widget = QFrame()

        main_layout.addWidget(bottom_widget)

        self.setLayout(main_layout)

    # 重置
    def onDeleteClicked(self):
        self.deletedInfoSignal.emit()

    def onNextClicked(self, isTitle, matchMode):
        # 调用父类的方法
        self.parent().parent().switchToNextInterface()
        self.filePathSignal.emit(file_path_G, isTitle, matchMode)
