# proje.py
import time
import math
import random
import threading
from datetime import datetime, timezone

from flask import Flask, render_template, send_from_directory, jsonify, Response
from flask_socketio import SocketIO, emit

# ---------- CONFIG ----------
THRESHOLD_C = 75.0
COOL_DOWN_SECONDS = 300
STATION_ID = "ST-009"
STEP_INTERVAL = 1.0   # saniye
# ----------------------------

app = Flask(__name__, static_folder="static", template_folder="templates")
# use threading mode so it works without eventlet/gevent if not installed
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ---------------- Simulation classes (düzeltilmiş) ----------------
class ThermalSensor:
    def __init__(self, name="S1", bias=0.0, noise_std=0.5):
        self.name = name
        self.bias = bias
        self.noise_std = noise_std
        self.last_value = None

    def read(self, true_temp):
        val = true_temp + self.bias + random.gauss(0, self.noise_std)
        self.last_value = val
        return val

    def inject_drift(self, delta):
        self.bias += delta

    def set_faulty(self, fixed_value):
        # sensörü sabit yanlış değere ayarlar
        self.bias = fixed_value - 25.0
        self.noise_std = 0.0

class ChargerStation:
    def __init__(self, station_id=STATION_ID, threshold=THRESHOLD_C, double_sensor=False):
        self.station_id = station_id
        self.threshold = threshold
        self.relay_closed = True
        self.last_shutdown_ts = None
        self.double_sensor = double_sensor
        self.s1 = ThermalSensor("S1")
        self.s2 = ThermalSensor("S2") if double_sensor else None
        self.true_temp = 45.0
        self.current = 200.0
        self.log = []

    def step(self, t_sec, scenario=None):
        # gerçek sıcaklık dinamiği (basit)
        self.true_temp += 0.005 * math.sin(t_sec / 5.0) + 0.01

        # senaryo enjekte etme
        if scenario == "drift" and 30 <= t_sec <= 35:
            self.s1.inject_drift(30.0)
        if scenario == "transient" and 30 <= t_sec <= 32:
            self.s1.inject_drift(35.0)
        if scenario == "double_sensor_fail" and 30 <= t_sec <= 35 and self.double_sensor:
            self.s1.inject_drift(30.0)

        r1 = self.s1.read(self.true_temp)
        r2 = self.s2.read(self.true_temp) if self.double_sensor else None

        event = None
        alarm = False

        if self.relay_closed:
            if self.double_sensor:
                if r1 > self.threshold and r2 > self.threshold:
                    alarm = True
                elif r1 > self.threshold and (abs(r1 - r2) > 5.0):
                    event = "Sensor deviation detected (mismatch); logged"
                elif r1 > self.threshold and r2 <= self.threshold:
                    # conservative: mark but do not immediate shutdown
                    event = "High reading on S1 only; awaiting confirmation"
            else:
                if r1 > self.threshold:
                    alarm = True

            if alarm:
                self.relay_closed = False
                self.current = 0.0
                self.last_shutdown_ts = time.time()
                event = event or "Unexpected thermal shutdown during charging."
                self._log_event(r1, event)
                self._notify_tech(event, r1)
        else:
            # relay açık (shutdown) durumunda cooldown kontrolü
            if self.last_shutdown_ts is not None:
                elapsed = time.time() - self.last_shutdown_ts
                if elapsed >= COOL_DOWN_SECONDS:
                    if r1 < (self.threshold - 5.0) and (r2 is None or r2 < (self.threshold - 5.0)):
                        self.relay_closed = True
                        self.current = 200.0
                        event = "Auto-restart after cooldown"
                        self._log_event(r1, event)
                else:
                    if r1 > self.threshold:
                        event = "Persistent high sensor reading during cooldown"
                        self._log_event(r1, event)

        if event is None:
            event = "OK" if self.relay_closed else "SHUTDOWN"

        # final log (konsola yazdırma için suppress=False)
        self._log_event(r1, event, true_temp=self.true_temp, current=self.current, suppress_print=False)

        return {
            "time": t_sec,
            "r1": r1,
            "r2": r2,
            "true_temp": self.true_temp,
            "current": self.current,
            "relay_closed": self.relay_closed,
            "event": event
        }

    def _log_event(self, sensor_val, event, true_temp=None, current=None, suppress_print=True):
        ts = datetime.now(timezone.utc).isoformat()
        tt = true_temp if true_temp is not None else self.true_temp
        cur = current if current is not None else self.current
        log_line = f"{ts} | {self.station_id} | S1={sensor_val:.2f}°C | True={tt:.2f}°C | I={cur:.2f}A | {event}"
        self.log.append(log_line)
        if not suppress_print:
            print(log_line)

    def _notify_tech(self, event, sensor_val):
        msg = f"[AUTONOTIFY] {datetime.now().isoformat()} - {self.station_id} - {event} - sensor={sensor_val:.1f}C"
        print(msg)

# --------------- End simulation classes ----------------

sim_instance = ChargerStation(double_sensor=True)
_sim_thread = None
_sim_thread_stop = threading.Event()

def sim_loop(scenario="normal", step_interval=STEP_INTERVAL):
    start = time.time()
    t = 0
    while not _sim_thread_stop.is_set():
        try:
            out = sim_instance.step(int(t), scenario=scenario)
            # websocket üzerinden tarayıcıya gönder
            socketio.emit("sim_data", {
                "t": int(t),
                "s1": round(out["r1"], 2),
                "s2": round(out["r2"], 2) if out["r2"] is not None else None,
                "true_temp": round(out["true_temp"], 2),
                "current": round(out["current"], 2),
                "relay_closed": out["relay_closed"],
                "event": out["event"]
            })
        except Exception as e:
            print("Simulation loop error:", e)
        time.sleep(step_interval)
        t = time.time() - start

@app.route("/")
def index():
    return render_template("index.html")

# Basit favicon isteği engelleme
@app.route("/favicon.ico")
def favicon():
    return Response(status=204)

# Basit API (opsiyonel) - son logları döner
@app.route("/api/logs")
def api_logs():
    return jsonify(sim_instance.log[-200:])

# Socket.IO events
@socketio.on("connect")
def on_connect():
    print("Client connected")
    # immediately send a status snapshot
    emit("status", {
        "station": sim_instance.station_id,
        "threshold": sim_instance.threshold,
        "relay_closed": sim_instance.relay_closed
    })

@socketio.on("disconnect")
def on_disconnect():
    print("Client disconnected")

def start_sim_thread(scenario="normal"):
    global _sim_thread
    if _sim_thread is None or not _sim_thread.is_alive():
        _sim_thread_stop.clear()
        _sim_thread = threading.Thread(target=sim_loop, kwargs={"scenario": scenario, "step_interval": STEP_INTERVAL}, daemon=True)
        _sim_thread.start()
        print("Simulation thread started.")

def stop_sim_thread():
    _sim_thread_stop.set()

if __name__ == "__main__":
    # Start sim.
    start_sim_thread(scenario="drift")  # default senaryoyu burada belirleyebilirsin: normal | drift | transient | double_sensor_fail
    # Çalıştır
    print("Starting Flask + SocketIO server on http://localhost:5000")
    try:
        socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)

    except KeyboardInterrupt:
        stop_sim_thread()
        print("Shutting down.")