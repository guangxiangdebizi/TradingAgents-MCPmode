from typing import Dict, Any
from loguru import logger
from ..base_agent import BaseAgent
from ..agent_states import AgentState
from ..mcp_manager import MCPManager


class AggressiveRiskAnalyst(BaseAgent):
    """激进风险分析师 - 倾向于承担更高风险以获取更高回报"""
    
    def __init__(self, mcp_manager: MCPManager):
        super().__init__(
            agent_name="aggressive_risk_analyst",
            mcp_manager=mcp_manager,
            role_description="激进风险分析师，倾向于承担较高风险以追求更高回报"
        )
    
    def get_system_prompt(self, state: AgentState) -> str:
        return f"""
你是一位激进的风险分析师，倾向于承担较高风险以追求更高的投资回报。

你的观点特征：
1. 相信高风险高回报的投资哲学
2. 愿意承担市场波动以获取超额收益
3. 关注成长性和爆发性机会
4. 对市场时机把握有信心
5. 倾向于积极的投资策略

风险评估角度：
- 强调机会成本的风险
- 关注错失投资机会的损失
- 相信通过主动管理可以控制风险
- 重视长期增长潜力
- 接受短期波动换取长期收益

辩论要求：
- 积极倡导投资机会
- 反驳过度保守的观点
- 强调风险可控性
- 提供积极的风险管理建议

请从激进风险管理的角度进行分析。
"""
    
    async def process(self, state: AgentState, progress_tracker=None) -> AgentState:
        """执行激进风险分析"""
        # 处理状态可能是字典或AgentState对象的情况
        user_query = state.get('user_query', '') if isinstance(state, dict) else state.user_query
        logger.info(f"激进风险分析师开始分析 - 用户问题: {user_query}")
        
        if not self.validate_state(state):
            return state
        
        try:
            # 获取风险辩论状态
            if isinstance(state, dict):
                risk_debate_state = state.get('risk_debate_state', {})
                trader_investment_plan = state.get('trader_investment_plan', '')
            else:
                risk_debate_state = state.risk_debate_state
                trader_investment_plan = state.trader_investment_plan
            history = risk_debate_state.get("history", "")
            aggressive_history = risk_debate_state.get("aggressive_history", "")
            current_safe_response = risk_debate_state.get("current_safe_response", "")
            current_neutral_response = risk_debate_state.get("current_neutral_response", "")
            count = risk_debate_state.get("count", 0)
            
            # 构建激进风险分析请求
            if count == 0:
                # 首轮发言
                analysis_request = f"""
基于交易员的投资计划，请从激进风险管理的角度进行分析。

交易员计划：
{trader_investment_plan}

分析要点：
1. 识别高回报投资机会
2. 评估风险可控性
3. 强调积极投资的必要性
4. 提供激进的风险管理策略
5. 反驳过度保守的担忧

请提供激进的风险分析观点。
"""
            else:
                # 回应其他风险分析师
                analysis_request = f"""
保守风险分析师的观点：
{current_safe_response}

中性风险分析师的观点：
{current_neutral_response}

请针对这些观点进行反驳，并坚持你的激进风险管理立场。

反驳要点：
1. 指出过度保守的机会成本
2. 强调风险的可管理性
3. 提供积极的风险控制方案
4. 维护激进投资策略的合理性

请提供有力的反驳和论证。
"""
            
            # 调用LLM进行分析
            analysis_result = await self.call_llm_with_context(state, analysis_request, progress_tracker)
            
            # 更新风险辩论状态
            new_risk_debate_state = {
                "history": history + f"\n\n【激进风险分析师 第{count+1}轮】:\n{analysis_result}",
                "aggressive_history": aggressive_history + f"\n\n第{count+1}轮: {analysis_result}",
                "safe_history": risk_debate_state.get("safe_history", ""),
                "neutral_history": risk_debate_state.get("neutral_history", ""),
                "current_aggressive_response": analysis_result,
                "current_safe_response": current_safe_response,
                "current_neutral_response": current_neutral_response,
                "count": count + 1
            }
            
            if isinstance(state, dict):
                state['risk_debate_state'] = new_risk_debate_state
            else:
                state.risk_debate_state = new_risk_debate_state
            
            logger.info(f"激进风险分析师完成第{count+1}轮分析")
            
        except Exception as e:
            error_msg = f"激进风险分析失败: {str(e)}"
            logger.error(error_msg)
            if isinstance(state, dict):
                if 'errors' not in state:
                    state['errors'] = []
                state['errors'].append(error_msg)
            else:
                state.add_error(error_msg)
        
        return state


