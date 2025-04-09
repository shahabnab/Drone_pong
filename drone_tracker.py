# drone_tracker.py

import time
import serial
import cupy as cp
import numpy as np
from scipy.optimize import least_squares

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

class DroneTracker(QObject):
    # Signal that emits the filtered drone position (a NumPy array [x, y, z]).
    dronePositionUpdated = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        # -------------------------- Serial Port Configuration --------------------------
        try:
            self.ser.close()
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

        # -------------------------- Anchor Positions --------------------------
        self.anchor_positions = np.array([
            [452, 190, 160],
            [0,   80, 160],
            [2,   287, 160],
            [4,   493, 160],
            [295, 570, 160],
            [289, 0,   160]
        ])

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

    def trilaterate_gpu(self, anchors, distances):
        anchors_gpu = cp.asarray(anchors)
        distances_gpu = cp.asarray(distances)
        initial_guess = np.array([150, 100, 50])

        def error_function(position):
            position_gpu = cp.asarray(position)
            d_calc_gpu = cp.linalg.norm(anchors_gpu - position_gpu, axis=1)
            return cp.asnumpy(d_calc_gpu - distances_gpu)

        result = least_squares(error_function, initial_guess, method='lm')
        return result.x if result.success else np.array([0, 0, 0])

    def update(self):
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
                            distances = eval(line_str)  # Consider json.loads for safety.
                            if isinstance(distances, list) and len(distances) == 6:
                                distances = np.array(distances, dtype=float)
                                invalid_count = np.sum(distances == -1)
                                if invalid_count > 2:
                                    print("Lost more than two anchors.")
                                    return

                                valid_mask = (distances != -1)
                                valid_anchors = self.anchor_positions[valid_mask]
                                valid_distances = distances[valid_mask]

                                if len(valid_distances) < 3:
                                    print("Not enough valid anchors to compute position.")
                                    return

                                drone_pos = self.trilaterate_gpu(valid_anchors, valid_distances)
                                self.drone_pos_filtered = self.alpha * self.drone_pos_filtered + (1 - self.alpha) * drone_pos

                                print("Drone Position (filtered):", self.drone_pos_filtered)
                                self.dronePositionUpdated.emit(self.drone_pos_filtered)

                                self.line_buffer.clear()
                                self.ser.flushInput()
                                self.ser.flushOutput()
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
