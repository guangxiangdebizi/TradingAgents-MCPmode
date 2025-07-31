from typing import Dict, Any

from ..base_agent import BaseAgent
from ..agent_states import AgentState
from ..mcp_manager import MCPManager
from datetime import datetime

class MarketAnalyst(BaseAgent):
    """市场分析师 - 负责整体市场趋势分析"""
    
    def __init__(self, mcp_manager: MCPManager):
        super().__init__(
            agent_name="market_analyst",
            mcp_manager=mcp_manager,
            role_description="市场分析师，专注于整体市场趋势、技术指标和宏观经济分析"
        )
    
    def get_system_prompt(self, state: AgentState) -> str:
        current_datetime = datetime.now()
        return f"""
你是一位资深的市场分析师，专门负责分析股票市场的整体趋势和技术指标。

如果用户不指定分析的时间，请你根据当前时间：{current_datetime.strftime('%Y年%m月%d日 %H:%M:%S')} ({current_datetime.strftime('%A')})
往前调用几个月的数据用来回答差不多即可。

重要工作原则：
- 必须使用可用的外部工具获取最新的实时数据
- 不要依赖过时的历史知识，要基于当前数据分析
- 在开始分析前，先使用工具获取相关股票的最新价格、技术指标等数据

你的职责包括：
1. 使用工具获取目标股票的最新技术指标（移动平均线、RSI、MACD等）
2. 通过工具评估整体市场环境和趋势
3. 基于实时数据分析交易量和价格行为模式
4. 提供基于最新技术分析的市场观点
5. 识别关键支撑位和阻力位

分析要求：
- 必须先使用工具获取客观的技术数据
- 提供具体的数据支撑
- 根据股票代码判断市场类型和特点
- 结合宏观经济环境
- 给出明确的技术面观点（看涨/看跌/中性）

请务必使用工具获取实时数据后再进行专业、客观的市场技术分析报告。
"""
    
    async def process(self, state: AgentState, progress_tracker=None) -> AgentState:
        """执行市场分析"""
        # 处理状态可能是字典或AgentState对象的情况
        user_query = state.get('user_query', '') if isinstance(state, dict) else state.user_query
        print(f"🔍 开始执行市场分析 - 用户问题: {user_query}")
        
        if not self.validate_state(state):
            return state
        
        try:
            # 构建分析请求
            analysis_request = f"""
请对用户问题 "{user_query}" 进行全面的市场技术分析。

"""
            
            # 调用LLM进行分析
            analysis_result = await self.call_llm_with_context(state, analysis_request, progress_tracker)
            
            # 格式化并保存结果
            formatted_result = self.format_output(analysis_result, state)
            if isinstance(state, dict):
                state['market_report'] = formatted_result
            else:
                state.market_report = formatted_result
            
            print("✅ 市场分析完成")
            
        except Exception as e:
            error_msg = f"市场分析失败: {str(e)}"
            print(f"❌ {error_msg}")
            if isinstance(state, dict):
                if 'errors' not in state:
                    state['errors'] = []
                state['errors'].append(error_msg)
                state['market_report'] = f"市场分析出现错误: {error_msg}"
            else:
                state.add_error(error_msg)
                state.market_report = f"市场分析出现错误: {error_msg}"
        
        return state


