from dataclasses import dataclass, field
from typing import Sequence, Union

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QProgressDialog as pd
from PySide6.QtWidgets import QMessageBox as mb

from barcoder.parser import Data, Dataset, Label, LabelType, LabelQtyMode, Font
from barcoder.exceptions import RenderDrawError, RenderSaveError

from .render import RenderLabel

__all__ = ['RenderThread']


@dataclass
class Progress:
    current_data: Union[Data, None] = None
    processed: int = 0
    successed: int = 0
    failed: int = 0
    failed_data: list[Data] = field(default_factory=list)
    interrupted: bool = False
    failure: bool = False


class RenderThread(QThread):

    signal_start = Signal(int)
    signal_progress = Signal()
    signal_finish = Signal()

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self._is_interrupted = False

        self.parent_window = parent
        self.progress: Progress
        self.progress_dlg: pd

        self.signal_start.connect(self.start_render)
        self.signal_progress.connect(self.update_progress)
        self.signal_finish.connect(self.finish_render)

    def interrupt(self):
        self.progress.interrupted = True

    def start_render(self, items: int):
        """Обработка сигнала начала рендеринга. Создает Диалог прогресса"""
        self.progress_dlg = pd('Генерация этикеток', 'Отмена', 0, items, self.parent_window)
        self.progress_dlg.setWindowTitle('Генерация этикеток')
        self.progress_dlg.setWindowModality(Qt.WindowModal)
        self.progress_dlg.canceled.connect(self.interrupt)  # pyright: ignore

    def update_progress(self):
        """Сигнал обновления прогресса рендеринга. Обновляет Диалог прогресса"""
        self.progress_dlg.setValue(self.progress.processed)
        if self.progress.current_data is not None:
            self.progress_dlg.setLabelText(f'Артикул: {self.progress.current_data.sku}')

    def finish_render(self):
        """
        Обработка сигнала завершения рендеринга.
        Показывает информационное окно, в зависимости от рез-та
        """
        p = self.progress
        if p.failure:
            mb(mb.Critical, 'Ошибка сохранения', 'Не удалось сохранить файл со сгенерированными этикетками',
               parent=self.parent_window).show()

        elif p.failed != 0:
            msg = mb(mb.Warning, 'Внимание',
                     f'PDF Файл создан, однако для {p.failed} наименований не были созданы этикетки',
                     parent=self.parent_window)
            msg.setDetailedText('\n'.join(f'{d.sku=}' for d in p.failed_data))
            msg.show()

        else:
            mb(mb.Information, 'Готово', 'PDF Файл с этикетками создан', parent=self.parent_window).show()

    def run(self,
            dataset: Dataset,
            filepath: str,
            label: Label,
            label_type: LabelType,
            qty_mode: LabelQtyMode,
            fonts: Sequence[Font]) -> None:
        """
        Начать процесс рендеринга
        """
        self.progress = Progress()
        self.render = RenderLabel(filepath, label, label_type, qty_mode, fonts)
        self.signal_start.emit(len(dataset))

        [self._draw(d) for d in dataset if not self.progress.interrupted]
        self._save()

    def _draw(self, data: Data):
        """Попытка отрисовки очередной этикетки"""
        self.progress.current_data = data
        self.signal_progress.emit()
        try:
            self.render.draw(data)
            self.progress.successed += 1
        except RenderDrawError:
            self.progress.failed += 1
            self.progress.failed_data += [data]
        finally:
            self.progress.processed += 1
            self.signal_progress.emit()

    def _save(self):
        """Попытка сохранить PDF документ"""
        if not self.progress.interrupted:
            try:
                self.render.save()
            except RenderSaveError:
                self.progress.failure = True
            finally:
                self.signal_finish.emit()
