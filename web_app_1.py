#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TradingAgents-MCPmode 专业辩论展示页面
基于专业时间轴设计的智能体分析结果展示
"""

import streamlit as st
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 页面配置
st.set_page_config(
    page_title="AI实验室 - 智能体辩论",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 隐藏Streamlit警告信息
import warnings
warnings.filterwarnings("ignore")
import logging
logging.getLogger().setLevel(logging.ERROR)

# 隐藏所有Streamlit默认元素
st.markdown("""
<style>
.stAlert, [data-baseweb="notification"], .stException { display: none !important; }
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 初始化会话状态
if "selected_session_file" not in st.session_state:
    st.session_state.selected_session_file = None
if "current_session_data" not in st.session_state:
    st.session_state.current_session_data = None

def get_session_files_list():
    """获取会话文件列表"""
    try:
        dump_dir = Path("src/dump")
        if not dump_dir.exists():
            return []
        json_files = list(dump_dir.glob("session_*.json"))
        return sorted(json_files, key=lambda f: f.stat().st_mtime, reverse=True)
    except:
        return []

def get_agent_info(agent_name: str) -> Dict[str, str]:
    """获取智能体信息"""
    agent_mapping = {
        'company_overview_analyst': {'name': '公司概述分析师', 'emoji': '🏢', 'type': 'analyst', 'side': 'left'},
        'market_analyst': {'name': '市场分析师', 'emoji': '📈', 'type': 'analyst', 'side': 'right'},
        'sentiment_analyst': {'name': '情绪分析师', 'emoji': '😊', 'type': 'analyst', 'side': 'left'},
        'news_analyst': {'name': '新闻分析师', 'emoji': '📰', 'type': 'analyst', 'side': 'right'},
        'fundamentals_analyst': {'name': '基本面分析师', 'emoji': '📋', 'type': 'analyst', 'side': 'left'},
        'shareholder_analyst': {'name': '股东分析师', 'emoji': '👥', 'type': 'analyst', 'side': 'right'},
        'product_analyst': {'name': '产品分析师', 'emoji': '🏭', 'type': 'analyst', 'side': 'left'},
        'bull_researcher': {'name': '看涨研究员', 'emoji': '🐂', 'type': 'bull', 'side': 'right'},
        'bear_researcher': {'name': '看跌研究员', 'emoji': '🐻', 'type': 'bear', 'side': 'left'},
        'research_manager': {'name': '研究经理', 'emoji': '👔', 'type': 'manager', 'side': 'right'},
        'trader': {'name': '交易员', 'emoji': '💼', 'type': 'manager', 'side': 'left'},
        'aggressive_risk_analyst': {'name': '激进风险分析师', 'emoji': '⚡', 'type': 'risk', 'side': 'right'},
        'safe_risk_analyst': {'name': '保守风险分析师', 'emoji': '🛡️', 'type': 'risk', 'side': 'left'},
        'neutral_risk_analyst': {'name': '中性风险分析师', 'emoji': '⚖️', 'type': 'risk', 'side': 'right'},
        'risk_manager': {'name': '风险经理', 'emoji': '🎯', 'type': 'risk', 'side': 'left'}
    }
    return agent_mapping.get(agent_name, {'name': agent_name, 'emoji': '🤖', 'type': 'other', 'side': 'left'})

