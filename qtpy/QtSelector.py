import sys
import os
import importlib
from qtpy import (
    QtWidgets,
    QtGui,
    get_env,
    set_env,
    PythonQtValueError,
)


api_list = [
    api
    for api in ("PyQt5", "PySide2", "PyQt6", "PySide6")
    if importlib.util.find_spec(api) is not None
]
api_list.insert(0, "auto")


class QtApiSelector(QtWidgets.QComboBox):
    def __init__(self, *args, **kwargs):
        QtWidgets.QComboBox.__init__(self, *args, **kwargs)
        api_list_lower = [elt.lower() for elt in api_list]
        self.addItems(api_list)
        self.setMaxVisibleItems(self.count())
        current_api_ = get_env("QT_API", "auto")
        current_api = current_api_.lower()
        if current_api not in api_list_lower:
            raise PythonQtValueError(
                f"Specified QT_API={current_api_} environement variable is not in valid options"
            )
        self.setCurrentIndex(api_list_lower.index(current_api.lower()))
        self.setFocus()
        self.currentTextChanged.connect(self.setApi)

    def setApi(self, Api):
        set_env("QT_API", Api)

    """def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Escape, QtCore.Qt.Key_Return):
            self.close()
        else:
            QtWidgets.QComboBox.keyPressEvent(self, event)"""


class QtScaleSelector(QtWidgets.QComboBox):
    def __init__(self, *args, **kwargs):
        QtWidgets.QComboBox.__init__(self, *args, **kwargs)
        scale_list = (
            ["auto"]
            + [str(s / 10) for s in range(1, 20)]
            + [str(s / 5) for s in range(10, 21)]
        )
        scale_list_lower = [elt.lower() for elt in scale_list]
        self.addItems(scale_list)
        self.setMaxVisibleItems(self.count())
        current_scale_ = get_env("QT_SCALE", "auto")
        current_scale = current_scale_.lower()
        if current_scale not in scale_list_lower:
            if current_scale.isdigit():
                scale_list_lower.append(current_scale)
                self.addItem(current_scale)
                self.setMaxVisibleItems(self.count())
            else:
                raise PythonQtValueError(
                    f"Specified QT_SCALE={current_scale} environement variable is not in valid options"
                )
        self.setCurrentIndex(scale_list_lower.index(current_scale.lower()))
        self.setFocus()
        self.currentTextChanged.connect(self.setScale)

    def setScale(self, scale):
        set_env("QT_SCALE", scale)

    """def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Escape, QtCore.Qt.Key_Return):
            self.close()
        else:
            QtWidgets.QComboBox.keyPressEvent(self, event)"""


class QtFontSizeSelector(QtWidgets.QComboBox):
    def __init__(self, *args, **kwargs):
        QtWidgets.QComboBox.__init__(self, *args, **kwargs)
        font_size_list = (
            [
                "default",
            ]
            + [f"{points}" for points in range(7, 15)]
            + [f"{pixels} pixels" for pixels in range(0, 81)]
        )
        font_size_list_lower = [elt.lower() for elt in font_size_list]
        self.addItems(font_size_list)
        self.setMaxVisibleItems(self.count())
        current_font_size_ = get_env("QT_FONT_SIZE", "default")
        current_font_size = current_font_size_.lower()
        if current_font_size not in font_size_list_lower:
            if current_font_size not in font_size_list_lower and (
                current_font_size.isdigit() or current_font_size.endswith(" pixels")
            ):
                font_size_list_lower.append(current_font_size)
                self.addItem(current_font_size)
                self.setMaxVisibleItems(self.count())
            else:
                raise PythonQtValueError(
                    f"Specified QT_SCALE={current_font_size} environement variable is not in valid options"
                )
        self.setCurrentIndex(font_size_list_lower.index(current_font_size.lower()))
        self.setFocus()
        self.currentTextChanged.connect(self.setFontSize)

    def setFontSize(self, font_size):
        set_env("QT_FONT_SIZE", font_size)

    """def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Escape, QtCore.Qt.Key_Return):
            self.close()
        else:
            QtWidgets.QComboBox.keyPressEvent(self, event)"""


class QtFontSelector(QtWidgets.QFontComboBox):
    def __init__(self, *args, **kwargs):
        QtWidgets.QFontComboBox.__init__(self, *args, **kwargs)
        self.insertItem(0, "default")
        self.setMaxVisibleItems(self.count())
        current_font = get_env("QT_FONT", "default")
        try:
            self.setCurrentText(current_font)
        except:
            self.addItem(current_font)
            self.setMaxVisibleItems(self.count())
            self.setCurrentText(current_font)
        self.setFocus()
        self.currentTextChanged.connect(self.setFont)

    def setFont(self, font):
        set_env("QT_FONT", font)

    """def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Escape, QtCore.Qt.Key_Return):
            self.close()
        else:
            QtWidgets.QComboBox.keyPressEvent(self, event)"""


class QtSelector(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        selectors = {
            "QT_API": QtApiSelector,
            "QT_SCALE": QtScaleSelector,
            "QT_FONT": QtFontSelector,
            "QT_FONT_SIZE": QtFontSizeSelector,
        }
        self.Layout = QtWidgets.QGridLayout(self)
        row = 0
        for name, selector in selectors.items():
            widget = selector()
            self.Layout.addWidget(QtWidgets.QLabel(text=name), row, 0)
            self.Layout.addWidget(widget, row, 1)
            row += 1
        self.Layout.setColumnStretch(1, 2)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setDesktopFileName("QtSelector")
    widget = QtSelector()
    widget.show()
    widget.setWindowTitle("Qt Selector")

    iconPath = os.path.dirname(__file__) + "/Qt_selector.svg"
    if os.path.exists(iconPath):
        widget.setWindowIcon(QtGui.QIcon(iconPath))
    app.exec_()
