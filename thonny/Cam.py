# ==========================================================
# ESP32-CAM  —  SoftAP + WebSocket + IMU + Camera Stream
# Single Code  (MessagePack included)
# ==========================================================

import network, socket, camera, utime, _thread, machine, ujson
from machine import Pin, I2C
import usocket as us
import ubinascii as binascii
import urandom as random
import ussl

# ================== INTERNAL MSGPACK MODULE ==================
# (embedded lightweight version — no external file needed)
# =============================================================
class _Ext: pass
def _pack(obj):
    if obj is None: return b"\xc0"
    if obj is True: return b"\xc3"
    if obj is False: return b"\xc2"
    if isinstance(obj, int):
        if obj >= 0:
            if obj <= 0x7f: return bytes([obj])
            if obj <= 0xff: return b"\xcc"+bytes([obj])
            if obj <= 0xffff: return b"\xcd"+obj.to_bytes(2,"big")
            return b"\xce"+obj.to_bytes(4,"big")
        else:
            if obj >= -32: return bytes([0xe0+(obj+32)])
            if obj >= -128: return b"\xd0"+(obj & 0xff).to_bytes(1,"big")
            return b"\xd1"+(obj & 0xffff).to_bytes(2,"big")
    if isinstance(obj, str):
        b = obj.encode(); l=len(b)
        if l<32: return bytes([0xa0|l])+b
        return b"\xd9"+bytes([l])+b
    if isinstance(obj, bytes):
        l=len(obj)
        return b"\xc4"+bytes([l])+obj
    if isinstance(obj, list):
        l=len(obj); out=b""
        for x in obj: out+=_pack(x)
        if l<16: return bytes([0x90|l])+out
        return b"\xdc"+l.to_bytes(2,"big")+out
    if isinstance(obj, dict):
        l=len(obj); out=b""
        for k,v in obj.items(): out+=_pack(k)+_pack(v)
        if l<16: return bytes([0x80|l])+out
        return b"\xde"+l.to_bytes(2,"big")+out
    return b""
def _unpack(buf):
    i=0
    def R(n):
        nonlocal i; d=buf[i:i+n]; i+=n; return d
    def O():
        nonlocal i
        c=buf[i]; i+=1
        if c<=0x7f: return c
        if 0xe0<=c<=0xff: return c-0x100
        if 0xa0<=c<=0xbf: l=c&0x1f; return R(l).decode()
        if 0x80<=c<=0x8f: l=c&0xf; return {O():O() for _ in range(l)}
        if 0x90<=c<=0x9f: l=c&0xf; return [O() for _ in range(l)]
        if c==0xc0: return None
        if c==0xc3: return True
        if c==0xc2: return False
        if c==0xcc: return R(1)[0]
        if c==0xcd: return int.from_bytes(R(2),"big")
        if c==0xd0: return int.from_bytes(R(1),"big",True)
        if c==0xd1: return int.from_bytes(R(2),"big",True)
        if c==0xd9: l=R(1)[0]; return R(l).decode()
        if c==0xc4: l=R(1)[0]; return R(l)
        if c==0xdc: l=int.from_bytes(R(2),"big"); return [O() for _ in range(l)]
        if c==0xde: l=int.from_bytes(R(2),"big"); return {O():O() for _ in range(l)}
        return None
    return O()
class msgpack:
    @staticmethod
    def packb(x): return _pack(x)
    @staticmethod
    def unpackb(x): return _unpack(x)

# ================= WIFI & SERVER SETTINGS =================
WIFI_SSID = "Subu-d5b538"
WIFI_PWD = "12345678"
# This is the IP of the external WebSocket SERVER the ESP32 connects to.
WS_URL = "ws://192.168.4.1:81/"
CAM_STREAM_PORT = 81 # The port for the HTTP video stream

local_ip = ""
ws = None

# ================= IMU SETTINGS (LSM6DSO) =================
I2C_SDA = 13
I2C_SCL = 14
LSM6_ADDR = 0x6A

imu_enabled = False
imu_mode = 0      # 1 gesture, 2 raw

i2c = I2C(0, scl=Pin(I2C_SCL), sda=Pin(I2C_SDA), freq=400000)

# ================= CAMERA CONTROL =================
camera_running = False
camera_thread_started = False

# ==========================================================
# ------------------- WEBSOCKET CLIENT ---------------------
# ==========================================================

def urlparse(uri):
    uri = uri[5:]
    host, path = uri.split("/",1)
    if ":" in host:
        h,p = host.split(":")
        return h,int(p),"/"+path
    return host,80,"/"+path

class WebSocketClient:
    def __init__(self, sock): self.sock=sock
    def send(self, data):
        header=b"\x82"+bytes([len(data)])
        self.sock.send(header+data)
    def recv(self):
        hdr=self.sock.recv(2)
        if not hdr: return b""
        l=hdr[1]&127
        return self.sock.recv(l)

