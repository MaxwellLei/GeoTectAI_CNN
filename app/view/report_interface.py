from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QSizePolicy, QTableWidgetItem, QFileDialog
from qfluentwidgets import (SimpleCardWidget, IconWidget, BodyLabel, PrimaryPushButton, InfoBar, InfoBarPosition,
                            FluentIcon, CaptionLabel, TableWidget, IndeterminateProgressRing)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import shutil
from PyQt5.QtGui import QColor, QPainter
import pandas as pd
from matplotlib.figure import Figure
import numpy as np
from PIL import Image
import re
import os
import torch
from torchvision import transforms
import matplotlib
import torch.nn as nn


matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei']
matplotlib.rcParams['axes.unicode_minus'] = False


# 定义卷积神经网络模型
class CNNNetCore(nn.Module):
    def __init__(self):
        super(CNNNetCore, self).__init__()
        self.conv1 = nn.Conv2d(3, 32, 3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.conv2 = nn.Conv2d(32, 64, 3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.conv3 = nn.Conv2d(64, 128, 3, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.fc1 = nn.Linear(128 * 5 * 3, 128)
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x):
        x = torch.relu(self.bn1(self.conv1(x)))
        x = torch.relu(self.bn2(self.conv2(x)))
        x = torch.relu(self.bn3(self.conv3(x)))
        x = x.view(-1, 128 * 5 * 3)
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return x


class ImagePredictor:
    def __init__(self, model_path, class_names):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = CNNNetCore().to(self.device)
        checkpoint = torch.load(model_path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()

        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
        ])

        self.class_names = class_names

    # 单项预测
    def predict(self, image_path):
        # 加载并预处理图像
        image = Image.open(image_path).convert('RGB')
        image_tensor = self.transform(image).unsqueeze(0).to(self.device)

        # 进行预测
        with torch.no_grad():
            outputs = self.model(image_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)

        # 获取预测结果和概率值
        predicted_class_index = torch.argmax(probabilities, dim=1).item()
        predicted_class_name = self.class_names[predicted_class_index]
        predicted_probability = probabilities[0][predicted_class_index].item()

        # 获取所有类别的概率
        all_probabilities = probabilities[0].cpu().numpy()

        return predicted_class_name, predicted_probability, all_probabilities

    # 批量预测
    def predict_batch(self, folder_path):
        results = []
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                image_path = os.path.join(folder_path, filename)
                try:
                    predicted_class, probability, all_probabilities = self.predict(image_path)
                    results.append({
                        'filename': filename,
                        'predicted_class': predicted_class,
                        'probability': probability,
                        'all_probabilities': all_probabilities
                    })
                except Exception as e:
                    print(f"Error processing {filename}: {str(e)}")

        return results


# 折线图
class MatplotlibWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(5, 2), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.ax = self.figure.add_subplot(111)
        self.show_default_message()

    def show_default_message(self):
        self.ax.clear()
        self.ax.text(0.5, 0.5, self.tr("点击对应样本，显示判别结果概率"),
                     ha='center', va='center', fontsize=12)
        self.ax.axis('off')
        self.canvas.draw()

    def plot(self, probabilities=None, class_names=None):
        self.ax.clear()
        if probabilities is None or class_names is None:
            self.show_default_message()
        else:
            x = np.arange(len(class_names))
            self.ax.bar(x, probabilities)
            self.ax.set_xticks(x)
            self.ax.set_xticklabels(class_names, rotation=45, ha='right')
            self.ax.set_ylim(0, 1)
            self.ax.set_ylabel(self.tr('概率值'))
        self.canvas.draw()


# 上半部分
class TopCardWidget(SimpleCardWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.plot_widget = MatplotlibWidget(self)
        layout.addWidget(self.plot_widget)

# 右上部分
class RightTopCard(SimpleCardWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.table = TableWidget(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.table)

        # 设置表格的尺寸策略为扩展
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        # 设置表格不可编辑
        self.table.setEditTriggers(TableWidget.NoEditTriggers)

        # 启用边框并设置圆角
        self.table.setBorderVisible(True)
        self.table.setBorderRadius(8)


# 右下最底下
class RightBottomCard(SimpleCardWidget):
    previousClicked = pyqtSignal()  # 上一步信号
    exportClicked = pyqtSignal()    # 导出信号

    def __init__(self, icon, title, content, parent=None):
        super().__init__(parent)
        self.iconWidget = IconWidget(icon)
        self.titleLabel = BodyLabel(title, self)
        self.contentLabel = CaptionLabel(content, self)
        self.nextButton = PrimaryPushButton(FluentIcon.PLAY_SOLID, self.tr("导出结果"))
        self.nextButton.clicked.connect(self.nextButtonClicked)
        self.previousButton = PrimaryPushButton(FluentIcon.CARE_LEFT_SOLID, self.tr("上一步"))
        self.previousButton.clicked.connect(self.previousButtonClicked)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        self.setFixedHeight(64)
        self.iconWidget.setFixedSize(32, 32)
        self.contentLabel.setTextColor("#606060", "#d2d2d2")
        self.nextButton.setFixedWidth(150)
        self.previousButton.setFixedWidth(150)

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
        self.exportClicked.emit()     # 发出信号

    # 上一步点击事件
    def previousButtonClicked(self):
        self.previousClicked.emit()     # 发出信号


# 饼状图
class MatplotlibPieWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(4, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.ax = self.figure.add_subplot(111)
        self.plot()

    def plot(self, sizes=None, labels=None):
        self.ax.clear()
        if sizes is None or labels is None:
            sizes = [30, 25, 20, 15, 10]
            labels = ['A', 'B', 'C', 'D', 'E']
        colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc']
        self.ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        self.ax.axis('equal')
        self.canvas.draw()

# 下面左侧部分
class LeftCardWidget(SimpleCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.pie_widget = MatplotlibPieWidget(self)
        layout.addWidget(self.pie_widget)


# 右边中间表格
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

        self.table.cellClicked.connect(self.on_cell_clicked)

    def on_cell_clicked(self, row, column):
        if hasattr(self, 'report_interface'):
            self.report_interface.update_plots(row)

    def load_file_to_table(self, file_path, has_header):
        has_header = 1 if has_header == 0 else 0
        try:
            # 根据文件扩展名选择适当的读取方法
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, header=0 if has_header else None)
            elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                df = pd.read_excel(file_path, header=0 if has_header else None)
            else:
                raise ValueError("不支持的格式")

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
            print(f"加载文件错误: {str(e)}")


class ProcessingThread(QThread):
    finished = pyqtSignal(list)

    def __init__(self, report_interface, mapping_data, file_path, has_header):
        super().__init__()
        self.report_interface = report_interface
        self.mapping_data = mapping_data
        self.file_path = file_path
        self.has_header = has_header

    def run(self):
        try:
            # 清空Temp文件夹
            temp_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'Temp')
            if os.path.exists(temp_folder):
                shutil.rmtree(temp_folder)
            os.makedirs(temp_folder)

            processed_data = self.report_interface.process_data(self.mapping_data, self.file_path, self.has_header)
            base_path = os.path.abspath(os.path.dirname(__file__))
            res_255_data = self.report_interface.process_data_255(self.report_interface.filter_nan_to_zero(processed_data),
                                                 os.path.join(base_path, '..', 'resource', 'model',
                                                              'all_quantiles.xlsx'))
            r_data = self.report_interface.prepare_image_data(res_255_data, temp_folder)

            predictor = ImagePredictor(os.path.join(base_path, '..', 'resource', 'model', 'cnn_mcmc_model.pth'),
                                       self.report_interface.class_names)
            batch_results = predictor.predict_batch(r_data)

            self.finished.emit(batch_results)

        except Exception as e:
            print(f"Error in processing thread: {str(e)}")


# 遮罩
class OverlayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        layout = QVBoxLayout(self)
        self.spinner = IndeterminateProgressRing()
        self.spinner.setFixedSize(100, 100)
        self.spinner.setStrokeWidth(4)
        layout.addWidget(self.spinner, 0, Qt.AlignCenter)
        self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 128))

# 主页面
class ReportInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                margin: 0;
                padding: 0;
            }
        """)

        # 创建主垂直布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 上部分
        self.top_card = TopCardWidget(self)
        main_layout.addWidget(self.top_card, 1)

        # 下部分
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 5, 0, 0)
        bottom_layout.setSpacing(5)
        main_layout.addWidget(bottom_widget, 1)

        # 下部分左侧
        self.left_card = LeftCardWidget()
        bottom_layout.addWidget(self.left_card, 1)

        # 下部分右侧
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)
        bottom_layout.addWidget(right_widget, 2)

        # 右侧上部分
        self.right_top_card = RightCenterCard()
        self.right_top_card.report_interface = self
        right_layout.addWidget(self.right_top_card, 4)

        # 右侧下部分
        self.right_bottom_card = RightBottomCard(FluentIcon.DOCUMENT, self.tr("导出报告"), self.tr("导出预测结果（不含概率值）"))
        self.right_bottom_card.previousClicked.connect(self.on_previous_clicked)
        self.right_bottom_card.exportClicked.connect(self.export_results)
        right_layout.addWidget(self.right_bottom_card, 1)

        # 创建遮罩层和进度环
        self.overlay = OverlayWidget(self)
        self.overlay.hide()

        self.class_names = [
                'ARCHEAN CRATON', 'CONTINENTAL FLOOD BASALT', 'CONVERGENT MARGIN',
                'INTRAPLATE VOLCANICS', 'OCEAN ISLAND', 'OCEAN-BASIN FLOOD BASALT',
                'OCEANIC PLATEAU', 'RIFT VOLCANICS', 'SEAMOUNT', 'SUBMARINE RIDGE'
            ]

    # 导出数据
    def export_results(self):
        if not hasattr(self.right_top_card, 'table'):
            print("未检测到输入数据")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, self.tr("保存结果"), "", "Excel Files (*.xlsx)")
        if file_path:
            try:
                df = self.table_to_dataframe(self.right_top_card.table)
                df.to_excel(file_path, index=False)
                InfoBar.success(
                    title=self.tr('成功'),
                    content=self.tr("导出预测结果成功"),
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.BOTTOM,
                    duration=2000,
                    parent=self.parent()
                )
                print(f"导出文件路径 {file_path}")
            except Exception as e:
                print(f"导出错误: {str(e)}")

    # 表格转dataframe
    def table_to_dataframe(self, table):
        rows = table.rowCount()
        cols = table.columnCount()
        headers = [table.horizontalHeaderItem(i).text() for i in range(cols)]
        df = pd.DataFrame(columns=headers, index=range(rows))
        for i in range(rows):
            for j in range(cols):
                df.iloc[i, j] = table.item(i, j).text() if table.item(i, j) else ''
        return df

    # 清除数据
    def clear_data(self):
        # 清除临时文件夹
        temp_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'Temp')
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)
            os.makedirs(temp_folder)

        # 清除表格
        if hasattr(self.right_top_card, 'table'):
            self.right_top_card.table.clear()
            self.right_top_card.table.setRowCount(0)
            self.right_top_card.table.setColumnCount(0)

        # 清除图表
        self.top_card.plot_widget.plot()
        self.left_card.pie_widget.plot()

        self.top_card.plot_widget.show_default_message()

        print("数据清除成功")

    # 添加预测结果
    def add_predictions_to_table(self, batch_results):
        table = self.right_top_card.table
        col_index = table.columnCount()
        table.insertColumn(col_index)
        table.setHorizontalHeaderItem(col_index, QTableWidgetItem("predict_res"))

        for row, result in enumerate(batch_results):
            item = QTableWidgetItem(result['predicted_class'])
            table.setItem(row, col_index, item)

        self.batch_results = batch_results

    # 上一步
    def on_previous_clicked(self):
        print(self.parent().parent().objectName())
        self.parent().parent().switchToPreviousInterface()

    # 下一步
    def on_next_clicked(self):
        self.right_top_card.nextClicked.emit()

    # 接受映射关系并处理数据
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay.setGeometry(self.rect())

    def Get_data(self, mapping_data, file_path, has_header):
        self.overlay.show()  # 显示遮罩层和进度环
        self.processing_thread = ProcessingThread(self, mapping_data, file_path, has_header)
        self.processing_thread.finished.connect(self.on_processing_finished)
        self.processing_thread.start()

    def on_processing_finished(self, batch_results):
        self.overlay.hide()  # 隐藏遮罩层和进度环
        self.right_top_card.load_file_to_table(self.processing_thread.file_path, self.processing_thread.has_header)
        self.add_predictions_to_table(batch_results)
        self.update_pie_chart(batch_results)

    def update_plots(self, row):
        if hasattr(self, 'batch_results') and row < len(self.batch_results):
            result = self.batch_results[row]
            probabilities = result['all_probabilities']
            self.top_card.plot_widget.plot(probabilities, self.class_names)
        else:
            self.top_card.plot_widget.show_default_message()

    def update_pie_chart(self, batch_results):
        class_counts = {class_name: 0 for class_name in self.class_names}
        for result in batch_results:
            class_counts[result['predicted_class']] += 1

        sizes = list(class_counts.values())
        labels = list(class_counts.keys())
        self.left_card.pie_widget.plot(sizes, labels)

    def process_data(self, mapping_data, file_path, has_header):
        try:
            # 读取Excel文件
            if has_header == 0:
                df = pd.read_excel(file_path, header=0)
            else:
                df = pd.read_excel(file_path, header=None)

            # 获取mapping_data中的列数
            num_columns = len(mapping_data)

            # 创建结果列表
            result_data = [[] for _ in range(num_columns)]

            # 处理标题行
            headers = [key.split('(')[0] for key in mapping_data.keys()]

            # 遍历mapping_data处理数据行
            for i, (key, value) in enumerate(mapping_data.items()):
                if value is not None:
                    # 如果值不是None，从Excel获取对应列的数据
                    col_data = df.iloc[:, int(value)].tolist()
                    result_data[i] = col_data
                else:
                    # 如果值是None，填充0
                    result_data[i] = [0] * len(df)
            result_array = np.array(result_data).T.tolist()
            # 在结果数组的开头插入标题行
            result_array.insert(0, headers)

            return result_array

        except Exception as e:
            print(f"处理数据错误: {str(e)}")
            return None

    # 排除非法值
    def filter_nan_to_zero(self, array_2d_data):
        arr = np.array(array_2d_data, dtype=object)
        if arr.shape[0] < 2:
            return arr
        for i in range(1, arr.shape[0]):
            for j in range(arr.shape[1]):
                if i == 27 and j == 1:
                    print(arr[i, j])
                    print(type(arr[i, j]))
                # 检查是否为NaN或"nan"
                if isinstance(arr[i, j], (float, np.floating)) and np.isnan(arr[i, j]) or arr[i, j] == "nan":
                    arr[i, j] = 0

        return arr

    # 分位数转换
    def process_data_255(self, input_array, excel_file_path):
        input_df = pd.DataFrame(input_array[1:], columns=input_array[0])

        # 读取Excel文件
        excel_df = pd.read_excel(excel_file_path)

        # 去除括号及其内容
        excel_columns = [re.sub(r'\([^)]*\)', '', col).strip() for col in excel_df.columns]

        result_df = pd.DataFrame()

        for col in input_df.columns:
            # 在Excel中查找匹配的列
            matching_cols = [i for i, excel_col in enumerate(excel_columns) if excel_col.lower() == col.lower()]

            if matching_cols:
                excel_col_index = matching_cols[0]

                # 获取Excel中的分位数间隔
                quantiles = excel_df.iloc[:, excel_col_index].dropna().tolist()
                if len(quantiles) != 254:
                    print(f"警告：列 '{col}' 在Excel中没有254个间隔值")
                    result_df[col] = input_df[col]
                    continue

                # 计算分位数
                def get_quantile(value):
                    if pd.isna(value) or value == 0:
                        return 0
                    quantile = np.searchsorted(quantiles, value, side='right')
                    return min(quantile + 1, 255)

                result_df[col] = input_df[col].apply(get_quantile).astype(int)
            else:
                print(f"警告：列 '{col}' 在Excel中未找到匹配")
                result_df[col] = input_df[col]
        return result_df

    # 合成 RBG 输入
    def prepare_image_data(self, df, output_folder):
        assert df.shape[1] == 42

        # 确保输出文件夹存在
        os.makedirs(output_folder, exist_ok=True)
        data = df.values
        # 获取数据的行数
        num_samples = data.shape[0]

        for i in range(num_samples):
            # 分离RGB通道
            r = data[i, :14]
            g = data[i, 14:28]
            b = data[i, 28:42]

            # 计算每个通道的平均值并四舍五入到整数
            r_avg = round(np.mean(r))
            g_avg = round(np.mean(g))
            b_avg = round(np.mean(b))

            # 添加平均值到每个通道
            r = np.append(r, r_avg)
            g = np.append(g, g_avg)
            b = np.append(b, b_avg)

            # 重塑为5x3的形状
            r = r.reshape(5, 3)
            g = g.reshape(5, 3)
            b = b.reshape(5, 3)

            # 将RGB通道合并为一个3D数组
            rgb = np.stack((r, g, b), axis=-1)

            # 确保值在0-255范围内
            rgb = np.clip(rgb, 0, 255).astype(np.uint8)

            # 创建图像
            img = Image.fromarray(rgb)

            # 保存图像
            img_path = os.path.join(output_folder, f"sample_{i + 1}.png")
            img.save(img_path)

            print(f"Sample {i + 1} saved to {img_path}")
            print("========================")

        return output_folder