import os

# os.environ["QT_API"] = "pyqt5"
import sys
from qtpy import QtWidgets, API_NAME, scaled, QT_SCALE

app = QtWidgets.QApplication(sys.argv)
app.setDesktopFileName("SmartPython")
# custom_font = QtGui.QFont()
# custom_font.setPointSize(10)
# custom_font.setPixelSize(18)
# app.setFont(custom_font)
font = app.font()
widget = QtWidgets.QLabel()
widget.resize(scaled(500), scaled(500))
widget.show()
widget.setText(
    f"""QT_API {API_NAME} 
QT_SCALE {QT_SCALE} 
-----
QT_ENABLE_HIGHDPI_SCALING {os.environ.get("QT_ENABLE_HIGHDPI_SCALING",None)}
QT_USE_PHYSICAL_DPI {os.environ.get("QT_USE_PHYSICAL_DPI",None)}
QT_FONT_DPI {os.environ.get("QT_FONT_DPI",None)}
-----
devicePixelRatio {widget.devicePixelRatio()}
logicalDotsPerInch {QtWidgets.QApplication.screens()[0].logicalDotsPerInch()}
font {font.family()}
font.pointSize {font.pointSize()}
font.pointSizeF {font.pointSizeF()}
font.pixelSize {font.pixelSize()}
"""
)
app.exec_()
