import struct
import logging

logger = logging.getLogger(__name__)

class MCProtocol3E:
    def __init__(self, plc):
        self.plc = plc  # Reference to the PlcSimulator

    def handle_request(self, data: bytes) -> bytes:
        if len(data) < 11:
            return b""
        
        subheader = data[0:2]
        if subheader != b"\x50\x00":
            # Invalid subheader
            return b""

        network_no = data[2]
        pc_no = data[3]
        io_no = data[4:6]
        station_no = data[7]
        req_len = struct.unpack("<H", data[7:9])[0]
        
        if len(data) < 9 + req_len:
            # Incomplete packet
            return b""
            
        cpu_timer = data[9:11]
        command = struct.unpack("<H", data[11:13])[0]
        subcommand = struct.unpack("<H", data[13:15])[0]
        
        # Parse based on command
        if command == 0x0401:  # Batch Read
            return self._handle_batch_read(data[2:7], cpu_timer, data[15:9+req_len])
        elif command == 0x1401:  # Batch Write
            return self._handle_batch_write(data[2:7], cpu_timer, data[15:9+req_len])
        else:
            # Unsupported command, return error
            return self._build_response(data[2:7], 0xC059, b"") # C059 is a general error code
            
    def _handle_batch_read(self, routing_info, cpu_timer, payload) -> bytes:
        if len(payload) < 6:
            return self._build_response(routing_info, 0xC059, b"")
            
        # 3E Frame device memory specifies Address in 3 bytes
        addr_bytes = payload[0:3]
        address = addr_bytes[0] | (addr_bytes[1] << 8) | (addr_bytes[2] << 16)
        
        device_code = payload[3]
        
        length = struct.unpack("<H", payload[4:6])[0]
        
        if device_code != 0xA8: # Only D-register supported for now
            return self._build_response(routing_info, 0xC05C, b"") # C05C: Error
            
        # Read from PLC memory
        try:
            values = self.plc.read_d_registers(address, length)
            # pack to bytes
            resp_data = struct.pack(f"<{length}H", *values)
            return self._build_response(routing_info, 0x0000, resp_data)
        except Exception as e:
            logger.error(f"Read error: {e}")
            return self._build_response(routing_info, 0xC059, b"")

    def _handle_batch_write(self, routing_info, cpu_timer, payload) -> bytes:
        if len(payload) < 6:
            return self._build_response(routing_info, 0xC059, b"")
            
        addr_bytes = payload[0:3]
        address = addr_bytes[0] | (addr_bytes[1] << 8) | (addr_bytes[2] << 16)
        
        device_code = payload[3]
        length = struct.unpack("<H", payload[4:6])[0]
        
        if device_code != 0xA8: # Only D-register supported for now
            return self._build_response(routing_info, 0xC05C, b"")
            
        data_bytes = payload[6:]
        if len(data_bytes) < length * 2:
            return self._build_response(routing_info, 0xC059, b"")
            
        values = struct.unpack(f"<{length}H", data_bytes[:length*2])
        
        try:
            self.plc.write_d_registers(address, values)
            return self._build_response(routing_info, 0x0000, b"")
        except Exception as e:
            logger.error(f"Write error: {e}")
            return self._build_response(routing_info, 0xC059, b"")
            
    def _build_response(self, routing_info, end_code, data: bytes) -> bytes:
        # Response Header: Subheader(D0 00) + Routing Info (Network No, PC No, IO No, Station No)
        header = b"\xD0\x00" + routing_info
        
        # End code (2 bytes) + Data length
        end_code_bytes = struct.pack("<H", end_code)
        resp_data_len = len(end_code_bytes) + len(data)
        
        # Build full frame
        frame = header + struct.pack("<H", resp_data_len) + end_code_bytes + data
        return frame
