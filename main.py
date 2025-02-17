import network
import socket
import time

ssid = "WIFI名稱"
password = "WIFI密碼"
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

while not wlan.isconnected():
    time.sleep(1)
print("連接成功，IP地址:", wlan.ifconfig()[0])

def handle_request(request):
    first_line = request.decode('utf-8').split('\r\n')[0]
    method, path, _ = first_line.split(' ')
    
    if path == '/favicon.ico':
        response = "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nContent-Length: 0\r\n\r\n"
    else:
        # 取得當前時間
        current_time = time.localtime()
        formatted_time = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            current_time[0], current_time[1], current_time[2],
            current_time[3], current_time[4], current_time[5]
        )

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Pi Pico W</title>
            <script>
                function updateTime() {{
                    let now = new Date();
                    let timeString = now.getFullYear() + "-" +
                        ("0" + (now.getMonth() + 1)).slice(-2) + "-" +
                        ("0" + now.getDate()).slice(-2) + " " +
                        ("0" + now.getHours()).slice(-2) + ":" +
                        ("0" + now.getMinutes()).slice(-2) + ":" +
                        ("0" + now.getSeconds()).slice(-2);
                    document.getElementById("time").innerHTML = timeString;
                }}
                setInterval(updateTime, 1000);
                window.onload = updateTime; 
            </script>
        </head>
        <body>
            <h1>Welcome to Pi Pico W!</h1>
            <p>This website is made by MicroPython</p>
            <p>Current Time: <span id="time">{formatted_time}</span></p>
        </body>
        </html>
        """
        headers = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: {len(html)}\r\nConnection: keep-alive\r\n\r\n"
        response = headers + html
        
    return response

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1] 
try:
    s.bind(addr)
except OSError as e:
    print("綁定端口失敗，嘗試關閉現有連接...")
    s.close()
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)

s.listen(1)
print('Web 伺服器正在運行，訪問：http://', wlan.ifconfig()[0])

while True:
    try:
        cl, addr = s.accept()
        print('客戶端連線來自', addr)
        
        request = b''
        while True:
            chunk = cl.recv(1024)
            request += chunk
            if b'\r\n\r\n' in request or not chunk:
                break
                
        print("完整請求內容：", request)
        
        response = handle_request(request)
        cl.send(response.encode())
        
    except Exception as e:
        print("錯誤：", e)
    
    finally:
        try:
            cl.close()
        except:
            pass

try:
    s.close()
except:
    pass
