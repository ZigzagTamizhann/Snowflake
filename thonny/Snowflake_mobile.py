import network
import socket
import time

# --- Wi-Fi Access Point (AP) அமைத்தல் ---
# ESP32 ஒரு Wi-Fi நெட்வொர்க்கை உருவாக்கும். உங்கள் மொபைலை இதில் இணைக்க வேண்டும்.
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid='ESP32-Tilt-Control', password='password') # நெட்வொர்க் பெயர் மற்றும் பாஸ்வேர்ட்

while not ap.active():
    pass

print('ESP32 Access Point ενεργό.')
print('IP முகவரி:', ap.ifconfig()[0])


# --- HTML மற்றும் JavaScript பக்கம் ---
# இந்த HTML கோட் மொபைல் பிரவுசரில் காட்டப்படும்.
# இது மொபைலின் சாய்வு மதிப்புகளைப் படித்து ESP32-க்கு அனுப்பும்.
html_page = """
<!DOCTYPE html>
<html>
<head>
    <title>ESP32 Tilt Sensor</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
        h1 { color: #333; }
        #data { font-size: 1.5em; color: #d9534f; }
        #status { color: #888; font-style: italic; margin-top: 20px; }
    </style>
</head>
<body>
    <h1>Mobile Tilt Values</h1>
    <p>உங்கள் மொபைலை சாய்த்து மதிப்புகளைப் பார்க்கவும்.</p>
    <div id="data">
        Alpha: 0<br>
        Beta: 0<br>
        Gamma: 0<br>
    </div>
    <div id="status">Waiting for sensor data...</div>

    <script>
        const statusDiv = document.getElementById('status');

        // இந்த பிரவுசர் 'DeviceOrientationEvent'-ஐ ஆதரிக்கிறதா என்று சோதிக்கவும்
        if (window.DeviceOrientationEvent) {
            statusDiv.innerHTML = "Sensor supported. Please move your device.";
            // மொபைலின் orientation sensor-ஐக் கவனிக்க ஒரு event listener-ஐ சேர்க்கவும்
            window.addEventListener('deviceorientation', function(event) {
                // alpha, beta, gamma மதிப்புகளைப் பெறுதல்
                let alpha = Math.round(event.alpha); // 0 to 360
                let beta = Math.round(event.beta);   // -180 to 180
                let gamma = Math.round(event.gamma); // -90 to 90

                // மதிப்புகளை வெப் பக்கத்தில் காட்டுதல்
                document.getElementById('data').innerHTML = `Alpha: ${alpha}<br>Beta: ${beta}<br>Gamma: ${gamma}`;
                statusDiv.innerHTML = "Sending data to ESP32...";

                // மதிப்புகளை ESP32-க்கு அனுப்புதல் (HTTP GET request)
                fetch(`/data?alpha=${alpha}&beta=${beta}&gamma=${gamma}`)
                    .catch(error => {
                        statusDiv.innerHTML = "Error sending data: " + error;
                    });
            });
        } else {
            statusDiv.innerHTML = "Sorry, your browser does not support device orientation events.";
        }
    </script>
</body>
</html>
"""

# --- வெப் சர்வர் அமைத்தல் ---
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # போர்ட்டை மீண்டும் பயன்படுத்த அனுமதிக்கவும்
s.bind(addr)
s.listen(1)

print('வெப் சர்வர் http://' + ap.ifconfig()[0] + ' இல் இயங்குகிறது...')

while True:
    try:
        conn, addr = s.accept()
        print('கிளையண்ட் இணைக்கப்பட்டது:', addr)
        request = conn.recv(1024)
        print("\n--- கோரிக்கை (Request) பெறப்பட்டது ---")
        print(request) # முழு கோரிக்கையையும் பிரிண்ட் செய்யவும்
        print("-------------------------------------\n")
        request_str = request.decode('utf-8')
        
        # URL-ஐப் பிரித்தெடுத்து மதிப்புகளைப் பெறுதல்
        if 'GET /data' in request_str:
            try:
                # Query string-ஐ பிரித்தெடுத்தல் (e.g., "alpha=10&beta=20...")
                query_string = request_str.split(' ')[1].split('?')[1]
                params = query_string.split('&')
                alpha = params[0].split('=')[1]
                beta = params[1].split('=')[1]
                gamma = params[2].split('=')[1]
                print(f"பெறப்பட்ட மதிப்புகள் -> Alpha: {alpha}, Beta: {beta}, Gamma: {gamma}")
            except (IndexError, ValueError):
                print("தவறான டேட்டா பெறப்பட்டது.")
            
            # பிரவுசருக்கு ஒரு சிறிய பதிலை அனுப்புதல்
            conn.send('HTTP/1.1 200 OK\n')
            conn.send('Content-Type: text/plain\n')
            conn.send('Connection: close\n\n')
            conn.send('OK')

        else: # முகப்புப் பக்கத்திற்கான கோரிக்கை வந்தால்
            # HTML பக்கத்தை அனுப்புதல்
            conn.send('HTTP/1.1 200 OK\n')
            conn.send('Content-Type: text/html\n')
            conn.send('Connection: close\n\n')
            conn.sendall(html_page)
        
        conn.close()

    except OSError as e:
        conn.close()
        print('இணைப்புப் பிழை:', e)
