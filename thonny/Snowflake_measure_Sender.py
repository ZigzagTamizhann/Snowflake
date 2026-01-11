import network
import socket
import time
from machine import Pin, UART
import Cayo

# --- Configuration ---
WIFI_SSID = "Measuring-Bot-Control"
WIFI_PASSWORD = "password123"
ULTRASONIC_TRIGGER_PIN = Cayo.IO12
ULTRASONIC_ECHO_PIN = Cayo.IO14
UART_TX_PIN = Cayo.IO17
UART_RX_PIN = Cayo.IO16

# --- UART (Serial) Communication Setup ---
uart = UART(1, baudrate=115200, tx=UART_TX_PIN, rx=UART_RX_PIN)
print(f"UART configured on tx={UART_TX_PIN}, rx={UART_RX_PIN}.")

# --- Ultrasonic Sensor Class ---
class Ultrasonic:
    def __init__(self, trigger_pin, echo_pin):
        self.trigger = Pin(trigger_pin, Pin.OUT)
        self.echo = Pin(echo_pin, Pin.IN)

    def distance_cm(self):
        self.trigger.value(0); time.sleep_us(2)
        self.trigger.value(1); time.sleep_us(10)
        self.trigger.value(0)
        try:
            pulse_duration = time.ticks_us()
            while self.echo.value() == 0:
                if time.ticks_diff(time.ticks_us(), pulse_duration) > 30000: return -1
            pulse_start = time.ticks_us()
            while self.echo.value() == 1:
                if time.ticks_diff(time.ticks_us(), pulse_start) > 30000: return -1
            pulse_end = time.ticks_us()
            distance = (time.ticks_diff(pulse_end, pulse_start) * 0.0343) / 2
            return distance
        except OSError:
            return -1

ultrasonic = Ultrasonic(ULTRASONIC_TRIGGER_PIN, ULTRASONIC_ECHO_PIN)

