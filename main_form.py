# main_form.py

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QMessageBox, QTextEdit
)
import pyqtgraph as pg
from drone_tracker import DroneTracker
from crazyflie_telemetry import CrazyflieTelemetry

class MainForm(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Real-Time Drone Tracking and Telemetry')
        self.resize(900, 700)

        # Player score variables.
        self.player1_score = 0
        self.player2_score = 0

        # Set up the central widget and main layout.
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Create horizontal layout for player score labels.
        score_layout = QHBoxLayout()
        self.lblPlayer1Score = QLabel(f"Player1 Score: {self.player1_score}")
        self.lblPlayer2Score = QLabel(f"Player2 Score: {self.player2_score}")
        score_layout.addWidget(self.lblPlayer1Score)
        score_layout.addWidget(self.lblPlayer2Score)
        main_layout.addLayout(score_layout)

        # Create and configure the PyQtGraph plot widget.
        self.plot_widget = pg.PlotWidget(title='Drone X-Y Position')
        self.plot_widget.setLabel('left', 'Y Position')
        self.plot_widget.setLabel('bottom', 'X Position')
        self.plot_widget.showGrid(x=True, y=True)
        main_layout.addWidget(self.plot_widget)

        # Plot anchor positions (X and Y only).
        anchors = [
            [452, 190],
            [0, 80],
            [2, 287],
            [4, 493],
            [295, 570],
            [289, 0]
        ]
        anchor_x = [p[0] for p in anchors]
        anchor_y = [p[1] for p in anchors]
        self.plot_widget.plot(anchor_x, anchor_y, pen=None, symbol='x', symbolSize=12, symbolBrush=(255, 0, 0))

        # Plot the rectangle.
        rectangle_x = [0, 5, 295, 289, 0]
        rectangle_y = [0, 573, 570, 0, 0]
        rect_item = pg.PlotDataItem(rectangle_x, rectangle_y, connect='all',
                                    pen=pg.mkPen(color='g', width=1))
        self.plot_widget.addItem(rect_item)

        # Initialize a plot data item for the drone's position.
        self.drone_curve = self.plot_widget.plot([], [], pen=None, symbol='o', symbolSize=10, symbolBrush=('b'))

        # Create the "Emergency Stop" button.
        self.btnEmergencyStop = QPushButton("Emergency Stop")
        main_layout.addWidget(self.btnEmergencyStop)
        self.btnEmergencyStop.clicked.connect(self.on_emergency_stop)

        # Create a text edit for Crazyflie telemetry messages.
        self.telemetryText = QTextEdit()
        self.telemetryText.setReadOnly(True)
        self.telemetryText.setPlaceholderText("Crazyflie telemetry messages appear here...")
        main_layout.addWidget(self.telemetryText)

        # Instantiate and start the DroneTracker.
        self.drone_tracker = DroneTracker()
        self.drone_tracker.dronePositionUpdated.connect(self.update_drone_position)

        # Instantiate the CrazyflieTelemetry receiver.
        self.cfTelemetry = CrazyflieTelemetry()
        self.cfTelemetry.telemetryUpdated.connect(self.append_telemetry_text)

    def update_drone_position(self, pos):
        """
        Update the drone's position on the plot.
        :param pos: NumPy array [x, y, z]
        """
        x_val = pos[0]
        y_val = pos[1]
        self.drone_curve.setData([x_val], [y_val])

    def append_telemetry_text(self, text):
        print("DEBUG: Telemetry message:", text)
        self.telemetryText.append(text)


    def on_emergency_stop(self):
        """Stop tracking and show an alert."""
        self.drone_tracker.stop()
        QMessageBox.warning(self, "Emergency", "Emergency stop activated. Drone tracking halted!")
    
    def update_score_labels(self):
        """Update the player score labels.
           (Call this method after updating self.player1_score or self.player2_score.)
        """
        self.lblPlayer1Score.setText(f"Player1 Score: {self.player1_score}")
        self.lblPlayer2Score.setText(f"Player2 Score: {self.player2_score}")
