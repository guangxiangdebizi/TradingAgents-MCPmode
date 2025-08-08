#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask服务器 - 为纯HTML辩论报告页面提供API
完全按照用户原始HTML和CSS设计
"""

from flask import Flask, jsonify, send_from_directory, render_template_string
import json
import os
from pathlib import Path
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    """主页 - 返回辩论报告HTML"""
    try:
        with open('debate_report.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "HTML文件未找到", 404

@app.route('/styles.css')
def styles():
    """CSS样式文件"""
    return send_from_directory('.', 'styles.css')

@app.route('/api/sessions')
def get_sessions():
    """获取会话列表API"""
    try:
        dump_dir = Path("src/dump")
        sessions = []
        
        if dump_dir.exists():
            json_files = list(dump_dir.glob("session_*.json"))
            json_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            for json_file in json_files:
                file_time = datetime.fromtimestamp(json_file.stat().st_mtime)
                sessions.append({
                    'file': json_file.name,
                    'name': json_file.name.replace('.json', ''),
                    'time': file_time.strftime('%m-%d %H:%M')
                })
        
        return jsonify(sessions)
    except Exception as e:
        return jsonify({'error': f"获取会话列表失败: {str(e)}"}), 500

@app.route('/api/session/<session_file>')
def get_session_data(session_file):
    """获取会话数据API"""
    try:
        dump_dir = Path("src/dump")
        json_file_path = dump_dir / session_file
        
        if not json_file_path.exists():
            return jsonify({'error': '会话文件不存在'}), 404
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        return jsonify(session_data)
    except Exception as e:
        return jsonify({'error': f"加载会话数据失败: {str(e)}"}), 500

if __name__ == '__main__':
    print("🚀 Flask HTML辩论报告服务器启动")
    print("📍 访问地址: http://localhost:8505")
    print("📁 工作目录:", os.getcwd())
    print("按 Ctrl+C 停止服务器")
    
    app.run(host='0.0.0.0', port=8505, debug=True)