# --- Web Page HTML ---
def get_web_page_html():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Measuring Bot</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; text-align: center; background-color: #282c34; color: white; }
            .container { max-width: 500px; margin: auto; padding: 15px; }
            .card { background-color: #3a3f4a; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
            .card h2 { margin-top: 0; color: #61dafb; }
            .joystick { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; user-select: none; margin-bottom: 20px; }
            .btn { background-color: #61dafb; color: #282c34; padding: 20px 0; font-size: 20px; border: none; border-radius: 8px; }
            .btn:active { background-color: #88eaff; }
            #forward { grid-column: 2; } #left { grid-column: 1; grid-row: 2; } #stop { grid-column: 2; grid-row: 2; background-color: #ff6e6e; } #right { grid-column: 3; grid-row: 2; } #backward { grid-column: 2; grid-row: 3; }
            .info-display { font-size: 1.2em; margin: 10px 0; }
            .info-display span { font-weight: bold; color: #6eff7e; }
            .mode-btn { background-color: #4CAF50; color: white; padding: 12px 18px; font-size: 16px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
            .mode-btn.active { background-color: #2a7c2d; }
            input[type=number] { padding: 8px; font-size: 16px; width: 80px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Measuring Bot</h1>
            <div class="card">
                <p class="info-display">Wall Distance: <span id="wall-dist">...</span> cm</p>
            </div>

            <div class="card">
                <h2>Mode</h2>
                <button id="manual-btn" class="mode-btn active" onclick="setMode('manual')">Manual</button>
                <button id="auto-btn" class="mode-btn" onclick="setMode('auto')">Auto</button>
            </div>

            <!-- Manual Mode UI -->
            <div id="manual-mode" class="card">
                <h2>Manual Control</h2>
                <div class="joystick">
                    <button id="forward" class="btn">▲</button>
                    <button id="left" class="btn">◄</button>
                    <button id="stop" class="btn">STOP</button>
                    <button id="right" class="btn">►</button>
                    <button id="backward" class="btn">▼</button>
                </div>
                <button id="find-btn" class="mode-btn" onclick="startManualMeasure()">1. Find</button>
                <button id="finish-btn" class="mode-btn" onclick="finishManualMeasure()">2. Finish</button>
                <p class="info-display">Measured Distance: <span id="manual-result">0</span> cm</p>
            </div>

            <!-- Auto Mode UI -->
            <div id="auto-mode" class="card" style="display:none;">
                <h2>Auto Control</h2>
                <label>Set Distance (cm): <input type="number" id="target-dist" value="50"></label>
                <button class="mode-btn" onclick="startAuto()">Start</button>
                <p class="info-display">Status: <span id="auto-status">Idle</span></p>
            </div>
        </div>

        <script>
            let manualMeasureStartTime = 0;

            function sendCommand(cmd) { fetch('/control?cmd=' + cmd); }

            document.querySelectorAll('.joystick .btn').forEach(btn => {
                const cmd = {forward: 'F', backward: 'B', left: 'L', right: 'R'}[btn.id];
                if (cmd) {
                    btn.addEventListener('mousedown', () => sendCommand(cmd));
                    btn.addEventListener('mouseup', () => sendCommand('S'));
                    btn.addEventListener('touchstart', (e) => { e.preventDefault(); sendCommand(cmd); });
                    btn.addEventListener('touchend', () => sendCommand('S'));
                }
            });
            document.getElementById('stop').addEventListener('click', () => sendCommand('S'));

            function setMode(mode) {
                document.getElementById('manual-mode').style.display = mode === 'manual' ? 'block' : 'none';
                document.getElementById('auto-mode').style.display = mode === 'auto' ? 'block' : 'none';
                document.getElementById('manual-btn').classList.toggle('active', mode === 'manual');
                document.getElementById('auto-btn').classList.toggle('active', mode === 'auto');
                sendCommand('S'); // Stop robot when changing modes
            }

            function startManualMeasure() {
                manualMeasureStartTime = Date.now();
                document.getElementById('manual-result').innerText = 'Moving...';
                alert('Find pressed. Now, use the backward button to move the car and press Finish.');
            }

            function finishManualMeasure() {
                if (manualMeasureStartTime === 0) {
                    alert('Please press "Find" first.');
                    return;
                }
                const duration = (Date.now() - manualMeasureStartTime) / 1000; // in seconds
                manualMeasureStartTime = 0;
                // Ask server to calculate distance based on time
                fetch(`/manual_finish?time=${duration.toFixed(2)}`)
                    .then(res => res.text())
                    .then(dist => {
                        document.getElementById('manual-result').innerText = dist;
                    });
            }

            function startAuto() {
                const target = document.getElementById('target-dist').value;
                document.getElementById('auto-status').innerText = 'Starting...';
                fetch(`/auto_start?target=${target}`)
                    .then(res => res.text())
                    .then(status => {
                        document.getElementById('auto-status').innerText = status;
                    });
            }

            // Periodically get distance from sensor
            setInterval(() => {
                fetch('/distance')
                    .then(res => res.text())
                    .then(dist => {
                        document.getElementById('wall-dist').innerText = dist;
                    });
            }, 1000);

            window.onload = () => setMode('manual');
        </script>
    </body>
    </html>
    """

# --- WiFi & Web Server Setup ---
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=WIFI_SSID, password=WIFI_PASSWORD)

while not ap.active(): time.sleep(0.5)

print("--- Measuring Bot Server ---")
print(f"WiFi Network: {WIFI_SSID}")
print(f"IP Address: http://{ap.ifconfig()[0]}")
print("----------------------------")

addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(1)

print("Web server is listening...")

# --- Main Server Loop ---
def parse_query(request_str):
    """Extracts query parameters from a GET request string."""
    params = {}
    query_start = request_str.find('?')
    if query_start != -1:
        query_string = request_str.split(' ')[1][query_start+1:]
        for part in query_string.split('&'):
            if '=' in part:
                key, value = part.split('=', 1)
                params[key] = value
    return params

def send_response(conn, body, content_type='text/html'):
    """Sends a standard HTTP response."""
    conn.send(f'HTTP/1.1 200 OK\nContent-Type: {content_type}\nConnection: close\n\n')
    conn.sendall(body)

while True:
    try:
        conn, addr = s.accept()
        request = conn.recv(1024).decode('utf-8')
        
        params = parse_query(request)
        
        if '/control' in request:
            cmd = params.get('cmd')
            if cmd:
                print(f"Sending command: {cmd}")
                uart.write(cmd + '\n')
            send_response(conn, 'OK', 'text/plain')

        elif '/distance' in request:
            dist = ultrasonic.distance_cm()
            send_response(conn, f"{dist:.1f}" if dist != -1 else "Error", 'text/plain')

        elif '/manual_finish' in request:
            # This is a simplified calculation.
            # You need to calibrate CAR_SPEED_CM_PER_SEC for your robot.
            CAR_SPEED_CM_PER_SEC = 15.0 
            try:
                duration = float(params.get('time', 0))
                calculated_dist = duration * CAR_SPEED_CM_PER_SEC
                send_response(conn, f"{calculated_dist:.1f}", 'text/plain')
            except (ValueError, TypeError):
                send_response(conn, "Invalid time", 'text/plain')

        elif '/auto_start' in request:
            try:
                target_dist = float(params.get('target'))
                threshold = 2.0 # Allowable error in cm
                print(f"Auto mode started. Target: {target_dist} cm")

                for _ in range(10): # Try for max 10 seconds
                    current_dist = ultrasonic.distance_cm()
                    if current_dist == -1: continue

                    error = target_dist - current_dist
                    print(f"Current: {current_dist:.1f}, Target: {target_dist}, Error: {error:.1f}")

                    if abs(error) <= threshold:
                        uart.write('S\n') # Stop
                        print("Position reached.")
                        break
                    elif error > 0: # Too close, need to move back
                        uart.write('B\n')
                    else: # Too far, need to move forward
                        uart.write('F\n')
                    
                    time.sleep(0.5) # Move for a short duration then re-check
                
                uart.write('S\n') # Final stop
                send_response(conn, 'Positioned', 'text/plain')

            except (ValueError, TypeError):
                send_response(conn, 'Invalid target', 'text/plain')

        else: # Serve the main page
            send_response(conn, get_web_page_html())
        
        conn.close()
    except Exception as e:
        if 'conn' in locals(): conn.close()
        print(f'Error: {e}')