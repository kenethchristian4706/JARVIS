import os
import psutil
from typing import Literal
from tools.base import BaseTool, BaseSchema

class GetSystemInfoSchema(BaseSchema):
    info_type: Literal["cpu", "memory", "disk", "all"]

class GetSystemInfoTool(BaseTool):
    name = "get_system_info"
    description = "Checks system resource usage such as CPU, RAM (memory), and disk space."
    example_queries = ["how much RAM is free", "check CPU usage", "show disk space"]
    schema_class = GetSystemInfoSchema
    safety_level: Literal["auto", "confirm"] = "auto"

    def extract(self, query: str) -> dict:
        q = query.lower()
        
        has_cpu = "cpu" in q or "processor" in q
        has_mem = "ram" in q or "memory" in q or "free" in q
        has_disk = "disk" in q or "space" in q or "storage" in q or "drive" in q
        
        # Determine info_type based on keywords
        if sum([has_cpu, has_mem, has_disk]) > 1:
            info_type = "all"
        elif has_cpu:
            info_type = "cpu"
        elif has_mem:
            info_type = "memory"
        elif has_disk:
            info_type = "disk"
        else:
            # Ambiguity handling: Ask one clarifying question
            print("I couldn't identify if you want CPU, memory, or disk information.")
            ans = input("Which system info would you like to see? (cpu/memory/disk/all): ").strip().lower()
            if ans in ("cpu", "memory", "disk", "all"):
                info_type = ans
            else:
                info_type = "all"
                
        return {"info_type": info_type}

    def execute(self, params: GetSystemInfoSchema) -> str:
        info_type = params.info_type
        
        # CPU usage
        cpu_usage = psutil.cpu_percent(interval=0.1)
        
        # Memory info
        mem = psutil.virtual_memory()
        mem_free_gb = mem.available / (1024 ** 3)
        mem_total_gb = mem.total / (1024 ** 3)
        
        # Disk info (using the drive of the current working directory)
        drive = os.path.splitdrive(os.getcwd())[0] or "/"
        disk = psutil.disk_usage(drive)
        disk_free_gb = disk.free / (1024 ** 3)
        disk_total_gb = disk.total / (1024 ** 3)
        
        # Format results based on requested type
        if info_type == "cpu":
            return f"CPU Usage: {cpu_usage}%"
        elif info_type == "memory":
            return f"RAM: {mem_free_gb:.1f}GB free (Total: {mem_total_gb:.1f}GB)"
        elif info_type == "disk":
            return f"Disk ({drive}): {disk_free_gb:.1f}GB free (Total: {disk_total_gb:.1f}GB)"
        else:  # all
            return f"CPU: {cpu_usage}% | RAM: {mem_free_gb:.1f}GB free | Disk: {disk_free_gb:.1f}GB free"
