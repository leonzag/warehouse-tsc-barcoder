from pathlib import Path
from typing import NamedTuple, Sequence

from PySide6.QtWidgets import QMainWindow
from PySide6.QtWidgets import QMessageBox as mb
from PySide6.QtWidgets import QProgressDialog as pd
from PySide6.QtWidgets import QFileDialog as fd

from .ui_mainwindow import Ui_MainWindow
from .previewwindow import PreviewWindow

from barcoder.parser import ExcelParser, LayoutsParser, Label, LabelType, LabelQtyMode, Dataset, Font
from barcoder.render import RenderThread
from barcoder.exceptions import ExcelParsingError
import config as conf

__all__ = ['MainWindow']


class ParsedData(NamedTuple):
    colnames: Sequence[str] = []
    correct: Dataset = []
    incorrect: Dataset = []


class MainWindow(QMainWindow):
    """
    Главное окно, в котором происходит подключение Excel файла с данными.
    Опрос пользователя (Какой размер этикетки, ее тип и т.д.).
    И непосредственный запуск генерации итогового PDF файла с готовыми этикетками
    """
    def __init__(self, layouts: LayoutsParser, fonts: Sequence[Font], parent=None):
        super(MainWindow, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.render_thread: RenderThread = RenderThread(self)
        self.preview_window = PreviewWindow()
        self.progress_dlg: pd

        self.layouts = layouts  # Макеты этикеток
        self.fonts = fonts  # Список шрифтов
        self.data = ParsedData()  # Распарсенные данные

        # Поля текущих установленных значений
        self.file_attached: Path  # Excel файл с привязками (данные для этикеток) для парсинга
        self.is_file_attached: bool = False
        self.update_ui()
        self.init_events()

        # Установка начальных пользовательских данных в селекторы
        [self.ui.cmb_type.addItem(t.value, userData=t) for t in layouts.types]
        [self.ui.cmb_qty_mode.addItem(q.value, userData=q) for q in layouts.qty_modes]
        self.ui.cmb_type.setCurrentIndex(0)
        self.ui.cmb_qty_mode.setCurrentIndex(0)
        self.cmb_label_refresh()  # Размеры этикеток (в соотв-ии с типом)

    def init_events(self):
        self.ui.cmb_type.currentIndexChanged.connect(self.cmb_type_changed)     # pyright: ignore
        self.ui.btn_create.clicked.connect(self.btn_click)                      # pyright: ignore
        self.ui.btn_file_preview.clicked.connect(self.btn_click)                # pyright: ignore
        self.ui.btn_file_attach.clicked.connect(self.btn_click)                 # pyright: ignore

        self.ui.menu_file_attach.triggered.connect(self.menu_item_click)        # pyright: ignore
        self.ui.menu_file_unattach.triggered.connect(self.menu_item_click)      # pyright: ignore
        self.ui.menu_help_about.triggered.connect(self.menu_item_click)         # pyright: ignore
        self.ui.menu_help_tutor.triggered.connect(self.menu_item_click)         # pyright: ignore

    def update_ui(self):
        """
        Обновление интерфейса в соответствии с состоянием основных селекторов и полей (подкл.файл и тд)
        """
        correct = self.all_items_corrects()
        self.ui.menu_file_attach.setDisabled(correct)
        self.ui.menu_file_unattach.setEnabled(correct)
        self.ui.btn_file_preview.setEnabled(correct)
        self.ui.btn_create.setEnabled(correct)
        if correct:
            self.update_preview_window()

    def all_items_corrects(self):
        amt = type(self.ui.cmb_qty_mode.currentData()) is LabelQtyMode
        type_ = type(self.ui.cmb_type.currentData()) is LabelType
        label = type(self.ui.cmb_label.currentData()) is Label
        file = self.is_file_attached and self.file_attached.is_file()
        return all((file, type_, label, amt))

    def update_preview_window(self):
        """Обновление окна предпросмотра файла"""
        self.preview_window.reset()
        if self.data.correct or self.data.incorrect:
            self.preview_window.set_data(self.data.colnames, self.data.correct, self.data.incorrect)

    def btn_click(self):
        """Обработка событий нажатий кнопок"""
        btn = self.sender()
        btn_name = btn.objectName()

        if btn_name == 'btn_file_attach':
            self.attach_and_parse_file()  # Прикрепление и парсинг исходного файла с данными для этикеток

        if btn_name == 'btn_file_preview':
            self.update_preview_window()  # Нажатие на Просмотр (активация окна предпросмотра исходного файла)
            self.preview_window.show()

        if btn_name == 'btn_create':
            self.create_file()  # Нажатие на кнопку Создать файл с ШК

        self.update_ui()  # Обновление состояния всех элементов (селекторы, доступность кнопок и тд)

    def menu_item_click(self):
        """Обработка события нажатия на пункт меню"""
        item = self.sender()
        item_name = item.objectName()

        if item_name == 'menu_file_attach':
            self.attach_and_parse_file()

        if item_name == 'menu_file_unattach':
            # Открепление исходного файла
            self.is_file_attached = False
            self.ui.lb_filename.clear()
            self.update_preview_window()

        self.update_ui()

    def cmb_label_refresh(self):
        """Обновить селектор выбора этикетки в соответствии с типом"""
        self.ui.cmb_label.clear()
        type_ = self.ui.cmb_type.currentData()
        for lb in reversed(self.layouts.get_labels_by_type(type_)):
            w, h = lb.size.width, lb.size.height
            caption = f'{w}✕{h} mm: {lb.name}'
            self.ui.cmb_label.addItem(caption, userData=lb)
        self.ui.cmb_label.setCurrentIndex(0)

    def cmb_type_changed(self):
        """Обработка события: изменение типа этикетки"""
        self.cmb_label_refresh()
        if self.all_items_corrects():
            self.parse_file_data()
            self.update_preview_window()

    def attach_and_parse_file(self):
        """
        Подключение Excel файла и его парсинг
        """
        fp, _ = fd.getOpenFileName(
            self, 'Выберите Excel-файл с артикулами',
            dir=str(Path.home()), filter='Excel Files (*.xlsx *.xlsm)'
        )
        if fp and Path(fp).is_file():
            fp = Path(fp)
            self.ui.lb_filename.setText(fp.name)
            self.file_attached, self.is_file_attached = fp, True
            self.parse_file_data()

    def parse_file_data(self) -> bool:
        """
        Собрать данные в зависимости от типа этикетки
        Возвращает True или False в зависимости от успеха
        """
        try:
            parsed = ExcelParser(self.file_attached, self.ui.cmb_type.currentData())
            self.data = ParsedData(parsed.colnames,
                                   parsed.correct_data,
                                   parsed.incorrect_data)
            return True

        except ExcelParsingError as e:
            msg = mb(mb.Critical, 'Ошибка чтения данных', 'Не удалось получить данные из Excel файла')
            msg.setDetailedText(str(e))
            msg.show()
        return False

    def create_file(self):
        """
        Диалог сохранения файла и процесс его создания
        """
        if self.data.incorrect:
            ans = mb.warning(
                self,
                'Внимание',
                'Имеются некорректные данные в подключенном файле.\n'
                'Нажмите "Просмотр" (в верхней части главного окна), чтобы увидеть подробности.\n'
                'Если вы все равно продоложите, этикетки с этими данными не будут сгенерированы.',
                mb.Ok, mb.Abort
            )
            if ans == mb.Abort:
                return

        filepath, _ = fd.getSaveFileName(self, 'Укажите имя файла pdf с ШК',
                                         dir=str(conf.HOME_DIR), filter='PDF Files (*.pdf)')
        if filepath:
            filepath = str(Path(filepath).with_suffix('.pdf'))

            self.render_thread.run(
                dataset=self.data.correct,
                filepath=filepath,
                label=self.ui.cmb_label.currentData(),
                label_type=self.ui.cmb_type.currentData(),
                qty_mode=self.ui.cmb_qty_mode.currentData(),
                fonts=self.fonts
            )
