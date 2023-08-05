#
# Copyright © 2009- The Spyder Development Team
# Copyright © 2014-2015 Colin Duquesnoy
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)

"""
**QtPy** is a shim over the various Python Qt bindings. It is used to write
Qt binding independent libraries or applications.

If one of the APIs has already been imported, then it will be used.

Otherwise, the shim will automatically select the first available API (PyQt5, PySide2,
PyQt6 and PySide6); in that case, you can force the use of one
specific bindings (e.g. if your application is using one specific bindings and
you need to use library that use QtPy) by setting up the ``QT_API`` environment
variable.

PyQt5
=====

For PyQt5, you don't have to set anything as it will be used automatically::

    >>> from qtpy import QtGui, QtWidgets, QtCore
    >>> print(QtWidgets.QWidget)

PySide2
======

Set the QT_API environment variable to 'pyside2' before importing other
packages::

    >>> import os
    >>> os.environ['QT_API'] = 'pyside2'
    >>> from qtpy import QtGui, QtWidgets, QtCore
    >>> print(QtWidgets.QWidget)

PyQt6
=====

    >>> import os
    >>> os.environ['QT_API'] = 'pyqt6'
    >>> from qtpy import QtGui, QtWidgets, QtCore
    >>> print(QtWidgets.QWidget)

PySide6
=======

    >>> import os
    >>> os.environ['QT_API'] = 'pyside6'
    >>> from qtpy import QtGui, QtWidgets, QtCore
    >>> print(QtWidgets.QWidget)

"""

from packaging.version import parse
import os
import platform
import sys
import warnings
import importlib

# Version of QtPy
__version__ = '2.4.0.dev0'

if os.name == "nt":
    from nt import environ as environ_nt
    import winreg
    import ctypes
    import subprocess

    orignal_environ = {key.upper(): value for key, value in environ_nt.items()}

    python_redefined_keys = set()
    for key, value in os.environ.items():
        if orignal_environ.get(key) != value:
            python_redefined_keys.add(key)

    def get_env(key, default=None):
        if key in python_redefined_keys:
            return os.environ[key]
        for reg_key in (
            winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Environment"),
            winreg.CreateKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"System\CurrentControlSet\Control\Session Manager\Environment",
            ),
        ):
            try:
                return winreg.QueryValueEx(reg_key, key)[0]
            except FileNotFoundError:
                pass
        return os.environ.get(key, default)  # utuile ?

    def set_env(key, value):
        info = subprocess.STARTUPINFO()
        info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        info.wShowWindow = 0  # Run Hidden
        os.environ[key] = value
        subprocess.Popen(["setx", key, value], startupinfo=info)

    # force process to be DPI Aware avoiding Window scalinf with blur with Qt6
    # as the same effect than change pythonw.exe property to DPI Aware
    try:  # >= win 8.1
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except:  # win 8.0 or less
        ctypes.windll.user32.SetProcessDPIAware()


elif os.name == "posix":
    # from posix import environ as environ_posix

    # encoding = sys.getfilesystemencoding()
    # orignal_environ = {
    #    key.decode(encoding, "surrogateescape"): value.decode(
    #        encoding, "surrogateescape"
    #    )
    #    for key, value in environ_posix.items()
    # }
    env_path = os.path.expanduser("~/.config/plasma-workspace/env/QtEnvironment.sh")
    orignal_environ = dict()
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if line.startswith("export "):
                    key, value = line[7:].strip().split("=")
                    orignal_environ[key] = value

    def get_env(key, default=None):
        if key in os.environ:
            return os.environ[key]
        return orignal_environ.get(key, default)

    def set_env(key, value):
        os.environ[key] = value
        env_path = os.path.expanduser("~/.config/plasma-workspace/env/QtEnvironment.sh")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    if line.startswith(f"export {key}="):
                        lines[i] = f"export {key}={value}\n"
                        break
                else:
                    lines.append(f"export {key}={value}\n")
        else:
            lines = [f"export {key}={value}\n"]
        with open(env_path, "w") as f:
            f.writelines(lines)

