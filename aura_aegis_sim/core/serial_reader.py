"""
serial_reader.py — ESP32 Serial Communication Module
Reads structured SMART telemetry and EVENT signals from ESP32 via UART.

Data format from ESP32:
  SMART:<wear>,<ecc>,<uecc>,<bad_blocks>,<pe_cycles>,<rber>,<temperature>,
        <latency>,<retry>,<relocated>,<program_fail>,<erase_fail>
  EVENT:WRITE | EVENT:FAIL | EVENT:REBOOT

Feedback to ESP32:
  LED:GREEN  / LED:YELLOW  / LED:RED  (newline terminated)
"""

import threading
from typing import Optional

# ── Default SMART snapshot (returned when no real data available) ─────────────
_DEFAULT_SMART: dict = {
    "wear":         0,
    "ecc":          0,
    "uecc":         0,
    "bad_blocks":   0,
    "pe_cycles":    0,
    "rber":         0.0,
    "temperature":  40,
    "latency":      0,
    "retry":        0,
    "relocated":    0,
    "program_fail": 0,
    "erase_fail":   0,
}

SMART_FIELDS = [
    ("wear",         int),
    ("ecc",          int),
    ("uecc",         int),
    ("bad_blocks",   int),
    ("pe_cycles",    int),
    ("rber",         float),
    ("temperature",  int),
    ("latency",      int),
    ("retry",        int),
    ("relocated",    int),
    ("program_fail", int),
    ("erase_fail",   int),
]

VALID_EVENTS = {"WRITE", "FAIL", "REBOOT"}


def _parse_smart_line(payload: str) -> Optional[dict]:
    """
    Parse the CSV portion of a SMART line.
    Returns a dict on success, None on any parsing error.
    """
    try:
        parts = payload.split(",")
        if len(parts) != len(SMART_FIELDS):
            return None
        result = {}
        for (name, cast), raw in zip(SMART_FIELDS, parts):
            result[name] = cast(raw.strip())
        return result
    except Exception:
        return None


class SerialReader:
    """
    Thread-safe serial reader for ESP32 structured telemetry.

    Parses two message types from the ESP32:
      • SMART:<csv>  → stores latest 12-field dict via get_smart()
      • EVENT:<name> → stores last event string via get_last_event()

    Falls back gracefully when no hardware is connected.
    Default port is COM5 at 115200 baud (per project spec).
    """

    def __init__(self, port: str = "COM5", baud: int = 115200):
        self.port = port
        self.baud = baud
        self._ser = None
        self._connected = False
        self._lock = threading.Lock()

        # ── Shared state (written from read_once, read from UI thread) ───────
        self._smart_data: dict = dict(_DEFAULT_SMART)
        self._last_event: Optional[str] = None

    # ── Connection Management ─────────────────────────────────────────────────

    def connect(self) -> bool:
        """Open serial port. Returns True on success."""
        try:
            import serial  # type: ignore
            self._ser = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                timeout=0.2,          # short timeout — non-blocking feel
            )
            self._ser.reset_input_buffer()
            self._connected = True
            return True
        except Exception:
            self._ser = None
            self._connected = False
            return False

    def disconnect(self):
        """Close serial port safely."""
        try:
            if self._ser and self._ser.is_open:
                self._ser.close()
        except Exception:
            pass
        self._ser = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        try:
            return self._connected and self._ser is not None and self._ser.is_open
        except Exception:
            return False

    # ── Data Reading ──────────────────────────────────────────────────────────

    def read_once(self):
        """
        Read and parse one line from serial.
        Updates internal _smart_data or _last_event.
        Call this from the Streamlit update loop (non-blocking — 0.2 s timeout).
        """
        if not self.is_connected:
            return

        try:
            with self._lock:
                raw = self._ser.readline()
        except Exception:
            self._connected = False
            return

        try:
            line = raw.decode("utf-8", errors="replace").strip()
        except Exception:
            return

        if not line:
            return

        if line.startswith("SMART:"):
            payload = line[6:]          # everything after "SMART:"
            parsed = _parse_smart_line(payload)
            if parsed is not None:
                with self._lock:
                    self._smart_data = parsed

        elif line.startswith("EVENT:"):
            event = line[6:].strip().upper()
            if event in VALID_EVENTS:
                with self._lock:
                    self._last_event = event

    def get_smart(self) -> dict:
        """Return the most recent SMART snapshot (thread-safe copy)."""
        with self._lock:
            return dict(self._smart_data)

    def get_last_event(self) -> Optional[str]:
        """
        Return and clear the most recent EVENT string, or None.
        Each event is consumed once.
        """
        with self._lock:
            ev = self._last_event
            self._last_event = None
            return ev

    # ── LED Feedback ──────────────────────────────────────────────────────────

    def send_feedback(self, signal: bytes):
        """
        Send LED command to ESP32.
        Preferred signals: b"LED:GREEN\\n"  b"LED:YELLOW\\n"  b"LED:RED\\n"
        """
        if not self.is_connected:
            return
        try:
            with self._lock:
                self._ser.write(signal)
        except Exception:
            pass

    def send_led(self, status: str):
        """
        Convenience helper.  status in {"GREEN", "YELLOW", "RED"}.
        Sends b"LED:GREEN\\n" etc.
        """
        if status not in {"GREEN", "YELLOW", "RED"}:
            return
        self.send_feedback(f"LED:{status}\n".encode("ascii"))

    # ── Port Discovery ────────────────────────────────────────────────────────

    @staticmethod
    def list_ports() -> list:
        """Return list of available serial port names."""
        try:
            import serial.tools.list_ports  # type: ignore
            ports = serial.tools.list_ports.comports()
            return [p.device for p in sorted(ports)]
        except Exception:
            return ["COM3", "COM4", "COM5", "/dev/ttyUSB0", "/dev/ttyUSB1"]

    # ── Context Manager ───────────────────────────────────────────────────────

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.disconnect()
