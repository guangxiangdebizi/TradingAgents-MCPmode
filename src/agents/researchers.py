from typing import Dict, Any
from datetime import datetime

from ..base_agent import BaseAgent
from ..agent_states import AgentState
from ..mcp_manager import MCPManager


class BullResearcher(BaseAgent):
    """看涨研究员 - 负责构建看涨论证"""
    
    def __init__(self, mcp_manager: MCPManager):
        super().__init__(
            agent_name="bull_researcher",
            mcp_manager=mcp_manager,
            role_description="看涨研究员，专门构建基于证据的看涨投资论证"
        )
    
    def get_system_prompt(self, state: AgentState) -> str:
        # 处理状态可能是字典或AgentState对象的情况
        user_query = state.get('user_query', '') if isinstance(state, dict) else state.user_query
        current_datetime = datetime.now()
        return f"""
你是一位专业的看涨研究员，负责为用户问题 "{user_query}" 构建强有力的看涨投资论证。

当前时间：{current_datetime.strftime('%Y年%m月%d日 %H:%M:%S')} ({current_datetime.strftime('%A')})

你的职责：
1. 基于所有可用的分析报告，构建看涨案例
2. 强调公司的增长潜力和投资机会
3. 识别被市场低估的价值
4. 反驳看跌观点，提供有力的反证
5. 提供具体的投资理由和目标价位

辩论要求：
- 基于客观数据和分析报告
- 逻辑清晰，论证有力
- 直接回应对方的看跌论点
- 保持专业和建设性的辩论态度
- 承认风险但强调机会大于风险

请构建有说服力的看涨投资论证。
"""
    
    async def process(self, state: AgentState, progress_tracker=None) -> AgentState:
        """执行看涨研究分析"""
        # 处理状态可能是字典或AgentState对象的情况
        user_query = state.get('user_query', '') if isinstance(state, dict) else state.user_query
        if not self.validate_state(state):
            return state
        
        try:
            # 获取辩论状态
            if isinstance(state, dict):
                investment_debate_state = state.get('investment_debate_state', {})
            else:
                investment_debate_state = state.investment_debate_state
            history = investment_debate_state.get("history", "")
            bull_history = investment_debate_state.get("bull_history", "")
            current_response = investment_debate_state.get("current_response", "")
            count = investment_debate_state.get("count", 0)
            
            # 构建看涨论证请求
            if count == 0:
                # 首轮发言
                analysis_request = f"""
基于所有可用的分析报告，请为用户问题 "{user_query}" 构建强有力的看涨投资案例。

重点关注：
1. 公司的核心竞争优势
2. 增长潜力和市场机会
3. 被低估的价值点
4. 技术面和基本面的积极信号
5. 具体的投资建议和目标价位

请提供详细的看涨论证。
"""
            else:
                # 回应看跌观点
                analysis_request = f"""
看跌研究员提出了以下观点：
{current_response}

请针对这些看跌观点进行有力的反驳，并进一步强化你的看涨论证。

反驳要点：
1. 指出看跌观点的局限性或偏见
2. 提供相反的证据和数据
3. 重新解释负面因素的影响
4. 强调被忽视的积极因素
5. 维护你的看涨立场

请提供有说服力的反驳和论证。
"""
            
            # 调用LLM进行分析
            analysis_result = await self.call_llm_with_context(state, analysis_request, progress_tracker)
            
            # 更新辩论状态
            new_investment_debate_state = {
                "history": history + f"\n\n【看涨研究员 第{count+1}轮】:\n{analysis_result}",
                "bull_history": bull_history + f"\n\n第{count+1}轮: {analysis_result}",
                "bear_history": investment_debate_state.get("bear_history", ""),
                "current_response": analysis_result,
                "count": count + 1
            }
            
            if isinstance(state, dict):
                state['investment_debate_state'] = new_investment_debate_state
            else:
                state.investment_debate_state = new_investment_debate_state
            
        except Exception as e:
            error_msg = f"看涨研究分析失败: {str(e)}"
            print(f"❌ {error_msg}")
            if isinstance(state, dict):
                if 'errors' not in state:
                    state['errors'] = []
                state['errors'].append(error_msg)
            else:
                state.add_error(error_msg)
        
        return state


