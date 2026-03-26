"""
serial_reader.py — ESP32 Serial Communication Module
Reads NAND wear simulation data from ESP32 potentiometer via UART.
Provides safe connection management with fallback values.
"""

import threading
import time
from typing import Optional


class SerialReader:
    """
    Thread-safe serial reader for ESP32 potentiometer data.
    Reads integer values (0–4095) from ESP32 via UART.
    Falls back gracefully when no hardware is connected.
    """

    def __init__(self, port: str = "COM3", baud: int = 115200):
        self.port = port
        self.baud = baud
        self._ser = None
        self._connected = False
        self._last_value: int = 0
        self._lock = threading.Lock()

    # ── Connection Management ──────────────────────────────────────────────

    def connect(self) -> bool:
        """Open serial port. Returns True on success."""
        try:
            import serial  # type: ignore
            self._ser = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                timeout=1.0,
            )
            # Flush any stale buffer
            self._ser.reset_input_buffer()
            self._connected = True
            return True
        except Exception as e:
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

    # ── Data Reading ──────────────────────────────────────────────────────

    def read_value(self) -> int:
        """
        Read one integer value from serial.
        Returns last known value on error, 0 on first failure.
        """
        if not self.is_connected:
            return self._last_value

        try:
            with self._lock:
                raw = self._ser.readline()  # blocks up to `timeout` seconds
            line = raw.decode("utf-8", errors="replace").strip()
            if line:
                val = int(float(line))
                val = max(0, min(4095, val))
                self._last_value = val
                return val
        except (ValueError, UnicodeDecodeError):
            pass  # non-numeric line — skip
        except Exception:
            self._connected = False

        return self._last_value

    def send_feedback(self, signal: bytes):
        """
        Send feedback byte to ESP32 (e.g. b'1' = critical, b'0' = normal).
        Used to toggle LED on hardware side.
        """
        if not self.is_connected:
            return
        try:
            with self._lock:
                self._ser.write(signal)
        except Exception:
            pass

    # ── Port Discovery ────────────────────────────────────────────────────

    @staticmethod
    def list_ports() -> list:
        """Return list of available serial port names."""
        try:
            import serial.tools.list_ports  # type: ignore
            ports = serial.tools.list_ports.comports()
            return [p.device for p in sorted(ports)]
        except Exception:
            return ["COM3", "COM4", "COM5", "/dev/ttyUSB0", "/dev/ttyUSB1"]

    # ── Context Manager ───────────────────────────────────────────────────

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.disconnect()
