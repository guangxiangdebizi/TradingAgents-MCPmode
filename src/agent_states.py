from typing import Dict, Any, List, Optional
from langgraph.graph import MessagesState
from pydantic import BaseModel


class InvestDebateState(BaseModel):
    """投资辩论状态管理"""
    history: str = ""  # 完整辩论历史
    bull_history: str = ""  # 看涨方历史
    bear_history: str = ""  # 看跌方历史
    current_response: str = ""  # 最新回应
    count: int = 0  # 辩论轮次
    

class RiskDebateState(BaseModel):
    """风险管理辩论状态"""
    history: str = ""  # 完整辩论历史
    aggressive_history: str = ""  # 激进方历史
    safe_history: str = ""  # 保守方历史
    neutral_history: str = ""  # 中性方历史
    current_aggressive_response: str = ""  # 激进方最新回应
    current_safe_response: str = ""  # 保守方最新回应
    current_neutral_response: str = ""  # 中性方最新回应
    count: int = 0  # 辩论轮次


class AgentState(MessagesState):
    """智能体状态管理 - 所有智能体间传递的核心状态"""
    
    # 基础信息
    user_query: str = ""  # 用户查询问题
    company_details: str = ""  # 公司基础信息（供分析师使用的占位符）
    
    # 分析师报告（智能体间传递的核心数据）
    company_overview_report: str = ""  # 公司概述分析师报告
    market_report: str = ""  # 市场分析师报告
    sentiment_report: str = ""  # 情绪分析师报告
    news_report: str = ""  # 新闻分析师报告
    fundamentals_report: str = ""  # 基本面分析师报告
    shareholder_report: str = ""  # 股东结构分析师报告
    product_report: str = ""  # 产品分析师报告
    
    # 研究员辩论状态
    investment_debate_state: Dict[str, Any] = {}
    investment_plan: str = ""  # 研究经理决策
    
    # 交易员决策
    trader_investment_plan: str = ""  # 交易员投资计划
    quant_strategy_plan: str = ""  # 量化交易员输出的量化策略逻辑
    
    # 风险管理辩论状态
    risk_debate_state: Dict[str, Any] = {}
    final_trade_decision: str = ""  # 最终交易决策
    
    # MCP工具调用历史
    mcp_tool_calls: List[Dict[str, Any]] = []
    
    # 智能体执行历史
    agent_execution_history: List[Dict[str, Any]] = []
    
    # 错误和警告信息
    errors: List[str] = []
    warnings: List[str] = []
    
    def add_agent_execution(self, agent_name: str, action: str, result: str, mcp_used: bool = False):
        """添加智能体执行记录"""
        from datetime import datetime
        self.agent_execution_history.append({
            "agent_name": agent_name,
            "action": action,
            "result": result,
            "mcp_used": mcp_used,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    def add_mcp_tool_call(self, agent_name: str, tool_name: str, tool_args: Dict, tool_result: Any):
        """添加MCP工具调用记录"""
        from datetime import datetime
        self.mcp_tool_calls.append({
            "agent_name": agent_name,
            "tool_name": tool_name,
            "tool_args": tool_args,
            "tool_result": str(tool_result),
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    def add_error(self, error_msg: str):
        """添加错误信息"""
        self.errors.append(error_msg)
    
    def add_warning(self, warning_msg: str):
        """添加警告信息"""
        self.warnings.append(warning_msg)
    
    def get_all_reports(self) -> Dict[str, str]:
        """获取所有分析师报告"""
        return {
            "company_overview_report": self.company_overview_report,
            "market_report": self.market_report,
            "sentiment_report": self.sentiment_report,
            "news_report": self.news_report,
            "fundamentals_report": self.fundamentals_report,
            "shareholder_report": self.shareholder_report,
            "product_report": self.product_report
        }
    
    def get_debate_summary(self) -> str:
        """获取辩论摘要"""
        investment_history = self.investment_debate_state.get("history", "")
        risk_history = self.risk_debate_state.get("history", "")
        
        summary = ""
        if investment_history:
            summary += f"投资辩论历史:\n{investment_history}\n\n"
        if risk_history:
            summary += f"风险管理辩论历史:\n{risk_history}\n\n"
        
        return summary.strip()