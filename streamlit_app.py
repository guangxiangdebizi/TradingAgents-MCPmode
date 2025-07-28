import streamlit as st
import asyncio
import json
import io
import base64
from datetime import datetime
from pathlib import Path
import sys
import threading
import queue
import time
from typing import Dict, Any, Optional

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.workflow_orchestrator import WorkflowOrchestrator
from src.report_generator import ReportGenerator
from src.progress_tracker import ProgressTracker
from loguru import logger
import tempfile
import os

# 配置页面
st.set_page_config(
    page_title="智能交易分析系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
}

.status-box {
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 1rem 0;
}

.status-running {
    background-color: #fff3cd;
    border: 1px solid #ffeaa7;
    color: #856404;
}

.status-completed {
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    color: #155724;
}

.status-error {
    background-color: #f8d7da;
    border: 1px solid #f5c6cb;
    color: #721c24;
}

.log-container {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 0.375rem;
    padding: 1rem;
    font-family: 'Courier New', monospace;
    font-size: 0.875rem;
    max-height: 400px;
    overflow-y: auto;
}

.progress-item {
    padding: 0.5rem;
    margin: 0.25rem 0;
    border-radius: 0.25rem;
    border-left: 4px solid #007bff;
    background-color: #f8f9fa;
}

.agent-card {
    border: 1px solid #dee2e6;
    border-radius: 0.5rem;
    padding: 1rem;
    margin: 0.5rem 0;
    background-color: white;
}

.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem;
    border-radius: 0.5rem;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# 初始化session state
if 'analysis_running' not in st.session_state:
    st.session_state.analysis_running = False
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'progress_logs' not in st.session_state:
    st.session_state.progress_logs = []
if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = None
if 'log_queue' not in st.session_state:
    st.session_state.log_queue = queue.Queue()


class StreamlitLogHandler:
    """Streamlit日志处理器"""
    
    def __init__(self, log_queue):
        self.log_queue = log_queue
    
    def write(self, message):
        if message.strip():
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_queue.put(f"[{timestamp}] {message.strip()}")
    
    def flush(self):
        pass


