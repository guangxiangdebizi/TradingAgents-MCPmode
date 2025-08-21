from typing import Dict, Any
from datetime import datetime

from ..base_agent import BaseAgent
from ..agent_states import AgentState
from ..mcp_manager import MCPManager


class ResearchManager(BaseAgent):
    """研究经理 - 负责评估辩论结果并做出投资决策"""
    
    def __init__(self, mcp_manager: MCPManager):
        super().__init__(
            agent_name="research_manager",
            mcp_manager=mcp_manager,
            role_description="研究经理，负责评估研究员辩论结果并做出最终投资决策"
        )
    
    def get_system_prompt(self, state: AgentState) -> str:
        current_datetime = datetime.now()
        return f"""
你是一位资深的投资组合经理和研究主管，负责评估研究团队的辩论结果并做出最终的投资决策。

当前时间：{current_datetime.strftime('%Y年%m月%d日 %H:%M:%S')} ({current_datetime.strftime('%A')})

你的职责：
1. 客观评估看涨和看跌研究员的论证质量
2. 综合考虑所有分析报告和辩论观点
3. 识别关键的投资机会和风险点
4. 做出明确的投资决策：买入、卖出或持有
5. 提供决策理由和风险管理建议

决策标准：
- 基于证据的客观分析
- 风险收益比的综合考量
- 根据股票代码判断相应市场的特殊性
- 符合投资组合的整体策略
- 明确的执行建议和时间框架

决策选项：
- 支持看涨观点：建议买入或增持
- 支持看跌观点：建议卖出或减持
- 中性立场：建议持有或观望

请做出专业的投资决策。
"""
    
    async def process(self, state: AgentState, progress_tracker=None) -> AgentState:
        """执行投资决策"""
        # 处理状态可能是字典或AgentState对象的情况
        user_query = state.get('user_query', '') if isinstance(state, dict) else state.user_query

        
        if not self.validate_state(state):
            return state
        
        try:
            # 获取完整辩论历史
            if isinstance(state, dict):
                investment_debate_state = state.get('investment_debate_state', {})
            else:
                investment_debate_state = state.investment_debate_state
            history = investment_debate_state.get("history", "")
            bull_history = investment_debate_state.get("bull_history", "")
            bear_history = investment_debate_state.get("bear_history", "")
            
            # 构建决策请求
            decision_request = f"""
作为投资组合经理，请基于以下信息对用户问题 "{user_query}" 做出最终投资决策。

完整辩论历史：
{history}

决策要求：
1. 客观评估看涨和看跌论证的质量
2. 识别最关键的投资因素
3. 评估风险收益比
4. 做出明确的投资建议（买入/卖出/持有）
5. 提供具体的执行建议和风险管理措施

请提供详细的投资决策报告。
"""
            
            # 调用LLM进行决策
            decision_result = await self.call_llm_with_context(state, decision_request, progress_tracker)
            
            # 格式化并保存决策
            formatted_decision = self.format_output(decision_result, state)
            if isinstance(state, dict):
                state['investment_plan'] = formatted_decision
            else:
                state.investment_plan = formatted_decision
            

            
        except Exception as e:
            error_msg = f"投资决策失败: {str(e)}"
            print(f"❌ {error_msg}")
            if isinstance(state, dict):
                if 'errors' not in state:
                    state['errors'] = []
                state['errors'].append(error_msg)
                state['investment_plan'] = f"投资决策出现错误: {error_msg}"
            else:
                state.add_error(error_msg)
                state.investment_plan = f"投资决策出现错误: {error_msg}"
        
        return state


