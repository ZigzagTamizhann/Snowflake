# c:\venkat\thonny\wifi_controller_esp32.py
import network
import socket
import select
import time
from machine import UART
import Cayo

latest_distance = "-1.0" # Global variable to store the latest distance

# --- Configuration ---
WIFI_SSID = "Snowflake-Car-Control"
WIFI_PASSWORD = "password123"

# --- UART (Serial) Communication Setup ---
# Use UART 1. Connect ESP32's TX (17) to Snowflake's RX and ESP32's RX (16) to Snowflake's TX.
# Ensure the GND pins of both boards are connected.
uart = UART(1, baudrate=115200, tx=Cayo.IO9, rx=Cayo.IO10, timeout=10) 
print("UART configured on tx=Cayo.IO9, rx=Cayo.IO10.")

# --- HTML & JavaScript for Web Interface ---
def get_web_page_html():
    """Returns the HTML for the robot control web page."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Snowflake Wi-Fi Control</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            :root { --bg: #282c34; --primary: #61dafb; --text: white; --danger: #ff6e6e; }
            body { font-family: Arial, sans-serif; text-align: center; background-color: var(--bg); color: var(--text); margin: 0; padding: 15px; }
            h1 { color: var(--primary); }
            .grid { display: grid; grid-template-columns: 1fr 1fr 1fr; grid-gap: 20px; max-width: 400px; margin: 20px auto; user-select: none; }
            .btn { grid-column: 2; background-color: var(--primary); color: var(--bg); padding: 25px 0; font-size: 24px; border: none; border-radius: 10px; cursor: pointer; }
            #left { grid-column: 1; grid-row: 2; }
            #right { grid-column: 3; grid-row: 2; }
            #stop { grid-column: 2; grid-row: 2; background-color: var(--danger); }
            #backward { grid-column: 2; grid-row: 3; }
            .slider-box { margin-top: 30px; }
            input[type=range] { width: 80%; max-width: 350px; }
            .tab { overflow: hidden; border-bottom: 1px solid var(--primary); }
            .tab button { background-color: inherit; float: left; border: none; outline: none; cursor: pointer; padding: 14px 16px; transition: 0.3s; font-size: 17px; color: var(--text); }
            .tab button:hover { background-color: #444; }
            .tab button.active { background-color: var(--primary); color: var(--bg); }
            .tabcontent { display: none; padding: 20px 12px; border-top: none; }
            .auto-controls { display: flex; flex-direction: column; align-items: center; gap: 15px; }
            .auto-controls input { font-size: 18px; padding: 8px; width: 100px; text-align: center; }
            .auto-controls button { font-size: 16px; padding: 12px 20px; }
        </style>
    </head>
    <body>
        <h1>Wi-Fi Robot Control</h1>
        <div class="info-box" style="margin-bottom: 20px;">
            <h3>Sensor Reading</h3>
            <p>Distance: <span id="distance">--</span> cm</p>
        </div>

        <div class="tab">
            <button class="tablinks active" onclick="openMode(event, 'Manual')">Manual</button>
            <button class="tablinks" onclick="openMode(event, 'Auto')">Auto</button>
        </div>

        <div id="Manual" class="tabcontent" style="display: block;">
            <h2>Manual Control</h2>
            <div class="grid">
                <button id="forward" class="btn">▲</button>
                <button id="left" class="btn">◄</button>
                <button id="stop" class="btn">STOP</button>
                <button id="right" class="btn">►</button>
                <button id="backward" class="btn">▼</button>
            </div>
            <div class="slider-box">
                <h3>Speed Control</h3>
                <input type="range" min="20" max="100" value="50" id="speedSlider">
            </div>
        </div>

        <div id="Auto" class="tabcontent">
            <h2>Automatic Movement</h2>
            <div class="auto-controls">
                <label for="targetDist">Target Distance (cm):</label>
                <input type="number" id="targetDist" value="20" min="5">
                <button onclick="autoMove()">Start Auto-Move</button>
            </div>
        </div>

        <script>
            function openMode(evt, modeName) {
                var i, tabcontent, tablinks;
                tabcontent = document.getElementsByClassName("tabcontent");
                for (i = 0; i < tabcontent.length; i++) {
                    tabcontent[i].style.display = "none";
                }
                tablinks = document.getElementsByClassName("tablinks");
                for (i = 0; i < tablinks.length; i++) {
                    tablinks[i].className = tablinks[i].className.replace(" active", "");
                }
                document.getElementById(modeName).style.display = "block";
                evt.currentTarget.className += " active";
            }

            // Send a command to the ESP32 server
            function sendCommand(cmd) {
                fetch('/?cmd=' + cmd).catch(err => console.error(err));
            }

            function autoMove() {
                const dist = document.getElementById('targetDist').value;
                if (dist) {
                    sendCommand('A' + dist); // Send command like 'A20'
                }
            }

            // --- Event Listeners for Manual Control ---
            const controls = {
                'forward': 'F', 'backward': 'B', 'left': 'L', 'right': 'R'
            };

            for (const [id, cmd] of Object.entries(controls)) {
                const button = document.getElementById(id);
                // For PC mouse clicks
                button.addEventListener('mousedown', () => sendCommand(cmd));
                button.addEventListener('mouseup', () => sendCommand('S'));
                // For mobile touch screens
                button.addEventListener('touchstart', (e) => { e.preventDefault(); sendCommand(cmd); });
                button.addEventListener('touchend', () => sendCommand('S'));
            }
            
            // Special case for the stop button
            document.getElementById('stop').addEventListener('click', () => sendCommand('S'));

            // Event listener for the speed slider
            document.getElementById('speedSlider').addEventListener('change', (e) => {
                sendCommand('V' + e.target.value);
            });

            // Fetch and update the distance display continuously
            setInterval(function() {
                fetch('/distance')
                    .then(response => response.text())
                    .then(data => {
                        document.getElementById('distance').innerText = data;
                    })
                    .catch(error => console.error('Error fetching distance:', error));
            }, 1000);
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

print("--- Snowflake Control Server ---")
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

# Create a list of readable streams
readable_streams = [s]

# --- Main Server Loop ---
while True:
    try:
        # Check for incoming UART data first (non-blocking)
        if uart.any():
            line = uart.readline()
            if line:
                latest_distance = line.decode('utf-8').strip()
                print(f"UART updated distance: {latest_distance}")

        # Wait for a connection on the socket, with a short timeout
        readable, _, _ = select.select(readable_streams, [], [], 0.1)

        if s in readable:
            conn, addr = s.accept()
            request = conn.recv(1024)
            request_str = request.decode('utf-8')

            # Check for different request paths
            if 'GET /distance' in request_str:
                # Handle the request for sensor data
                conn.send('HTTP/1.1 200 OK\nContent-Type: text/plain\n\n')
                conn.send(latest_distance)
            elif 'GET /?cmd=' in request_str:
                # Handle robot control commands
                cmd_start = request_str.find('/?cmd=') + 6
                cmd_end = request_str.find(' ', cmd_start)
                command = request_str[cmd_start:cmd_end]
                print(f'Received command: {command}')
                uart.write(command + '\n')
                # Respond to the command request
                conn.send('HTTP/1.1 200 OK\n\n')
            else:
                # Serve the main HTML page
                conn.send('HTTP/1.1 200 OK\nContent-Type: text/html\nConnection: close\n\n')
                conn.sendall(get_web_page_html())
            
            conn.close()
    except Exception as e:
        print(f'An error occurred: {e}')
        time.sleep(1)
