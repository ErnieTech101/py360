"""
config.py - PY360 System Configuration Reader
Part of the Python Mainframe Experience Layer

Reads PY360.cfg and exposes system configuration
to all other PY360 modules. Also runs the IPL sequence.
"""

import os
import datetime

SIM_ROOT  = os.path.dirname(os.path.abspath(__file__))
CFG_FILE  = os.path.join(SIM_ROOT, "PY360.cfg")

# Global config store - populated by load()
_cfg = {
    "sysname":   "PY360",
    "sysplex":   "LOCALPLEX",
    "nodename":  "UNKNOWN",
    "console":   {"cols": 80, "rows": 24},
    "volumes":   {},
    "iodevices": {},
    "defaults":  {"lrecl": 80, "recfm": "FB", "blksize": 800},
    "timezone":  {"offset": None, "name": "UNKNOWN"}
}


# --- Catalog I/O ---

def load():
    """Parse PY360.cfg and populate the config store."""
    if not os.path.exists(CFG_FILE):
        return  # silently use defaults

    with open(CFG_FILE, "r") as f:
        lines = f.readlines()

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith(";"):
            continue

        parts = line.split()
        if not parts:
            continue

        keyword = parts[0].upper()

        if keyword == "SYSNAME" and len(parts) >= 2:
            _cfg["sysname"] = parts[1]

        elif keyword == "SYSPLEX" and len(parts) >= 2:
            _cfg["sysplex"] = parts[1]

        elif keyword == "NODENAME" and len(parts) >= 2:
            _cfg["nodename"] = parts[1]

        elif keyword == "CONSOLE":
            params = _parse_params(parts[1:])
            _cfg["console"]["cols"] = int(params.get("COLS", 80))
            _cfg["console"]["rows"] = int(params.get("ROWS", 24))

        elif keyword == "VOLUME":
            params = _parse_params(parts[1:])
            volser = params.get("VOLSER")
            if volser:
                _cfg["volumes"][volser] = {
                    "type": params.get("TYPE", "DASD"),
                    "path": os.path.join(SIM_ROOT,
                                        params.get("PATH", f"datasets\\{volser}"))
                }

        elif keyword == "IODEVICE":
            params = _parse_params(parts[1:])
            addr = params.get("ADDR")
            if addr:
                _cfg["iodevices"][addr] = {
                    "type": params.get("TYPE", "PRINTER"),
                    "name": params.get("NAME", f"DEV{addr}"),
                    "file": os.path.join(SIM_ROOT, params.get("FILE",
                                        f"spool\\{addr}.txt")),
                    "mode": params.get("MODE", "APPEND")
                }

        elif keyword == "TIMEZONE":
            params = _parse_params(parts[1:])
            tz_val = params.get("TZOFFSET", "AUTO")
            if tz_val.upper() == "AUTO":
                local_tz = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
                offset   = datetime.datetime.now(datetime.timezone.utc).astimezone().utcoffset()
                hours    = int(offset.total_seconds() // 3600)
                _cfg["timezone"]["offset"] = hours
                _cfg["timezone"]["name"]   = str(local_tz)
            else:
                _cfg["timezone"]["offset"] = int(tz_val)
                _cfg["timezone"]["name"]   = f"UTC{int(tz_val):+d}"

        elif keyword == "LRECL" and len(parts) >= 2:
            _cfg["defaults"]["lrecl"] = int(parts[1])

        elif keyword == "RECFM" and len(parts) >= 2:
            _cfg["defaults"]["recfm"] = parts[1]

        elif keyword == "BLKSIZE" and len(parts) >= 2:
            _cfg["defaults"]["blksize"] = int(parts[1])


def _parse_params(tokens: list) -> dict:
    """Parse KEY=VALUE tokens into a dict."""
    result = {}
    for token in tokens:
        if "=" in token:
            k, v = token.split("=", 1)
            result[k.upper()] = v
    return result


# --- Accessors ---

def sysname()   -> str:  return _cfg["sysname"]
def sysplex()   -> str:  return _cfg["sysplex"]
def nodename()  -> str:  return _cfg["nodename"]
def console()   -> dict: return _cfg["console"]
def volumes()   -> dict: return _cfg["volumes"]
def iodevices() -> dict: return _cfg["iodevices"]
def defaults()  -> dict: return _cfg["defaults"]

def get_device(addr: str) -> dict | None:
    return _cfg["iodevices"].get(addr.upper())

def get_volume(volser: str) -> dict | None:
    return _cfg["volumes"].get(volser.upper())


# --- IPL Sequence ---

def run_ipl():
    """
    Execute the PY360 IPL sequence.
    Displays timestamped, numbered console messages.
    Called from py360.py or directly for testing.
    """
    import time
    import platform
    import psutil
    import wmi

    ipl_counter = [0]  # list so nested function can mutate it

    def ipl_msg(msg: str, warn: bool = False):
        ipl_counter[0] += 1
        prefix = "PY360W" if warn else "PY360I"
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"{ts} IPL{ipl_counter[0]:03d} {prefix} {msg}")
        time.sleep(0.5)

    # Header
    print("PY360 Python-based Single-User ASCII Mainframe Simulation for Windows 10/11")
    print("-" * 79)
    time.sleep(0.5)
    ipl_msg("IPL Start")

    # Host info via psutil/platform
    ram_total      = psutil.virtual_memory().total // (1024 * 1024)
    ram_avail      = psutil.virtual_memory().available // (1024 * 1024)
    cpu_cores_phys = psutil.cpu_count(logical=False)
    cpu_cores_logi = psutil.cpu_count(logical=True)
    cpu_freq       = int(psutil.cpu_freq().current)
    cpu_freq_max   = int(psutil.cpu_freq().max)
    disk_tot       = psutil.disk_usage('C:\\').total // (1024 * 1024)
    disk_free      = psutil.disk_usage('C:\\').free  // (1024 * 1024)
    host_name      = platform.node()
    host_os        = f"{platform.system()} {platform.release()}"
    cpu_arch       = platform.machine()

    # Deep CPU via WMI
    cpu_name = cpu_id = cpu_mfr = "UNKNOWN"
    l2_cache = l3_cache = 0
    try:
        c = wmi.WMI()
        for cpu in c.Win32_Processor():
            cpu_name = cpu.Name.strip()
            cpu_id   = cpu.ProcessorId.strip()
            cpu_mfr  = cpu.Manufacturer.strip()
            l2_cache = cpu.L2CacheSize or 0
            l3_cache = cpu.L3CacheSize or 0
            break
    except Exception as e:
        ipl_msg(f"WMI UNAVAILABLE: {e}", warn=True)

    ipl_msg(f"HOST OS: {host_os}  NODE: {host_name}")
    ipl_msg(f"PROCESSOR: {cpu_name}")
    ipl_msg(f"PROCESSOR ID: {cpu_id}  MFR: {cpu_mfr}")
    ipl_msg(f"ARCHITECTURE: {cpu_arch}  PHYSICAL CORES: {cpu_cores_phys}  LOGICAL: {cpu_cores_logi}")
    ipl_msg(f"FREQUENCY: {cpu_freq} MHZ  MAX: {cpu_freq_max} MHZ")
    ipl_msg(f"CACHE: L2={l2_cache}K  L3={l3_cache}K")
    ipl_msg(f"REAL STORAGE: {ram_total}M  AVAILABLE: {ram_avail}M")
    ipl_msg(f"DASD VOLUME C:  CAPACITY: {disk_tot}M  FREE: {disk_free}M")
    ipl_msg("HOST ENVIRONMENT VERIFIED")
    ipl_msg("LOADING PY360 NUCLEUS...")

    # Load config
    load()

    # Timezone fallback
    if _cfg["timezone"]["offset"] is None:
        local_tz = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
        offset   = datetime.datetime.now(datetime.timezone.utc).astimezone().utcoffset()
        _cfg["timezone"]["offset"] = int(offset.total_seconds() // 3600)
        _cfg["timezone"]["name"]   = str(local_tz)

    tz = _cfg["timezone"]
    ipl_msg(f"SYSTEM NAME: {sysname()}  SYSPLEX: {sysplex()}  NODE: {nodename()}")
    ipl_msg(f"TIMEZONE: {tz['name']}  OFFSET: UTC{tz['offset']:+d}")
    ipl_msg(f"CONSOLE: {console()['cols']} COLUMNS  {console()['rows']} ROWS")

    for volser, d in volumes().items():
        rel = os.path.relpath(d['path'], SIM_ROOT)
        ipl_msg(f"MOUNTING DASD VOLUME {volser:<8}  PATH={rel}")

    for addr, d in iodevices().items():
        rel = os.path.relpath(d['file'], SIM_ROOT)
        ipl_msg(f"DEVICE {addr} ONLINE  TYPE={d['type']:<8} NAME={d['name']:<8} FILE={rel}")

    ipl_msg("JES2  INITIATING JOB ENTRY SUBSYSTEM")
    ipl_msg("JES2  SPOOL VOLUMES MOUNTED AND AVAILABLE")
    ipl_msg("JES2  2 INITIATORS ACTIVE - READY TO ACCEPT JOBS")
    ipl_msg("JES2  $HASP426 SPECIFY OPTIONS - RECOVERY SUPPRESSED")

    # Install sample library
    import samples
    samples.install_samples(ipl_msg=lambda m: ipl_msg(m))

    ipl_msg("IPL Complete - System Ready")
    print("-" * 79)


if __name__ == "__main__":
    run_ipl()