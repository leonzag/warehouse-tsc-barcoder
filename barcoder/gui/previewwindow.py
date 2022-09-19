from collections.abc import Sequence
from PySide6.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt

from .ui_previewwindow import Ui_PreviewWindow
from barcoder.parser import Dataset


class PreviewWindow(QWidget):
    def __init__(self, parent=None, windowModality=Qt.ApplicationModal):
        super(PreviewWindow, self).__init__(parent)
        self.ui = Ui_PreviewWindow()
        self.ui.setupUi(self)
        if windowModality:
            self.setWindowModality(windowModality)

    def reset(self):
        self.ui.table_successed.clearContents()
        self.ui.table_broken.clearContents()

    @staticmethod
    def _fill_table(table: QTableWidget, columns: Sequence[str], list_data: Dataset):
        table.clearContents()
        table.setColumnCount(len(columns))
        table.setRowCount(len(list_data))

        table.setHorizontalHeaderLabels(columns)

        for row, data in enumerate(list_data):
            for col, field in enumerate(data._fields):
                item = QTableWidgetItem(str(data._asdict()[field]))
                table.setItem(row, col, item)

        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def set_data(self, colnames: Sequence[str], correct_data: Dataset, incorrect_data: Dataset):
        """
        Заполнить таблицу предпросмотра данными
        """
        if correct_data:
            self._fill_table(self.ui.table_successed, colnames, correct_data)
            self.ui.tabWidget.setTabEnabled(1, False)  # Вкладка с некоррестными данными не активна
            self.ui.tabWidget.setCurrentIndex(0)       # Вкладка с корректными - открыта по умолчанию

        if incorrect_data:
            self._fill_table(self.ui.table_broken, colnames, incorrect_data)
            self.ui.tabWidget.setTabEnabled(1, True)  # Вкладка с некорректными данными активна
            self.ui.tabWidget.setCurrentIndex(1)      # открыта по умолчанию
