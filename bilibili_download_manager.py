from subprocess import Popen, PIPE
from re import compile, VERBOSE
from time import sleep
from threading import Thread
from loguru import logger
from PySide6.QtWidgets import *
from PySide6 import QtCore
from PySide6.QtUiTools import QUiLoader

timeout = 10
p = compile(
    r"""
    [\s\S]*                # skip site info
    title:\s*              # skip title tag
    (?P<title>[\s\S]*?)\r\n  # match title
    streams:[\s\S]*?\r\n     # skip streams tag
    [ \[\]DASH_\r\n]*        # enter DASH
    [- format:]*(?P<dash_format>[a-zA-Z0-9-]*)\r\n
    [ container:]*(?P<dash_container>[a-zA-Z0-9]*)\r\n
    [ quality:]*(?P<dash_quality>[\s\S]*?)\r\n
    [ size:]*(?P<dash_size>[0-9.]*)[\s\S]*
    """, VERBOSE)


def load_ui(file_name):
    ui_file = QtCore.QFile(file_name)
    if not ui_file.open(QtCore.QIODevice.ReadOnly):
        logger.error(f"Cannot open {ui_file_name}: {ui_file.errorString()}")
        sys.exit(-1)
    ui = QUiLoader().load(ui_file)
    ui_file.close()
    if not ui:
        logger.error(f"Failed to load ui: {loader.errorString()}")
        sys.exit(-1)
    return ui


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # load ui
        self.ui = load_ui("main.ui")

        # connect buttons
        self.ui.get_video_info.clicked.connect(self.get_video_info)

        self.ui.show()

    def you_get_video_info(self):
        args = ["you-get", "-t", str(timeout), "-i", self.ui.video_addr.text()]
        logger.info(f"Executing: {' '.join(args)}")
        proc = Popen(args, stdout=PIPE)
        sleep(timeout + 1)
        res = proc.stdout.read().decode()
        logger.debug(res)
        m = p.match(res)
        if m:
            self.ui.title.setText(m.group("title"))
            self.ui.format.setText(
                f"{m.group('dash_container')} ({m.group('dash_format')})")
            self.ui.quality.setText(m.group("dash_quality"))
            self.ui.video_size.setText(m.group("dash_size"))
            self.ui.get_video_info.setEnabled(True)
        else:
            # oops
            logger.error("FAILED to parse.")
            self.ui.get_video_info.setEnabled(True)

    @QtCore.Slot()
    def get_video_info(self):
        self.ui.get_video_info.setEnabled(False)
        Thread(target=self.you_get_video_info).start()


if __name__ == "__main__":
    app = QApplication([], WindowFlags=QtCore.Qt.WindowStaysOnTopHint
                       )  # fix casade but seems not really fixed it
    w_main_window = MainWindow()
    app.exec()
