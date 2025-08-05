import os
import sys

from PyQt5.QtCore import Qt, QTranslator
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import FluentTranslator

from app.common.config import cfg
from app.view.main_window import MainWindow


# 屏幕 DPI 缩放
if cfg.get(cfg.dpiScale) != "Auto":
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))
else:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)

# 创建 application 对象
app = QApplication(sys.argv)
app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)

# 初始化-多语言加载
locale = cfg.get(cfg.language).value
print( cfg.get(cfg.language))
translator = FluentTranslator(locale)
galleryTranslator = QTranslator()
# galleryTranslator.load(locale, "app", ".", ":/app/i18n")

if str(cfg.get(cfg.language)) == "Language.ENGLISH":
    galleryTranslator.load(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app', 'resource', 'i18n', 'app.en_US.qm'))
else:
    galleryTranslator.load(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app', 'resource', 'i18n', 'app.zh_CN.qm'))
# print(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app', 'resource', 'i18n', 'app.en_US.qm'))

app.installTranslator(translator)
app.installTranslator(galleryTranslator)

# 创建主窗口
w = MainWindow()
w.show()

app.exec()
