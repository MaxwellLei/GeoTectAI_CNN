from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QTableWidgetItem, QSizePolicy)
from qfluentwidgets import (SimpleCardWidget, IconWidget, BodyLabel, PrimaryPushButton, TableWidget,
                            FluentIcon, ScrollArea, ComboBox, StrongBodyLabel, CaptionLabel,
                            IndeterminateProgressRing)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
import re
import pandas as pd


class MappingCard(SimpleCardWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.titleLabel = BodyLabel(title, self)
        self.comboBox = ComboBox(self)
        self.comboBox.setMaxVisibleItems(10)  # 限制可见项目数量

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(20, 10, 20, 10)
        self.hBoxLayout.setSpacing(10)
        self.hBoxLayout.addWidget(self.titleLabel)
        self.hBoxLayout.addWidget(self.comboBox, 1)

        self.setFixedHeight(50)


# 左侧匹配栏
class LeftCard(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('leftCard')
        self.setStyleSheet('''
            ScrollArea#leftCard {
                border: none;
                background-color: transparent;
            }
        ''')

        self.scrollWidget = QWidget()
        self.scrollLayout = QVBoxLayout(self.scrollWidget)
        self.scrollLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollLayout.setSpacing(1)

        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        card_title = StrongBodyLabel(text=self.tr("匹配映射"))
        card_title.setContentsMargins(5,0,0,0)
        self.scrollLayout.addWidget(card_title)

        self.form_items = [
            "SIO2(WT%)", "TIO2(WT%)", "AL2O3(WT%)", "FEOT(WT%)", "CAO(WT%)", "MGO(WT%)", "MNO(WT%)", "K2O(WT%)",
            "NA2O(WT%)", "P2O5(WT%)", "SC(PPM)", "V(PPM)", "CR(PPM)", "CO(PPM)", "LA(PPM)", "CE(PPM)", "PR(PPM)",
            "ND(PPM)", "SM(PPM)", "EU(PPM)", "GD(PPM)", "TB(PPM)", "DY(PPM)", "HO(PPM)", "ER(PPM)", "TM(PPM)",
            "YB(PPM)", "LU(PPM)", "NI(PPM)", "CU(PPM)", "ZN(PPM)", "RB(PPM)", "SR(PPM)", "Y(PPM)", "ZR(PPM)",
            "NB(PPM)", "BA(PPM)", "HF(PPM)", "TA(PPM)", "PB(PPM)", "TH(PPM)", "U(PPM)"
        ]

        self.mapping_cards = []
        for item in self.form_items:
            card = MappingCard(item)
            card.comboBox.currentTextChanged.connect(self.on_combo_changed)
            self.mapping_cards.append(card)
            self.scrollLayout.addWidget(card)

        self.available_items = []
        self.match_items = []
        print(self.available_items)

    def update_combo_items(self, items, matchMode):
        self.available_items = items.copy()
        self.match_items = items.copy()

        for card in self.mapping_cards:
            card.comboBox.currentTextChanged.disconnect(self.on_combo_changed)
            card.comboBox.clear()

            # 处理 titleLabel 的值
            title = card.titleLabel.text()
            title_without_parentheses = re.sub(r'\([^)]*\)', '', title).strip()

            matched_item = ''
            if matchMode == 0:
                # 部分匹配模式
                for item in self.available_items:
                    if title_without_parentheses.lower() in item.lower():
                        matched_item = item
                        break
            elif matchMode == 1:
                # 完全匹配模式
                for item in self.available_items:
                    if title_without_parentheses.lower() == item.lower():
                        matched_item = item
                        break

            combo_items = [''] + self.available_items
            card.comboBox.addItems(combo_items)

            if matched_item:
                card.comboBox.setCurrentText(matched_item)
                self.available_items.remove(matched_item)

            card.comboBox.currentTextChanged.connect(self.on_combo_changed)

    def on_combo_changed(self, text):
        try:
            sender = self.sender()
            if not isinstance(sender, ComboBox):
                return

            previous_text = sender.property("previous_text")
            sender.setProperty("previous_text", text)

            if previous_text and previous_text not in self.available_items:
                self.available_items.append(previous_text)
            if text and text in self.available_items:
                self.available_items.remove(text)

            for card in self.mapping_cards:
                current_text = card.comboBox.currentText()
                card.comboBox.blockSignals(True)
                card.comboBox.clear()
                items_to_add = [''] + [item for item in self.available_items if item != current_text]
                if current_text and current_text != '':
                    items_to_add.append(current_text)
                card.comboBox.addItems(items_to_add)
                card.comboBox.setCurrentText(current_text)
                card.comboBox.blockSignals(False)

        except Exception as e:
            print(f"Error in on_combo_changed: {str(e)}")


# 右中-表格
class RightCenterCard(SimpleCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.table = TableWidget(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.table)

        # 设置表格的尺寸策略为扩展
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        # 设置表格不可编辑
        self.table.setEditTriggers(TableWidget.NoEditTriggers)

    def load_file_to_table(self, file_path, has_header):
        self.file_path_save = file_path
        self.has_header_save = has_header
        has_header = 1 if has_header == 0 else 0
        try:
            # 根据文件扩展名选择适当的读取方法
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, header=0 if has_header else None)
            elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                df = pd.read_excel(file_path, header=0 if has_header else None)
            else:
                raise ValueError("Unsupported file format")

            # 清除表格中现有的数据
            self.table.clear()
            self.table.setRowCount(0)
            self.table.setColumnCount(0)

            # 设置列数
            self.table.setColumnCount(len(df.columns))

            # 设置列标题
            if has_header:
                self.table.setHorizontalHeaderLabels(df.columns.astype(str))
            else:
                self.table.setHorizontalHeaderLabels([f"Column {i + 1}" for i in range(len(df.columns))])

            # 填充数据
            for row_index, row in df.iterrows():
                row_position = self.table.rowCount()
                self.table.insertRow(row_position)
                for col, value in enumerate(row):
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # 设置为不可编辑
                    self.table.setItem(row_position, col, item)

            # 调整列宽以适应内容
            self.table.resizeColumnsToContents()

        except Exception as e:
            print(f"Error loading file: {str(e)}")


# 右下
class RightBottomCard(SimpleCardWidget):
    nextClicked = pyqtSignal()
    previousClicked = pyqtSignal()

    def __init__(self, icon, title, content, parent=None):
        super().__init__(parent)
        self.iconWidget = IconWidget(icon)
        self.titleLabel = BodyLabel(title, self)
        self.contentLabel = CaptionLabel(content, self)
        self.nextButton = PrimaryPushButton(FluentIcon.PLAY_SOLID, self.tr("下一步"))
        self.nextButton.clicked.connect(self.nextButtonClicked)
        self.previousButton = PrimaryPushButton(FluentIcon.CARE_LEFT_SOLID, self.tr("上一步"))
        self.previousButton.clicked.connect(self.previousButtonClicked)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        self.setFixedHeight(64)
        self.iconWidget.setFixedSize(32, 32)
        self.contentLabel.setTextColor("#606060", "#d2d2d2")
        self.nextButton.setFixedWidth(120)
        self.previousButton.setFixedWidth(140)

        self.hBoxLayout.setContentsMargins(20, 11, 11, 11)
        self.hBoxLayout.setSpacing(15)
        self.hBoxLayout.addWidget(self.iconWidget)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignVCenter)
        self.vBoxLayout.addWidget(self.contentLabel, 0, Qt.AlignVCenter)
        self.vBoxLayout.setAlignment(Qt.AlignVCenter)
        self.hBoxLayout.addLayout(self.vBoxLayout)

        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.previousButton, 0, Qt.AlignRight)
        self.hBoxLayout.addWidget(self.nextButton, 0, Qt.AlignRight)

    # 下一步点击事件
    def nextButtonClicked(self):
        self.nextClicked.emit()     # 发出信号

    # 上一步点击事件
    def previousButtonClicked(self):
        self.previousClicked.emit()     # 发出信号


