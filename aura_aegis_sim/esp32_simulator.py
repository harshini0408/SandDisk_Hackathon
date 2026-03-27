import serial
import time
import random
import threading

# SET THIS TO THE PORT YOUR ESP32 WOULD CONNECT TO, 
# OR THE OTHER END OF A VIRTUAL COM PORT PAIR (e.g. COM6 if app is on COM5)
PORT = "COM5"
BAUD = 115200

def read_feedback(ser):
    """Listens for the LED:COLOR feedback from Streamlit"""
    while True:
        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode().strip()
                print(f"[Feedback received from AURA] -> {line}")
        except Exception:
            break
        time.sleep(0.1)

def run():
    try:
        ser = serial.Serial(PORT, BAUD, timeout=1)
        print(f"ESP32 Simulator started on {PORT}")
        
        # Start background thread to print LED feedback
        t = threading.Thread(target=read_feedback, args=(ser,), daemon=True)
        t.start()

        wear = 0
        loop_counter = 0

        while True:
            # 1. Generate SMART Telemetry (~5 Hz)
            # SMART:<wear>,<ecc>,<uecc>,<bad_blocks>,<pe_cycles>,<rber>,<temperature>,<latency>,<retry>,<relocated>,<program_fail>,<erase_fail>
            wear = min(100, wear + random.randint(0, 1))
            ecc = 100 + (wear * 5) + random.randint(0, 50)
            uecc = 1 if wear > 85 and random.random() < 0.1 else 0
            bad_blocks = 10 + int(wear * 0.5)
            pe_cycles = wear * 30
            rber = round(0.0001 * wear, 6)
            temp = 40 + int(wear * 0.2)
            latency = 75 + int(wear * 0.5)
            retry = wear // 2
            relocated = wear // 4
            prog_fail = wear // 10
            erase_fail = wear // 15

            smart_msg = f"SMART:{wear},{ecc},{uecc},{bad_blocks},{pe_cycles},{rber:.6f},{temp},{latency},{retry},{relocated},{prog_fail},{erase_fail}"
            ser.write((smart_msg + "\n").encode())
            print(f"Sent: {smart_msg}")

            # 2. Randomly trigger events every ~100 loops
            loop_counter += 1
            if loop_counter % 100 == 0:
                event = random.choice(["WRITE", "FAIL", "REBOOT"])
                event_msg = f"EVENT:{event}"
                ser.write((event_msg + "\n").encode())
                print(f"Sent: {event_msg}")

            time.sleep(0.2) # ~5 Hz

    except serial.SerialException as e:
        print(f"Error opening port {PORT}: {e}")
        print("Note: If you don't have hardware, make sure you're using a virtual serial port pair (like com0com).")

if __name__ == "__main__":
    run()