def ws_connect(uri):
    host,port,path = urlparse(uri)
    s = us.socket()
    s.connect(us.getaddrinfo(host,port)[0][-1])
    key = binascii.b2a_base64(bytes(random.getrandbits(8) for _ in range(16)))[:-1]
    hdr = ("GET {} HTTP/1.1\r\nHost: {}:{}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {}\r\nSec-WebSocket-Version: 13\r\n\r\n"
          ).format(path,host,port,key.decode())
    s.send(hdr.encode())
    while s.readline() not in (b"\r\n",b""): pass
    return WebSocketClient(s)

# ==========================================================
# ------------------------  IMU  ---------------------------
# ==========================================================

def imu_init():
    try:
        i2c.writeto_mem(LSM6_ADDR,0x10,b'\x60')
        i2c.writeto_mem(LSM6_ADDR,0x11,b'\x50')
        print("IMU READY")
    except:
        print("IMU ERROR")

def imu_read():
    d=i2c.readfrom_mem(LSM6_ADDR,0x28,4)
    ax=int.from_bytes(d[0:2],"little",True)*0.000061
    ay=int.from_bytes(d[2:4],"little",True)*0.000061
    return ax,ay

def detect_gesture(ax,ay):
    if ay>0.6: return "backward"
    if ay<-0.6: return "forward"
    if ax>0.6: return "left"
    if ax<-0.6: return "right"
    return "stop"

def imu_thread():
    global imu_enabled, imu_mode
    while True:
        if imu_enabled:
            ax,ay = imu_read()
            if imu_mode==1: send_gesture(detect_gesture(ax,ay))
            else: send_raw(ax,ay)
        utime.sleep_ms(500)

# ==========================================================
# -------------------  SEND MESSAGE  -----------------------
# ==========================================================

def send_msgpack(o):
    try: ws.send(msgpack.packb(o))
    except: pass

def send_ip():
    send_msgpack({"msg":"ipaddr","ip":local_ip})

def send_gesture(g):
    send_msgpack({"mode":"Board","program":{"loop":{"0":{"MExBo":{"gesture":g}}}}})

def send_raw(ax,ay):
    send_msgpack({"mode":"IMU_RAW","data":{"ax":ax,"ay":ay}})

# ==========================================================
# --------------------- CAMERA STREAM ----------------------
# ==========================================================

def camera_server():
    global camera_running
    camera.init(0)
    camera.framesize(camera.FRAME_QVGA)
    s=socket.socket()
    s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    # MODIFIED: Use the defined CAM_STREAM_PORT (81)
    s.bind(("0.0.0.0",CAM_STREAM_PORT)); s.listen(1) 
    while camera_running:
        c,a=s.accept()
        req=c.recv(1024)
        if b"/stream" in req:
            c.send(b"HTTP/1.1 200 OK\r\nContent-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n")
            while camera_running:
                f=camera.capture()
                if not f or isinstance(f,int): continue
                try:
                    c.send(b"--frame\r\nContent-Type: image/jpeg\r\n\r\n")
                    c.send(f); c.send(b"\r\n")
                except: break
        else:
            c.send(b"""HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
                <html><body style='text-align:center;background:black;color:white'>
                <h2>ESP32-CAM MicroPython</h2><img src='/stream'></body></html>""")
        c.close()

def cam_start():
    global camera_running,camera_thread_started
    camera_running=True
    if not camera_thread_started:
        camera_thread_started=True
        _thread.start_new_thread(camera_server,())

def cam_stop():
    global camera_running
    camera_running=False

# ==========================================================
# ------------------ RECEIVE WEB SOCKET --------------------
# ==========================================================

def ws_loop():
    global imu_enabled, imu_mode
    while True:
        try: data = ws.recv()
        except: reconnect_ws(); continue
        if not data: continue
        msg = msgpack.unpackb(data)
        tgt = msg.get("target")
        if tgt=="imu":
            if msg.get("state")=="start":
                imu_mode=int(msg.get("mode",1)); imu_enabled=True
            elif msg.get("state")=="stop":
                imu_enabled=False
        if tgt=="camera":
            if msg.get("state")=="start": cam_start()
            elif msg.get("state")=="stop": cam_stop()

def reconnect_ws():
    global ws
    while True:
        try:
            ws = ws_connect(WS_URL)
            send_ip()
            print("WebSocket Connected")
            break
        except:
            print("WS Retry...")
            utime.sleep(3)

# ==========================================================
# ----------------------- MAIN -----------------------------
# ==========================================================

def wifi_connect():
    global local_ip
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    sta.connect(WIFI_SSID, WIFI_PWD)
    print("Connecting to WiFi...")
    while not sta.isconnected():
        utime.sleep(1)
        print("...")
    local_ip = sta.ifconfig()[0]
    print("WiFi Connected: {}".format(local_ip))
    # ADDED: Clear output for the camera stream URL
    print("==================================================")
    print("📢 Camera Stream URL: http://{}:{}/stream".format(local_ip, CAM_STREAM_PORT))
    print("==================================================")


def main():
    wifi_connect()
    imu_init()
    _thread.start_new_thread(imu_thread,())
    reconnect_ws()
    ws_loop()

main()

