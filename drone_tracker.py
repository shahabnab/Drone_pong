# drone_tracker.py

import time
import serial
import cupy as cp
import numpy as np
from scipy.optimize import least_squares

from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from playsound import playsound
import threading
# Import if needed for type hinting or references:
# from crazyflie_telemetry import CrazyflieTelemetry

def play_sound_non_blocking(sound_file):
    threading.Thread(target=playsound, args=(sound_file,), daemon=True).start()

class DroneTracker(QObject):
    # Signal that emits the filtered drone position (a NumPy array [x, y, z]).
    dronePositionUpdated = pyqtSignal(object)
    
    def __init__(self, parent=None, cfTelemetry=None):
        super().__init__(parent)
        
        # Store a reference to the CrazyflieTelemetry object
        self.cfTelemetry = cfTelemetry
        
        # Initialize game parameters
        self.player1_line_y = 565
        self.player2_line_y = 10
        self.virtual_wall_x = 285
        self.virtual_wall = False
        
        # Initialize score
        self.player1_score = 0
        self.player2_score = 0

        # These will get set from outside (main_form.py)
        self.player1_score_label = None  
        self.player2_score_label = None  
        self.virtual_wall_label = None
        
        # -------------------------- Serial Port Configuration --------------------------
        try:
            self.ser.close()  # Attempt to close previously open connection (if any)
        except Exception:
            pass

        self.SERIAL_PORT = 'COM26'  # Change as necessary
        self.BAUD_RATE = 460800     # Change to match your device's baud rate

        self.ser = serial.Serial(
            port=self.SERIAL_PORT,
            baudrate=self.BAUD_RATE,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1
        )

        self.ser.flushInput()
        self.ser.flushOutput()
        time.sleep(0.2)

        # ---------------------- CuPy Warm-up (Avoid Delays) ----------------------------
        cp.cuda.Device(0).use()
        cp.linalg.norm(cp.array([[1, 2, 3], [4, 5, 6]]), axis=1)

        # -------------------------- Low-Pass Filter Setup --------------------------
        self.alpha = 0.50
        self.drone_pos_filtered = np.array([0.0, 0.0, 0.0])

        # -------------------------- Serial Read Buffer --------------------------
        self.line_buffer = bytearray()
        self.distance_read_check = True

        # -------------------------- Timer for Updates --------------------------
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)  # 50 ms interval


    def check_score(self):
        if self.drone_pos[1] >= self.player1_line_y:
            self.player1_score += 1
            if self.player1_score_label is not None:
                self.player1_score_label.setText(f"Player 1 Score: {self.player1_score}")
            self.send_command(0x4A)
            time.sleep(1)
            
            print("Player 1 Score")
            # play_sound_non_blocking("wining.mp3")
                
        if self.drone_pos[1] <= self.player2_line_y:
            self.player2_score += 1
            if self.player2_score_label is not None:
                self.player2_score_label.setText(f"Player 2 Score: {self.player2_score}")
            self.send_command(0x4B)
            print("Player 2 Score")
            time.sleep(1)
            # play_sound_non_blocking("wining.mp3")
                
        if self.drone_pos[0] >= self.virtual_wall_x:
            self.virtual_wall = True
            if self.virtual_wall_label is not None:
                self.virtual_wall_label.setText(f"Virtual wall hit: {self.virtual_wall}")
            
            self.send_command(0xFF)  # Now calls the method below
            print("Virtual wall hit")
            time.sleep(3)
            # play_sound_non_blocking("wining.mp3")


    def update(self):
        # Process available data from the serial port.
        while self.ser.in_waiting > 0:
            char = self.ser.read(1)
            if not char:
                break

            if char == b'\n':
                if self.distance_read_check:
                    line_str = self.line_buffer.decode('utf-8').strip()
                    self.line_buffer.clear()
                    self.ser.flushInput()
                    self.ser.flushOutput()

                    if line_str:
                        try:
                            coords = eval(line_str)  # For safety, consider using json.loads instead.
                            self.drone_pos = np.array(coords, dtype=float)
                            self.drone_pos_filtered = (
                                self.alpha * self.drone_pos_filtered + 
                                (1 - self.alpha) * self.drone_pos
                            )

                            print("Drone Position (filtered):", self.drone_pos_filtered)
                            self.check_score()
                            
                            # Emit the updated position via signal.
                            self.dronePositionUpdated.emit(self.drone_pos_filtered)

                        except Exception as e:
                            print("Error parsing line:", e, "| Line was:", line_str)

                else:
                    self.line_buffer.clear()
            else:
                self.line_buffer.append(char[0])

    def stop(self):
        self.timer.stop()
        if self.ser.is_open:
            self.ser.close()

    # -----------------------------------------------------------------
    #   This method calls the CrazyflieTelemetry object's send_command
    # -----------------------------------------------------------------
    def send_command(self, value):
        """
        Forward commands to the CrazyflieTelemetry object if available.
        """
        if self.cfTelemetry is not None:
            self.cfTelemetry.send_command(value)
        else:
            print("No CrazyflieTelemetry instance available to handle the command.")
