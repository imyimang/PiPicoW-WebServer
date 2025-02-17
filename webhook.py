import urequests
import ujson
import time
import network
import socket
import sys
import ustruct

ssid = "WIFI名稱"
password = "WIFI密碼"
WEBHOOK_URL = "webhook url"
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

while not wlan.isconnected():
    time.sleep(1)
print("連接成功，IP地址:", wlan.ifconfig()[0])

def url_decode(encoded_str):
    """修正 URL 解碼，並保證中文字符正確解碼"""
    decoded = ""
    i = 0
    while i < len(encoded_str):
        if encoded_str[i] == '%':
            hex_val = encoded_str[i+1:i+3]
            decoded += chr(int(hex_val, 16))
            i += 3
        else:
            decoded += encoded_str[i].replace('+', ' ')
            i += 1

    return decoded.encode('utf-8').decode('utf-8')

def handle_request(request):
    first_line = request.decode('utf-8').split('\r\n')[0]
    method, path, *_ = first_line.split(' ')

    if path == '/favicon.ico':
        response = "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Length: 0\r\n\r\n"
    
    elif path.startswith('/send?message='):
        message = path.split('/send?message=')[1]
        message = url_decode(message)
        print("解碼後的訊息:", message)
        
        # 發送到 Discord Webhook
        payload = ujson.dumps({"content": message})
        headers = {"Content-Type": "application/json"}
        try:
            response = urequests.post(WEBHOOK_URL, data=payload, headers=headers)
            print("Webhook 回應狀態碼：", response.status_code)
            if response.status_code == 204:
                status = "訊息已發送！"
            else:
                status = f"錯誤：Webhook 發送失敗，狀態碼：{response.status_code}"
            response.close()
        except Exception as e:
            status = f"錯誤：{str(e)}"
        
        status_utf8 = status.encode('utf-8')
        response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Length: {len(status_utf8)}\r\n\r\n{status}"
    
    else:
        # 取得當前時間
        current_time = time.localtime()
        formatted_time = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            current_time[0], current_time[1], current_time[2],
            current_time[3], current_time[4], current_time[5]
        )
        
        html = f"""
        <!DOCTYPE html>
        <html lang="zh-TW">
        <head>
            <meta charset="UTF-8">
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
                
                function sendMessage() {{
                    let message = document.getElementById("messageInput").value;
                    if (message.trim() === "") {{
                        alert("請輸入訊息！");
                        return;
                    }}
                    let url = "/send?message=" + encodeURIComponent(message);
                    
                    fetch(url)
                    .then(response => response.text())
                    .then(text => {{
                        alert(text);
                        document.getElementById("messageInput").value = "";
                    }})
                    .catch(error => {{
                        alert("錯誤：" + error);
                    }});
                }}
            </script>
        </head>
        <body>
            <h1>歡迎來到 Pi Pico W！</h1>
            <p>這個網站是使用 MicroPython 建立的</p>
            <p>當前時間：<span id="time">{formatted_time}</span></p>
            <h2>發送訊息到 Discord</h2>
            <input type="text" id="messageInput" placeholder="輸入訊息..." />
            <button onclick="sendMessage()">發送</button>
        </body>
        </html>
        """
        html_utf8 = html.encode('utf-8')
        headers = f"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=UTF-8\r\nContent-Length: {len(html_utf8)}\r\nConnection: keep-alive\r\n\r\n"
        response = headers + html_utf8.decode('utf-8')
    
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