else:
    raise Exception("unknow OS")


# disable  Qt Scaling and leave use scale all wath we decide with the scaled function
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
os.environ["QT_USE_PHYSICAL_DPI"] = "1"


QT_FONT_SIZE = get_env("QT_FONT_SIZE", "default").lower()
QT_FONT = get_env("QT_FONT", "default")

class PythonQtError(RuntimeError):
    """Generic error superclass for QtPy."""


class PythonQtWarning(RuntimeWarning):
    """Warning class for QtPy."""


class PythonQtValueError(ValueError):
    """Error raised if an invalid QT_API is specified."""


class QtBindingsNotFoundError(PythonQtError, ImportError):
    """Error raised if no bindings could be selected."""
    _msg = 'No Qt bindings could be found'

    def __init__(self):
        super().__init__(self._msg)


class QtModuleNotFoundError(ModuleNotFoundError, PythonQtError):
    """Raised when a Python Qt binding submodule is not installed/supported."""
    _msg = 'The {name} module was not found.'
    _msg_binding = '{binding}'
    _msg_extra = ''

    def __init__(self, *, name, msg=None, **msg_kwargs):
        global API_NAME
        binding = self._msg_binding.format(binding=API_NAME)
        msg = msg or f'{self._msg} {self._msg_extra}'.strip()
        msg = msg.format(name=name, binding=binding, **msg_kwargs)
        super().__init__(msg, name=name)


class QtModuleNotInOSError(QtModuleNotFoundError):
    """Raised when a module is not supported on the current operating system."""
    _msg = '{name} does not exist on this operating system.'


class QtModuleNotInQtVersionError(QtModuleNotFoundError):
    """Raised when a module is not implemented in the current Qt version."""
    _msg = '{name} does not exist in {version}.'

    def __init__(self, *, name, msg=None, **msg_kwargs):
        global QT5, QT6
        version = 'Qt5' if QT5 else 'Qt6'
        super().__init__(name=name, version=version)


class QtBindingMissingModuleError(QtModuleNotFoundError):
    """Raised when a module is not supported by a given binding."""
    _msg_extra = 'It is not currently implemented in {binding}.'


class QtModuleNotInstalledError(QtModuleNotFoundError):
    """Raise when a module is supported by the binding, but not installed."""
    _msg_extra = 'It must be installed separately'

    def __init__(self, *, missing_package=None, **superclass_kwargs):
        self.missing_package = missing_package
        if missing_package is not None:
             self._msg_extra += ' as {missing_package}.'
        super().__init__(missing_package=missing_package, **superclass_kwargs)


# Qt API environment variable name
QT_API = 'QT_API'

# Names of the expected PyQt5 api
PYQT5_API = ['pyqt5']

PYQT6_API = ['pyqt6']

# Names of the expected PySide2 api
PYSIDE2_API = ['pyside2']

# Names of the expected PySide6 api
PYSIDE6_API = ['pyside6']

# Minimum supported versions of Qt and the bindings
QT5_VERSION_MIN = PYQT5_VERSION_MIN = '5.9.0'
PYSIDE2_VERSION_MIN = '5.12.0'
QT6_VERSION_MIN = PYQT6_VERSION_MIN = PYSIDE6_VERSION_MIN = '6.2.0'

QT_VERSION_MIN = QT5_VERSION_MIN
PYQT_VERSION_MIN = PYQT5_VERSION_MIN
PYSIDE_VERSION_MIN = PYSIDE2_VERSION_MIN

# Detecting if a binding was specified by the user
binding_specified = QT_API in os.environ

API_NAMES = {'pyqt5': 'PyQt5', 'pyside2': 'PySide2',
             'pyqt6': 'PyQt6', 'pyside6': 'PySide6'}