class SafeRiskAnalyst(BaseAgent):
    """保守风险分析师 - 强调风险控制和资本保护"""
    
    def __init__(self, mcp_manager: MCPManager):
        super().__init__(
            agent_name="safe_risk_analyst",
            mcp_manager=mcp_manager,
            role_description="保守风险分析师，强调风险控制和资本保护"
        )
    
    def get_system_prompt(self, state: AgentState) -> str:
        return f"""
你是一位保守的风险分析师，优先考虑资本保护和风险控制。

你的观点特征：
1. 资本保护优先于收益追求
2. 强调下行风险的控制
3. 偏好稳定和可预测的投资
4. 对市场不确定性保持警惕
5. 倾向于谨慎的投资策略

风险评估角度：
- 重点关注潜在损失
- 强调不确定性和黑天鹅事件
- 质疑过度乐观的假设
- 重视流动性和安全边际
- 偏好分散投资和对冲策略

辩论要求：
- 强调风险控制的重要性
- 质疑激进投资策略
- 提供保守的风险管理建议
- 警示潜在的投资陷阱

请从保守风险管理的角度进行分析。
"""
    
    async def process(self, state: AgentState, progress_tracker=None) -> AgentState:
        """执行保守风险分析"""
        # 处理状态可能是字典或AgentState对象的情况
        user_query = state.get('user_query', '') if isinstance(state, dict) else state.user_query
        logger.info(f"保守风险分析师开始分析 - 用户问题: {user_query}")
        
        if not self.validate_state(state):
            return state
        
        try:
            # 获取风险辩论状态
            if isinstance(state, dict):
                risk_debate_state = state.get('risk_debate_state', {})
            else:
                risk_debate_state = state.risk_debate_state
            history = risk_debate_state.get("history", "")
            safe_history = risk_debate_state.get("safe_history", "")
            current_aggressive_response = risk_debate_state.get("current_aggressive_response", "")
            current_neutral_response = risk_debate_state.get("current_neutral_response", "")
            count = risk_debate_state.get("count", 0)
            
            # 构建保守风险分析请求
            analysis_request = f"""
激进风险分析师的观点：
{current_aggressive_response}

中性风险分析师的观点：
{current_neutral_response}

请从保守风险管理的角度进行分析和反驳。

分析要点：
1. 识别被忽视的风险因素
2. 质疑过度乐观的假设
3. 强调资本保护的重要性
4. 提供保守的风险控制建议
5. 警示潜在的投资陷阱

请提供保守的风险分析观点。
"""
            
            # 调用LLM进行分析
            analysis_result = await self.call_llm_with_context(state, analysis_request, progress_tracker)
            
            # 更新风险辩论状态
            new_risk_debate_state = {
                "history": history + f"\n\n【保守风险分析师 第{count+1}轮】:\n{analysis_result}",
                "aggressive_history": risk_debate_state.get("aggressive_history", ""),
                "safe_history": safe_history + f"\n\n第{count+1}轮: {analysis_result}",
                "neutral_history": risk_debate_state.get("neutral_history", ""),
                "current_aggressive_response": current_aggressive_response,
                "current_safe_response": analysis_result,
                "current_neutral_response": current_neutral_response,
                "count": count + 1
            }
            
            if isinstance(state, dict):
                state['risk_debate_state'] = new_risk_debate_state
            else:
                state.risk_debate_state = new_risk_debate_state
            
            logger.info(f"保守风险分析师完成第{count+1}轮分析")
            
        except Exception as e:
            error_msg = f"保守风险分析失败: {str(e)}"
            logger.error(error_msg)
            if isinstance(state, dict):
                if 'errors' not in state:
                    state['errors'] = []
                state['errors'].append(error_msg)
            else:
                state.add_error(error_msg)
        
        return state


class NeutralRiskAnalyst(BaseAgent):
    """中性风险分析师 - 平衡风险和收益的考量"""
    
    def __init__(self, mcp_manager: MCPManager):
        super().__init__(
            agent_name="neutral_risk_analyst",
            mcp_manager=mcp_manager,
            role_description="中性风险分析师，平衡风险和收益的考量"
        )
    
    def get_system_prompt(self, state: AgentState) -> str:
        return f"""
你是一位中性的风险分析师，致力于平衡风险和收益的考量。

你的观点特征：
1. 客观平衡风险和收益
2. 基于数据和概率进行分析
3. 不偏向激进或保守立场
4. 重视风险调整后的收益
5. 倾向于理性和均衡的策略

风险评估角度：
- 量化风险收益比
- 考虑多种情景和概率
- 平衡短期和长期考量
- 重视投资组合的整体效应
- 基于历史数据和统计分析

辩论要求：
- 提供客观的风险评估
- 平衡激进和保守观点
- 基于数据进行论证
- 提供中性的风险管理建议

请从中性风险管理的角度进行分析。
"""
    
    async def process(self, state: AgentState, progress_tracker=None) -> AgentState:
        """执行中性风险分析"""
        # 处理状态可能是字典或AgentState对象的情况
        user_query = state.get('user_query', '') if isinstance(state, dict) else state.user_query
        logger.info(f"中性风险分析师开始分析 - 用户问题: {user_query}")
        
        if not self.validate_state(state):
            return state
        
        try:
            # 获取风险辩论状态
            if isinstance(state, dict):
                risk_debate_state = state.get('risk_debate_state', {})
            else:
                risk_debate_state = state.risk_debate_state
            history = risk_debate_state.get("history", "")
            neutral_history = risk_debate_state.get("neutral_history", "")
            current_aggressive_response = risk_debate_state.get("current_aggressive_response", "")
            current_safe_response = risk_debate_state.get("current_safe_response", "")
            count = risk_debate_state.get("count", 0)
            
            # 构建中性风险分析请求
            analysis_request = f"""
激进风险分析师的观点：
{current_aggressive_response}

保守风险分析师的观点：
{current_safe_response}

请从中性风险管理的角度进行客观分析。

分析要点：
1. 客观评估双方观点的合理性
2. 量化风险收益比
3. 提供平衡的风险评估
4. 基于数据和概率进行分析
5. 给出中性的风险管理建议

请提供客观中性的风险分析。
"""
            
            # 调用LLM进行分析
            analysis_result = await self.call_llm_with_context(state, analysis_request, progress_tracker)
            
            # 更新风险辩论状态
            new_risk_debate_state = {
                "history": history + f"\n\n【中性风险分析师 第{count+1}轮】:\n{analysis_result}",
                "aggressive_history": risk_debate_state.get("aggressive_history", ""),
                "safe_history": risk_debate_state.get("safe_history", ""),
                "neutral_history": neutral_history + f"\n\n第{count+1}轮: {analysis_result}",
                "current_aggressive_response": current_aggressive_response,
                "current_safe_response": current_safe_response,
                "current_neutral_response": analysis_result,
                "count": count + 1
            }
            
            if isinstance(state, dict):
                state['risk_debate_state'] = new_risk_debate_state
            else:
                state.risk_debate_state = new_risk_debate_state
            
            logger.info(f"中性风险分析师完成第{count+1}轮分析")
            
        except Exception as e:
            error_msg = f"中性风险分析失败: {str(e)}"
            logger.error(error_msg)
            if isinstance(state, dict):
                if 'errors' not in state:
                    state['errors'] = []
                state['errors'].append(error_msg)
            else:
                state.add_error(error_msg)
        
        return state


