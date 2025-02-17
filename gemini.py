import urequests
import ujson
import time
import network
import socket
import sys
import ustruct


ssid = "WIFI名稱"
password = "WIFI密碼"
API_KEY = "API key"  # 在此處填入你的 API 金鑰
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

while not wlan.isconnected():
    time.sleep(1)
print("連接成功，IP地址:", wlan.ifconfig()[0])

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"



def handle_request(request):
    first_line = request.decode('utf-8').split('\r\n')[0]
    method, path, *_ = first_line.split(' ')

    if path.startswith('/query?message='):
        message = path.split('/query?message=')[1]
        print("接收到的查詢訊息:", message) 
        
        # 發送到 Gemini API
        payload = {
            "contents": [{
                "parts": [{"text": message}]
            }]
        }
        headers = {"Content-Type": "application/json"}
        try:
            response = urequests.post(f"{API_URL}?key={API_KEY}", json=payload, headers=headers)
            
            # 檢查 API 回應
            if response.status_code == 200:
                result = response.json()
                print("API 回應內容：", result)  # 打印完整回應內容
                
                # 提取生成的文本
                try:
                    response_text = result['candidates'][0]['content']['parts'][0]['text']
                except KeyError:
                    response_text = '未找到生成的文本'
            else:
                response_text = f"錯誤：API 請求失敗，狀態碼：{response.status_code}, 錯誤訊息：{response.text}"

        except Exception as e:
            response_text = f"錯誤：{str(e)}"
        html = f"""
        <html>
        <body>
            <h1>API 回應：</h1>
            <p>{response_text}</p>
        </body>
        </html>
        """
        html_utf8 = html.encode('utf-8')
        headers = f"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=UTF-8\r\nContent-Length: {len(html_utf8)}\r\nConnection: keep-alive\r\n\r\n"
        response = headers + html_utf8.decode('utf-8')
    
    else:
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
                    let url = "/query?message=" + encodeURIComponent(message);
                    
                    fetch(url)
                    .then(response => response.text())
                    .then(text => {{
                        document.getElementById("apiResponse").innerHTML = text;
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
            <h2>發送訊息到 API</h2>
            <input type="text" id="messageInput" placeholder="輸入訊息..." />
            <button onclick="sendMessage()">發送</button>
            <p id="apiResponse">請輸入訊息後發送</p>
        </body>
        </html>
        """
        html_utf8 = html.encode('utf-8')
        headers = f"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=UTF-8\r\nContent-Length: {len(html_utf8)}\r\nConnection: keep-alive\r\n\r\n"
        response = headers + html_utf8.decode('utf-8')
    
    return response

# 開啟 socket 來處理 HTTP 請求
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