def get_download_link(file_path: str, file_name: str) -> str:
    """生成文件下载链接"""
    with open(file_path, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{file_name}">📥 下载 {file_name}</a>'


async def run_analysis_async(user_query: str, log_queue):
    """异步运行分析"""
    try:
        # 创建工作流编排器
        orchestrator = WorkflowOrchestrator()
        st.session_state.orchestrator = orchestrator
        
        # 初始化编排器
        await orchestrator.initialize()
        
        # 运行分析
        result = await orchestrator.run_analysis(user_query)
        
        # 关闭编排器
        await orchestrator.close()
        
        return result
    except Exception as e:
        logger.error(f"分析过程中发生错误: {e}")
        raise e


def setup_logger_for_streamlit(log_queue):
    """为Streamlit设置日志处理器"""
    def log_sink(message):
        # 提取日志消息的文本部分
        log_text = message.record["message"]
        timestamp = message.record["time"].strftime("%H:%M:%S")
        level = message.record["level"].name
        
        # 根据日志级别添加emoji
        emoji_map = {
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "DEBUG": "🔍",
            "SUCCESS": "✅"
        }
        emoji = emoji_map.get(level, "📝")
        
        # 检查是否是工具调用相关的日志
        if "工具返回结果" in log_text or "工具调用" in log_text or "MCP工具" in log_text:
            # 对工具调用日志进行特殊格式化
            formatted_message = f"[{timestamp}] 🔧 {log_text}"
        elif "===" in log_text and "结果" in log_text:
            # 工具结果分隔符
            formatted_message = f"[{timestamp}] 📊 {log_text}"
        elif "结果片段" in log_text:
            # 工具结果片段
            formatted_message = f"[{timestamp}] 📄 {log_text}"
        else:
            formatted_message = f"[{timestamp}] {emoji} {log_text}"
        
        log_queue.put(formatted_message)
    
    # 添加自定义日志处理器
    logger.add(log_sink, level="INFO", format="{message}")


def run_analysis_thread(user_query: str, log_queue):
    """在线程中运行分析"""
    try:
        # 设置日志处理器
        setup_logger_for_streamlit(log_queue)
        
        # 运行异步分析
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(run_analysis_async(user_query, log_queue))
        loop.close()
        
        # 保存结果
        st.session_state.analysis_result = result
        st.session_state.analysis_running = False
        
        log_queue.put("🎉 分析完成！")
        
    except Exception as e:
        st.session_state.analysis_running = False
        log_queue.put(f"❌ 分析失败: {str(e)}")
        logger.error(f"分析线程错误: {e}")


def main():
    # 主标题
    st.markdown('<h1 class="main-header">🤖 智能交易分析系统</h1>', unsafe_allow_html=True)
    
    # 侧边栏
    with st.sidebar:
        st.header("📋 控制面板")
        
        # 用户输入
        user_query = st.text_area(
            "请输入您的交易分析问题：",
            placeholder="例如：分析苹果公司的股票投资价值",
            height=100
        )
        
        # 分析按钮
        if st.button("🚀 开始分析", disabled=st.session_state.analysis_running):
            if user_query.strip():
                st.session_state.analysis_running = True
                st.session_state.analysis_result = None
                st.session_state.progress_logs = []
                
                # 启动分析线程
                analysis_thread = threading.Thread(
                    target=run_analysis_thread,
                    args=(user_query, st.session_state.log_queue)
                )
                analysis_thread.daemon = True
                analysis_thread.start()
                
                st.success("分析已开始！")
            else:
                st.error("请输入有效的问题")
        
        # 停止按钮
        if st.button("⏹️ 停止分析", disabled=not st.session_state.analysis_running):
            st.session_state.analysis_running = False
            st.warning("分析已停止")
        
        st.divider()
        
        # 报告生成设置
        st.header("📄 报告生成")
        
        report_format = st.selectbox(
            "选择报告格式：",
            ["markdown", "docx", "pdf"],
            index=0
        )
        
        report_title = st.text_input(
            "报告标题：",
            value="交易分析报告"
        )
        
        # 生成报告按钮
        if st.button("📊 生成报告", disabled=st.session_state.analysis_result is None):
            if st.session_state.analysis_result:
                try:
                    generator = ReportGenerator()
                    
                    # 转换结果为字典格式
                    if hasattr(st.session_state.analysis_result, '__dict__'):
                        result_dict = st.session_state.analysis_result.__dict__
                    else:
                        result_dict = st.session_state.analysis_result
                    
                    # 生成报告
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_path = f"report_{timestamp}.{report_format}"
                    
                    file_path = generator.generate_report(
                        data=result_dict,
                        output_format=report_format,
                        output_path=output_path,
                        title=report_title
                    )
                    
                    st.success(f"报告已生成：{file_path}")
                    
                    # 提供下载链接
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            st.download_button(
                                label=f"📥 下载 {report_format.upper()} 报告",
                                data=f.read(),
                                file_name=f"trading_report_{timestamp}.{report_format}",
                                mime="application/octet-stream"
                            )
                    
                except Exception as e:
                    st.error(f"生成报告失败：{str(e)}")
    
    # 主内容区域
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 状态显示
        if st.session_state.analysis_running:
            st.markdown('<div class="status-box status-running">🔄 分析正在进行中...</div>', unsafe_allow_html=True)
        elif st.session_state.analysis_result:
            st.markdown('<div class="status-box status-completed">✅ 分析已完成</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-box">💡 请在左侧输入问题开始分析</div>', unsafe_allow_html=True)
        
        # 进度显示
        if st.session_state.analysis_running:
            # 简单的进度指示器
            st.progress(0.5)  # 显示50%进度作为运行指示
            st.write("**状态**: 分析正在进行中...")
            st.write("**提示**: 请查看下方实时日志了解详细进度")
        
        # 实时日志显示
        st.subheader("📋 实时日志")
        
        # 获取新日志
        new_logs = []
        try:
            while True:
                log_message = st.session_state.log_queue.get_nowait()
                new_logs.append(log_message)
                # 检查分析完成标志
                if "🎉 分析完成！" in log_message:
                    st.session_state.analysis_running = False
        except queue.Empty:
            pass
        
        # 添加新日志到session state
        if new_logs:
            st.session_state.progress_logs.extend(new_logs)
            # 限制日志数量
            if len(st.session_state.progress_logs) > 100:
                st.session_state.progress_logs = st.session_state.progress_logs[-100:]
        
        # 显示日志
        if st.session_state.progress_logs:
            # 创建两个标签页：实时日志和工具调用详情
            log_tab1, log_tab2 = st.tabs(["📋 实时日志", "🔧 工具调用详情"])
            
            with log_tab1:
                log_text = "\n".join(st.session_state.progress_logs[-20:])  # 显示最近20条
                st.markdown(f'<div class="log-container">{log_text}</div>', unsafe_allow_html=True)
            
            with log_tab2:
                # 过滤出工具调用相关的日志
                tool_logs = [log for log in st.session_state.progress_logs 
                           if any(keyword in log for keyword in ["工具调用", "工具返回结果", "工具参数", "===.*结果", "结果片段"])]
                
                if tool_logs:
                    st.markdown("**🔧 MCP工具调用记录：**")
                    for tool_log in tool_logs[-10:]:  # 显示最近10条工具日志
                        # 根据日志类型使用不同的样式
                        if "工具返回结果" in tool_log:
                            st.success(tool_log)
                        elif "工具调用" in tool_log:
                            st.info(tool_log)
                        elif "工具参数" in tool_log:
                            st.code(tool_log)
                        elif "===" in tool_log and "结果" in tool_log:
                            st.markdown(f"**{tool_log}**")
                        elif "结果片段" in tool_log:
                            st.text(tool_log)
                        else:
                            st.write(tool_log)
                else:
                    st.info("暂无工具调用记录")
        else:
            st.info("暂无日志信息")
        
        # 自动刷新 - 减少刷新频率以避免状态更新延迟
        if st.session_state.analysis_running:
            time.sleep(2)  # 增加刷新间隔
            st.rerun()
    
    with col2:
        # 系统信息
        st.subheader("📊 系统状态")
        
        # 智能体状态卡片
        agents_info = [
            ("📈 市场分析师", "技术分析"),
            ("💭 情绪分析师", "市场情绪"),
            ("📰 新闻分析师", "新闻事件"),
            ("🏢 基本面分析师", "财务分析"),
            ("🐂 看涨研究员", "投资机会"),
            ("🐻 看跌研究员", "风险识别"),
            ("👔 研究经理", "投资决策"),
            ("📊 交易员", "执行计划"),
            ("⚡ 激进风险分析师", "高风险评估"),
            ("🛡️ 保守风险分析师", "低风险评估"),
            ("⚖️ 中性风险分析师", "平衡评估"),
            ("🎯 风险经理", "最终决策")
        ]
        
        for agent_name, description in agents_info:
            with st.container():
                st.markdown(f"""
                <div class="agent-card">
                    <strong>{agent_name}</strong><br>
                    <small>{description}</small>
                </div>
                """, unsafe_allow_html=True)
        
        # 统计信息
        st.subheader("📈 统计信息")
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("智能体数量", 12)
        with col_b:
            st.metric("分析状态", "运行中" if st.session_state.analysis_running else "待机")
    
    # 结果显示
    if st.session_state.analysis_result:
        st.divider()
        st.subheader("📋 分析结果")
        
        # 创建标签页
        tab1, tab2, tab3 = st.tabs(["📊 结果概览", "📄 详细报告", "🔍 原始数据"])
        
        with tab1:
            # 结果概览
            result = st.session_state.analysis_result
            
            if hasattr(result, 'user_query'):
                st.write(f"**用户问题**: {result.user_query}")
            
            # 显示各个报告的摘要
            reports = [
                ('market_report', '📊 市场分析'),
                ('sentiment_report', '💭 情绪分析'),
                ('news_report', '📰 新闻分析'),
                ('fundamentals_report', '🏢 基本面分析'),
                ('research_decision', '👔 投资决策'),
                ('execution_plan', '📈 执行计划'),
                ('final_risk_decision', '🛡️ 风险决策')
            ]
            
            for attr_name, display_name in reports:
                if hasattr(result, attr_name):
                    report_content = getattr(result, attr_name)
                    if report_content:
                        with st.expander(display_name):
                            # 显示报告内容的前200个字符
                            preview = report_content[:200] + "..." if len(report_content) > 200 else report_content
                            st.write(preview)
        
        with tab2:
            # 详细报告
            if hasattr(st.session_state.analysis_result, '__dict__'):
                result_dict = st.session_state.analysis_result.__dict__
            else:
                result_dict = st.session_state.analysis_result
            
            # 生成临时markdown报告
            try:
                generator = ReportGenerator()
                markdown_content = generator._generate_markdown_content(result_dict, "交易分析报告")
                st.markdown(markdown_content)
            except Exception as e:
                st.error(f"生成详细报告失败：{str(e)}")
        
        with tab3:
            # 原始数据
            st.json(st.session_state.analysis_result.__dict__ if hasattr(st.session_state.analysis_result, '__dict__') else st.session_state.analysis_result)


if __name__ == "__main__":
    main()