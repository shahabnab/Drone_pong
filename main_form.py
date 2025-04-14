# main_form.py

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QMessageBox, QTextEdit
)
from PyQt5.QtCore import Qt

import pyqtgraph as pg

from drone_tracker import DroneTracker
from crazyflie_telemetry import CrazyflieTelemetry, STATE_COMMANDS

class MainForm(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Real-Time Drone Tracking and Telemetry')
        self.resize(900, 700)

        # --------------------- Score / Layout Setup ---------------------
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Player score variables
        self.player1_score = 0
        self.player2_score = 0

        # Horizontal layout for the scoreboard
        score_layout = QHBoxLayout()
        self.lblPlayer1Score = QLabel("Player1 Score: 0")
        self.lblPlayer2Score = QLabel("Player2 Score: 0")
        self.lblVirtualWall = QLabel("Virtual Wall: False")

        score_layout.addWidget(self.lblPlayer1Score)
        score_layout.addWidget(self.lblPlayer2Score)
        score_layout.addWidget(self.lblVirtualWall)
        main_layout.addLayout(score_layout)

        # --------------------- Plot Widget ---------------------
        self.plot_widget = pg.PlotWidget(title='Drone X-Y Position')
        self.plot_widget.setLabel('left', 'Y Position')
        self.plot_widget.setLabel('bottom', 'X Position')
        self.plot_widget.showGrid(x=True, y=True)
        main_layout.addWidget(self.plot_widget)

        # Example anchors (adjust to your actual anchor positions if needed)
        anchors = [
            [452, 190],
            [0,   80],
            [2,   287],
            [4,   493],
            [295, 570],
            [289, 0]
        ]
        anchor_x = [p[0] for p in anchors]
        anchor_y = [p[1] for p in anchors]
        self.plot_widget.plot(anchor_x, anchor_y, pen=None, symbol='x', symbolSize=12)

        # Example boundary rectangle
        rectangle_x = [0,   5,   295, 289, 0]
        rectangle_y = [0, 573, 570,   0,   0]
        rect_item = pg.PlotDataItem(rectangle_x, rectangle_y, connect='all', pen=pg.mkPen(color='g', width=1))
        self.plot_widget.addItem(rect_item)

        # Drone position plot
        self.drone_curve = self.plot_widget.plot([], [], pen=None, symbol='o', symbolSize=10)

        # --------------------- Buttons and Layouts ---------------------
        # Emergency Stop
        self.btnEmergencyStop = QPushButton("Emergency Stop")
        main_layout.addWidget(self.btnEmergencyStop)
        self.btnEmergencyStop.clicked.connect(self.on_emergency_stop)

        # Crazyflie control buttons layout
        self.cfButtonsLayout = QHBoxLayout()
        main_layout.addLayout(self.cfButtonsLayout)

        # Connect button (optional – see notes below)
        self.btnCfConnect = QPushButton("Connect")
        self.btnCfConnect.clicked.connect(self.on_cf_connect)
        self.cfButtonsLayout.addWidget(self.btnCfConnect)

        # State Command buttons (ARM, UNARM, etc.)
        for val, label in STATE_COMMANDS:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, v=val: self.on_cf_command(v))
            self.cfButtonsLayout.addWidget(btn)

        # --------------------- Telemetry Text Box ---------------------
        self.telemetryText = QTextEdit()
        self.telemetryText.setReadOnly(True)
        self.telemetryText.setPlaceholderText("Crazyflie telemetry messages appear here...")
        main_layout.addWidget(self.telemetryText)

        # --------------------- Crazyflie Telemetry ---------------------
        # 1) Create the CrazyflieTelemetry object
        self.cfTelemetry = CrazyflieTelemetry()
        self.cfTelemetry.telemetryUpdated.connect(self.append_telemetry_text)

        # --------------------- DroneTracker Setup ----------------------
        # 2) Pass it to DroneTracker so send_command() calls will work
        self.drone_tracker = DroneTracker(cfTelemetry=self.cfTelemetry)
        self.drone_tracker.player1_score_label = self.lblPlayer1Score
        self.drone_tracker.player2_score_label = self.lblPlayer2Score
        self.drone_tracker.virtual_wall_label  = self.lblVirtualWall

        # Connect the drone tracker’s position update signal to our plot
        self.drone_tracker.dronePositionUpdated.connect(self.update_drone_position)

    # -----------------------------------------------------------------
    #                           Callbacks
    # -----------------------------------------------------------------
    def on_emergency_stop(self):
        """
        Stop the drone tracker updates and show an alert.
        """
        self.drone_tracker.stop()
        QMessageBox.warning(self, "Emergency", "Emergency stop activated. Drone tracking halted!")

    def on_cf_connect(self):
        """
        Optional: If your CrazyflieTelemetry class implements a 'connect()' method,
        you can call it here to re-initialize the link or handle reconnection logic.
        """
        # For example, if you created a method inside CrazyflieTelemetry:
        #    def connect(self):
        #        self.cf.open_link("radio://...")
        #
        # Then here you could do:
        #    self.cfTelemetry.connect()
        #
        # If not, you can remove or repurpose this button.
        pass

    def on_cf_command(self, command):
        """
        Sends a state command to the Crazyflie (ARM, UNARM, etc.).
        """
        self.cfTelemetry.send_command(command)

    # -----------------------------------------------------------------
    #                          Utilities
    # -----------------------------------------------------------------
    def update_drone_position(self, pos):
        """
        Receives filtered position from DroneTracker and updates the plot.
        """
        x_val, y_val = pos[0], pos[1]
        self.drone_curve.setData([x_val], [y_val])

    def append_telemetry_text(self, text):
        """
        Appends messages from CrazyflieTelemetry to the QTextEdit.
        """
        self.telemetryText.append(text)
