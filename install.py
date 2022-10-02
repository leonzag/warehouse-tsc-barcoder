from pathlib import Path
import subprocess as sp
import os

from config import APP_NAME, APP_ICON


UI = Path('ui/gui')
RES = Path('ui/resources.qrc')
DEST = Path('barcoder/gui')

if __name__ == "__main__":
    print('\n-> Конвертация .ui файлов интерфейса в .py файлы')
    for ui in (ui for ui in UI.iterdir() if ui.suffix == '.ui'):
        pyui = DEST / ('ui_' + ui.with_suffix('.py').name)
        print(f'$> pyside6-uic {ui} > {pyui}')
        proc = sp.run(f'pyside6-uic {ui} > {pyui}', encoding='utf8', shell=True)

    print('\n-> Конвертация .qrc файла ресурсов в .py файл')
    pyres = DEST / ('rc_' + RES.with_suffix('.py').name)
    print(f'$> pyside6-rcc {RES} > {pyres}')
    proc = sp.run(f'pyside6-rcc {RES} > {pyres}', encoding='utf8', shell=True)

    print('\n-> Компиляция (упаковка) программы в исполняемый контейнер (Например EXE)')
    compile_cmd = [
        'pyinstaller',
        '--noconfirm',
        '--onefile',
        '--windowed',
        '--name', f'{APP_NAME}',
        '--icon', f'assets/img/{APP_ICON}',
        '--collect-submodules', 'reportlab.graphics.barcode'
    ]
    if os.name == 'nt':
        compile_cmd += ['--add-data', './assets;assets/', '--uac-admin']
    else:
        compile_cmd += ['--add-data', './assets:assets/']

    compile_cmd += ['main.py']
    print('$> ' + ' '.join(compile_cmd), end='\n\n')
    proc = sp.run(compile_cmd, encoding='utf8')
