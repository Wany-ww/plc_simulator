import socket
import struct
import time

def test_mc_protocol(port=8080):
    # 3E Batch Read D0, length 2
    # Subheader(50 00), Net(00), PC(FF), IO(FF 03), Sta(00), Len(0C 00), Timer(10 00), Cmd(01 04), Sub(00 00), Addr(00 00 00), Code(A8), Len(02 00)
    read_3e = b"\x50\x00\x00\xFF\xFF\x03\x00\x0C\x00\x10\x00\x01\x04\x00\x00\x00\x00\x00\xA8\x02\x00"
    
    # 4E Batch Read D0, length 2
    # Subheader(54 00), Serial(01 00), Res(00 00), Net(00), PC(FF), IO(FF 03), Sta(00), Len(0C 00), Timer(10 00), Cmd(01 04), Sub(00 00), Addr(00 00 00), Code(A8), Len(02 00)
    read_4e = b"\x54\x00\x01\x00\x00\x00\x00\xFF\xFF\x03\x00\x0C\x00\x10\x00\x01\x04\x00\x00\x00\x00\x00\xA8\x02\x00"

    # Batch Write D10, values [123, 456]
    # 3E: ... Cmd(01 14), Sub(00 00), Addr(0A 00 00), Code(A8), Len(02 00), Data(7B 00 C8 01)
    write_3e = b"\x50\x00\x00\xFF\xFF\x03\x00\x10\x00\x10\x00\x01\x14\x00\x00\x0A\x00\x00\xA8\x02\x00\x7B\x00\xC8\x01"

    try:
        with socket.create_connection(("127.0.0.1", port), timeout=2) as sock:
            # Test Write
            print("Sending 3E Write D10 = [123, 456]")
            sock.sendall(write_3e)
            resp = sock.recv(1024)
            print(f"3E Write Resp: {resp.hex()}")
            
            # Test 3E Read
            print("Sending 3E Read D10, len 2")
            # Update read_3e to read D10
            read_3e_d10 = b"\x50\x00\x00\xFF\xFF\x03\x00\x0C\x00\x10\x00\x01\x04\x00\x00\x0A\x00\x00\xA8\x02\x00"
            sock.sendall(read_3e_d10)
            resp = sock.recv(1024)
            print(f"3E Read Resp: {resp.hex()}")
            if len(resp) >= 11:
                vals = struct.unpack("<2H", resp[-4:])
                print(f"Read values: {vals}")

            # Test 4E Read
            print("Sending 4E Read D10, len 2")
            read_4e_d10 = b"\x54\x00\x01\x00\x00\x00\x00\xFF\xFF\x03\x00\x0C\x00\x10\x00\x01\x04\x00\x00\x0A\x00\x00\xA8\x02\x00"
            sock.sendall(read_4e_d10)
            resp = sock.recv(1024)
            print(f"4E Read Resp: {resp.hex()}")
            if len(resp) >= 15:
                vals = struct.unpack("<2H", resp[-4:])
                print(f"Read values: {vals}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_mc_protocol()
