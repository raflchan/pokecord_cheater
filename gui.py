import os
import sys

import clipboard
from PyQt5 import uic
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget

from poke_spotter import PokeSpotter


class Gui(QMainWindow):
    def __init__(self, matches: list, img_dir: str):
        super(Gui, self).__init__()
        self.ui = uic.loadUi('assets/ui/gui.ui', self)
        self.matches = matches
        self.current_idx = -1
        self.img_dir = img_dir

        self.next_match()
        self.ui.buttonNext.clicked.connect(self.next_match)
        self.ui.buttonPrev.clicked.connect(self.prev_match)
        self.ui.buttonCopy.clicked.connect(self.copy_match)

        self.show()
        
    def next_match(self):
        self.current_idx = self.current_idx + 1 if self.current_idx + 1 < len(self.matches) else 0
        self.set_match()

    def prev_match(self):
        self.current_idx = len(self.matches) - 1 if self.current_idx == 0 else self.current_idx - 1
        self.set_match()

    def set_match(self):
        path = os.path.join(self.img_dir, self.matches[self.current_idx]) + '.png'
        self.ui.labelImage.setPixmap(QPixmap(path))
        self.labelName.setText(self.matches[self.current_idx])

    def copy_match(self):
        clipboard.copy(f'p!catch {self.matches[self.current_idx]}')
        self.ui.statusBar.showMessage('copied!', 3000)

def main():
    spotter = PokeSpotter()
    matches = spotter.spot()
    if len(matches) == 0:
        print('NO MATCHES!')
        return

    app = QApplication(sys.argv)
    _ui = Gui(matches, 'assets/pokedex')
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
