import network
import socket
import select
import time
from machine import UART
import Cayo

latest_distance = "-1.0" # Global variable to store the latest distance

# --- Configuration ---
WIFI_SSID = "Subu-Radar"
WIFI_PASSWORD = "password123"

# --- UART (Serial) Communication Setup ---
# Use UART 1. Connect ESP32's TX (Cayo.IO9) to Subu's RX (IO2)
# and ESP32's RX (Cayo.IO10) to Subu's TX (IO1).
uart = UART(1, baudrate=115200, tx=Cayo.IO9, rx=Cayo.IO10, timeout=10) 
print("UART configured on tx=Cayo.IO9, rx=Cayo.IO10.")

# --- HTML, CSS & JavaScript for Web Interface ---
def get_web_page_html():
    """Returns the HTML for the radar web page."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Subu Radar</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: monospace; text-align: center; background-color: #000; color: #0F0; margin: 0; padding: 15px; }
            h1 { text-shadow: 0 0 5px #0F0; margin-bottom: 10px; }
            #radarContainer { position: relative; width: 90vw; max-width: 500px; aspect-ratio: 1 / 1; margin: 20px auto; }
            #radarCanvas { width: 100%; height: 100%; background-color: #020; border-radius: 50%; }
            #distanceDisplay { margin-top: 20px; font-size: 1.5em; }
            .controls { display: grid; grid-template-columns: 1fr 1fr 1fr; grid-gap: 15px; max-width: 300px; margin: 20px auto; user-select: none; }
            .btn { background-color: #0A0; color: #000; padding: 20px 0; font-size: 24px; border: 2px solid #0F0; border-radius: 10px; cursor: pointer; }
            .btn:active { background-color: #0F0; }
            #forward { grid-column: 2; }
            #left { grid-column: 1; grid-row: 2; }
            #stop { grid-column: 2; grid-row: 2; background-color: #A00; border-color: #F00; }
            #right { grid-column: 3; grid-row: 2; }
            #backward { grid-column: 2; grid-row: 3; }
        </style>
    </head>
    <body>
        <h1>Subu RADAR SYSTEM</h1>
        <div id="radarContainer">
            <canvas id="radarCanvas"></canvas>
        </div>
        <div id="distanceDisplay">DISTANCE: <span id="dist_val">--</span> cm</div>

        <div class="controls">
            <button id="forward" class="btn">▲</button>
            <button id="left" class="btn">◄</button>
            <button id="stop" class="btn">■</button>
            <button id="right" class="btn">►</button>
            <button id="backward" class="btn">▼</button>
        </div>

        <script>
            const canvas = document.getElementById('radarCanvas');
            const ctx = canvas.getContext('2d');
            let angle = 0;
            let obstacleDist = -1;

            function resizeCanvas() {
                const size = canvas.offsetWidth;
                canvas.width = size;
                canvas.height = size;
                drawRadar();
            }

            function drawRadar() {
                const size = canvas.width;
                const center = size / 2;
                
                // Black background
                ctx.fillStyle = 'rgba(0, 20, 0, 1)';
                ctx.fillRect(0, 0, size, size);

                // Concentric circles
                ctx.strokeStyle = 'rgba(0, 255, 0, 0.3)';
                ctx.lineWidth = 1;
                for (let i = 1; i <= 4; i++) {
                    ctx.beginPath();
                    ctx.arc(center, center, (center / 4) * i, 0, 2 * Math.PI);
                    ctx.stroke();
                }

                // Crosshairs
                ctx.beginPath();
                ctx.moveTo(0, center);
                ctx.lineTo(size, center);
                ctx.moveTo(center, 0);
                ctx.lineTo(center, size);
                ctx.stroke();

                // Sweeping line
                ctx.save();
                ctx.translate(center, center);
                ctx.rotate(angle);
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

                // Draw obstacle
                if (obstacleDist > 0 && obstacleDist <= 100) { // Max range 100cm for display
                    const r = (obstacleDist / 100) * center;
                    ctx.fillStyle = 'rgba(255, 0, 0, 0.9)';
                    ctx.strokeStyle = 'rgba(255, 255, 255, 0.9)';
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    // Obstacle is always in front (top of the circle)
                    ctx.arc(center, center - r, 5, 0, 2 * Math.PI);
                    ctx.fill();
                    ctx.stroke();
                }
            }

            function animate() {
                angle += 0.03;
                if (angle > 2 * Math.PI) {
                    angle = 0;
                }
                drawRadar();
                requestAnimationFrame(animate);
            }

            // --- Manual Control Functions ---
            function sendCommand(cmd) {
                fetch('/?cmd=' + cmd).catch(err => console.error('Error:', err));
            }

            const control_buttons = {
                'forward': 'F', 'backward': 'B', 'left': 'L', 'right': 'R'
            };

            for (const [id, cmd] of Object.entries(control_buttons)) {
                const button = document.getElementById(id);
                // Use mousedown/touchstart to start moving
                button.addEventListener('mousedown', () => sendCommand(cmd));
                button.addEventListener('touchstart', (e) => { e.preventDefault(); sendCommand(cmd); });
                // Use mouseup/touchend to stop
                button.addEventListener('mouseup', () => sendCommand('S'));
                button.addEventListener('touchend', () => sendCommand('S'));
            }

            // Add a separate click listener for the explicit stop button
            document.getElementById('stop').addEventListener('click', () => sendCommand('S'));
            // --- End Manual Control ---

            // Fetch and update the distance display continuously
            setInterval(function() {
                fetch('/distance')
                    .then(response => response.text())
                    .then(data => {
                        obstacleDist = parseFloat(data);
                        document.getElementById('dist_val').innerText = (obstacleDist >= 0) ? obstacleDist.toFixed(1) : "N/A";
                    })
                    .catch(error => console.error('Error fetching distance:', error));
            }, 200);

            window.addEventListener('resize', resizeCanvas);
            resizeCanvas();
            animate();
        </script>
    </body>
    </html>
    """

# --- WiFi Access Point Setup ---
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=WIFI_SSID, password=WIFI_PASSWORD)

while not ap.active():
    time.sleep(0.5)

print("--- Subu Radar Server ---")
print(f"WiFi Network: {WIFI_SSID}")
print(f"IP Address: http://{ap.ifconfig()[0]}")
print("-----------------------------")

# --- Web Server Setup ---
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(1)

print("Web server is listening...")

# --- Main Server Loop ---
while True:
    try:
        # Check for incoming UART data first (non-blocking)
        if uart.any():
            line = uart.readline()
            if line:
                latest_distance = line.decode('utf-8').strip()

        # Wait for a web connection, with a short timeout
        r, _, _ = select.select([s], [], [], 0.05)

        if r:
            conn, addr = s.accept()
            request = conn.recv(1024).decode('utf-8')

            if 'GET /distance' in request:
                conn.send('HTTP/1.1 200 OK\nContent-Type: text/plain\n\n')
                conn.send(latest_distance)
            elif 'GET /?cmd=' in request:
                # Handle robot control commands
                cmd_start = request.find('/?cmd=') + 6
                cmd_end = request.find(' ', cmd_start)
                command = request[cmd_start:cmd_end]
                uart.write(command + '\n') # Send command to receiver
                print(f"Sent command: {command}")
                conn.send('HTTP/1.1 200 OK\n\n') # Acknowledge command
            else:
                conn.send('HTTP/1.1 200 OK\nContent-Type: text/html\nConnection: close\n\n')
                conn.sendall(get_web_page_html())
            
            conn.close()
    except Exception as e:
        print(f'An error occurred: {e}')
        time.sleep(1)