modules = list(API_NAMES.values())

# allow to change API without restarting Spyder on Windows
API_ = get_env(QT_API, "auto")
API = API_.lower()
if os.path.split(sys.argv[0])[1] == "spyder":
    API = "pyqt5"

if API == "auto":
    for module in modules:
        if module in sys.modules:
            API = module.lower()
            break
    else:
        for module in modules:
            if importlib.util.find_spec(module) is not None:
                API = module.lower()
                break
            else:
                raise QtBindingsNotFoundError

initial_api = API
if API not in list(API_NAMES.keys()) + list(API_NAMES.values()):
    raise PythonQtValueError(
        f'Specified QT_API={API_} environement variable is not in valid options: {", ".join(["default"] + list(API_NAMES.values()))}'
    )

is_old_pyqt = is_pyqt46 = False
QT5 = PYQT5 = True
QT4 = QT6 = PYQT4 = PYQT6 = PYSIDE = PYSIDE2 = PYSIDE6 = False

PYQT_VERSION = None
PYSIDE_VERSION = None
QT_VERSION = None

if API in PYQT5_API:
    try:
        from PyQt5.QtCore import PYQT_VERSION_STR as PYQT_VERSION  # analysis:ignore
        from PyQt5.QtCore import QT_VERSION_STR as QT_VERSION  # analysis:ignore

        QT5 = PYQT5 = True

        if sys.platform == 'darwin':
            macos_version = parse(platform.mac_ver()[0])
            if macos_version < parse('10.10'):
                if parse(QT_VERSION) >= parse('5.9'):
                    raise PythonQtError("Qt 5.9 or higher only works in "
                                        "macOS 10.10 or higher. Your "
                                        "program will fail in this "
                                        "system.")
            elif macos_version < parse('10.11'):
                if parse(QT_VERSION) >= parse('5.11'):
                    raise PythonQtError("Qt 5.11 or higher only works in "
                                        "macOS 10.11 or higher. Your "
                                        "program will fail in this "
                                        "system.")

            del macos_version
    except ImportError:
        API = 'pyside2'
    else:
        os.environ[QT_API] = API

if API in PYSIDE2_API:
    try:
        from PySide2 import __version__ as PYSIDE_VERSION  # analysis:ignore
        from PySide2.QtCore import __version__ as QT_VERSION  # analysis:ignore

        PYQT5 = False
        QT5 = PYSIDE2 = True

        if sys.platform == 'darwin':
            macos_version = parse(platform.mac_ver()[0])
            if macos_version < parse('10.11'):
                if parse(QT_VERSION) >= parse('5.11'):
                    raise PythonQtError("Qt 5.11 or higher only works in "
                                        "macOS 10.11 or higher. Your "
                                        "program will fail in this "
                                        "system.")

            del macos_version
    except ImportError:
        API = 'pyqt6'
    else:
        os.environ[QT_API] = API

if API in PYQT6_API:
    try:
        from PyQt6.QtCore import PYQT_VERSION_STR as PYQT_VERSION  # analysis:ignore
        from PyQt6.QtCore import QT_VERSION_STR as QT_VERSION  # analysis:ignore

        QT5 = PYQT5 = False
        QT6 = PYQT6 = True

    except ImportError:
        API = 'pyside6'
    else:
        os.environ[QT_API] = API

if API in PYSIDE6_API:
    try:
        from PySide6 import __version__ as PYSIDE_VERSION  # analysis:ignore
        from PySide6.QtCore import __version__ as QT_VERSION  # analysis:ignore

        QT5 = PYQT5 = False
        QT6 = PYSIDE6 = True

    except ImportError:
        raise QtBindingsNotFoundError from None
    else:
        os.environ[QT_API] = API


# If a correct API name is passed to QT_API and it could not be found,
# switches to another and informs through the warning
if API != initial_api and binding_specified:
    warnings.warn(
        f'Selected binding {initial_api!r} could not be found; '
        f'falling back to {API!r}',
        PythonQtWarning,
    )