def load_session_data(json_file_path: str):
    """加载会话数据"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        st.session_state.selected_session_file = json_file_path
        st.session_state.current_session_data = session_data
    except Exception as e:
        print(f"加载失败: {str(e)}")



def create_timeline_item(agent: Dict[str, Any], index: int) -> str:
    """创建时间轴项目HTML"""
    agent_name = agent.get('agent_name', 'Unknown')
    result_content = agent.get('result', '')
    
    if not result_content:
        return ""
    
    agent_info = get_agent_info(agent_name)
    side = agent_info['side']
    
    # 限制内容长度
    if len(result_content) > 800:
        result_content = result_content[:800] + "..."
    
    # 获取时间戳
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    timeline_html = f"""
    <div class="timeline-item {side}" style="animation-delay: {index * 0.1}s;">
        <div class="timeline-card">
            <div class="card-header">
                <span class="agent-name">{agent_info['emoji']} {agent_info['name']}</span>
            </div>
            <div class="card-content">
                <p>{result_content}</p>
                <div class="timestamp">{timestamp}</div>
            </div>
        </div>
    </div>
    """
    return timeline_html

def get_vote_stats(agents: List[Dict[str, Any]]) -> Dict[str, int]:
    """统计投票结果"""
    bull_count = 0
    bear_count = 0
    
    for agent in agents:
        agent_name = agent.get('agent_name', '')
        result = agent.get('result', '').lower()
        
        if 'bull' in agent_name or '看涨' in result or '买入' in result or '上涨' in result:
            bull_count += 1
        elif 'bear' in agent_name or '看跌' in result or '卖出' in result or '下跌' in result:
            bear_count += 1
    
    return {'bull': bull_count, 'bear': bear_count}

def main():
    """主界面 - 专业时间轴设计"""
    
    # 完整的CSS样式 - 基于原HTML设计
    st.markdown("""
    <style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    .main-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 30px 20px;
        background: #f8f9fa;
        min-height: 100vh;
        font-family: 'Microsoft YaHei', 'PingFang SC', 'Helvetica Neue', Arial, sans-serif;
    }
    
    /* 顶部导航栏 */
    .top-nav {
        background: white;
        border-radius: 12px;
        padding: 15px 30px;
        margin-bottom: 30px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #e9ecef;
    }
    
    .nav-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .nav-left {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .nav-icon {
        font-size: 20px;
    }
    
    .nav-title {
        font-size: 18px;
        font-weight: 600;
        color: #2196F3;
    }
    
    /* 报告标题区 */
    .title-section {
        text-align: center;
        margin-bottom: 40px;
    }
    
    .main-title {
        font-size: 32px;
        color: #333;
        margin-bottom: 10px;
        font-weight: 600;
    }
    
    .stock-code {
        color: #2196F3;
        font-weight: 700;
    }
    
    .subtitle {
        color: #666;
        font-size: 14px;
        margin: 0;
    }
    
    /* 专家投票结果卡片 */
    .vote-card {
        background: white;
        border-radius: 12px;
        padding: 30px;
        margin-bottom: 40px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #e9ecef;
    }
    
    .vote-header {
        text-align: center;
        margin-bottom: 25px;
    }
    
    .vote-header h3 {
        color: #333;
        font-size: 18px;
        font-weight: 600;
        margin: 0;
    }
    
    .vote-content {
        max-width: 400px;
        margin: 0 auto;
    }
    
    .vote-stats {
        display: flex;
        justify-content: space-between;
        margin-bottom: 20px;
        text-align: center;
    }
    
    .bullish, .bearish {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    
    .vote-number {
        font-size: 24px;
        font-weight: 700;
        margin-bottom: 5px;
    }
    
    .bullish .vote-number {
        color: #28a745;
    }
    
    .bearish .vote-number {
        color: #dc3545;
    }
    
    .vote-label {
        font-size: 14px;
        color: #666;
    }
    
    .vote-bar {
        display: flex;
        height: 8px;
        border-radius: 4px;
        overflow: hidden;
        background: #f8f9fa;
    }
    
    .bar-bullish {
        background: #28a745;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 12px;
        font-weight: 600;
        min-width: 60px;
    }
    
    .bar-bearish {
        background: #dc3545;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 12px;
        font-weight: 600;
        min-width: 60px;
    }
    
    /* 通用区块样式 */
    .debate-section {
        margin-bottom: 50px;
    }
    
    .section-title {
        font-size: 24px;
        color: #2196F3;
        margin-bottom: 8px;
        text-align: center;
        font-weight: 600;
    }
    
    .section-subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 30px;
        font-size: 14px;
    }
    
    /* 时间轴样式 */
    .timeline {
        position: relative;
        max-width: 800px;
        margin: 0 auto;
        padding: 20px 0;
    }
    
    .timeline::before {
        content: '';
        position: absolute;
        left: 50%;
        top: 0;
        bottom: 0;
        width: 2px;
        background: #e9ecef;
        transform: translateX(-50%);
    }
    
    .timeline-item {
        position: relative;
        margin-bottom: 30px;
        width: 50%;
        opacity: 0;
        animation: fadeInUp 0.6s ease forwards;
    }
    
    .timeline-item.left {
        left: 0;
        padding-right: 30px;
    }
    
    .timeline-item.right {
        left: 50%;
        padding-left: 30px;
    }
    
    .timeline-item::before {
        content: '';
        position: absolute;
        top: 20px;
        width: 12px;
        height: 12px;
        background: #2196F3;
        border-radius: 50%;
        border: 3px solid white;
        box-shadow: 0 0 0 3px #e9ecef;
    }
    
    .timeline-item.left::before {
        right: -6px;
    }
    
    .timeline-item.right::before {
        left: -6px;
    }
    
    .timeline-card {
        background: white;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #e9ecef;
        transition: all 0.3s ease;
    }
    
    .timeline-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
    }
    
    .timeline-card .card-header {
        background: #2196F3;
        padding: 12px 20px;
        color: white;
    }
    
    .agent-name {
        font-weight: 600;
        font-size: 14px;
    }
    
    .timeline-card .card-content {
        padding: 20px;
    }
    
    .timeline-card .card-content p {
        color: #555;
        line-height: 1.7;
        margin-bottom: 15px;
        margin-top: 0;
    }
    
    .timestamp {
        font-size: 12px;
        color: #999;
        text-align: right;
        border-top: 1px solid #f0f0f0;
        padding-top: 10px;
        margin-top: 15px;
    }
    
    /* 动画效果 */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* 响应式设计 */
    @media (max-width: 768px) {
        .timeline::before {
            left: 20px;
        }
        
        .timeline-item {
            width: 100%;
            left: 0 !important;
            padding-left: 50px;
            padding-right: 0;
        }
        
        .timeline-item::before {
            left: 14px !important;
            right: auto !important;
        }
        
        .main-title {
            font-size: 24px;
        }
        
        .section-title {
            font-size: 20px;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 主容器开始
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # 顶部导航栏
    st.markdown("""
    <div class="top-nav">
        <div class="nav-container">
            <div class="nav-left">
                <span class="nav-icon">🔬</span>
                <span class="nav-title">人工智能实验室</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 会话选择
    json_files = get_session_files_list()
    if not json_files:
        st.error("📭 暂无历史分析数据")
        return
    
    # 文件选择器
    file_options = []
    for json_file in json_files:
        file_time = datetime.fromtimestamp(json_file.stat().st_mtime)
        display_name = f"{json_file.name} ({file_time.strftime('%m-%d %H:%M')})"
        file_options.append(display_name)
    
    selected_index = st.selectbox(
        "选择分析会话",
        range(len(file_options)),
        format_func=lambda i: file_options[i],
        key="session_selector"
    )
    
    # 加载选中的会话
    if selected_index is not None:
        selected_file = str(json_files[selected_index])
        if st.session_state.selected_session_file != selected_file:
            load_session_data(selected_file)
    
    # 显示分析结果
    if st.session_state.current_session_data:
        agents = st.session_state.current_session_data.get('agents', [])
        completed_agents = [agent for agent in agents if agent.get('status') == 'completed' and agent.get('result')]
        
        if completed_agents:
            # 报告标题区
            st.markdown("""
            <div class="title-section">
                <h1 class="main-title">智能体协同分析报告</h1>
                <p class="subtitle">人工智能实验室智能分析Agent协同分析</p>
            </div>
            """, unsafe_allow_html=True)
            
            # 专家投票结果
            vote_stats = get_vote_stats(completed_agents)
            total_votes = vote_stats['bull'] + vote_stats['bear']
            
            if total_votes > 0:
                bull_percentage = (vote_stats['bull'] / total_votes) * 100
                bear_percentage = (vote_stats['bear'] / total_votes) * 100
                
                st.markdown(f"""
                <div class="vote-card">
                    <div class="vote-header">
                        <h3>📊 专家投票结果</h3>
                    </div>
                    <div class="vote-content">
                        <div class="vote-stats">
                            <div class="bullish">
                                <span class="vote-number">{vote_stats['bull']}</span>
                                <span class="vote-label">看涨 Bullish</span>
                            </div>
                            <div class="bearish">
                                <span class="vote-number">{vote_stats['bear']}</span>
                                <span class="vote-label">看跌 Bearish</span>
                            </div>
                        </div>
                        <div class="vote-bar">
                            <div class="bar-bullish" style="width: {bull_percentage}%">{bull_percentage:.1f}%</div>
                            <div class="bar-bearish" style="width: {bear_percentage}%">{bear_percentage:.1f}%</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # 专家辩论过程
            st.markdown("""
            <div class="debate-section">
                <h2 class="section-title">🗣️ 专家辩论过程</h2>
                <p class="section-subtitle">AI智能体协同分析过程实时记录</p>
                <div class="timeline">
            """, unsafe_allow_html=True)
            
            # 生成时间轴项目
            timeline_html = ""
            for index, agent in enumerate(completed_agents):
                item_html = create_timeline_item(agent, index)
                if item_html:
                    timeline_html += item_html
            
            # 显示时间轴
            st.markdown(timeline_html, unsafe_allow_html=True)
            
            # 结束时间轴和辩论区域
            st.markdown("""
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 统计信息
            st.markdown(f"""
            <div style="text-align: center; margin-top: 30px; padding: 20px; background: white; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08);">
                <h4 style="color: #2196F3; margin-bottom: 10px;">📊 分析统计</h4>
                <p style="color: #666; margin: 0;">共有 <strong>{len(completed_agents)}</strong> 个智能体参与了此次分析</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("该会话中暂无完成的智能体分析结果")
    else:
        st.info("请选择一个分析会话来查看辩论过程")
    
    # 主容器结束
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