class SentimentAnalyst(BaseAgent):
    """情绪分析师 - 负责社交媒体和市场情绪分析"""
    
    def __init__(self, mcp_manager: MCPManager):
        super().__init__(
            agent_name="sentiment_analyst",
            mcp_manager=mcp_manager,
            role_description="情绪分析师，专注于社交媒体情绪、投资者心理和市场氛围分析"
        )
    
    def get_system_prompt(self, state: AgentState) -> str:
        current_datetime = datetime.now()
        return f"""
你是一位专业的市场情绪分析师，专门分析社交媒体、新闻评论和投资者情绪。

当前时间：{current_datetime.strftime('%Y年%m月%d日 %H:%M:%S')} ({current_datetime.strftime('%A')})

重要工作原则：
- 必须使用可用的外部工具获取最新的市场情绪数据
- 不要依赖过时的历史知识，要基于当前实时数据分析
- 在开始分析前，先使用工具获取相关的市场数据和情绪指标

你的职责包括：
1. 使用工具获取社交媒体上关于目标股票的最新讨论情绪
2. 通过工具评估投资者心理和市场氛围
3. 基于实时数据识别情绪驱动的市场机会或风险
4. 分析散户和机构投资者的当前情绪差异
5. 提供基于最新情绪分析的投资洞察

分析要求：
- 必须先使用工具获取各种情绪指标
- 区分短期情绪波动和长期趋势
- 根据股票代码判断市场投资者的特点
- 识别情绪极端点（过度乐观/悲观）
- 给出情绪面的投资建议

请务必使用工具获取实时情绪数据后再提供专业的市场情绪分析报告。
"""
    
    async def process(self, state: AgentState, progress_tracker=None) -> AgentState:
        """执行情绪分析"""
        # 处理状态可能是字典或AgentState对象的情况
        user_query = state.get('user_query', '') if isinstance(state, dict) else state.user_query
        print(f"😊 开始执行情绪分析 - 用户问题: {user_query}")
        
        if not self.validate_state(state):
            return state
        
        try:
            analysis_request = f"""
请对用户问题 "{user_query}" 进行全面的市场情绪分析。

"""
            
            analysis_result = await self.call_llm_with_context(state, analysis_request, progress_tracker)
            formatted_result = self.format_output(analysis_result, state)
            if isinstance(state, dict):
                state['sentiment_report'] = formatted_result
            else:
                state.sentiment_report = formatted_result
            
            print("✅ 情绪分析完成")
            
        except Exception as e:
            error_msg = f"情绪分析失败: {str(e)}"
            print(f"❌ {error_msg}")
            if isinstance(state, dict):
                if 'errors' not in state:
                    state['errors'] = []
                state['errors'].append(error_msg)
                state['sentiment_report'] = f"情绪分析出现错误: {error_msg}"
            else:
                state.add_error(error_msg)
                state.sentiment_report = f"情绪分析出现错误: {error_msg}"
        
        return state


class NewsAnalyst(BaseAgent):
    """新闻分析师 - 负责新闻事件和信息面分析"""
    
    def __init__(self, mcp_manager: MCPManager):
        super().__init__(
            agent_name="news_analyst",
            mcp_manager=mcp_manager,
            role_description="新闻分析师，专注于新闻事件、政策变化和信息面分析"
        )
    
    def get_system_prompt(self, state: AgentState) -> str:
        current_datetime = datetime.now()
        return f"""
你是一位专业的新闻分析师，专门分析影响股票价格的新闻事件和信息。

当前时间：{current_datetime.strftime('%Y年%m月%d日 %H:%M:%S')} ({current_datetime.strftime('%A')})

重要工作原则：
- 必须使用可用的外部工具获取最新的新闻信息和市场数据
- 不要依赖过时的历史知识，要基于当前最新信息分析
- 在开始分析前，先使用工具搜索相关的最新新闻和市场动态

你的职责包括：
1. 使用工具搜索与目标股票相关的最新新闻事件
2. 通过工具获取最新政策变化信息并评估对股票的影响
3. 基于实时信息识别重大事件的市场影响程度
4. 使用工具分析行业动态和竞争格局变化
5. 提供基于最新信息面数据的投资判断

分析要求：
- 必须先使用工具获取时效性强的重要新闻
- 区分短期事件影响和长期趋势
- 根据股票代码判断相应市场的政策环境
- 评估新闻的可信度和影响范围
- 给出信息面的投资建议

请务必使用工具获取最新新闻信息后再提供专业的新闻信息分析报告。
"""
    
    async def process(self, state: AgentState, progress_tracker=None) -> AgentState:
        """执行新闻分析"""
        # 处理状态可能是字典或AgentState对象的情况
        user_query = state.get('user_query', '') if isinstance(state, dict) else state.user_query
        print(f"📰 开始执行新闻分析 - 用户问题: {user_query}")
        
        if not self.validate_state(state):
            return state
        
        try:
            analysis_request = f"""
请对用户问题 "{user_query}" 进行全面的新闻信息分析。

"""
            
            analysis_result = await self.call_llm_with_context(state, analysis_request, progress_tracker)
            formatted_result = self.format_output(analysis_result, state)
            if isinstance(state, dict):
                state['news_report'] = formatted_result
            else:
                state.news_report = formatted_result
            
            print("✅ 新闻分析完成")
            
        except Exception as e:
            error_msg = f"新闻分析失败: {str(e)}"
            print(f"❌ {error_msg}")
            if isinstance(state, dict):
                if 'errors' not in state:
                    state['errors'] = []
                state['errors'].append(error_msg)
                state['news_report'] = f"新闻分析出现错误: {error_msg}"
            else:
                state.add_error(error_msg)
                state.news_report = f"新闻分析出现错误: {error_msg}"
        
        return state