class BearResearcher(BaseAgent):
    """看跌研究员 - 负责构建看跌论证"""
    
    def __init__(self, mcp_manager: MCPManager):
        super().__init__(
            agent_name="bear_researcher",
            mcp_manager=mcp_manager,
            role_description="看跌研究员，专门识别投资风险和构建看跌论证"
        )
    
    def get_system_prompt(self, state: AgentState) -> str:
        # 处理状态可能是字典或AgentState对象的情况
        user_query = state.get('user_query', '') if isinstance(state, dict) else state.user_query
        current_datetime = datetime.now()
        return f"""
你是一位专业的看跌研究员，负责为用户问题 "{user_query}" 识别投资风险和构建看跌论证。

当前时间：{current_datetime.strftime('%Y年%m月%d日 %H:%M:%S')} ({current_datetime.strftime('%A')})

你的职责：
1. 基于所有可用的分析报告，识别投资风险
2. 强调公司面临的挑战和负面因素
3. 质疑过度乐观的估值和预期
4. 反驳看涨观点，提供风险警示
5. 提供谨慎的投资建议

辩论要求：
- 基于客观数据和风险分析
- 逻辑严密，风险识别准确
- 直接回应对方的看涨论点
- 保持专业和客观的分析态度
- 强调风险管理的重要性

请构建有说服力的看跌风险论证。
"""
    
    async def process(self, state: AgentState, progress_tracker=None) -> AgentState:
        """执行看跌研究分析"""
        # 处理状态可能是字典或AgentState对象的情况
        user_query = state.get('user_query', '') if isinstance(state, dict) else state.user_query
        if not self.validate_state(state):
            return state
        
        try:
            # 获取辩论状态
            if isinstance(state, dict):
                investment_debate_state = state.get('investment_debate_state', {})
            else:
                investment_debate_state = state.investment_debate_state
            history = investment_debate_state.get("history", "")
            bear_history = investment_debate_state.get("bear_history", "")
            current_response = investment_debate_state.get("current_response", "")
            count = investment_debate_state.get("count", 0)
            
            # 构建看跌论证请求
            if not current_response or current_response.strip() == "":
                # 如果没有看涨观点，则进行独立的风险分析
                analysis_request = f"""
基于所有可用的分析报告，请为用户问题 "{user_query}" 进行专业的风险分析和构建看跌论证。

分析要点：
1. 识别主要投资风险因素
2. 强调潜在的负面因素
3. 质疑过度乐观的市场预期
4. 提供风险警示和谨慎建议
5. 构建完整的看跌投资案例

请提供专业的风险分析和看跌论证。
"""
            else:
                # 回应看涨观点
                analysis_request = f"""
看涨研究员提出了以下观点：
{current_response}

请针对这些看涨观点进行专业的风险分析和反驳，并构建看跌论证。

分析要点：
1. 识别看涨观点中的风险盲点
2. 强调被忽视的负面因素
3. 质疑过度乐观的假设
4. 提供风险警示和谨慎建议
5. 构建完整的看跌案例

请提供专业的风险分析和看跌论证。
"""
            
            # 调用LLM进行分析
            analysis_result = await self.call_llm_with_context(state, analysis_request, progress_tracker)
            
            # 更新辩论状态
            new_investment_debate_state = {
                "history": history + f"\n\n【看跌研究员 第{count+1}轮】:\n{analysis_result}",
                "bull_history": investment_debate_state.get("bull_history", ""),
                "bear_history": bear_history + f"\n\n第{count+1}轮: {analysis_result}",
                "current_response": analysis_result,
                "count": count + 1
            }
            
            if isinstance(state, dict):
                state['investment_debate_state'] = new_investment_debate_state
            else:
                state.investment_debate_state = new_investment_debate_state
            
        except Exception as e:
            error_msg = f"看跌研究分析失败: {str(e)}"
            print(f"❌ {error_msg}")
            if isinstance(state, dict):
                if 'errors' not in state:
                    state['errors'] = []
                state['errors'].append(error_msg)
            else:
                state.add_error(error_msg)
        
        return state