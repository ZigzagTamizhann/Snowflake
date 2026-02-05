import network
import socket
import time
from machine import UART
import json

import Cayo

# --- Configuration ---
WIFI_SSID = "Subu-Path-Control"
WIFI_PASSWORD = "password123"

# --- UART (Serial) Communication Setup ---
# ESP32's TX (IO9) to Subu's RX and ESP32's RX (IO10) to Subu's TX.
uart = UART(1, baudrate=115200, tx=Cayo.IO9, rx=Cayo.IO10) 
print("UART configured on tx=Cayo.IO9, rx=Cayo.IO10.")

# --- HTML, CSS & JavaScript for Web Interface ---
def get_web_page_html():
    """Returns the HTML for the path control web page."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Subu Path Control</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; text-align: center; background-color: #282c34; color: white; }
            h1 { color: #61dafb; }
            .grid-container { display: inline-grid; margin: 20px auto; border: 1px solid #61dafb; user-select: none; }
            .grid-cell { width: 40px; height: 40px; border: 1px solid #555; background-color: #444; cursor: pointer; }
            .grid-cell.selected { background-color: #61dafb; }
            .grid-cell.start { background-color: #6eff7e; }
            .grid-cell.end { background-color: #ff6e6e; }
            .controls, .info { margin: 20px; }
            button { background-color: #61dafb; color: #282c34; padding: 10px 20px; font-size: 16px; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background-color: #88eaff; }
            input { padding: 5px; }
        </style>
    </head>
    <body>
        <h1>Subu Path Control</h1>
        <div class="controls">
            <label>Rows: <input type="number" id="rows" value="5" min="2"></label>
            <label>Cols: <input type="number" id="cols" value="5" min="2"></label>
            <button onclick="createGrid()">Create Grid</button>
        </div>
        <div id="grid" class="grid-container"></div>
        <div class="controls">
            <button onclick="runPath()">Run Path</button>
            <button onclick="resetPath()">Reset</button>
        </div>
        <div class="info">
            <p>Path: <span id="path-display"></span></p>
        </div>

        <script>
            let path = [];
            let gridCreated = false;

            function createGrid() {
                const rows = document.getElementById('rows').value;
                const cols = document.getElementById('cols').value;
                const grid = document.getElementById('grid');
                grid.innerHTML = '';
                grid.style.gridTemplateColumns = `repeat(${cols}, 40px)`;
                path = [];
                updatePathDisplay();

                for (let r = 0; r < rows; r++) {
                    for (let c = 0; c < cols; c++) {
                        const cell = document.createElement('div');
                        cell.classList.add('grid-cell');
                        cell.dataset.row = r;
                        cell.dataset.col = c;
                        cell.onclick = () => selectCell(r, c);
                        grid.appendChild(cell);
                    }
                }
                gridCreated = true;
            }

            function selectCell(r, c) {
                if (!gridCreated) return;
                const cellId = `${r},${c}`;
                const pathIndex = path.findIndex(p => p.r === r && p.c === c);

                if (pathIndex > -1) { // If cell is already in path, remove it and subsequent cells
                    path.splice(pathIndex);
                } else {
                    // --- IF CONDITION ADDED FOR CONTINUOUS PATH ---
                    // Allow adding a point only if it's the first point or adjacent to the last point.
                    if (path.length > 0) {
                        const lastPoint = path[path.length - 1];
                        const isAdjacent = Math.abs(lastPoint.r - r) + Math.abs(lastPoint.c - c) === 1;
                        if (!isAdjacent) {
                            alert("Please select a cell next to the last point to create a continuous path.");
                            return; // Ignore click if not adjacent
                        }
                    }
                    path.push({r, c}); // Add the new point to the path
                }
                updatePathDisplay();
                updateGridSelection();
            }
            
            function updateGridSelection() {
                document.querySelectorAll('.grid-cell').forEach(cell => {
                    cell.classList.remove('selected', 'start', 'end');
                    const r = parseInt(cell.dataset.row);
                    const c = parseInt(cell.dataset.col);
                    const pathIndex = path.findIndex(p => p.r === r && p.c === c);
                    if(pathIndex > -1) {
                        if (pathIndex === 0) cell.classList.add('start');
                        else if (pathIndex === path.length - 1) cell.classList.add('end');
                        else cell.classList.add('selected');
                    }
                });
            }

            function updatePathDisplay() {
                document.getElementById('path-display').innerText = path.map(p => `(${p.r},${p.c})`).join(' -> ');
            }

            function resetPath() {
                path = [];
                updatePathDisplay();
                updateGridSelection();
            }

            function runPath() {
                if (path.length < 2) {
                    alert("Please select a path with at least a start and end point.");
                    return;
                }
                console.log("Sending path:", path);
                fetch('/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(path)
                }).catch(err => console.error(err));
            }

            // Create a default grid on load
            window.onload = createGrid;
        </script>
    </body>
    </html>
    """

# --- Path to Commands Logic ---
def calculate_commands(path):
    """Converts a list of coordinates into a sequence of robot commands (F, L, R)."""
    if not path or len(path) < 2:
        return []

    commands = []
    # Initial orientation: 0=North, 1=East, 2=South, 3=West
    orientation = 0 

    for i in range(len(path) - 1):
        current_pos = path[i]
        next_pos = path[i+1]

        dr = next_pos['r'] - current_pos['r']
        dc = next_pos['c'] - current_pos['c']

        target_orientation = -1
        if dr == -1 and dc == 0: target_orientation = 0 # North
        elif dr == 0 and dc == 1: target_orientation = 1 # East
        elif dr == 1 and dc == 0: target_orientation = 2 # South
        elif dr == 0 and dc == -1: target_orientation = 3 # West

        if target_orientation == -1: continue # Skip diagonal/invalid moves

        # Calculate turns needed
        turn = (target_orientation - orientation + 4) % 4
        if turn == 1: # Turn right
            commands.append('R')
        elif turn == 2: # Turn 180 (Right, Right)
            commands.append('R')
            commands.append('R')
        elif turn == 3: # Turn left
            commands.append('L')
        
        orientation = target_orientation
        commands.append('F') # Move forward

    return commands

# --- WiFi & Web Server Setup ---
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=WIFI_SSID, password=WIFI_PASSWORD)

while not ap.active():
    time.sleep(0.5)

print("--- Subu Path Control Server ---")
print(f"WiFi Network: {WIFI_SSID}")
print(f"IP Address: http://{ap.ifconfig()[0]}")
print("------------------------------------")

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
        request_str = request.decode('utf-8')

        if 'POST /run' in request_str:
            content_length_start = request_str.find('Content-Length: ') + 16
            content_length_end = request_str.find('\r\n', content_length_start)
            content_length = int(request_str[content_length_start:content_length_end])
            
            body_start = request_str.find('\r\n\r\n') + 4
            path_data = json.loads(request_str[body_start:body_start+content_length])
            
            print(f"Received path data: {path_data}")
            commands = calculate_commands(path_data)
            print(f"Calculated commands: {commands}")

            for cmd in commands:
                uart.write(cmd + '\n')
                print(f"Sent: {cmd}")
                time.sleep(1.2) # Wait for the robot to complete the move
            
            conn.send('HTTP/1.1 200 OK\n\n')
        else:
            # Serve the web page
            conn.send('HTTP/1.1 200 OK\nContent-Type: text/html\nConnection: close\n\n')
            conn.sendall(get_web_page_html())
        
        conn.close()
    except Exception as e:
        if 'conn' in locals(): conn.close()
        print(f'Error: {e}')