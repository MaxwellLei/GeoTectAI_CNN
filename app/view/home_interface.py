import os

from PyQt5.QtCore import Qt, QPoint, QSize, QUrl, QRect, QPropertyAnimation
from PyQt5.QtGui import QFont, QColor, QPainter
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QGraphicsOpacityEffect
from qfluentwidgets import (BodyLabel, CaptionLabel, TransparentToolButton, FluentIcon,
                            ImageLabel, isDarkTheme, SimpleCardWidget, HeaderCardWidget,
                            HyperlinkLabel, HorizontalFlipView, PrimaryPushButton, TitleLabel,
                            PillPushButton, setFont, ScrollArea, VerticalSeparator)

from qfluentwidgets.components.widgets.acrylic_label import AcrylicBrush


# 全屏图像灯箱
class LightBox(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        # 判断主题
        if isDarkTheme():
            tintColor = QColor(32, 32, 32, 200)
        else:
            tintColor = QColor(255, 255, 255, 160)

        # 获取当前文件路径
        base_path = os.path.abspath(os.path.dirname(__file__))
        # 获取图片的路径
        image_paths = [
            os.path.join(base_path, '..', 'resource', 'images', 'I_box', '1.jpg'),
            os.path.join(base_path, '..', 'resource', 'images', 'I_box', '2.jpg'),
            os.path.join(base_path, '..', 'resource', 'images', 'I_box', '3.jpg'),
            os.path.join(base_path, '..', 'resource', 'images', 'I_box', '4.jpg'),
        ]

        # 绘制背景
        self.acrylicBrush = AcrylicBrush(self, 30, tintColor, QColor(0, 0, 0, 0))
        # 实现淡入淡出
        self.opacityEffect = QGraphicsOpacityEffect(self)
        self.opacityAni = QPropertyAnimation(self.opacityEffect, b"opacity", self)
        self.opacityEffect.setOpacity(1)
        self.setGraphicsEffect(self.opacityEffect)

        # 创建新查看照片布局窗口
        self.vBoxLayout = QVBoxLayout(self)
        # 布局的关闭按钮
        self.closeButton = TransparentToolButton(FluentIcon.CLOSE, self)
        self.flipView = HorizontalFlipView(self)
        self.flipView.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.nameLabel = BodyLabel('屏幕截图 1', self)
        self.pageNumButton = PillPushButton('1 / 4', self)

        self.pageNumButton.setCheckable(False)
        self.pageNumButton.setFixedSize(80, 32)
        setFont(self.nameLabel, 16, QFont.DemiBold)

        self.closeButton.setFixedSize(32, 32)
        self.closeButton.setIconSize(QSize(14, 14))
        self.closeButton.clicked.connect(self.fadeOut)

        self.vBoxLayout.setContentsMargins(26, 28, 26, 28)
        self.vBoxLayout.addWidget(self.closeButton, 0, Qt.AlignRight | Qt.AlignTop)
        self.vBoxLayout.addWidget(self.flipView, 1)
        self.vBoxLayout.addWidget(self.nameLabel, 0, Qt.AlignHCenter)
        self.vBoxLayout.addSpacing(10)
        self.vBoxLayout.addWidget(self.pageNumButton, 0, Qt.AlignHCenter)
        # 添加图片显示
        self.flipView.addImages(image_paths)

        self.flipView.currentIndexChanged.connect(self.setCurrentIndex)

    def setCurrentIndex(self, index: int):
        self.nameLabel.setText(f'屏幕截图 {index + 1}')
        self.pageNumButton.setText(f'{index + 1} / {self.flipView.count()}')
        self.flipView.setCurrentIndex(index)

    def paintEvent(self, e):
        if self.acrylicBrush.isAvailable():
            return self.acrylicBrush.paint()

        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        if isDarkTheme():
            painter.setBrush(QColor(32, 32, 32))
        else:
            painter.setBrush(QColor(255, 255, 255))

        painter.drawRect(self.rect())

    def resizeEvent(self, e):
        w = self.width() - 52
        self.flipView.setItemSize(QSize(w, w * 9 // 16))

    # 显示图片放大展示窗口
    def fadeIn(self):
        rect = QRect(self.mapToGlobal(QPoint()), self.size())
        self.acrylicBrush.grabImage(rect)
        # 设置动画
        self.opacityAni.setStartValue(0)
        self.opacityAni.setEndValue(1)
        self.opacityAni.setDuration(150)
        self.opacityAni.start()
        self.show()

    # 隐藏图片放大显示窗口
    def fadeOut(self):
        self.opacityAni.setStartValue(1)
        self.opacityAni.setEndValue(0)
        self.opacityAni.setDuration(150)
        self.opacityAni.finished.connect(self._onAniFinished)
        self.opacityAni.start()

    # 动画完成后释放隐藏窗口
    def _onAniFinished(self):
        self.opacityAni.finished.disconnect()
        self.hide()


class StatisticsWidget(QWidget):
    """ Statistics widget """

    def __init__(self, title: str, value: str, parent=None):
        super().__init__(parent=parent)
        self.titleLabel = CaptionLabel(title, self)
        self.valueLabel = BodyLabel(value, self)
        self.vBoxLayout = QVBoxLayout(self)

        self.vBoxLayout.setContentsMargins(16, 0, 16, 0)
        self.vBoxLayout.addWidget(self.valueLabel, 0, Qt.AlignTop)
        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignBottom)

        setFont(self.valueLabel, 18, QFont.DemiBold)
        self.titleLabel.setTextColor(QColor(96, 96, 96), QColor(206, 206, 206))


class AppInfoCard(SimpleCardWidget):
    """ App information card """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.iconLabel = ImageLabel(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'resource', 'images', 'logo.png'), self)
        self.iconLabel.setBorderRadius(8, 8, 8, 8)
        self.iconLabel.scaledToWidth(120)

        self.nameLabel = TitleLabel('GeoTectAI_CNN', self)
        self.installButton = PrimaryPushButton(self.tr('访问网站'), self)
        self.companyLabel = HyperlinkLabel(
            QUrl('https://github.com/MaxwellLei/GeoTectAI_CNN'), 'Github', self)
        self.installButton.setFixedWidth(160)

        self.descriptionLabel = BodyLabel(
            self.tr('GeoTectAI_CNN 是一个基于 PyQt5 的 Fluent 风格软件，软件旨在帮助地质学家判别构造环境类别，提供了一种工具。'), self)
        self.descriptionLabel.setWordWrap(True)

        self.tagButton = PillPushButton(self.tr('深度学习'), self)
        self.tagButton.setCheckable(False)
        setFont(self.tagButton, 12)
        self.tagButton.setFixedSize(80, 32)

        self.shareButton = TransparentToolButton(FluentIcon.SHARE, self)
        self.shareButton.setFixedSize(32, 32)
        self.shareButton.setIconSize(QSize(14, 14))

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()
        self.topLayout = QHBoxLayout()
        self.statisticsLayout = QHBoxLayout()
        self.buttonLayout = QHBoxLayout()

        self.initLayout()
        self.setBorderRadius(8)

    def initLayout(self):
        self.hBoxLayout.setSpacing(30)
        self.hBoxLayout.setContentsMargins(34, 24, 24, 24)
        self.hBoxLayout.addWidget(self.iconLabel)
        self.hBoxLayout.addLayout(self.vBoxLayout)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)

        # name label and install button
        self.vBoxLayout.addLayout(self.topLayout)
        self.topLayout.setContentsMargins(0, 0, 0, 0)
        self.topLayout.addWidget(self.nameLabel)
        self.topLayout.addWidget(self.installButton, 0, Qt.AlignRight)

        # company label
        self.vBoxLayout.addSpacing(3)
        self.vBoxLayout.addWidget(self.companyLabel)

        # statistics widgets
        self.vBoxLayout.addLayout(self.statisticsLayout)
        self.statisticsLayout.setContentsMargins(0, 0, 0, 0)
        self.statisticsLayout.setAlignment(Qt.AlignLeft)

        # description label
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addWidget(self.descriptionLabel)

        # 按钮布局
        self.vBoxLayout.addSpacing(12)
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addLayout(self.buttonLayout)
        self.buttonLayout.addWidget(self.tagButton, 0, Qt.AlignLeft)
        self.buttonLayout.addWidget(self.shareButton, 0, Qt.AlignRight)