class RiskManager(BaseAgent):
    """风险经理 - 负责评估风险辩论结果并做出最终风险决策"""
    
    def __init__(self, mcp_manager: MCPManager):
        super().__init__(
            agent_name="risk_manager",
            mcp_manager=mcp_manager,
            role_description="风险经理，负责评估风险辩论结果并做出最终风险管理决策"
        )
    
    def get_system_prompt(self, state: AgentState) -> str:
        return f"""
你是一位资深的风险管理经理，负责评估风险团队的辩论结果并做出最终的风险管理决策。

你的职责：
1. 综合评估激进、保守、中性三方的风险观点
2. 基于交易员计划制定风险控制措施
3. 平衡风险控制和收益追求
4. 做出最终的交易执行决策
5. 提供具体的风险管理指导

决策考量：
- 风险承受能力和投资目标
- 市场环境和不确定性
- 投资组合的整体风险
- 监管要求和合规性
- 流动性和操作风险

最终决策：
- 批准交易计划（可能需要调整）
- 拒绝交易计划
- 要求修改风险控制措施
- 设定额外的监控要求

请做出专业的风险管理决策。
"""
    
    async def process(self, state: AgentState, progress_tracker=None) -> AgentState:
        """执行最终风险决策"""
        # 处理状态可能是字典或AgentState对象的情况
        user_query = state.get('user_query', '') if isinstance(state, dict) else state.user_query
        logger.info(f"风险经理开始最终决策 - 用户问题: {user_query}")
        
        if not self.validate_state(state):
            return state
        
        try:
            # 获取完整风险辩论历史
            if isinstance(state, dict):
                risk_debate_state = state.get('risk_debate_state', {})
                trader_investment_plan = state.get('trader_investment_plan', '')
            else:
                risk_debate_state = state.risk_debate_state
                trader_investment_plan = state.trader_investment_plan
            history = risk_debate_state.get("history", "")
            
            # 构建最终决策请求
            decision_request = f"""
作为风险管理经理，请基于以下信息对用户问题 "{user_query}" 做出最终的风险管理决策。

交易员计划：
{trader_investment_plan}

风险团队辩论历史：
{history}

决策要求：
1. 综合评估三方风险观点的合理性
2. 评估交易计划的风险水平
3. 制定具体的风险控制措施
4. 做出最终的交易执行决策
5. 提供风险监控和应急预案

请提供最终的风险管理决策。
"""
            
            # 调用LLM进行最终决策
            decision_result = await self.call_llm_with_context(state, decision_request, progress_tracker)
            
            # 格式化并保存最终决策
            formatted_decision = self.format_output(decision_result, state)
            if isinstance(state, dict):
                state['final_trade_decision'] = formatted_decision
            else:
                state.final_trade_decision = formatted_decision
            
            logger.info("风险经理完成最终决策")
            
        except Exception as e:
            error_msg = f"最终风险决策失败: {str(e)}"
            logger.error(error_msg)
            if isinstance(state, dict):
                if 'errors' not in state:
                    state['errors'] = []
                state['errors'].append(error_msg)
                state['final_trade_decision'] = f"最终风险决策出现错误: {error_msg}"
            else:
                state.add_error(error_msg)
                state.final_trade_decision = f"最终风险决策出现错误: {error_msg}"
        
        return state