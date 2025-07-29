#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON分析报告转HTML转换器
将progress_logs中的JSON格式分析报告转换为精美的交互式HTML网页
"""

import json
import os
from datetime import datetime
from pathlib import Path
import argparse
import re

class AnalysisReportConverter:
    """分析报告转换器"""
    
    def __init__(self):
        self.html_template = self._get_html_template()
    
    def _get_html_template(self):
        """获取现代化交互式HTML模板"""
        template = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI智能投资分析报告 - {{query}}</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/aos@2.3.4/dist/aos.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/aos@2.3.4/dist/aos.css" rel="stylesheet">
    <style>
        :root {{
            --primary-color: #667eea;
            --secondary-color: #764ba2;
            --accent-color: #f093fb;
            --success-color: #4ade80;
            --warning-color: #fbbf24;
            --danger-color: #f87171;
            --dark-color: #1f2937;
            --light-color: #f8fafc;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --border-color: #e2e8f0;
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
            --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.6;
            color: var(--text-primary);
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            min-height: 100vh;
            overflow-x: hidden;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        /* 顶部导航栏 */
        .navbar {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border-color);
            z-index: 1000;
            padding: 1rem 0;
            transition: all 0.3s ease;
        }}
        
        .navbar.scrolled {{
            background: rgba(255, 255, 255, 0.98);
            box-shadow: var(--shadow-md);
        }}
        
        .nav-content {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .nav-brand {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--primary-color);
            text-decoration: none;
        }}
        
        .nav-menu {{
            display: flex;
            gap: 2rem;
            list-style: none;
        }}
        
        .nav-link {{
            color: var(--text-secondary);
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s ease;
            cursor: pointer;
        }}
        
        .nav-link:hover, .nav-link.active {{
            color: var(--primary-color);
        }}
        
        /* 主要内容区域 */
        .main-content {{
            margin-top: 100px;
        }}
        
        /* 报告头部 */
        .report-header {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 24px;
            padding: 3rem;
            margin-bottom: 2rem;
            box-shadow: var(--shadow-xl);
            backdrop-filter: blur(20px);
            position: relative;
            overflow: hidden;
        }}
        
        .report-header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--primary-color), var(--accent-color), var(--secondary-color));
        }}
        
        .report-title {{
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 1rem;
            text-align: center;
        }}
        
        .report-meta {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-top: 2rem;
        }}
        
        .meta-item {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 1rem;
            background: var(--light-color);
            border-radius: 12px;
            border: 1px solid var(--border-color);
        }}
        
        .meta-icon {{
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            color: white;
        }}
        
        .meta-content h4 {{
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin-bottom: 0.25rem;
        }}
        
        .meta-content p {{
            font-weight: 600;
            color: var(--text-primary);
        }}
        
        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.875rem;
        }}
        
        .status-completed {{
            background: rgba(74, 222, 128, 0.1);
            color: var(--success-color);
            border: 1px solid rgba(74, 222, 128, 0.2);
        }}
        
        .status-running {{
            background: rgba(251, 191, 36, 0.1);
            color: var(--warning-color);
            border: 1px solid rgba(251, 191, 36, 0.2);
        }}
        
        .status-failed {{
            background: rgba(248, 113, 113, 0.1);
            color: var(--danger-color);
            border: 1px solid rgba(248, 113, 113, 0.2);
        }}
        
        /* 智能体卡片网格 */
        .agents-section {{
            margin-bottom: 3rem;
        }}
        
        .section-title {{
            font-size: 2rem;
            font-weight: 700;
            color: white;
            margin-bottom: 1.5rem;
            text-align: center;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        
        .agents-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 1.5rem;
        }}
        
        .agent-card {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 0;
            box-shadow: var(--shadow-lg);
            backdrop-filter: blur(20px);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            overflow: hidden;
            position: relative;
        }}
        
        .agent-card:hover {{
            transform: translateY(-8px) scale(1.02);
            box-shadow: var(--shadow-xl);
        }}
        
        .agent-header {{
            padding: 1.5rem;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            position: relative;
        }}
        
        .agent-header::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        }}
        
        .agent-info {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        
        .agent-avatar {{
            width: 60px;
            height: 60px;
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            backdrop-filter: blur(10px);
        }}
        
        .agent-details h3 {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.25rem;
        }}
        
        .agent-timing {{
            font-size: 0.875rem;
            opacity: 0.9;
        }}
        
        .agent-content {{
            padding: 1.5rem;
            max-height: 400px;
            overflow-y: auto;
        }}
        
        .agent-content::-webkit-scrollbar {{
            width: 6px;
        }}
        
        .agent-content::-webkit-scrollbar-track {{
            background: var(--light-color);
            border-radius: 3px;
        }}
        
        .agent-content::-webkit-scrollbar-thumb {{
            background: var(--border-color);
            border-radius: 3px;
        }}
        
        .agent-content::-webkit-scrollbar-thumb:hover {{
            background: var(--text-secondary);
        }}
        
        .content-section {{
            margin-bottom: 1.5rem;
        }}
        
        .content-section:last-child {{
            margin-bottom: 0;
        }}
        
        .content-section h4 {{
            font-size: 1rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .content-section h4::before {{
            content: '';
            width: 4px;
            height: 16px;
            background: var(--primary-color);
            border-radius: 2px;
        }}
        
        .content-section p {{
            color: var(--text-secondary);
            margin-bottom: 0.75rem;
            line-height: 1.7;
        }}
        
        .content-section ul {{
            list-style: none;
            margin-left: 0;
        }}
        
        .content-section li {{
            position: relative;
            padding-left: 1.5rem;
            margin-bottom: 0.5rem;
            color: var(--text-secondary);
            line-height: 1.6;
        }}
        
        .content-section li::before {{
            content: '•';
            position: absolute;
            left: 0;
            color: var(--primary-color);
            font-weight: bold;
        }}
        
        /* 总结部分 */
        .summary-section {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 24px;
            padding: 3rem;
            margin-top: 3rem;
            box-shadow: var(--shadow-xl);
            backdrop-filter: blur(20px);
        }}
        
        .summary-title {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 2rem;
            text-align: center;
            position: relative;
        }}
        
        .summary-title::after {{
            content: '';
            position: absolute;
            bottom: -10px;
            left: 50%;
            transform: translateX(-50%);
            width: 60px;
            height: 3px;
            background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
            border-radius: 2px;
        }}
        
        /* 页脚 */
        .footer {{
            text-align: center;
            margin-top: 4rem;
            padding: 2rem;
            color: rgba(255, 255, 255, 0.8);
            font-size: 0.875rem;
        }}
        
        .footer-content {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 1rem;
            flex-wrap: wrap;
        }}
        
        .footer-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        /* 加载动画 */
        .loading-spinner {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        /* 响应式设计 */
        @media (max-width: 768px) {{
            .container {{
                padding: 10px;
            }}
            
            .report-header {{
                padding: 2rem 1.5rem;
            }}
            
            .report-title {{
                font-size: 2rem;
            }}
            
            .agents-grid {{
                grid-template-columns: 1fr;
            }}
            
            .nav-menu {{
                display: none;
            }}
            
            .report-meta {{
                grid-template-columns: 1fr;
            }}
        }}
        
        /* 无结果状态 */
        .no-results {{
            text-align: center;
            padding: 3rem;
            color: var(--text-secondary);
        }}
        
        .no-results i {{
            font-size: 3rem;
            margin-bottom: 1rem;
            opacity: 0.5;
        }}
        
        /* 工具提示 */
        .tooltip {{
            position: relative;
            cursor: help;
        }}
        
        .tooltip::after {{
            content: attr(data-tooltip);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: var(--dark-color);
            color: white;
            padding: 0.5rem 0.75rem;
            border-radius: 6px;
            font-size: 0.75rem;
            white-space: nowrap;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
            z-index: 1000;
        }}
        
        .tooltip:hover::after {{
            opacity: 1;
            visibility: visible;
        }}
        
        /* 平滑滚动 */
        html {{
            scroll-behavior: smooth;
        }}
        
        /* 自定义滚动条 */
        ::-webkit-scrollbar {{
            width: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: rgba(255, 255, 255, 0.1);
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: rgba(255, 255, 255, 0.3);
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: rgba(255, 255, 255, 0.5);
        }}
    </style>
</head>
<body>
    <!-- 导航栏 -->
    <nav class="navbar" id="navbar">
        <div class="nav-content">
            <a href="#" class="nav-brand">
                <i class="fas fa-chart-line"></i> AI投资分析
            </a>
            <ul class="nav-menu">
                <li><a href="#overview" class="nav-link">概览</a></li>
                <li><a href="#agents" class="nav-link">智能体分析</a></li>
                <li><a href="#summary" class="nav-link">总结</a></li>
            </ul>
        </div>
    </nav>

    <div class="container">
        <div class="main-content">
            <!-- 报告头部 -->
            <div class="report-header" id="overview" data-aos="fade-up">
                <h1 class="report-title">
                    <i class="fas fa-robot"></i> AI智能投资分析报告
                </h1>
                <div class="report-meta">
                    <div class="meta-item">
                        <div class="meta-icon" style="background: var(--primary-color);">
                            <i class="fas fa-search"></i>
                        </div>
                        <div class="meta-content">
                            <h4>分析标的</h4>
                            <p>{{query}}</p>
                        </div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-icon" style="background: var(--secondary-color);">
                            <i class="fas fa-fingerprint"></i>
                        </div>
                        <div class="meta-content">
                            <h4>会话ID</h4>
                            <p>{{session_id}}</p>
                        </div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-icon" style="background: var(--success-color);">
                            <i class="fas fa-calendar-plus"></i>
                        </div>
                        <div class="meta-content">
                            <h4>创建时间</h4>
                            <p>{{created_at}}</p>
                        </div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-icon" style="background: var(--warning-color);">
                            <i class="fas fa-sync-alt"></i>
                        </div>
                        <div class="meta-content">
                            <h4>更新时间</h4>
                            <p>{{updated_at}}</p>
                        </div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-icon" style="background: var(--accent-color);">
                            <i class="fas fa-tasks"></i>
                        </div>
                        <div class="meta-content">
                            <h4>分析状态</h4>
                            <p><span class="status-badge status-{{status}}">{{status_text}}</span></p>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 智能体分析部分 -->
            <div class="agents-section" id="agents">
                <h2 class="section-title" data-aos="fade-up">
                    <i class="fas fa-users-cog"></i> 智能体协作分析
                </h2>
                <div class="agents-grid">
                    {{agents_content}}
                </div>
            </div>
            
            <!-- 总结部分 -->
            {{summary_section}}
        </div>
        
        <!-- 页脚 -->
        <div class="footer">
            <div class="footer-content">
                <div class="footer-item">
                    <i class="fas fa-robot"></i>
                    <span>AI智能体团队协作生成</span>
                </div>
                <div class="footer-item">
                    <i class="fas fa-clock"></i>
                    <span>生成时间: {{generation_time}}</span>
                </div>
                <div class="footer-item">
                    <i class="fas fa-code"></i>
                    <span>TradingAgents-MCPmode</span>
                </div>
            </div>
        </div>
    </div>

    <script>
        // 初始化AOS动画
         AOS.init({
             duration: 800,
             easing: 'ease-in-out',
             once: true,
             offset: 100
         });
        
        // 导航栏滚动效果
         window.addEventListener('scroll', function() {
             const navbar = document.getElementById('navbar');
             if (window.scrollY > 50) {
                 navbar.classList.add('scrolled');
             } else {
                 navbar.classList.remove('scrolled');
             }
         });
        
        // 平滑滚动导航
         document.querySelectorAll('.nav-link').forEach(link => {
             link.addEventListener('click', function(e) {
                 e.preventDefault();
                 const targetId = this.getAttribute('href').substring(1);
                 const targetElement = document.getElementById(targetId);
                 if (targetElement) {
                     const offsetTop = targetElement.offsetTop - 100;
                     window.scrollTo({
                         top: offsetTop,
                         behavior: 'smooth'
                     });
                 }
                 
                 // 更新活动状态
                 document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
                 this.classList.add('active');
             });
         });
        
        // 智能体卡片交互效果
         document.querySelectorAll('.agent-card').forEach(card => {
             card.addEventListener('mouseenter', function() {
                 this.style.transform = 'translateY(-8px) scale(1.02)';
             });
             
             card.addEventListener('mouseleave', function() {
                 this.style.transform = 'translateY(0) scale(1)';
             });
         });
        
        // 添加页面加载完成后的动画
         window.addEventListener('load', function() {
             document.body.style.opacity = '1';
         });
        
        // 响应式菜单切换（移动端）
         function toggleMobileMenu() {
             const navMenu = document.querySelector('.nav-menu');
             navMenu.classList.toggle('active');
         }
        
        // 添加键盘导航支持
         document.addEventListener('keydown', function(e) {
             if (e.key === 'Escape') {
                 // 关闭任何打开的模态框或菜单
                 document.querySelectorAll('.modal, .dropdown').forEach(el => {
                     el.classList.remove('active');
                 });
             }
         });
    </script>
</body>
</html>
        '''
        return template
    
    def _get_agent_display_name(self, agent_key):
        """获取智能体显示名称"""
        agent_names = {
            'market_analyst': '市场分析师',
            'sentiment_analyst': '情绪分析师', 
            'news_analyst': '新闻分析师',
            'fundamentals_analyst': '基本面分析师',
            'bull_researcher': '看涨研究员',
            'bear_researcher': '看跌研究员',
            'research_manager': '研究经理',
            'trader': '交易员',
            'aggressive_risk_analyst': '激进风险分析师',
            'safe_risk_analyst': '保守风险分析师',
            'neutral_risk_analyst': '中性风险分析师',
            'risk_manager': '风险管理经理'
        }
        return agent_names.get(agent_key, agent_key.replace('_', ' ').title())
    
    def _get_agent_icon(self, agent_key):
        """获取智能体图标"""
        icons = {
            'market_analyst': 'fas fa-chart-line',
            'sentiment_analyst': 'fas fa-heart-pulse',
            'news_analyst': 'fas fa-newspaper', 
            'fundamentals_analyst': 'fas fa-calculator',
            'bull_researcher': 'fas fa-arrow-trend-up',
            'bear_researcher': 'fas fa-arrow-trend-down',
            'research_manager': 'fas fa-user-tie',
            'trader': 'fas fa-handshake',
            'aggressive_risk_analyst': 'fas fa-bolt',
            'safe_risk_analyst': 'fas fa-shield-halved',
            'neutral_risk_analyst': 'fas fa-balance-scale',
            'risk_manager': 'fas fa-user-shield'
        }
        return icons.get(agent_key, 'fas fa-robot')
    
    def _get_agent_color(self, agent_key):
        """获取智能体主题色"""
        colors = {
            'market_analyst': '#3b82f6',
            'sentiment_analyst': '#8b5cf6',
            'news_analyst': '#f59e0b', 
            'fundamentals_analyst': '#10b981',
            'bull_researcher': '#22c55e',
            'bear_researcher': '#ef4444',
            'research_manager': '#6b7280',
            'trader': '#f59e0b',
            'aggressive_risk_analyst': '#8b5cf6',
            'safe_risk_analyst': '#06b6d4',
            'neutral_risk_analyst': '#84cc16',
            'risk_manager': '#374151'
        }
        return colors.get(agent_key, '#667eea')
    
    def _format_content(self, content):
        """格式化内容为现代化HTML"""
        if not content:
            return '''
            <div class="no-results">
                <i class="fas fa-exclamation-circle"></i>
                <p>暂无分析结果</p>
            </div>
            '''
        
        # 如果content是字典且包含result字段
        if isinstance(content, dict) and 'result' in content:
            content = content['result']
        elif isinstance(content, str):
            try:
                # 尝试解析JSON字符串
                parsed = eval(content) if content.startswith('{') else content
                if isinstance(parsed, dict) and 'result' in parsed:
                    content = parsed['result']
            except:
                pass
        
        # 转换Markdown格式到HTML
        content = str(content)
        
        # 处理标题
        content = re.sub(r'### (.+)', r'<div class="content-section"><h4><i class="fas fa-chevron-right"></i> \1</h4>', content)
        content = re.sub(r'#### (.+)', r'<div class="content-section"><h4><i class="fas fa-chevron-right"></i> \1</h4>', content)
        content = re.sub(r'##### (.+)', r'<div class="content-section"><h4><i class="fas fa-chevron-right"></i> \1</h4>', content)
        
        # 处理粗体
        content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
        
        # 处理列表
        lines = content.split('\n')
        formatted_lines = []
        in_list = False
        current_section = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('- ') or line.startswith('* '):
                if not in_list:
                    if current_section:
                        formatted_lines.extend(current_section)
                        current_section = []
                    formatted_lines.append('<ul>')
                    in_list = True
                formatted_lines.append(f'<li>{line[2:]}</li>')
            elif line.startswith(('1. ', '2. ', '3. ', '4. ', '5. ', '6. ', '7. ', '8. ', '9. ')):
                if not in_list:
                    if current_section:
                        formatted_lines.extend(current_section)
                        current_section = []
                    formatted_lines.append('<ol>')
                    in_list = True
                formatted_lines.append(f'<li>{line[3:]}</li>')
            else:
                if in_list:
                    formatted_lines.append('</ul>' if '<ul>' in formatted_lines else '</ol>')
                    in_list = False
                if line:
                    if line.startswith('<div class="content-section">'):
                        if current_section:
                            formatted_lines.extend(current_section)
                            formatted_lines.append('</div>')
                        current_section = [line]
                    else:
                        current_section.append(f'<p>{line}</p>')
        
        if in_list:
            formatted_lines.append('</ul>' if '<ul>' in formatted_lines else '</ol>')
        
        if current_section:
            formatted_lines.extend(current_section)
            formatted_lines.append('</div>')
        
        return '\n'.join(formatted_lines)
    
    def _calculate_duration(self, start_time, end_time):
        """计算执行时长"""
        try:
            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            duration = end - start
            total_seconds = duration.total_seconds()
            if total_seconds < 60:
                return f"{total_seconds:.1f}秒"
            elif total_seconds < 3600:
                return f"{total_seconds/60:.1f}分钟"
            else:
                return f"{total_seconds/3600:.1f}小时"
        except:
            return "未知"
    
    def convert_json_to_html(self, json_file_path, output_file_path=None):
        """将JSON文件转换为现代化交互式HTML"""
        try:
            # 读取JSON文件
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取基本信息
            session_id = data.get('session_id', 'Unknown')
            user_query = data.get('user_query', '未知查询')
            created_at = data.get('created_at', '')
            updated_at = data.get('updated_at', '')
            status = data.get('status', 'unknown')
            
            # 状态显示
            status_text_map = {
                'completed': '已完成',
                'running': '运行中', 
                'failed': '失败',
                'unknown': '未知'
            }
            status_text = status_text_map.get(status, status)
            
            # 格式化时间
            try:
                created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                created_at = created_dt.strftime('%Y年%m月%d日 %H:%M:%S')
            except:
                pass
            
            try:
                updated_dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                updated_at = updated_dt.strftime('%Y年%m月%d日 %H:%M:%S')
            except:
                pass
            
            # 生成智能体内容
            agents_content = ""
            agents_data = data.get('agents_data', {})
            
            for i, (agent_key, agent_info) in enumerate(agents_data.items()):
                agent_name = self._get_agent_display_name(agent_key)
                agent_icon = self._get_agent_icon(agent_key)
                agent_color = self._get_agent_color(agent_key)
                
                # 获取执行时间
                start_time = agent_info.get('start_time', '')
                end_time = agent_info.get('end_time', '')
                duration = self._calculate_duration(start_time, end_time) if start_time and end_time else "未知"
                
                # 获取结果内容
                results = agent_info.get('results', [])
                content = ""
                if results:
                    # 取最新的结果
                    latest_result = results[-1]
                    content = latest_result.get('content', '')
                
                formatted_content = self._format_content(content)
                
                # 添加AOS动画延迟
                aos_delay = i * 100
                
                agents_content += f'''
                <div class="agent-card" data-aos="fade-up" data-aos-delay="{aos_delay}">
                    <div class="agent-header" style="background: linear-gradient(135deg, {agent_color}, {agent_color}dd);">
                        <div class="agent-info">
                            <div class="agent-avatar">
                                <i class="{agent_icon}"></i>
                            </div>
                            <div class="agent-details">
                                <h3>{agent_name}</h3>
                                <div class="agent-timing">
                                    <i class="fas fa-clock"></i> 执行时长: {duration}
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="agent-content">
                        {formatted_content if formatted_content else '<div class="no-results"><i class="fas fa-exclamation-circle"></i><p>暂无分析结果</p></div>'}
                    </div>
                </div>
                '''
            
            # 生成总结部分（如果有的话）
            summary_section = ""
            if 'final_report' in data or 'summary' in data:
                summary_content = data.get('final_report', data.get('summary', ''))
                if summary_content:
                    formatted_summary = self._format_content(summary_content)
                    summary_section = f'''
                    <div class="summary-section" id="summary" data-aos="fade-up">
                        <h2 class="summary-title">
                            <i class="fas fa-clipboard-check"></i> 分析总结
                        </h2>
                        <div class="summary-content">
                            {formatted_summary}
                        </div>
                    </div>
                    '''
            
            # 生成当前时间
            generation_time = datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
            
            # 填充模板
            html_content = self.html_template.replace('{{query}}', user_query)
            html_content = html_content.replace('{{session_id}}', session_id)
            html_content = html_content.replace('{{created_at}}', created_at)
            html_content = html_content.replace('{{updated_at}}', updated_at)
            html_content = html_content.replace('{{status}}', status)
            html_content = html_content.replace('{{status_text}}', status_text)
            html_content = html_content.replace('{{agents_content}}', agents_content)
            html_content = html_content.replace('{{summary_section}}', summary_section)
            html_content = html_content.replace('{{generation_time}}', generation_time)
            
            # 确定输出文件路径
            if not output_file_path:
                json_path = Path(json_file_path)
                output_file_path = json_path.parent / f"{json_path.stem}_premium_report.html"
            
            # 写入HTML文件
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✅ 精美HTML报告已生成: {output_file_path}")
            return str(output_file_path)
            
        except Exception as e:
            print(f"❌ 转换失败: {str(e)}")
            return None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='将JSON分析报告转换为精美的交互式HTML')
    parser.add_argument('json_file', help='输入的JSON文件路径')
    parser.add_argument('-o', '--output', help='输出的HTML文件路径（可选）')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.json_file):
        print(f"❌ 文件不存在: {args.json_file}")
        return
    
    converter = AnalysisReportConverter()
    result = converter.convert_json_to_html(args.json_file, args.output)
    
    if result:
        print(f"🎉 转换成功！可以在浏览器中打开查看: {result}")
    else:
        print("💥 转换失败！")

if __name__ == '__main__':
    main()