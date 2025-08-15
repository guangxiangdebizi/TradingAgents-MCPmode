import os
import asyncio
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

from .agent_states import AgentState
from .mcp_manager import MCPManager
from .progress_tracker import ProgressTracker
from .agents.analysts import (
    CompanyOverviewAnalyst, MarketAnalyst, SentimentAnalyst, NewsAnalyst, FundamentalsAnalyst, ShareholderAnalyst, ProductAnalyst
)
from .agents.researchers import BullResearcher, BearResearcher
from .agents.managers import ResearchManager, Trader
from .agents.risk_management import (
    AggressiveRiskAnalyst, SafeRiskAnalyst, NeutralRiskAnalyst, RiskManager
)


class WorkflowOrchestrator:
    """工作流编排器 - 管理整个智能体交互流程"""
    
    def __init__(self, config_file: str = "mcp_config.json"):
        # 加载环境变量
        load_dotenv()
        
        # 初始化MCP管理器
        self.mcp_manager = MCPManager(config_file)
        
        # 初始化进度管理器
        self.progress_manager = None
        
        # 初始化所有智能体
        self.agents = self._initialize_agents()
        
        # 工作流配置
        self.max_debate_rounds = int(os.getenv("MAX_DEBATE_ROUNDS", "3"))
        self.max_risk_debate_rounds = int(os.getenv("MAX_RISK_DEBATE_ROUNDS", "2"))
        self.debug_mode = os.getenv("DEBUG_MODE", "true").lower() == "true"
        self.verbose_logging = os.getenv("VERBOSE_LOGGING", "true").lower() == "true"
        
        # 创建状态图
        self.workflow = self._create_workflow()
        
        # 本轮启用的智能体集合（为空表示默认启用全部）
        self.active_agents: Set[str] = set()
        
        print("🚀 工作流编排器初始化完成")
    
    def _initialize_agents(self) -> Dict[str, Any]:
        """初始化所有智能体"""
        agents = {
            # 分析师团队
            "company_overview_analyst": CompanyOverviewAnalyst(self.mcp_manager),
            "market_analyst": MarketAnalyst(self.mcp_manager),
            "sentiment_analyst": SentimentAnalyst(self.mcp_manager),
            "news_analyst": NewsAnalyst(self.mcp_manager),
            "fundamentals_analyst": FundamentalsAnalyst(self.mcp_manager),
            "shareholder_analyst": ShareholderAnalyst(self.mcp_manager),
            "product_analyst": ProductAnalyst(self.mcp_manager),
            
            # 研究员团队
            "bull_researcher": BullResearcher(self.mcp_manager),
            "bear_researcher": BearResearcher(self.mcp_manager),
            
            # 管理层
            "research_manager": ResearchManager(self.mcp_manager),
            "trader": Trader(self.mcp_manager),
            
            # 风险管理团队
            "aggressive_risk_analyst": AggressiveRiskAnalyst(self.mcp_manager),
            "safe_risk_analyst": SafeRiskAnalyst(self.mcp_manager),
            "neutral_risk_analyst": NeutralRiskAnalyst(self.mcp_manager),
            "risk_manager": RiskManager(self.mcp_manager)
        }
        
        print(f"初始化了 {len(agents)} 个智能体")
        return agents
    
    def _create_workflow(self) -> StateGraph:
        """创建工作流状态图"""
        workflow = StateGraph(AgentState)
        
        # 添加节点
        workflow.add_node("company_overview_analyst", self._company_overview_analyst_node)
        workflow.add_node("market_analyst", self._market_analyst_node)
        workflow.add_node("sentiment_analyst", self._sentiment_analyst_node)
        workflow.add_node("news_analyst", self._news_analyst_node)
        workflow.add_node("fundamentals_analyst", self._fundamentals_analyst_node)
        workflow.add_node("shareholder_analyst", self._shareholder_analyst_node)
        workflow.add_node("product_analyst", self._product_analyst_node)
        # 新增：分析师并行聚合节点
        workflow.add_node("analysts_parallel", self._analysts_parallel_node)
        
        workflow.add_node("bull_researcher", self._bull_researcher_node)
        workflow.add_node("bear_researcher", self._bear_researcher_node)
        workflow.add_node("research_manager", self._research_manager_node)
        
        workflow.add_node("trader", self._trader_node)
        
        workflow.add_node("aggressive_risk_analyst", self._aggressive_risk_analyst_node)
        workflow.add_node("safe_risk_analyst", self._safe_risk_analyst_node)
        workflow.add_node("neutral_risk_analyst", self._neutral_risk_analyst_node)
        workflow.add_node("risk_manager", self._risk_manager_node)
        
        # 设置入口点
        workflow.set_entry_point("company_overview_analyst")
        
        # 添加边（定义流程）
        # 第零阶段：公司概述分析
        # 概述后进入分析师并行节点（内部并发执行6个分析师）
        workflow.add_edge("company_overview_analyst", "analysts_parallel")
        
        # 第一阶段：分析师并行（在单独节点中完成），完成后进入研究员辩论
        workflow.add_edge("analysts_parallel", "bull_researcher")
        
        # 第二阶段：研究员辩论（由并行节点汇聚后进入）
        workflow.add_conditional_edges(
            "bull_researcher",
            self._should_continue_investment_debate,
            {
                "bear_researcher": "bear_researcher",
                "research_manager": "research_manager"
            }
        )
        workflow.add_conditional_edges(
            "bear_researcher",
            self._should_continue_investment_debate,
            {
                "bull_researcher": "bull_researcher",
                "research_manager": "research_manager"
            }
        )
        
        # 第三阶段：交易员决策
        workflow.add_edge("research_manager", "trader")
        
        # 第四阶段：风险管理辩论
        workflow.add_edge("trader", "aggressive_risk_analyst")
        workflow.add_conditional_edges(
            "aggressive_risk_analyst",
            self._should_continue_risk_debate,
            {
                "safe_risk_analyst": "safe_risk_analyst",
                "risk_manager": "risk_manager"
            }
        )
        workflow.add_conditional_edges(
            "safe_risk_analyst",
            self._should_continue_risk_debate,
            {
                "neutral_risk_analyst": "neutral_risk_analyst",
                "risk_manager": "risk_manager"
            }
        )
        workflow.add_conditional_edges(
            "neutral_risk_analyst",
            self._should_continue_risk_debate,
            {
                "aggressive_risk_analyst": "aggressive_risk_analyst",
                "risk_manager": "risk_manager"
            }
        )
        
        # 结束
        workflow.add_edge("risk_manager", END)
        
        return workflow.compile()
    
    # 节点处理函数
    async def _company_overview_analyst_node(self, state: AgentState) -> AgentState:
        """公司概述分析师节点"""
        print("🏢 第0阶段：公司概述分析师")
        self._check_cancel()
        if not self._is_active("company_overview_analyst"):
            self._skip_agent("company_overview_analyst")
            self._check_cancel()
            return state
        # 不再在这里调用start_agent，让BaseAgent自己处理
        result = await self.agents["company_overview_analyst"].process(state, self.progress_manager)
        self._check_cancel()
        return result

    async def _market_analyst_node(self, state: AgentState) -> AgentState:
        """市场分析师节点"""
        print("🔍 第1阶段：市场分析师")
        self._check_cancel()
        if not self._is_active("market_analyst"):
            self._skip_agent("market_analyst")
            self._check_cancel()
            return state
        # 不再在这里调用start_agent，让BaseAgent自己处理
        result = await self.agents["market_analyst"].process(state, self.progress_manager)
        self._check_cancel()
        return result
    
    async def _sentiment_analyst_node(self, state: AgentState) -> AgentState:
        """情绪分析师节点"""
        print("😊 情绪分析师")
        self._check_cancel()
        if not self._is_active("sentiment_analyst"):
            self._skip_agent("sentiment_analyst")
            self._check_cancel()
            return state
        # 不再在这里调用start_agent，让BaseAgent自己处理
        result = await self.agents["sentiment_analyst"].process(state, self.progress_manager)
        self._check_cancel()
        return result

    async def _news_analyst_node(self, state: AgentState) -> AgentState:
        """新闻分析师节点"""
        print("📰 新闻分析师")
        self._check_cancel()
        if not self._is_active("news_analyst"):
            self._skip_agent("news_analyst")
            self._check_cancel()
            return state
        # 不再在这里调用start_agent，让BaseAgent自己处理
        result = await self.agents["news_analyst"].process(state, self.progress_manager)
        self._check_cancel()
        return result

    async def _fundamentals_analyst_node(self, state: AgentState) -> AgentState:
        """基本面分析师节点"""
        print("📊 基本面分析师")
        self._check_cancel()
        if not self._is_active("fundamentals_analyst"):
            self._skip_agent("fundamentals_analyst")
            self._check_cancel()
            return state
        # 不再在这里调用start_agent，让BaseAgent自己处理
        result = await self.agents["fundamentals_analyst"].process(state, self.progress_manager)
        self._check_cancel()
        return result

    async def _shareholder_analyst_node(self, state: AgentState) -> AgentState:
        """股东分析师节点"""
        print("👥 股东分析师")
        self._check_cancel()
        if not self._is_active("shareholder_analyst"):
            self._skip_agent("shareholder_analyst")
            self._check_cancel()
            return state
        # 不再在这里调用start_agent，让BaseAgent自己处理
        result = await self.agents["shareholder_analyst"].process(state, self.progress_manager)
        self._check_cancel()
        return result

    async def _product_analyst_node(self, state: AgentState) -> AgentState:
        """产品分析师节点"""
        print("🏭 产品分析师")
        self._check_cancel()
        if not self._is_active("product_analyst"):
            self._skip_agent("product_analyst")
            self._check_cancel()
            return state
        # 不再在这里调用start_agent，让BaseAgent自己处理
        result = await self.agents["product_analyst"].process(state, self.progress_manager)
        self._check_cancel()
        return result

    async def _analysts_parallel_node(self, state: AgentState) -> AgentState:
        """分析师并行节点：并发执行6个分析师并合并结果"""
        import copy
        from asyncio import gather, create_task, wait, FIRST_COMPLETED

        analyst_names = [
            name for name in [
                "market_analyst",
                "sentiment_analyst",
                "news_analyst",
                "fundamentals_analyst",
                "shareholder_analyst",
                "product_analyst",
            ] if self._is_active(name)
        ]

        # 为避免并发写 state 产生竞态，对每个任务使用深拷贝
        self._check_cancel()
        tasks = []
        for name in analyst_names:
            state_copy = copy.deepcopy(state)
            tasks.append(create_task(self.agents[name].process(state_copy, self.progress_manager)))

        if not tasks:
            # 全部禁用，直接返回
            return state

        # 协作式取消：轮询检查取消标记，必要时取消剩余任务
        pending = set(tasks)
        done_results = []
        while pending:
            self._check_cancel()
            done, pending = await wait(pending, timeout=0.3, return_when=FIRST_COMPLETED)
            for d in done:
                done_results.append(await d)
        results = done_results

        # 将各自字段安全合并回主state（兼容字典或对象）
        def setter(k: str, v: Any):
            if isinstance(state, dict):
                state[k] = v
            else:
                setattr(state, k, v)

        def getter_from(res, k: str) -> str:
            if isinstance(res, dict):
                return res.get(k, "")
            return getattr(res, k, "")

        # 需要合并的字段列表
        report_keys = [
            "market_report",
            "sentiment_report",
            "news_report",
            "fundamentals_report",
            "shareholder_report",
            "product_report",
        ]

        # 合并报告字段（后到者覆盖为空的不覆盖）
        for key in report_keys:
            for res in results:
                val = getter_from(res, key)
                if isinstance(val, str) and val.strip():
                    setter(key, val)

        # 合并执行/工具调用历史（如果存在）
        hist_keys = ["agent_execution_history", "mcp_tool_calls", "warnings", "errors"]
        for hkey in hist_keys:
            merged: List[Any] = []
            for res in results:
                part = getter_from(res, hkey)
                if isinstance(part, list):
                    merged.extend(part)
            if merged:
                setter(hkey, merged)

        return state

    async def _bull_researcher_node(self, state: AgentState) -> AgentState:
        """多头研究员节点"""
        print("📈 多头研究员")
        self._check_cancel()
        if not self._is_active("bull_researcher"):
            # 跳过但推进一轮，避免条件边返回未映射的节点
            self._increment_investment_round(state)
            self._skip_agent("bull_researcher")
            self._check_cancel()
            return state
        result = await self.agents["bull_researcher"].process(state, self.progress_manager)
        self._check_cancel()
        return result

    async def _bear_researcher_node(self, state: AgentState) -> AgentState:
        """空头研究员节点"""
        print("📉 空头研究员")
        self._check_cancel()
        if not self._is_active("bear_researcher"):
            # 跳过但推进一轮
            self._increment_investment_round(state)
            self._skip_agent("bear_researcher")
            self._check_cancel()
            return state
        result = await self.agents["bear_researcher"].process(state, self.progress_manager)
        self._check_cancel()
        return result

    async def _research_manager_node(self, state: AgentState) -> AgentState:
        """研究经理节点"""
        print("🧑‍💼 研究经理")
        self._check_cancel()
        if not self._is_active("research_manager"):
            self._skip_agent("research_manager")
            self._check_cancel()
            return state
        result = await self.agents["research_manager"].process(state, self.progress_manager)
        self._check_cancel()
        return result

    async def _trader_node(self, state: AgentState) -> AgentState:
        """交易员节点"""
        print("👨‍💻 交易员")
        self._check_cancel()
        if not self._is_active("trader"):
            self._skip_agent("trader")
            self._check_cancel()
            return state
        result = await self.agents["trader"].process(state, self.progress_manager)
        self._check_cancel()
        return result

    async def _aggressive_risk_analyst_node(self, state: AgentState) -> AgentState:
        """激进风险分析师节点"""
        print("🔥 激进风险分析师")
        self._check_cancel()
        if not self._is_active("aggressive_risk_analyst"):
            self._increment_risk_round(state)
            self._skip_agent("aggressive_risk_analyst")
            self._check_cancel()
            return state
        result = await self.agents["aggressive_risk_analyst"].process(state, self.progress_manager)
        self._check_cancel()
        return result

    async def _safe_risk_analyst_node(self, state: AgentState) -> AgentState:
        """保守风险分析师节点"""
        print("🛡️ 保守风险分析师")
        self._check_cancel()
        if not self._is_active("safe_risk_analyst"):
            self._increment_risk_round(state)
            self._skip_agent("safe_risk_analyst")
            self._check_cancel()
            return state
        result = await self.agents["safe_risk_analyst"].process(state, self.progress_manager)
        self._check_cancel()
        return result

    async def _neutral_risk_analyst_node(self, state: AgentState) -> AgentState:
        """中立风险分析师节点"""
        print("⚖️ 中立风险分析师")
        self._check_cancel()
        if not self._is_active("neutral_risk_analyst"):
            self._increment_risk_round(state)
            self._skip_agent("neutral_risk_analyst")
            self._check_cancel()
            return state
        result = await self.agents["neutral_risk_analyst"].process(state, self.progress_manager)
        self._check_cancel()
        return result

    async def _risk_manager_node(self, state: AgentState) -> AgentState:
        """风险管理器节点"""
        print("🛡️ 风险管理器")
        self._check_cancel()
        if not self._is_active("risk_manager"):
            self._skip_agent("risk_manager")
            self._check_cancel()
            return state
        result = await self.agents["risk_manager"].process(state, self.progress_manager)
        self._check_cancel()
        return result

    # 条件判断函数
    def _should_continue_investment_debate(self, state) -> str:
        """判断是否继续投资辩论"""
        if isinstance(state, dict):
            investment_debate_state = state.get('investment_debate_state', {})
        else:
            investment_debate_state = state.investment_debate_state
        count = investment_debate_state.get("count", 0)
        
        # 计算当前轮数：每2次发言为1轮
        current_round = (count + 1) // 2 + ((count + 1) % 2)  # 向上取整
        
        print(f"🤔 投资辩论判断: 当前发言次数={count}, 当前轮数={current_round}, 最大轮数={self.max_debate_rounds}")
        
        if current_round <= self.max_debate_rounds:
            # 根据当前次数决定下一个发言者
            if count % 2 == 1:  # 奇数次，看跌研究员发言
                print(f"📉 继续投资辩论 - 看跌研究员 (第{current_round}轮)")
                return "bear_researcher"
            else:  # 偶数次，看涨研究员发言
                print(f"📈 继续投资辩论 - 看涨研究员 (第{current_round}轮)")
                return "bull_researcher"
        else:
            print(f"🏁 投资辩论结束({self.max_debate_rounds}轮完成)，进入研究经理")
            return "research_manager"
    
    def _should_continue_risk_debate(self, state) -> str:
        """判断是否继续风险辩论"""
        if isinstance(state, dict):
            risk_debate_state = state.get('risk_debate_state', {})
        else:
            risk_debate_state = state.risk_debate_state
        count = risk_debate_state.get("count", 0)
        
        # 计算当前轮数：每3次发言为1轮
        current_round = (count + 1) // 3 + ((count + 1) % 3 > 0)  # 向上取整
        
        print(f"🤔 风险辩论判断: 当前发言次数={count}, 当前轮数={current_round}, 最大轮数={self.max_risk_debate_rounds}")
        
        if current_round <= self.max_risk_debate_rounds:
            # 风险辩论轮次：激进 -> 保守 -> 中性 -> 激进...
            remainder = count % 3
            if remainder == 1:
                print(f"🛡️ 继续风险辩论 - 保守风险分析师 (第{current_round}轮)")
                return "safe_risk_analyst"
            elif remainder == 2:
                print(f"⚖️ 继续风险辩论 - 中性风险分析师 (第{current_round}轮)")
                return "neutral_risk_analyst"
            else:
                print(f"⚡ 继续风险辩论 - 激进风险分析师 (第{current_round}轮)")
                return "aggressive_risk_analyst"
        else:
            print(f"🏁 风险辩论结束({self.max_risk_debate_rounds}轮完成)，进入风险经理")
            return "risk_manager"
    
    def _check_cancel(self):
        """检查是否需要取消分析"""
        if self.cancel_checker and callable(self.cancel_checker):
            if self.cancel_checker():
                raise asyncio.CancelledError("分析已被用户取消")

    async def initialize(self) -> bool:
        """初始化MCP连接"""
        try:
            success = await self.mcp_manager.initialize()
            if success:
                print("✅ 工作流编排器初始化成功")
            else:
                print("⚠️ MCP连接失败，将在无工具模式下运行")
            return success
        except Exception as e:
            print(f"❌ 工作流编排器初始化失败: {e}")
            return False

    async def run_analysis(self, user_query: str, cancel_checker=None, active_agents: Optional[List[str]] = None) -> AgentState:
        """运行完整的交易分析流程"""
        print("🚀 智能交易分析系统启动")
        print(f"📝 用户查询: {user_query}")
        
        # 存储取消检查器
        self.cancel_checker = cancel_checker
        # 配置本轮启用的智能体集合
        if active_agents is None or len(active_agents) == 0:
            self.active_agents = set(self.agents.keys())
        else:
            # 只保留已存在的合法agent名
            self.active_agents = set([a for a in active_agents if a in self.agents])
        
        # 初始化进度跟踪器
        self.progress_manager = ProgressTracker()
        self.progress_manager.update_user_query(user_query)
        # 写入本轮启用的智能体列表到会话JSON
        try:
            self.progress_manager.set_active_agents(sorted(list(self.active_agents)))
        except Exception:
            pass
        self.progress_manager.log_workflow_start({"user_query": user_query})
        
        # 初始化状态
        initial_state = AgentState(
            user_query=user_query,
            investment_debate_state={"count": 0, "history": "", "bull_history": "", "bear_history": "", "current_response": ""},
            risk_debate_state={"count": 0, "history": "", "aggressive_history": "", "safe_history": "", "neutral_history": "", 
                             "current_aggressive_response": "", "current_safe_response": "", "current_neutral_response": ""},
            messages=[]
        )
        
        try:
            # 检查取消状态
            self._check_cancel()
            
            # 运行工作流
            workflow_result = await self.workflow.ainvoke(initial_state)
            
            # LangGraph返回字典，需要转换为AgentState对象
            if isinstance(workflow_result, dict):
                # 创建新的AgentState对象并复制数据
                final_state = AgentState(
                    user_query=workflow_result.get('user_query', user_query),
                    investment_debate_state=workflow_result.get('investment_debate_state', {}),
                    risk_debate_state=workflow_result.get('risk_debate_state', {}),
                    messages=workflow_result.get('messages', []),
                    market_report=workflow_result.get('market_report', ''),
                    sentiment_report=workflow_result.get('sentiment_report', ''),
                    news_report=workflow_result.get('news_report', ''),
                    fundamentals_report=workflow_result.get('fundamentals_report', ''),
                    shareholder_report=workflow_result.get('shareholder_report', ''),  # 添加这一行
                    investment_plan=workflow_result.get('investment_plan', ''),
                    trader_investment_plan=workflow_result.get('trader_investment_plan', ''),
                    final_trade_decision=workflow_result.get('final_trade_decision', ''),
                    errors=workflow_result.get('errors', []),
                    warnings=workflow_result.get('warnings', []),
                    agent_execution_history=workflow_result.get('agent_execution_history', []),
                    mcp_tool_calls=workflow_result.get('mcp_tool_calls', [])
                )
            else:
                final_state = workflow_result
            
            print("✅ 分析流程完成")
            
            # 记录最终结果到进度跟踪器
            if self.progress_manager:
                final_results = {
                    "final_state": self._state_to_dict(final_state),
                    "completion_time": datetime.now().isoformat(),
                    "success": True
                }
                self.progress_manager.set_final_results(final_results)
                self.progress_manager.log_workflow_completion({"success": True})
            
            if self.verbose_logging:
                self._log_analysis_summary(final_state)
            
            return final_state
            
        except asyncio.CancelledError as e:
            print(f"⚠️ 分析流程已取消: {e}")
            
            # 记录取消到进度跟踪器
            if self.progress_manager:
                try:
                    self.progress_manager.add_warning("分析已被用户取消")
                    # 将会话状态标记为取消
                    self.progress_manager.session_data["status"] = "cancelled"
                    self.progress_manager._save_json()
                except Exception:
                    pass
                try:
                    self.progress_manager.log_workflow_completion({"success": False, "cancelled": True})
                except Exception:
                    pass
            
            # 安全地添加取消信息
            try:
                if hasattr(initial_state, 'add_warning'):
                    initial_state.add_warning("分析已被用户取消")
                elif isinstance(initial_state, dict):
                    if 'warnings' not in initial_state:
                        initial_state['warnings'] = []
                    initial_state['warnings'].append("分析已被用户取消")
            except Exception:
                pass
            return initial_state
            
        except Exception as e:
            print(f"❌ 分析流程失败: {e}")
            
            # 记录错误到进度跟踪器
            if self.progress_manager:
                error_results = {
                    "error": str(e),
                    "completion_time": datetime.now().isoformat(),
                    "success": False
                }
                self.progress_manager.add_error(str(e))
                self.progress_manager.log_workflow_completion({"success": False})
            
            # 安全地添加错误信息
            try:
                if hasattr(initial_state, 'add_error'):
                    initial_state.add_error(f"工作流执行失败: {str(e)}")
                elif isinstance(initial_state, dict):
                    if 'errors' not in initial_state:
                        initial_state['errors'] = []
                    initial_state['errors'].append(f"工作流执行失败: {str(e)}")
            except Exception:
                pass
            return initial_state
    
    def _state_to_dict(self, state):
        """将AgentState对象转换为字典格式"""
        if isinstance(state, dict):
            return state
        
        # 将AgentState对象的属性转换为字典
        state_dict = {}
        for attr in dir(state):
            if not attr.startswith('_') and not callable(getattr(state, attr)):
                try:
                    value = getattr(state, attr)
                    # 确保值是可序列化的
                    if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                        state_dict[attr] = value
                    else:
                        state_dict[attr] = str(value)
                except Exception:
                    continue
        return state_dict
    
    def _log_analysis_summary(self, state):
        """记录分析摘要"""
        print("\n" + "="*50)
        print("分析流程摘要")
        print("="*50)
        
        # 处理状态可能是字典或AgentState对象的情况
        if isinstance(state, dict):
            user_query = state.get('user_query', '')
            agent_execution_history = state.get('agent_execution_history', [])
            mcp_tool_calls = state.get('mcp_tool_calls', [])
            investment_debate_state = state.get('investment_debate_state', {})
            risk_debate_state = state.get('risk_debate_state', {})
            errors = state.get('errors', [])
            warnings = state.get('warnings', [])
        else:
            user_query = state.user_query
            agent_execution_history = state.agent_execution_history
            mcp_tool_calls = state.mcp_tool_calls
            investment_debate_state = state.investment_debate_state
            risk_debate_state = state.risk_debate_state
            errors = state.errors
            warnings = state.warnings
        
        print(f"用户问题: {user_query}")
        
        # 智能体执行统计
        mcp_enabled_count = len([h for h in agent_execution_history if h.get("mcp_used", False)])
        total_executions = len(agent_execution_history)
        print(f"智能体执行次数: {total_executions}")
        print(f"MCP工具使用次数: {mcp_enabled_count}")
        print(f"MCP工具调用次数: {len(mcp_tool_calls)}")
        
        # 辩论统计
        investment_rounds = investment_debate_state.get("count", 0)
        risk_rounds = risk_debate_state.get("count", 0)
        print(f"投资辩论轮次: {investment_rounds}")
        print(f"风险辩论轮次: {risk_rounds}")
        
        # 错误和警告
        if errors:
            print(f"错误数量: {len(errors)}")
            for error in errors:
                print(f"  - {error}")
        
        if warnings:
            print(f"警告数量: {len(warnings)}")
            for warning in warnings:
                print(f"  - {warning}")
        
        print("="*50)
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """获取工作流信息"""
        return {
            "agents_count": len(self.agents),
            "max_debate_rounds": self.max_debate_rounds,
            "max_risk_debate_rounds": self.max_risk_debate_rounds,
            "debug_mode": self.debug_mode,
            "verbose_logging": self.verbose_logging,
            "mcp_tools_info": self.mcp_manager.get_tools_info(),
            "agents_info": {name: agent.get_agent_info() for name, agent in self.agents.items()}
        }
    
    def get_agent_permissions(self) -> Dict[str, bool]:
        """获取智能体MCP权限配置"""
        return self.mcp_manager.agent_permissions
    
    def get_enabled_agents(self) -> List[str]:
        """获取启用MCP工具的智能体列表"""
        return self.mcp_manager.get_enabled_agents()
    
    async def close(self):
        """关闭资源"""
        await self.mcp_manager.close()
        print("工作流编排器已关闭")

    # ===== 本轮启用控制 & 辅助方法 =====
    def set_debate_rounds(self, investment_rounds: Optional[int] = None, risk_rounds: Optional[int] = None):
        """设置本轮辩论的最大轮次（立即生效，用于下一次 run_analysis）。"""
        if isinstance(investment_rounds, int) and investment_rounds >= 0:
            old_inv = self.max_debate_rounds
            self.max_debate_rounds = investment_rounds
            print(f"🌀 投资辩论轮次已更新: {old_inv} → {investment_rounds}")
        if isinstance(risk_rounds, int) and risk_rounds >= 0:
            old_risk = self.max_risk_debate_rounds
            self.max_risk_debate_rounds = risk_rounds
            print(f"🌀 风险辩论轮次已更新: {old_risk} → {risk_rounds}")

    def set_active_agents(self, active_agents: List[str]):
        """外部设置本轮启用的智能体集合"""
        if not active_agents:
            self.active_agents = set(self.agents.keys())
        else:
            self.active_agents = set([a for a in active_agents if a in self.agents])

    def _is_active(self, agent_name: str) -> bool:
        return (not self.active_agents) or (agent_name in self.active_agents)

    def _skip_agent(self, agent_name: str):
        try:
            if self.progress_manager:
                self.progress_manager.add_warning(f"智能体已禁用，本轮跳过", agent_name=agent_name)
        except Exception:
            pass

    def _increment_investment_round(self, state: AgentState):
        try:
            if isinstance(state, dict):
                inv = state.get('investment_debate_state', {})
                inv['count'] = int(inv.get('count', 0)) + 1
                state['investment_debate_state'] = inv
            else:
                inv = getattr(state, 'investment_debate_state', {}) or {}
                inv['count'] = int(inv.get('count', 0)) + 1
                state.investment_debate_state = inv
        except Exception:
            pass

        try:
            if self.progress_manager:
                self.progress_manager.update_debate_state("investment", {
                    "count": (state.get('investment_debate_state', {}).get('count') if isinstance(state, dict) else state.investment_debate_state.get('count', 0))
                })
        except Exception:
            pass

    def _increment_risk_round(self, state: AgentState):
        try:
            if isinstance(state, dict):
                rsk = state.get('risk_debate_state', {})
                rsk['count'] = int(rsk.get('count', 0)) + 1
                state['risk_debate_state'] = rsk
            else:
                rsk = getattr(state, 'risk_debate_state', {}) or {}
                rsk['count'] = int(rsk.get('count', 0)) + 1
                state.risk_debate_state = rsk
        except Exception:
            pass

        try:
            if self.progress_manager:
                self.progress_manager.update_debate_state("risk", {
                    "count": (state.get('risk_debate_state', {}).get('count') if isinstance(state, dict) else state.risk_debate_state.get('count', 0))
                })
        except Exception:
            pass