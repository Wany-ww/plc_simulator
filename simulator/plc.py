import asyncio
import logging
import random
import os
import traceback
from .mc_protocol import MCProtocolHandler

logger = logging.getLogger(__name__)

class PlcSimulator:
    def __init__(self, config, update_callback=None):
        self.config = config
        self.name = config.get("name", "Unnamed")
        self.port = config.get("port", 5000)
        self.series = config.get("series", "Q")
        self.script_path = config.get("script_path", "")
        self.script_interval_ms = config.get("script_interval_ms", 1000)
        
        # Disconnect simulation
        disc_cfg = config.get("disconnect_event", {})
        self.disc_interval = disc_cfg.get("interval_sec", 0)
        self.disc_chance = disc_cfg.get("chance_percent", 0)
        
        # Memory (D0 ~ D65535, 16-bit unsigned integers)
        self.d = [0] * 65536
        
        # Status
        self.is_running = False
        self.server = None
        self.script_task = None
        self.connections = set()
        
        # Callback when D-registers change (for WebSocket UI updates)
        self.update_callback = update_callback
        
        self.protocol = MCProtocolHandler(self)
        
        # Load user script
        self.script_globals = {}
        self._load_script()

    def _load_script(self):
        self.script_globals = {}
        if self.script_path and os.path.exists(self.script_path):
            try:
                with open(self.script_path, "r", encoding="utf-8") as f:
                    code = f.read()
                exec(code, self.script_globals)
                logger.info(f"Loaded script for {self.name}")
            except Exception as e:
                logger.error(f"Error loading script {self.script_path}: {e}")

    def read_d_registers(self, start_addr, length):
        if start_addr + length > 65536:
            raise ValueError("Out of bounds")
        return self.d[start_addr : start_addr + length]

    def write_d_registers(self, start_addr, values):
        length = len(values)
        if start_addr + length > 65536:
            raise ValueError("Out of bounds")
        for i, val in enumerate(values):
            self.d[start_addr + i] = val & 0xFFFF
        
        if self.update_callback:
            # Notify frontend
            self.update_callback(self.name, start_addr, length, self.d[start_addr:start_addr+length])

    async def _handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        logger.info(f"[{self.name}] Client connected from {addr}")
        self.connections.add(writer)
        
        last_disc_check = asyncio.get_event_loop().time()
        
        try:
            while self.is_running:
                # Disconnect simulation
                if self.disc_interval > 0:
                    current_time = asyncio.get_event_loop().time()
                    if current_time - last_disc_check > self.disc_interval:
                        last_disc_check = current_time
                        if random.randint(1, 100) <= self.disc_chance:
                            logger.info(f"[{self.name}] Simulating disconnect for {addr}")
                            break # Close connection

                try:
                    data = await asyncio.wait_for(reader.read(4096), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                    
                if not data:
                    break
                    
                response = self.protocol.handle_request(data)
                if response:
                    writer.write(response)
                    await writer.drain()
        except Exception as e:
            logger.error(f"[{self.name}] Client error: {e}")
        finally:
            logger.info(f"[{self.name}] Client disconnected {addr}")
            self.connections.discard(writer)
            writer.close()
            try:
                await writer.wait_closed()
            except:
                pass

    async def _run_script_loop(self):
        while self.is_running:
            if "update" in self.script_globals:
                try:
                    # Keep track of old state to only send updates for changed values? 
                    # For performance, maybe let the script or UI decide, but here we just run it.
                    self.script_globals["update"](self)
                    # For simplicity, if script modifies 'd', we can notify UI here
                    # Or we require script to call a specific API, but direct access is spec'd.
                    # We will send a generic "update" event, or the UI can poll.
                    # Given websocket, maybe broadcast full array is too big. We will figure it out in manager.
                    if self.update_callback:
                        self.update_callback(self.name, -1, -1, None) # indicate script update
                except Exception as e:
                    logger.error(f"[{self.name}] Script error: {e}")
                    traceback.print_exc()
            
            await asyncio.sleep(self.script_interval_ms / 1000.0)

    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        
        # Reload script just in case
        self._load_script()
        
        try:
            self.server = await asyncio.start_server(
                self._handle_client, "0.0.0.0", self.port
            )
            logger.info(f"[{self.name}] Started on port {self.port}")
            
            self.script_task = asyncio.create_task(self._run_script_loop())
            
            # Note: Not waiting for server to complete here, it runs in background
            asyncio.create_task(self.server.serve_forever())
        except Exception as e:
            self.is_running = False
            logger.error(f"[{self.name}] Failed to start: {e}")

    async def stop(self):
        if not self.is_running:
            return
        self.is_running = False
        
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.server = None
            
        for writer in list(self.connections):
            writer.close()
        self.connections.clear()
        
        if self.script_task:
            self.script_task.cancel()
            self.script_task = None
            
        logger.info(f"[{self.name}] Stopped")
