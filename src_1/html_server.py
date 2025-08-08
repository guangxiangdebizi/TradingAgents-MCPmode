#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的HTML页面服务器，为辩论报告页面提供API
"""

import json
import os
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse
import mimetypes

class DebateReportHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.getcwd(), **kwargs)
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        # API路由
        if path == '/api/sessions':
            self.handle_sessions_api()
        elif path.startswith('/api/session/'):
            session_file = path.replace('/api/session/', '')
            self.handle_session_data_api(session_file)
        else:
            # 静态文件服务
            if path == '/':
                self.path = '/debate_dynamic.html'
            super().do_GET()
    
    def handle_sessions_api(self):
        """获取会话列表API"""
        try:
            dump_dir = Path("../src/dump")
            sessions = []
            
            if dump_dir.exists():
                json_files = list(dump_dir.glob("session_*.json"))
                json_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                
                for json_file in json_files:
                    try:
                        # 尝试从文件中读取会话信息
                        with open(json_file, 'r', encoding='utf-8') as f:
                            session_data = json.load(f)
                        
                        # 提取用户查询作为会话名称
                        user_query = session_data.get('user_query', '未知查询')
                        session_id = session_data.get('session_id', json_file.stem)
                        created_at = session_data.get('created_at', '')
                        
                        # 格式化时间
                        if created_at:
                            try:
                                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                time_str = dt.strftime('%Y-%m-%d %H:%M')
                            except:
                                time_str = session_id
                        else:
                            file_time = datetime.fromtimestamp(json_file.stat().st_mtime)
                            time_str = file_time.strftime('%Y-%m-%d %H:%M')
                        
                        sessions.append({
                            'file': json_file.name,
                            'name': f'{time_str} - {user_query}',
                            'query': user_query,
                            'session_id': session_id
                        })
                    except Exception as file_error:
                        # 如果读取文件失败，使用文件名
                        file_time = datetime.fromtimestamp(json_file.stat().st_mtime)
                        sessions.append({
                            'file': json_file.name,
                            'name': f'{file_time.strftime("%Y-%m-%d %H:%M")} - {json_file.stem}',
                            'query': '解析失败',
                            'session_id': json_file.stem
                        })
            
            self.send_json_response(sessions)
        except Exception as e:
            self.send_error_response(f"获取会话列表失败: {str(e)}")
    
    def handle_session_data_api(self, session_file):
        """获取会话数据API"""
        try:
            dump_dir = Path("../src/dump")
            json_file_path = dump_dir / session_file
            
            if not json_file_path.exists():
                self.send_error_response("会话文件不存在")
                return
            
            with open(json_file_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            self.send_json_response(session_data)
        except Exception as e:
            self.send_error_response(f"加载会话数据失败: {str(e)}")
    
    def send_json_response(self, data):
        """发送JSON响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(json_data.encode('utf-8'))
    
    def send_error_response(self, message):
        """发送错误响应"""
        self.send_response(500)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        error_data = {'error': message}
        json_data = json.dumps(error_data, ensure_ascii=False)
        self.wfile.write(json_data.encode('utf-8'))
    
    def guess_type(self, path):
        """猜测文件类型"""
        mimetype, _ = mimetypes.guess_type(path)
        if mimetype is None:
            if path.endswith('.css'):
                return 'text/css'
            elif path.endswith('.js'):
                return 'application/javascript'
            elif path.endswith('.html'):
                return 'text/html'
        return mimetype or 'application/octet-stream'

def run_server(port=8505):
    """运行服务器"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, DebateReportHandler)
    
    print(f"🚀 HTML辩论报告服务器启动")
    print(f"📍 访问地址: http://localhost:{port}")
    print(f"📁 工作目录: {os.getcwd()}")
    print("按 Ctrl+C 停止服务器")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹️  服务器已停止")
        httpd.shutdown()

if __name__ == "__main__":
    run_server()
