import json
import os
import asyncio
from typing import Dict, Any, Optional
from .plc import PlcSimulator

class PlcManager:
    def __init__(self, config_path="data/config.json", scripts_dir="data/scripts"):
        self.config_path = config_path
        self.scripts_dir = scripts_dir
        self.plcs: Dict[str, PlcSimulator] = {}
        self.update_callback = None
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        os.makedirs(self.scripts_dir, exist_ok=True)
        
        self.load_config()

    def set_update_callback(self, callback):
        self.update_callback = callback
        for plc in self.plcs.values():
            plc.update_callback = callback

    def load_config(self):
        if not os.path.exists(self.config_path):
            self.save_config([])
            return
            
        with open(self.config_path, "r", encoding="utf-8") as f:
            try:
                config_list = json.load(f)
                for cfg in config_list:
                    name = cfg.get("name")
                    if name:
                        plc = PlcSimulator(cfg, self.update_callback)
                        self.plcs[name] = plc
            except json.JSONDecodeError:
                print(f"Error decoding {self.config_path}")

    def save_config(self, configs=None):
        if configs is None:
            configs = [plc.config for plc in self.plcs.values()]
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(configs, f, indent=2)

    def get_plc(self, name: str) -> Optional[PlcSimulator]:
        return self.plcs.get(name)

    def create_plc(self, config: Dict[str, Any]):
        name = config.get("name")
        if not name or name in self.plcs:
            raise ValueError(f"PLC with name {name} already exists or invalid.")
        
        # Set default script path if not provided
        if not config.get("script_path"):
            config["script_path"] = os.path.join(self.scripts_dir, f"{name}_update.py")
            # Create a default script
            with open(config["script_path"], "w", encoding="utf-8") as f:
                f.write(f"# Script for {name}\n\ndef update(plc):\n    pass\n")
                
        plc = PlcSimulator(config, self.update_callback)
        self.plcs[name] = plc
        self.save_config()
        return plc

    def update_plc(self, name: str, config: Dict[str, Any]):
        plc = self.get_plc(name)
        if not plc:
            raise ValueError("PLC not found")
            
        was_running = plc.is_running
        if was_running:
            asyncio.create_task(plc.stop())
            
        # Keep old script path if new one not provided
        if "script_path" not in config:
            config["script_path"] = plc.config.get("script_path")
            
        plc.config.update(config)
        plc.port = config.get("port", plc.port)
        plc.series = config.get("series", plc.series)
        plc.script_interval_ms = config.get("script_interval_ms", plc.script_interval_ms)
        
        disc_cfg = config.get("disconnect_event", {})
        plc.disc_interval = disc_cfg.get("interval_sec", plc.disc_interval)
        plc.disc_chance = disc_cfg.get("chance_percent", plc.disc_chance)
        
        self.save_config()
        
        if was_running:
            asyncio.create_task(plc.start())

    def delete_plc(self, name: str):
        plc = self.get_plc(name)
        if plc:
            if plc.is_running:
                asyncio.create_task(plc.stop())
            del self.plcs[name]
            self.save_config()

    def get_script(self, name: str) -> str:
        plc = self.get_plc(name)
        if not plc or not plc.script_path or not os.path.exists(plc.script_path):
            return ""
        with open(plc.script_path, "r", encoding="utf-8") as f:
            return f.read()

    def save_script(self, name: str, code: str):
        plc = self.get_plc(name)
        if not plc:
            raise ValueError("PLC not found")
        if not plc.script_path:
            plc.script_path = os.path.join(self.scripts_dir, f"{name}_update.py")
            self.save_config()
            
        with open(plc.script_path, "w", encoding="utf-8") as f:
            f.write(code)
            
        # Reload if running
        plc._load_script()

    async def start_all(self):
        for plc in self.plcs.values():
            await plc.start()

    async def stop_all(self):
        for plc in self.plcs.values():
            await plc.stop()
