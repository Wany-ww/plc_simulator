import struct
import logging

logger = logging.getLogger(__name__)

class MCProtocolHandler:
    def __init__(self, plc):
        self.plc = plc

    def handle_request(self, data: bytes) -> bytes:
        if len(data) < 11:
            return b""
        
        subheader = data[0:2]
        
        if subheader == b"\x50\x00": # 3E Frame
            return self._handle_3e(data)
        elif subheader == b"\x54\x00": # 4E Frame
            return self._handle_4e(data)
        else:
            logger.warning(f"Unknown subheader: {subheader.hex()}")
            return b""

    def _handle_3e(self, data: bytes) -> bytes:
        if len(data) < 11: return b""
        
        routing_info = data[2:7]
        # station_no = data[6] # for reference
        req_len = struct.unpack("<H", data[7:9])[0]
        
        if len(data) < 9 + req_len:
            return b""
            
        cpu_timer = data[9:11]
        command = struct.unpack("<H", data[11:13])[0]
        subcommand = struct.unpack("<H", data[13:15])[0]
        payload = data[15:9+req_len]
        
        response_payload = self._process_command(command, subcommand, payload)
        
        return self._build_response(b"\xD0\x00", routing_info, response_payload)

    def _handle_4e(self, data: bytes) -> bytes:
        if len(data) < 15: return b""
        
        serial_no = data[2:4]
        # reserved = data[4:6]
        routing_info = data[6:11]
        req_len = struct.unpack("<H", data[11:13])[0]
        
        if len(data) < 13 + req_len:
            return b""
            
        cpu_timer = data[13:15]
        command = struct.unpack("<H", data[15:17])[0]
        subcommand = struct.unpack("<H", data[17:19])[0]
        payload = data[19:13+req_len]
        
        response_payload = self._process_command(command, subcommand, payload)
        
        # 4E Response: Subheader (D4 00) + Serial + Reserved(00 00) + Routing + Length + EndCode + Data
        return self._build_response(b"\xD4\x00", routing_info, response_payload, serial_no=serial_no)

    def _process_command(self, command, subcommand, payload) -> tuple:
        """Returns (end_code, data_bytes)"""
        if command == 0x0401:  # Batch Read
            return self._handle_batch_read(payload)
        elif command == 0x1401:  # Batch Write
            return self._handle_batch_write(payload)
        else:
            return (0xC059, b"") # Unsupported command

    def _handle_batch_read(self, payload) -> tuple:
        if len(payload) < 6:
            return (0xC059, b"")
            
        address = payload[0] | (payload[1] << 8) | (payload[2] << 16)
        device_code = payload[3]
        length = struct.unpack("<H", payload[4:6])[0]
        
        if device_code != 0xA8: # Only D-register supported
            return (0xC05C, b"")
            
        try:
            values = self.plc.read_d_registers(address, length)
            resp_data = struct.pack(f"<{length}H", *values)
            return (0x0000, resp_data)
        except Exception as e:
            logger.error(f"Read error: {e}")
            return (0xC059, b"")

    def _handle_batch_write(self, payload) -> tuple:
        if len(payload) < 6:
            return (0xC059, b"")
            
        address = payload[0] | (payload[1] << 8) | (payload[2] << 16)
        device_code = payload[3]
        length = struct.unpack("<H", payload[4:6])[0]
        
        if device_code != 0xA8:
            return (0xC05C, b"")
            
        data_bytes = payload[6:]
        if len(data_bytes) < length * 2:
            return (0xC059, b"")
            
        values = struct.unpack(f"<{length}H", data_bytes[:length*2])
        
        try:
            self.plc.write_d_registers(address, values)
            return (0x0000, b"")
        except Exception as e:
            logger.error(f"Write error: {e}")
            return (0xC059, b"")

    def _build_response(self, subheader, routing_info, payload_tuple, serial_no=None) -> bytes:
        end_code, data = payload_tuple
        end_code_bytes = struct.pack("<H", end_code)
        resp_len = len(end_code_bytes) + len(data)
        
        frame = subheader
        if serial_no: # 4E
            frame += serial_no + b"\x00\x00"
            
        frame += routing_info
        frame += struct.pack("<H", resp_len)
        frame += end_code_bytes
        frame += data
        return frame

# Alias for backward compatibility if needed, but we should use a single handler
MCProtocol3E = MCProtocolHandler