# 多线程工作
class Worker(QThread):
    finished = pyqtSignal()

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    # 完成信号
    def run(self):
        self.func(*self.args, **self.kwargs)
        self.finished.emit()


# 数据统计页面
class StatisticsInterface(QWidget):
    mappingDataReady = pyqtSignal(dict, str, int)
    def __init__(self):
        super().__init__()

        self.setStyleSheet("background-color: transparent;")

        # 创建主水平布局
        main_layout = QHBoxLayout(self)

        # 左侧部分（占1/3宽度）
        self.left_card = LeftCard()
        main_layout.addWidget(self.left_card, 1)

        # 右侧部分（占2/3宽度）
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)  # 移除右侧布局的边距
        right_layout.setSpacing(0)  # 减少垂直间距
        main_layout.addWidget(right_widget, 3)

        # 右上部分
        cardTitle = StrongBodyLabel(text=self.tr("数据预览"))
        cardTitle.setFixedHeight(20)  # 设置固定高度，根据需要调整数值
        right_layout.addWidget(cardTitle)
        self.right_center_widget = RightCenterCard()
        right_layout.addWidget(self.right_center_widget)

        # 右下部分
        right_bottom_widget = RightBottomCard(FluentIcon.IOT, self.tr("预测"), self.tr("检查输入无误后，点击下一步生成预测报告"))
        right_bottom_widget.nextClicked.connect(self.onNextClicked)
        right_bottom_widget.previousClicked.connect(self.onPreviousClicked)
        right_layout.addWidget(right_bottom_widget)

    # 清除数据
    def clear_data(self):
        # 清除右侧表格数据
        self.right_center_widget.table.clear()
        self.right_center_widget.table.setRowCount(0)
        self.right_center_widget.table.setColumnCount(0)

        # 清除左侧匹配栏数据
        for card in self.left_card.mapping_cards:
            card.comboBox.clear()
            card.comboBox.addItem('')

        # 重置可用项目列表
        self.left_card.available_items = []

        # 重置文件路径和其他相关变量
        if hasattr(self, 'file_path'):
            del self.file_path

    # 显示加载中
    def show_loading_spinner(self):
        self.spinner = IndeterminateProgressRing(self)
        self.spinner.setFixedSize(50, 50)
        self.spinner.setStrokeWidth(4)
        self.spinner.move(self.width() // 2 - 25, self.height() // 2 - 25)
        self.spinner.show()

    # 隐藏加载中
    def hide_loading_spinner(self):
        if hasattr(self, 'spinner'):
            self.spinner.hide()
            self.spinner.deleteLater()

    # 切换下一步
    def onNextClicked(self):
        mapping_data, file_path, has_header = self.get_mapping_data()

        # 计算非 None 值的数量
        non_none_count = sum(1 for value in mapping_data.values() if value is not None)

        if non_none_count >= 3:
            print("Mapping data:", mapping_data)
            print("File path:", file_path)
            print("Has header:", has_header)
            self.mappingDataReady.emit(mapping_data, file_path, has_header)  # 发出信号，传递匹配映射
            self.parent().parent().switchToNextInterface()
        else:
            print("映射不足", f"请至少完成3个映射才能继续。当前完成了 {non_none_count} 个映射。")

    # 切换上一步
    def onPreviousClicked(self):
        # 调用父类的方法
        self.parent().parent().switchToPreviousInterface()

    # 获取文件路径和设置
    def GetFilePath(self, file_path, isTitle, matchMode):
        self.show_loading_spinner()

        def load_data():
            self.right_center_widget.load_file_to_table(file_path, isTitle)
            self.update_left_card(file_path, isTitle, matchMode)

        self.worker = Worker(load_data)
        self.worker.finished.connect(self.hide_loading_spinner)
        self.worker.start()

    # 更新左侧列表卡片
    def update_left_card(self, file_path, isTitle, matchMode):
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, header=0 if isTitle else None)
            elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                df = pd.read_excel(file_path, header=0 if isTitle else None)
            else:
                raise ValueError("不支持的格式")

            if isTitle == 0:
                print(df.iloc[0].tolist())
                combo_items = df.iloc[0].tolist()
            else:
                combo_items = [f"Column {i + 1}: {col}" for i, col in enumerate(df.columns)]

            self.left_card.update_combo_items(combo_items, matchMode)

        except Exception as e:
            print(f"更新左侧失败: {str(e)}")

    # 获取映射
    def get_mapping_data(self):
        mapping_data = {}
        for card in self.left_card.mapping_cards:
            label = card.titleLabel.text()
            value = card.comboBox.currentText()
            if value:
                column_index = self.left_card.match_items.index(value)
                mapping_data[label] = column_index
            else:
                mapping_data[label] = None
        return mapping_data, self.right_center_widget.file_path_save, self.right_center_widget.has_header_save