class Trader(BaseAgent):
    """交易员 - 负责制定具体的交易执行计划"""
    
    def __init__(self, mcp_manager: MCPManager):
        super().__init__(
            agent_name="trader",
            mcp_manager=mcp_manager,
            role_description="交易员，负责制定具体的交易执行计划和策略"
        )
    
    def get_system_prompt(self, state: AgentState) -> str:
        current_datetime = datetime.now()
        return f"""
你是一位专业的交易员，负责将投资决策转化为具体的交易执行计划。

当前时间：{current_datetime.strftime('%Y年%m月%d日 %H:%M:%S')} ({current_datetime.strftime('%A')})

你的职责：
1. 基于研究经理的投资决策制定交易计划
2. 确定具体的买卖点位和时机
3. 设计风险控制措施（止损、止盈）
4. 考虑市场流动性和交易成本
5. 提供详细的执行策略

交易计划要素：
- 交易方向（买入/卖出）
- 目标价位和数量
- 入场时机和策略
- 止损和止盈设置
- 风险控制措施
- 市场监控要点

考虑因素：
- 根据股票代码判断相应市场的交易特点
- 当前市场流动性状况
- 交易成本和滑点
- 市场时间和交易窗口

请制定专业的交易执行计划。
"""
    
    async def process(self, state: AgentState, progress_tracker=None) -> AgentState:
        """执行交易计划制定"""
        # 处理状态可能是字典或AgentState对象的情况
        user_query = state.get('user_query', '') if isinstance(state, dict) else state.user_query

        
        if not self.validate_state(state):
            return state
        
        try:
            # 获取投资决策
            if isinstance(state, dict):
                investment_plan = state.get('investment_plan', '')
            else:
                investment_plan = state.investment_plan
            
            # 构建交易计划请求
            trading_request = f"""
基于研究经理的投资决策，请为用户问题 "{user_query}" 制定详细的交易执行计划。

投资决策：
{investment_plan}

交易计划要求：
1. 具体的交易策略（买入/卖出/持有）
2. 目标价位和仓位管理
3. 入场和出场时机
4. 止损止盈设置
5. 风险控制措施
6. 市场监控要点
7. 应急预案

请提供可执行的详细交易计划。
"""
            
            # 调用LLM制定交易计划
            trading_result = await self.call_llm_with_context(state, trading_request, progress_tracker)
            
            # 格式化并保存交易计划
            formatted_plan = self.format_output(trading_result, state)
            if isinstance(state, dict):
                state['trader_investment_plan'] = formatted_plan
            else:
                state.trader_investment_plan = formatted_plan
            

            
        except Exception as e:
            error_msg = f"交易计划制定失败: {str(e)}"
            print(f"❌ {error_msg}")
            if isinstance(state, dict):
                if 'errors' not in state:
                    state['errors'] = []
                state['errors'].append(error_msg)
                state['trader_investment_plan'] = f"交易计划制定出现错误: {error_msg}"
            else:
                state.add_error(error_msg)
                state.trader_investment_plan = f"交易计划制定出现错误: {error_msg}"
        
        return state


class QuantitativeTrader(BaseAgent):
    """量化交易员 - 将交易员输出转化为量化可执行的策略逻辑"""
    
    def __init__(self, mcp_manager: MCPManager):
        super().__init__(
            agent_name="quantitative_trader",
            mcp_manager=mcp_manager,
            role_description="量化交易员，基于交易员计划产出量化策略逻辑（信号、因子、风控、回测框架）"
        )
    
    def get_system_prompt(self, state: AgentState) -> str:
        current_datetime = datetime.now()
        return f"""
你是一位资深的量化交易员。你的任务是：基于交易员的文字版交易计划，抽取并固化为可执行的量化策略逻辑。

当前时间：{current_datetime.strftime('%Y年%m月%d日 %H:%M:%S')} ({current_datetime.strftime('%A')})

输出必须包含：
1) 策略框架：频率（日/小时/分钟）、标的范围（单票/多票/指数/行业）、数据依赖（行情/财务/新闻/情绪等）
2) 信号与因子：
   - 技术面（MA/EMA/MACD/RSI/KDJ/布林带/成交量指标等）的明确参数与阈值
   - 基本面或量价特征：选股/择时的因子定义、标准化/去极值/行业中性化处理
3) 交易规则：开仓/加仓/减仓/平仓条件；仓位管理；多空条件（若适用）
4) 风险控制：止损/止盈、波动率目标、最大回撤约束、单票/行业/整体风控、持仓上限
5) 执行细节：撮合方式、滑点与冲击成本假设、盘中与收盘信号差异
6) 回测设计：
   - 时间区间、滚动窗口、步长
   - 指标：年化收益、波动率、夏普、卡玛、最大回撤、胜率/盈亏比、因子IC/ICIR
7) 伪代码/公式：用清晰步骤或伪代码描述核心计算与交易流程（便于工程落地）

请严格从交易员计划中抽取意图与逻辑，不要臆造与其相矛盾的设定；若交易员计划缺失关键信息，请做“保守合理默认值”的补全，并在“假设与默认”段落显式列出。
"""
    
    async def process(self, state: AgentState, progress_tracker=None) -> AgentState:
        """将交易员文本计划转化为量化策略逻辑"""
        # 兼容 dict/对象两种状态
        user_query = state.get('user_query', '') if isinstance(state, dict) else state.user_query
        if isinstance(state, dict):
            trader_plan = state.get('trader_investment_plan', '')
        else:
            trader_plan = state.trader_investment_plan
        
        if not self.validate_state(state):
            return state
        
        try:
            request = f"""
基于以下交易员计划，为用户问题 "{user_query}" 产出“量化可执行策略逻辑”说明书：

交易员计划：
{trader_plan}

请给出完整、结构化且可落地的量化策略描述（含因子定义、参数、规则、风控、回测与伪代码）。
"""
            result = await self.call_llm_with_context(state, request, progress_tracker)
            formatted = self.format_output(result, state)
            if isinstance(state, dict):
                state['quant_strategy_plan'] = formatted
            else:
                state.quant_strategy_plan = formatted
        except Exception as e:
            error_msg = f"量化策略生成失败: {str(e)}"
            print(f"❌ {error_msg}")
            if isinstance(state, dict):
                if 'errors' not in state:
                    state['errors'] = []
                state['errors'].append(error_msg)
                state['quant_strategy_plan'] = f"量化策略生成出现错误: {error_msg}"
            else:
                state.add_error(error_msg)
                state.quant_strategy_plan = f"量化策略生成出现错误: {error_msg}"
        
        return state