# Set display name of the Qt API
API_NAME = API_NAMES[API]
os.environ["PYQTGRAPH_QT_LIB"] = API_NAME

try:
    # QtDataVisualization backward compatibility (QtDataVisualization vs. QtDatavisualization)
    # Only available for Qt5 bindings > 5.9 on Windows
    from . import QtDataVisualization as QtDatavisualization  # analysis:ignore
except (ImportError, PythonQtError):
    pass


def _warn_old_minor_version(name, old_version, min_version):
    """Warn if using a Qt or binding version no longer supported by QtPy."""
    warning_message = (
        f'{name} version {old_version} is not supported by QtPy. '
        'To ensure your application works correctly with QtPy, '
        f'please upgrade to {name} {min_version} or later.'
    )
    warnings.warn(warning_message, PythonQtWarning)


# Warn if using an End of Life or unsupported Qt API/binding minor version
if QT_VERSION:
    if QT5 and (parse(QT_VERSION) < parse(QT5_VERSION_MIN)):
        _warn_old_minor_version('Qt5', QT_VERSION, QT5_VERSION_MIN)
    elif QT6 and (parse(QT_VERSION) < parse(QT6_VERSION_MIN)):
        _warn_old_minor_version('Qt6', QT_VERSION, QT6_VERSION_MIN)

if PYQT_VERSION:
    if PYQT5 and (parse(PYQT_VERSION) < parse(PYQT5_VERSION_MIN)):
        _warn_old_minor_version('PyQt5', PYQT_VERSION, PYQT5_VERSION_MIN)
    elif PYQT6 and (parse(PYQT_VERSION) < parse(PYQT6_VERSION_MIN)):
        _warn_old_minor_version('PyQt6', PYQT_VERSION, PYQT6_VERSION_MIN)
elif PYSIDE_VERSION:
    if PYSIDE2 and (parse(PYSIDE_VERSION) < parse(PYSIDE2_VERSION_MIN)):
        _warn_old_minor_version('PySide2', PYSIDE_VERSION, PYSIDE2_VERSION_MIN)
    elif PYSIDE6 and (parse(PYSIDE_VERSION) < parse(PYSIDE6_VERSION_MIN)):
        _warn_old_minor_version('PySide6', PYSIDE_VERSION, PYSIDE6_VERSION_MIN)


 

from qtpy import QtCore, QtWidgets

eps = sys.float_info.epsilon


QT_SCALE = get_env("QT_SCALE", "auto").lower()
if QT_SCALE == "auto":
    QT_SCALE = None
else:
    QT_SCALE = float(QT_SCALE)
    if QT_SCALE == round(QT_SCALE):
        QT_SCALE = int(QT_SCALE)


def scaled(obj, *args):
    # scale = QtGui.QFontMetrics(QtGui.QFont()).height()/25.
    global QT_SCALE
    if QT_SCALE is None:
        QT_SCALE = QtWidgets.QApplication.screens()[0].logicalDotsPerInch() / 192.0
    scale = QT_SCALE
    if scale == 0:
        scale
    if args:
        return scaled((obj,) + args)
    elif scale == 1:
        return obj
    elif isinstance(obj, QtCore.QRect):
        x, y, width, height = obj.getRect()
        return QtCore.QRect(
            round(x * scale + eps),
            round(y * scale + eps),
            round(width * scale + eps),
            round(height * scale + eps),
        )
    elif isinstance(obj, int):
        return int(round(obj * scale + eps))  # id somthing make 1 pixel, and scale 0.5
    elif isinstance(obj, tuple):
        return (scaled(elt) for elt in obj)
    elif isinstance(obj, list):
        return [scaled(elt) for elt in obj]
    else:  # float , QtCore.QMargins, QtCore.QSize
        return obj * scale


if __name__ == "__main__":
    scaled(1)
