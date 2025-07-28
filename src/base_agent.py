import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage
from loguru import logger
from .agent_states import AgentState
from .mcp_manager import MCPManager


class BaseAgent(ABC):
    """基础智能体类 - 所有智能体的基类"""
    
    def __init__(self, agent_name: str, mcp_manager: MCPManager, role_description: str = ""):
        self.agent_name = agent_name
        self.mcp_manager = mcp_manager
        self.role_description = role_description
        
        # 获取LLM实例
        self.llm = mcp_manager.llm
        
        # 检查是否启用MCP工具
        self.mcp_enabled = mcp_manager.is_agent_mcp_enabled(agent_name)
        
        # 不在初始化时获取工具，而是在使用时动态获取
        self.available_tools = []
        
        # 延迟创建智能体实例，等到MCP工具初始化完成后再创建
        self.agent = None
        
        logger.info(f"智能体 {agent_name} 初始化完成，MCP工具: {'启用' if self.mcp_enabled else '禁用'}")
    
    def ensure_agent_created(self):
        """确保智能体实例已创建（在MCP工具初始化后调用）"""
        if self.agent is None:
            self.agent = self.mcp_manager.create_agent_with_tools(self.agent_name)
            logger.info(f"智能体 {self.agent_name} 实例创建完成")
    
    @abstractmethod
    def get_system_prompt(self, state: AgentState) -> str:
        """获取系统提示词 - 子类必须实现"""
        pass
    
    @abstractmethod
    async def process(self, state: AgentState) -> AgentState:
        """处理智能体逻辑 - 子类必须实现"""
        pass
    
    def build_context_prompt(self, state: AgentState) -> str:
        """构建上下文提示词"""
        context_parts = []
        
        # 添加当前日期时间信息
        current_datetime = datetime.now()
        context_parts.append(f"当前日期时间: {current_datetime.strftime('%Y年%m月%d日 %H:%M:%S')} ({current_datetime.strftime('%A')})")
        
        # 处理状态可能是字典或AgentState对象的情况
        if isinstance(state, dict):
            user_query = state.get('user_query', '')
            investment_plan = state.get('investment_plan', '')
            trader_investment_plan = state.get('trader_investment_plan', '')
            
            # 获取报告
            market_report = state.get('market_report', '')
            sentiment_report = state.get('sentiment_report', '')
            news_report = state.get('news_report', '')
            fundamentals_report = state.get('fundamentals_report', '')
            
            reports = {
                "market_report": market_report,
                "sentiment_report": sentiment_report,
                "news_report": news_report,
                "fundamentals_report": fundamentals_report
            }
            
            # 获取辩论历史
            investment_debate_state = state.get('investment_debate_state', {})
            risk_debate_state = state.get('risk_debate_state', {})
            investment_history = investment_debate_state.get("history", "")
            risk_history = risk_debate_state.get("history", "")
            
            debate_summary = ""
            if investment_history:
                debate_summary += f"投资辩论历史:\n{investment_history}\n\n"
            if risk_history:
                debate_summary += f"风险管理辩论历史:\n{risk_history}\n\n"
            debate_summary = debate_summary.strip()
        else:
            user_query = state.user_query
            investment_plan = state.investment_plan
            trader_investment_plan = state.trader_investment_plan
            reports = state.get_all_reports()
            debate_summary = state.get_debate_summary()
        
        # 基础信息
        context_parts.append(f"用户问题: {user_query}")
        # 交易日期和市场类型信息现在通过当前日期时间提供
        
        # 分析师报告
        for report_name, report_content in reports.items():
            if report_content.strip():
                context_parts.append(f"{report_name}: {report_content}")
        
        # 辩论历史
        if debate_summary:
            context_parts.append(f"辩论历史:\n{debate_summary}")
        
        # 投资计划
        if investment_plan:
            context_parts.append(f"研究经理决策: {investment_plan}")
        
        # 交易员计划
        if trader_investment_plan:
            context_parts.append(f"交易员计划: {trader_investment_plan}")
        
        return "\n\n".join(context_parts)
    

    
    async def call_llm_with_context(self, state: AgentState, user_message: str, progress_tracker=None) -> str:
        """使用上下文调用LLM"""
        try:
            # 确保智能体实例已创建
            self.ensure_agent_created()
            
            # 记录开始执行
            if progress_tracker:
                progress_tracker.log_agent_start(self.agent_name, {
                    "user_message_length": len(user_message),
                    "mcp_enabled": self.mcp_enabled,
                    "available_tools_count": len(self.available_tools) if self.available_tools else 0
                })
            
            # 详细日志：开始分析
            logger.info(f"🤖 [{self.agent_name}] 开始分析...")
            logger.info(f"📝 [{self.agent_name}] 分析请求: {user_message[:100]}{'...' if len(user_message) > 100 else ''}")
            
            # 构建系统提示和上下文（不包含工具描述，因为智能体已经预先绑定了工具）
            system_prompt = self.get_system_prompt(state)
            context_prompt = self.build_context_prompt(state)
            
            # 将系统和上下文组合成一个系统消息
            system_level_prompt = f"""{system_prompt}

{context_prompt}"""

            # 动态获取当前可用工具
            current_tools = self.mcp_manager.get_tools_for_agent(self.agent_name) if self.mcp_enabled else []

            # 详细日志：显示工具状态
            if self.mcp_enabled and current_tools:
                logger.info(f"🔧 [{self.agent_name}] 可用工具: {[tool.name for tool in current_tools]}")
            else:
                logger.info(f"🔧 [{self.agent_name}] 无外部工具，使用纯LLM分析")

            # 如果启用了MCP工具，使用智能体（参考test.py的简洁方式）
            if self.mcp_enabled and current_tools:
                logger.info(f"⚡ [{self.agent_name}] 正在调用LLM（带MCP工具）...")
                
                # 构建简单的消息列表，让框架自动处理工具绑定
                messages = [
                    {"role": "system", "content": system_level_prompt},
                    {"role": "user", "content": user_message}
                ]

                response = await self.agent.ainvoke({
                    "messages": messages
                })
                
                # 提取最终回复
                messages = response.get("messages", [])
                if messages:
                    # 通常最后一个消息是最终的AI回复
                    final_message = messages[-1]
                    if hasattr(final_message, 'content'):
                        result = final_message.content
                    else:
                        result = "(无法提取内容)"
                else:
                    result = "(未收到消息)"
            else:
                # 如果没有启用MCP工具，直接调用LLM
                logger.info(f"⚡ [{self.agent_name}] 正在调用LLM（无工具）...")
                full_prompt = f"""{system_level_prompt}\n\n用户请求: {user_message}"""
                response = await self.llm.ainvoke([HumanMessage(content=full_prompt)])
                result = response.content

                
                # 检查最终响应中是否包含工具调用
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    logger.info(f"🔧 [{self.agent_name}] LLM响应包含 {len(response.tool_calls)} 个新的工具调用")
                    for i, tool_call in enumerate(response.tool_calls, 1):
                        tool_name = tool_call.get('name', 'unknown')
                        tool_args = tool_call.get('args', {})
                        logger.info(f"🆕 [{self.agent_name}] 新工具调用 {i}: {tool_name}")
                        logger.info(f"📝 [{self.agent_name}] 新工具参数: {tool_args}")
                
                # 记录工具使用
                if isinstance(state, dict):
                    if 'agent_executions' not in state:
                        state['agent_executions'] = []
                    state['agent_executions'].append({
                        'agent_name': self.agent_name,
                        'action': "LLM调用(带MCP工具)",
                        'result': result,  # 保留完整结果
                        'mcp_used': True
                    })
                else:
                    state.add_agent_execution(
                        agent_name=self.agent_name,
                        action="LLM调用(带MCP工具)",
                        result=result,  # 保留完整结果
                        mcp_used=True
                    )

                
                # 记录执行
                if isinstance(state, dict):
                    if 'agent_executions' not in state:
                        state['agent_executions'] = []
                    state['agent_executions'].append({
                        'agent_name': self.agent_name,
                        'action': "LLM调用(无工具)",
                        'result': result,  # 保留完整结果
                        'mcp_used': False
                    })
                else:
                    state.add_agent_execution(
                        agent_name=self.agent_name,
                        action="LLM调用(无工具)",
                        result=result,  # 保留完整结果
                        mcp_used=False
                    )
            
            # 详细日志：显示完整的分析结果
            logger.info(f"✅ [{self.agent_name}] 分析完成")
            logger.info(f"📊 [{self.agent_name}] 分析结果长度: {len(result)} 字符")
            logger.info(f"📋 [{self.agent_name}] ===== 分析结果 =====")
            # 将长文本分段显示，每段最多500字符
            content_lines = result.split('\n')
            current_chunk = ""
            for line in content_lines:
                if len(current_chunk + line) > 500:
                    if current_chunk:
                        logger.info(f"📄 [{self.agent_name}] {current_chunk}")
                    current_chunk = line
                else:
                    current_chunk += ("\n" if current_chunk else "") + line
            if current_chunk:
                logger.info(f"📄 [{self.agent_name}] {current_chunk}")
            logger.info(f"📋 [{self.agent_name}] ===== 分析结果结束 =====")
            
            # 记录执行完成
            if progress_tracker:
                progress_tracker.log_agent_complete(self.agent_name, result, {
                    "result_length": len(result),
                    "success": True,
                    "mcp_used": self.mcp_enabled and self.available_tools
                })
            
            return result
            
        except Exception as e:
            error_msg = f"LLM调用失败: {str(e)}"
            logger.error(f"智能体 {self.agent_name} - {error_msg}")
            
            # 记录执行失败
            if progress_tracker:
                progress_tracker.log_agent_complete(self.agent_name, error_msg, {
                    "error": error_msg,
                    "success": False
                })
            
            if isinstance(state, dict):
                if 'errors' not in state:
                    state['errors'] = []
                state['errors'].append(f"{self.agent_name}: {error_msg}")
            else:
                state.add_error(f"{self.agent_name}: {error_msg}")
            return f"抱歉，处理过程中出现错误: {error_msg}"
    
    async def call_mcp_tool(self, state: AgentState, tool_name: str, tool_args: Dict) -> Any:
        """调用MCP工具"""
        if not self.mcp_enabled:
            error_msg = f"智能体 {self.agent_name} 未启用MCP工具"
            logger.warning(error_msg)
            if isinstance(state, dict):
                if 'warnings' not in state:
                    state['warnings'] = []
                state['warnings'].append(error_msg)
            else:
                state.add_warning(error_msg)
            return {"error": error_msg}
        
        try:
            logger.info(f"🔧 [{self.agent_name}] 准备调用工具: {tool_name}")
            logger.info(f"📝 [{self.agent_name}] 工具参数: {tool_args}")
            
            result = await self.mcp_manager.call_tool_for_agent(
                agent_name=self.agent_name,
                tool_name=tool_name,
                tool_args=tool_args
            )
            
            # 记录工具调用
            if isinstance(state, dict):
                if 'mcp_tool_calls' not in state:
                    state['mcp_tool_calls'] = []
                state['mcp_tool_calls'].append({
                    'agent_name': self.agent_name,
                    'tool_name': tool_name,
                    'tool_args': tool_args,
                    'tool_result': result
                })
            else:
                state.add_mcp_tool_call(
                    agent_name=self.agent_name,
                    tool_name=tool_name,
                    tool_args=tool_args,
                    tool_result=result
                )
            
            # 显示详细的工具调用结果
            result_str = str(result)
            logger.info(f"✅ [{self.agent_name}] 工具 {tool_name} 调用成功")
            logger.info(f"📏 [{self.agent_name}] 工具返回结果长度: {len(result_str)} 字符")
            
            # 分段显示完整结果
            if len(result_str) > 1000:
                logger.info(f"📊 [{self.agent_name}] ===== 工具 {tool_name} 返回结果 =====")
                # 将长文本分段显示，每段最多800字符
                for i in range(0, len(result_str), 800):
                    chunk = result_str[i:i+800]
                    chunk_num = i // 800 + 1
                    logger.info(f"📄 [{self.agent_name}] 结果片段 {chunk_num}: {chunk}")
                logger.info(f"📊 [{self.agent_name}] ===== 工具结果结束 =====")
            else:
                logger.info(f"📊 [{self.agent_name}] 工具返回完整结果: {result_str}")
            
            return result
            
        except Exception as e:
            error_msg = f"MCP工具调用失败: {str(e)}"
            logger.error(f"❌ [{self.agent_name}] {error_msg}")
            if isinstance(state, dict):
                if 'errors' not in state:
                    state['errors'] = []
                state['errors'].append(f"{self.agent_name}: {error_msg}")
            else:
                state.add_error(f"{self.agent_name}: {error_msg}")
            return {"error": error_msg}
    
    def get_agent_info(self) -> Dict[str, Any]:
        """获取智能体信息"""
        return {
            "name": self.agent_name,
            "role_description": self.role_description,
            "mcp_enabled": self.mcp_enabled,
            "available_tools_count": len(self.available_tools),
            "available_tools": [tool.name for tool in self.available_tools] if self.available_tools else []
        }
    
    def validate_state(self, state: AgentState) -> bool:
        """验证状态有效性"""
        # 处理状态可能是字典或AgentState对象的情况
        if isinstance(state, dict):
            user_query = state.get('user_query', '')
            if not user_query:
                if 'errors' not in state:
                    state['errors'] = []
                state['errors'].append(f"{self.agent_name}: 缺少用户查询信息")
                return False
        else:
            if not state.user_query:
                state.add_error(f"{self.agent_name}: 缺少用户查询信息")
                return False
        
        return True
    
    def format_output(self, content: str, state: AgentState) -> str:
        """格式化输出内容"""
        from datetime import datetime
        
        # 处理状态可能是字典或AgentState对象的情况
        if isinstance(state, dict):
            user_query = state.get('user_query', '')
        else:
            user_query = state.user_query
        
        formatted_content = f"""
=== {self.agent_name} 分析报告 ===
时间: {datetime.now().strftime('%Y%m%d %H:%M:%S')}
用户问题: {user_query}
MCP工具: {'启用' if self.mcp_enabled else '禁用'}

{content}

=== 报告结束 ===
"""
        return formatted_content.strip()