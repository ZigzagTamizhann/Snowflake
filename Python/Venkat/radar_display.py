import serial
import re
import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

#.....
# --- Configuration ---
# Change the COM port here where your Subu board is connected
SERIAL_PORT = 'COM39'  # Change the COM port here where your Subu board is connected
BAUD_RATE = 115200
HTTP_PORT = 8000

# --- Global State ---
state = {
    "robot_pos": (0, 0),
    "robot_orientation": "?",
    "distance": -1.0,
    "status": "Initializing...",
    "grid_rows": 3,
    "grid_cols": 3
}
state_lock = threading.Lock()
httpd = None  # Global variable for the server instance
shutdown_event = threading.Event()

# --- Serial Reader Thread ---
def serial_reader():
    """Thread that continuously reads from the serial port."""
    global state
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")
    except serial.SerialException as e:
        print(f"Error: Could not open serial port '{SERIAL_PORT}'.")
        print(f"Details: {e}")
        return

    while not shutdown_event.is_set():
        if not ser.is_open:
            break
        try:
            line = ser.readline().decode('utf-8').strip()
            if line:
                with state_lock:
                    if "Position:" in line:
                        match = re.search(r"Position: \((\d+), (\d+)\), Facing: (['N','E','S','W'])", line)
                        if match: state["robot_pos"] = (int(match.group(1)), int(match.group(2))); state["robot_orientation"] = match.group(3)
                    elif "Distance measured:" in line:
                        match = re.search(r"Distance measured: ([\d\.]+)", line)
                        if match: state["distance"] = float(match.group(1))
                    elif "STATUS:" in line:
                        # Use the message directly after STATUS:
                        state["status"] = line.split("STATUS:", 1)[1].strip()
        except serial.SerialException as e:
            print(f"Serial connection error: {e}. Closing thread.")
            break # Exit thread on connection loss
        except Exception as e:
            print(f"Serial read error: {e}")
    ser.close()
    print("Serial reader thread has stopped and port is closed.")