class FundamentalsAnalyst(BaseAgent):
    """基本面分析师 - 负责公司财务和基本面分析"""
    
    def __init__(self, mcp_manager: MCPManager):
        super().__init__(
            agent_name="fundamentals_analyst",
            mcp_manager=mcp_manager,
            role_description="基本面分析师，专注于公司财务数据、估值和基本面分析"
        )
    
    def get_system_prompt(self, state: AgentState) -> str:
        current_datetime = datetime.now()
        return f"""
你是一位资深的基本面分析师，专门分析公司的财务状况和内在价值。

当前时间：{current_datetime.strftime('%Y年%m月%d日 %H:%M:%S')} ({current_datetime.strftime('%A')})

重要工作原则：
- 必须使用可用的外部工具获取最新的财务数据和公司信息
- 不要依赖过时的历史知识，要基于当前最新财务数据分析
- 在开始分析前，先使用工具获取相关公司的最新财务报表和指标
请你获取公司最近两个完整财政年度（{current_datetime.year-1}年和{current_datetime.year}年）的最新财报数据，包括：
  • 年度和季度收入报表
  • 利润表和净利润数据
  • 资产负债表
  • 现金流量表
  • 关键财务指标和比率
如果{current_datetime.year}年完整年报未发布，请获取最新可用的季度报告和{current_datetime.year-1}年年报。

你的职责包括：
1. 使用工具获取公司的最新财务报表和关键财务指标
2. 通过工具查询公司的盈利能力和成长性数据
3. 使用工具获取估值数据进行分析（PE、PB、DCF等）
4. 基于实时信息分析公司的竞争优势和护城河
5. 提供基于最新基本面数据的投资建议

分析要求：
- 必须先使用工具获取最新的财务数据
- 与同行业公司进行对比分析
- 根据股票代码判断相应市场的估值特点
- 评估公司的长期投资价值
- 给出明确的基本面评级

请务必使用工具获取最新财务数据后再提供专业的基本面分析报告。
"""
    
    async def process(self, state: AgentState, progress_tracker=None) -> AgentState:
        """执行基本面分析"""
        # 处理状态可能是字典或AgentState对象的情况
        user_query = state.get('user_query', '') if isinstance(state, dict) else state.user_query
        print(f"📊 开始执行基本面分析 - 用户问题: {user_query}")
        
        if not self.validate_state(state):
            return state
        
        try:
            analysis_request = f"""
请对用户问题 "{user_query}" 进行全面的基本面分析。

重要提示：请务必使用您可用的外部工具来获取最新的财务数据和公司信息，不要仅凭已有知识进行分析。

"""
            
            analysis_result = await self.call_llm_with_context(state, analysis_request, progress_tracker)
            formatted_result = self.format_output(analysis_result, state)
            if isinstance(state, dict):
                state['fundamentals_report'] = formatted_result
            else:
                state.fundamentals_report = formatted_result
            
            print("✅ 基本面分析完成")
            
        except Exception as e:
            error_msg = f"基本面分析失败: {str(e)}"
            print(f"❌ {error_msg}")
            if isinstance(state, dict):
                if 'errors' not in state:
                    state['errors'] = []
                state['errors'].append(error_msg)
                state['fundamentals_report'] = f"基本面分析出现错误: {error_msg}"
            else:
                state.add_error(error_msg)
                state.fundamentals_report = f"基本面分析出现错误: {error_msg}"
        
        return state


