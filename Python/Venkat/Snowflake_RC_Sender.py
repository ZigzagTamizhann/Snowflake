# c:\venkat\thonny\wifi_controller_esp32.py
import network
import socket
import time
from machine import UART
import Cayo

# --- Configuration ---
WIFI_SSID = "Snowflake-Car-Control"
WIFI_PASSWORD = "password123"

# --- UART (Serial) Communication Setup ---
# Use UART 1. Connect ESP32's TX (17) to Snowflake's RX and ESP32's RX (16) to Snowflake's TX.
# Ensure the GND pins of both boards are connected.
uart = UART(1, baudrate=115200, tx=Cayo.IO9, rx=Cayo.IO10) 
print("UART configured on tx=Cayo.IO9, rx=Cayo.IO10.")

# --- HTML & JavaScript for Web Interface ---
def get_web_page_html():
    """Returns the HTML for the robot control web page."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Snowflake Wi-Fi Control</title>
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
        </style>
    </head>
    <body>
        <h1>Wi-Fi Robot Control</h1>
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
        <script>
            // Send a command to the ESP32 server
            function sendCommand(cmd) {
                fetch('/?cmd=' + cmd).catch(err => console.error(err));
            }

            // Add event listeners for all buttons
            const controls = {
                'forward': 'F', 'backward': 'B', 'left': 'L', 'right': 'R'
            };

            for (const [id, cmd] of Object.entries(controls)) {
                const button = document.getElementById(id);
                button.addEventListener('mousedown', () => sendCommand(cmd));
                button.addEventListener('mouseup', () => sendCommand('S'));
                button.addEventListener('touchstart', (e) => { e.preventDefault(); sendCommand(cmd); });
                button.addEventListener('touchend', () => sendCommand('S'));
            }
            
            // Special case for the stop button
            document.getElementById('stop').addEventListener('click', () => sendCommand('S'));

            // Event listener for the speed slider
            document.getElementById('speedSlider').addEventListener('change', (e) => {
                sendCommand('V' + e.target.value);
            });
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

# --- Main Server Loop ---
while True:
    try:
        conn, addr = s.accept()
        request = conn.recv(1024)
        
        # Find the command in the HTTP GET request
        request_str = request.decode('utf-8')
        cmd_start = request_str.find('/?cmd=')
        if cmd_start != -1:
            cmd_end = request_str.find(' ', cmd_start)
            command = request_str[cmd_start + 6:cmd_end]
            print(f'Received command: {command}')
            # Send the command over UART to the Snowflake board
            uart.write(command + '\n')

        # Serve the web page
        conn.send('HTTP/1.1 200 OK\nContent-Type: text/html\nConnection: close\n\n')
        conn.sendall(get_web_page_html())
        conn.close()
        
    except OSError as e:
        if 'conn' in locals():
            conn.close()
        print(f'Connection error: {e}')
