import http.server
import socketserver
import webbrowser
import os

PORT = 8000

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)

def start_server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"服务器已启动，访问 http://localhost:{PORT}/record_audio.html")
        webbrowser.open(f'http://localhost:{PORT}/record_audio.html')
        httpd.serve_forever()

if __name__ == "__main__":
    # 检查HTML文件是否存在
    if not os.path.exists('record_audio.html'):
        print("错误：record_audio.html 文件不存在")
        print("请确保 audio_server.py 和 record_audio.html 在同一目录下")
        exit(1)
    
    print("启动网页录音应用...")
    start_server()