class ShareholderAnalyst(BaseAgent):
    """股东分析师 - 负责股东结构和大宗交易分析"""
    
    def __init__(self, mcp_manager: MCPManager):
        super().__init__(
            agent_name="shareholder_analyst",
            mcp_manager=mcp_manager,
            role_description="股东分析师，专注于股东结构变化、前十大股东、流通股东和大宗交易分析"
        )
    
    def get_system_prompt(self, state: AgentState) -> str:
        current_datetime = datetime.now()
        return f"""
你是一位资深的股东结构分析师，专门分析股东构成和大宗交易情况，从股权结构角度挖掘投资线索。

当前时间：{current_datetime.strftime('%Y年%m月%d日 %H:%M:%S')} ({current_datetime.strftime('%A')})

重要工作原则：
- 必须使用可用的外部工具获取最新的股东数据和大宗交易信息
- 不要依赖过时的历史知识，要基于当前最新数据分析
- 在开始分析前，先使用工具获取相关公司的最新股东信息

你的职责包括：
1. 使用工具获取股东户数变化趋势数据（过去6-12个月）
2. 通过工具查询最新的前十大股东信息和变化情况
3. 获取前十大流通股东的最新数据和变动
4. 搜索和分析近期的大宗交易记录
5. 从股权结构变化中挖掘投资机会和风险信号

分析要求：
- 必须先使用工具获取客观的股丝数据
- 关注股东户数的增减趋势及其含义
- 分析主要股东的增减持行为
- 特别关注机构投资者的动向
- 分析大宗交易的频率、价格和规模
- 根据股票代码判断相应市场的特点
- 给出明确的股权结构分析结论（看涨/看跌/中性）

重点关注事项：
- 股东户数减少通常意味着筹码集中，可能是看涨信号
- 股东户数增加可能意味着分散持有，需谨慎分析
- 机构投资者增持通常是正面信号
- 大宗交易的价格相对于市价的折价/溢价情况
- 内幕人士的买卖行为

请务必使用工具获取实时数据后再提供专业、深入的股东结构分析报告。
"""
    
    async def process(self, state: AgentState, progress_tracker=None) -> AgentState:
        """执行股东结构分析"""
        # 处理状态可能是字典或AgentState对象的情况
        user_query = state.get('user_query', '') if isinstance(state, dict) else state.user_query
        print(f"📊 开始执行股东结构分析 - 用户问题: {user_query}")
        
        if not self.validate_state(state):
            return state
        
        try:
            # 构建分析请求
            analysis_request = f"""
请对用户问题 "{user_query}" 进行全面的股东结构和大宗交易分析。

"""
            
            # 调用LLM进行分析
            analysis_result = await self.call_llm_with_context(state, analysis_request, progress_tracker)
            
            # 格式化并保存结果
            formatted_result = self.format_output(analysis_result, state)
            if isinstance(state, dict):
                state['shareholder_report'] = formatted_result
            else:
                state.shareholder_report = formatted_result
            
            print("✅ 股东结构分析完成")
            
        except Exception as e:
            error_msg = f"股东结构分析失败: {str(e)}"
            print(f"❌ {error_msg}")
            if isinstance(state, dict):
                if 'errors' not in state:
                    state['errors'] = []
                state['errors'].append(error_msg)
                state['shareholder_report'] = f"股东结构分析出现错误: {error_msg}"
            else:
                state.add_error(error_msg)
                state.shareholder_report = f"股丝结构分析出现错误: {error_msg}"
        
        return state