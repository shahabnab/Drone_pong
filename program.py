# program.py

import sys
from PyQt5.QtWidgets import QApplication
from main_form import MainForm
from cflib.crtp import init_drivers
from playsound import playsound

def main():
    #playsound("wining.mp3")
    init_drivers()
    app = QApplication(sys.argv)
    main_window = MainForm()
    main_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