class GalleryCard(HeaderCardWidget):
    """ Gallery card """

    def __init__(self, parent=None):
        super().__init__(parent)

        # 获取当前文件路径
        base_path = os.path.abspath(os.path.dirname(__file__))
        # 获取图片的路径
        image_paths = [
            os.path.join(base_path, '..', 'resource', 'images', 'I_box', '1.jpg'),
            os.path.join(base_path, '..', 'resource', 'images', 'I_box', '2.jpg'),
            os.path.join(base_path, '..', 'resource', 'images', 'I_box', '3.jpg'),
            os.path.join(base_path, '..', 'resource', 'images', 'I_box', '4.jpg'),
        ]

        self.setTitle(self.tr('屏幕截图'))
        self.setBorderRadius(8)

        self.flipView = HorizontalFlipView(self)
        self.flipView.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.expandButton = TransparentToolButton(
            FluentIcon.CHEVRON_RIGHT_MED, self)

        self.expandButton.setFixedSize(32, 32)
        self.expandButton.setIconSize(QSize(12, 12))

        self.flipView.addImages(image_paths)
        self.flipView.setBorderRadius(8)
        self.flipView.setSpacing(10)

        self.headerLayout.addWidget(self.expandButton, 0, Qt.AlignRight)
        self.viewLayout.addWidget(self.flipView)


class HomeInterface(ScrollArea):
    def __init__(self, parent=None):
            super().__init__(parent)
            self.view = QWidget(self)

            self.vBoxLayout = QVBoxLayout(self.view)
            self.appCard = AppInfoCard(self)
            self.galleryCard = GalleryCard(self)

            self.setWidget(self.view)
            self.setWidgetResizable(True)
            self.setObjectName("HomeInterface")

            self.lightBox = LightBox(self)
            self.lightBox.hide()
            self.galleryCard.flipView.itemClicked.connect(self.showLightBox)

            # self.vBoxLayout.setSpacing(10)
            self.vBoxLayout.setContentsMargins(0, 0, 10, 30)
            self.vBoxLayout.addWidget(self.appCard,)
            self.vBoxLayout.addWidget(self.galleryCard,)

            self.enableTransparentBackground()

    def showLightBox(self):
        index = self.galleryCard.flipView.currentIndex()
        self.lightBox.setCurrentIndex(index)
        self.lightBox.fadeIn()


    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.lightBox.resize(self.size())