# --- Web Server ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.get_html().encode('utf-8'))
        elif self.path == '/data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            with state_lock:
                self.wfile.write(json.dumps(state).encode('utf-8'))
        else:
            self.send_error(404, "File Not Found")

    def get_html(self):
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Subu Security Radar</title>
            <style>
                body { font-family: monospace; background-color: #000; color: #0F0; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                .main-container { display: flex; gap: 40px; border: 2px solid #0F0; padding: 20px; background-color: #1a1a1a; box-shadow: 0 0 20px #0F0; }
                .info-panel { width: 300px; }
                .radar-panel { width: 300px; height: 300px; }
                h1 { text-shadow: 0 0 5px #0F0; margin-bottom: 10px; text-align: center; }
                #info, #grid-container { font-size: 1.1em; line-height: 1.6; }
                #grid { display: inline-grid; border: 1px solid #444; margin-top: 10px; }
                .grid-cell { width: 40px; height: 40px; text-align: center; line-height: 40px; color: #666; }
                .robot { background-color: #0F0; color: #000; border-radius: 50%; }
                #radarCanvas { width: 100%; height: 100%; background-color: #020; border-radius: 50%; }
                .status-obstacle { color: #F00; font-weight: bold; text-shadow: 0 0 5px #F00; }
            </style>
        </head>
        <body>
            <div class="main-container">
                <div class="info-panel">
                    <h1>SYSTEM STATUS</h1>
                    <div id="info">
                        <div>STATUS: <span id="status">Initializing...</span></div>
                        <div>DISTANCE: <span id="distance">N/A</span></div>
                        <div>POSITION: <span id="position">?</span></div>
                    </div>
                    <div id="grid-container">
                        <div style="margin-top: 20px;">GRID VIEW:</div>
                        <div id="grid"></div>
                    </div>
                </div>
                <div class="radar-panel">
                    <canvas id="radarCanvas"></canvas>
                </div>
            </div>

            <script>
                const canvas = document.getElementById('radarCanvas');
                const ctx = canvas.getContext('2d');
                let radarAngle = 0;
                let currentData = {};

                function resizeCanvas() {
                    const size = canvas.offsetWidth;
                    canvas.width = size;
                    canvas.height = size;
                }

                function updateData() {
                    fetch('/data')
                        .then(response => response.json())
                        .then(data => {
                            currentData = data; // Store latest data
                            const statusEl = document.getElementById('status');
                            statusEl.innerText = data.status;
                            statusEl.className = data.status.includes('OBSTACLE') ? 'status-obstacle' : '';

                            document.getElementById('distance').innerText = data.distance >= 0 ? data.distance.toFixed(1) + ' cm' : 'N/A';
                            document.getElementById('position').innerText = `(${data.robot_pos[0]}, ${data.robot_pos[1]}) Facing: ${data.robot_orientation}`;
                            drawGrid(data);
                        })
                        .catch(err => console.error(err));
                }

                function drawRadar() {
                    const size = canvas.width;
                    const center = size / 2;
                    const obstacleDist = currentData.distance || -1;

                    ctx.fillStyle = 'rgba(0, 20, 0, 1)';
                    ctx.fillRect(0, 0, size, size);

                    ctx.strokeStyle = 'rgba(0, 255, 0, 0.3)';
                    ctx.lineWidth = 1;
                    for (let i = 1; i <= 4; i++) {
                        ctx.beginPath();
                        ctx.arc(center, center, (center / 4) * i, 0, 2 * Math.PI);
                        ctx.stroke();
                    }

                    ctx.save();
                    ctx.translate(center, center);
                    ctx.rotate(radarAngle);
                    const gradient = ctx.createLinearGradient(0, 0, center, 0);
                    gradient.addColorStop(0, 'rgba(0, 255, 0, 0)');
                    gradient.addColorStop(1, 'rgba(0, 255, 0, 0.8)');
                    ctx.strokeStyle = gradient;
                    ctx.lineWidth = 3;
                    ctx.beginPath();
                    ctx.moveTo(0, 0);
                    ctx.lineTo(center, 0);
                    ctx.stroke();
                    ctx.restore();

                    if (obstacleDist > 0 && obstacleDist <= 50) { // Max display range
                        const r = (obstacleDist / 50) * center;
                        ctx.fillStyle = 'rgba(255, 0, 0, 0.9)';
                        ctx.strokeStyle = 'rgba(255, 255, 255, 0.9)';
                        ctx.lineWidth = 2;
                        ctx.beginPath();
                        ctx.arc(center, center - r, 5, 0, 2 * Math.PI); // Obstacle always at the top
                        ctx.fill();
                        ctx.stroke();
                    }
                }

                function animate() {
                    radarAngle += 0.03;
                    if (radarAngle > 2 * Math.PI) radarAngle = 0;
                    drawRadar();
                    requestAnimationFrame(animate);
                }

                function drawGrid(data) {
                    const grid = document.getElementById('grid');
                    grid.innerHTML = '';
                    grid.style.gridTemplateColumns = `repeat(${data.grid_cols}, 40px)`;

                    for (let r = 0; r < data.grid_rows; r++) {
                        for (let c = 0; c < data.grid_cols; c++) {
                            const cell = document.createElement('div');
                            cell.className = 'grid-cell';
                            if (r === data.robot_pos[0] && c === data.robot_pos[1]) {
                                cell.classList.add('robot');
                                const arrow = {'N': '^', 'E': '>', 'S': 'v', 'W': '<'}[data.robot_orientation] || '?';
                                cell.innerText = arrow;
                            } else {
                                cell.innerText = '.';
                            }
                            grid.appendChild(cell);
                        }
                    }
                }

                setInterval(updateData, 500); // Update every 0.5 seconds
                window.onload = () => { resizeCanvas(); updateData(); animate(); };
                window.onresize = resizeCanvas;
            </script>
        </body>
        </html>
        """

def run_server():
    """HTTP சர்வரைத் தொடங்கும்."""
    global httpd
    try:
        server_address = ('', HTTP_PORT)
        httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
        print(f"Web server running at http://localhost:{HTTP_PORT}")
        # serve_forever() blocks, so we run it until shutdown is called
        while not shutdown_event.is_set():
            httpd.handle_request()
        print("Web server thread has stopped.")
    except Exception as e:
        print(f"Could not start web server: {e}")
        shutdown_event.set() # Signal other threads to stop

if __name__ == "__main__":
    # Start the web server in a separate thread
    server_thread = threading.Thread(target=run_server)
    server_thread.start()

    # Wait for the server to start
    while httpd is None and server_thread.is_alive() and not shutdown_event.is_set():
        pass

    if not shutdown_event.is_set():
        # Start the serial reader in a separate thread
        serial_thread = threading.Thread(target=serial_reader)
        serial_thread.start()

    try:
        # Let the main thread run so other threads can run
        server_thread.join()
        if 'serial_thread' in locals():
            serial_thread.join()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        shutdown_event.set()
        if httpd:
            # This is a bit of a hack to unblock handle_request
            # A proper solution would involve sockets with timeouts
            pass
        print("Shutdown complete.")