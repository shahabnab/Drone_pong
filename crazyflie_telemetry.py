# crazyflie_telemetry.py

from PyQt5.QtCore import QObject, pyqtSignal
from cflib.crtp import init_drivers
from cflib.crazyflie import Crazyflie
from cflib.crtp.crtpstack import CRTPPacket

TELEMETRY_PORT = 0x0F
TELEMETRY_CHANNEL = 0x07

class CrazyflieTelemetry(QObject):
    # Signal that emits telemetry messages as strings.
    telemetryUpdated = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cf = Crazyflie()

        # Register connection callbacks.
        self.cf.connected.add_callback(self.on_connect)
        self.cf.disconnected.add_callback(self.on_disconnect)
        
        # Emit an initial message.
        self.telemetryUpdated.emit("[INFO] Connecting ...\n")
        
        
        # Open the Crazyflie link – change parameters as needed.
        self.cf.open_link("radio://0/78/2M/E7E7E7E7E5")
        

    def on_connect(self, uri):
        print("DEBUG: on_connect called with uri:", uri)
        self.telemetryUpdated.emit(f"[Connected] {uri}\n")
        self.cf.add_port_callback(TELEMETRY_PORT, self.packet_callback)

    
    def on_disconnect(self, uri):
        print("DEBUG: on_disconnect called with uri:", uri)
        self.telemetryUpdated.emit(f"[Disconnected] {uri}\n")

    def send_command(self, value):
        pk = CRTPPacket()
        pk.port = TELEMETRY_PORT
        pk.channel = TELEMETRY_CHANNEL
        pk.data = bytes([value])
        pk.size = 1
        self.cf.send_packet(pk)
        self.telemetryUpdated.emit(f"[Sent] 0x{value:02X}\n")

    def packet_callback(self, pkt):
        data = pkt.data
        if len(data) >= 16:
            def u16(h, l): 
                return (h << 8) | l

            def i16(h, l):
                val = (h << 8) | l
                return val - 0x10000 if val >= 0x8000 else val

            droneFlags = u16(data[0], data[1])
            front  = u16(data[2], data[3])
            back   = u16(data[4], data[5])
            left   = u16(data[6], data[7])
            right  = u16(data[8], data[9])
            up     = u16(data[10], data[11])
            z      = u16(data[12], data[13])
            iscaled_yaw = i16(data[14], data[15])
            yaw_deg = (iscaled_yaw * 360.0) / 65536.0 % 360.0

            msg = (
                f"[Packet] Port: {pkt.port}, Channel: {pkt.channel}\n"
                f"[Flags ] 0x{droneFlags:04X}\n"
                f"[MultiR] F: {front} B: {back} L: {left} R: {right} U: {up}\n"
                f"[FlowD ] Height: {z} mm\n"
                f"[IMU   ] Yaw: {yaw_deg:.2f}°\n\n"
            )
            self.telemetryUpdated.emit(msg)



