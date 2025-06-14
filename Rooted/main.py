# main.py
import sys
from controllers.planner import Planner
from PySide6.QtWidgets import QApplication
from controllers.planner import Planner
from data.database import DatabaseHelper, PLANDAGEN
from views.main_view import RootedApp
from data.database import DatabaseHelper  # Toegevoegd

if __name__ == "__main__":

    app = QApplication(sys.argv)
    window = RootedApp()
    window.show()

    # De planner **pas starten ná het tonen van de GUI**:
    planner = Planner()
    planner.plan_next_task()

    sys.exit(app.exec())

