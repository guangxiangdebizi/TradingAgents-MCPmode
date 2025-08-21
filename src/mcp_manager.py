import os
import json
import asyncio
import time
from typing import Dict, Any, List, Optional
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
# from loguru import logger  # 已移除


class MCPManager:
    """MCP工具管理器 - 负责MCP连接、工具发现和权限控制"""
    
    def __init__(self, config_file: str = "mcp_config.json"):
        # 加载环境变量
        load_dotenv()
        
        # 加载配置文件
        self.config = self._load_config(config_file)
        
        # 初始化大模型
        self.llm = self._init_llm()
        
        # MCP客户端和工具
        self.client: Optional[MultiServerMCPClient] = None
        self.tools: List = []
        self.tools_by_server: Dict[str, List] = {}
        
        # 智能体权限配置
        self.agent_permissions = self._load_agent_permissions()
        
        # 对话历史
        self.conversation_history: List[Dict[str, str]] = []
        
        print("MCP管理器初始化完成")
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"配置文件加载成功: {config_file}")
            return config
        except FileNotFoundError:
            print(f"⚠️ 配置文件未找到: {config_file}，使用默认配置")
            return {"servers": {}, "agent_permissions": {}}
        except json.JSONDecodeError as e:
            print(f"❌ 配置文件格式错误: {e}")
            return {"servers": {}, "agent_permissions": {}}
    
    def _init_llm(self) -> ChatOpenAI:
        """初始化大模型 - 从环境变量加载配置"""
        # 大模型配置只从环境变量加载
        api_key = os.getenv("LLM_API_KEY", "your_api_key_here")
        base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        model_name = os.getenv("LLM_MODEL", "gpt-4")
        temperature = float(os.getenv("LLM_TEMPERATURE", "0.1"))
        max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4000"))
        print(f"[LLM INIT] Loaded from env -> LLM_MODEL={model_name}, LLM_TEMPERATURE={temperature}, LLM_MAX_TOKENS={max_tokens}, LLM_BASE_URL={base_url}")
        
        llm = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens
        )
        try:
            print(
                f"[LLM INIT] ChatOpenAI config -> model={getattr(llm, 'model', getattr(llm, 'model_name', None))}, "
                f"temperature={getattr(llm, 'temperature', None)}, max_tokens={getattr(llm, 'max_tokens', None)}"
            )
        except Exception as _:
            pass
        
        print(f"大模型初始化完成: {model_name} @ {base_url}")
        return llm
    
    def _load_agent_permissions(self) -> Dict[str, bool]:
        """从环境变量加载智能体MCP工具使用权限"""
        permissions = {}
        
        # 从环境变量加载权限配置
        env_mapping = {
            "company_overview_analyst": "COMPANY_OVERVIEW_ANALYST_MCP_ENABLED",
            "market_analyst": "MARKET_ANALYST_MCP_ENABLED",
            "sentiment_analyst": "SENTIMENT_ANALYST_MCP_ENABLED",
            "news_analyst": "NEWS_ANALYST_MCP_ENABLED",
            "fundamentals_analyst": "FUNDAMENTALS_ANALYST_MCP_ENABLED",
            "shareholder_analyst": "SHAREHOLDER_ANALYST_MCP_ENABLED",
            "product_analyst": "PRODUCT_ANALYST_MCP_ENABLED",
            "bull_researcher": "BULL_RESEARCHER_MCP_ENABLED",
            "bear_researcher": "BEAR_RESEARCHER_MCP_ENABLED",
            "research_manager": "RESEARCH_MANAGER_MCP_ENABLED",
            "trader": "TRADER_MCP_ENABLED",
            "aggressive_risk_analyst": "AGGRESSIVE_RISK_ANALYST_MCP_ENABLED",
            "safe_risk_analyst": "SAFE_RISK_ANALYST_MCP_ENABLED",
            "neutral_risk_analyst": "NEUTRAL_RISK_ANALYST_MCP_ENABLED",
            "risk_manager": "RISK_MANAGER_MCP_ENABLED"
        }
        
        for agent_name, env_var in env_mapping.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                permissions[agent_name] = env_value.lower() == 'true'
            else:
                # 如果环境变量未设置，默认为false
                permissions[agent_name] = False
        
        print(f"智能体权限配置从环境变量加载完成: {permissions}")
        return permissions
    
    async def initialize(self, mcp_config: Optional[Dict] = None) -> bool:
        """初始化MCP客户端和工具"""
        try:
            # 如果已经有客户端，先关闭
            if self.client:
                await self.close()
            
            # 使用配置创建MCP客户端
            config = mcp_config or self.config.get("servers", {})
            if not config:
                print("⚠️ 未找到MCP服务器配置，跳过MCP初始化")
                return False
            
            self.client = MultiServerMCPClient(config)
            
            # 获取所有可用工具
            self.tools = await self.client.get_tools()
            print(f"✅ 成功连接到MCP服务器，发现 {len(self.tools)} 个工具")
            
            # 按服务器组织工具
            self.tools_by_server = await self._organize_tools_by_server()
            
            return True
            
        except Exception as e:
            print(f"❌ MCP客户端初始化失败: {e}")
            # 确保清理状态
            self.client = None
            self.tools = []
            self.tools_by_server = {}
            return False
    

    
    async def _organize_tools_by_server(self) -> Dict[str, List]:
        """按服务器组织工具"""
        tools_by_server = {}
        
        for tool in self.tools:
            # 尝试从工具名称或描述中推断服务器
            server_name = "default"
            if hasattr(tool, 'server_name'):
                server_name = tool.server_name
            elif "finance" in tool.name.lower() or "stock" in tool.name.lower():
                server_name = "finance-data-server"
            
            if server_name not in tools_by_server:
                tools_by_server[server_name] = []
            tools_by_server[server_name].append(tool)
        
        return tools_by_server
    
    def get_tools_for_agent(self, agent_name: str) -> List:
        """获取指定智能体可用的工具列表"""
        # 检查权限
        if not self.agent_permissions.get(agent_name, False):
            print(f"智能体 {agent_name} 未被授权使用MCP工具")
            return []
        
        # 检查客户端连接状态
        if not self.client or not self.tools:
            print(f"智能体 {agent_name} - MCP客户端未连接或无可用工具")
            return []
        
        # 返回所有可用工具
        print(f"智能体 {agent_name} 可使用 {len(self.tools)} 个MCP工具")
        return self.tools
    
    def create_agent_with_tools(self, agent_name: str):
        """为指定智能体创建带工具的React智能体"""
        tools = self.get_tools_for_agent(agent_name)
        
        if not tools:
            # 没有工具权限，返回基础智能体
            return create_react_agent(self.llm, [])
        
        # 创建带工具的智能体
        agent = create_react_agent(self.llm, tools)
        print(f"为智能体 {agent_name} 创建了带 {len(tools)} 个工具的React智能体")
        return agent
    
    def get_tools_info(self) -> Dict[str, Any]:
        """获取工具信息列表，按MCP服务器分组"""
        if not self.tools_by_server:
            return {"servers": {}, "total_tools": 0, "server_count": 0}
        
        servers_info = {}
        total_tools = 0
        
        for server_name, server_tools in self.tools_by_server.items():
            tools_info = []
            
            for tool in server_tools:
                tool_info = {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {},
                    "required": []
                }
                
                # 获取工具参数schema
                try:
                    schema = None
                    if hasattr(tool, 'args_schema') and tool.args_schema:
                        if isinstance(tool.args_schema, dict):
                            schema = tool.args_schema
                        elif hasattr(tool.args_schema, 'model_json_schema'):
                            schema = tool.args_schema.model_json_schema()
                    
                    if schema and isinstance(schema, dict):
                        if 'properties' in schema:
                            tool_info["parameters"] = schema['properties']
                            tool_info["required"] = schema.get('required', [])
                
                except Exception as e:
                    print(f"⚠️ 获取工具 '{tool.name}' 参数信息失败: {e}")
                
                tools_info.append(tool_info)
            
            servers_info[server_name] = {
                "name": server_name,
                "tools": tools_info,
                "tool_count": len(tools_info)
            }
            
            total_tools += len(tools_info)
        
        return {
            "servers": servers_info,
            "total_tools": total_tools,
            "server_count": len(servers_info),
            "agent_permissions": self.agent_permissions
        }
    
    async def call_tool_for_agent(self, agent_name: str, tool_name: str, tool_args: Dict) -> Any:
        """为指定智能体调用MCP工具"""
        # 检查权限
        if not self.agent_permissions.get(agent_name, False):
            error_msg = f"智能体 {agent_name} 未被授权使用MCP工具"
            print(f"⚠️ {error_msg}")
            return {"error": error_msg}
        
        # 检查客户端连接状态
        if not self.client:
            error_msg = "MCP客户端未初始化或连接已断开"
            print(f"❌ {error_msg}")
            return {"error": error_msg}
        
        # 查找工具
        target_tool = None
        for tool in self.tools:
            if tool.name == tool_name:
                target_tool = tool
                break
        
        if not target_tool:
            error_msg = f"未找到工具: {tool_name}"
            print(f"❌ {error_msg}")
            return {"error": error_msg}
        
        try:
            # 调用工具
            result = await target_tool.ainvoke(tool_args)
            print(f"智能体 {agent_name} 成功调用工具 {tool_name}")
            return result
        except Exception as e:
            error_msg = f"工具调用失败: {e}"
            print(f"❌ {error_msg}")
            # 如果是连接错误，清理客户端状态
            if "BrokenResourceError" in str(e) or "connection" in str(e).lower():
                print("🔄 检测到连接错误，清理MCP客户端状态")
                self.client = None
                self.tools = []
                self.tools_by_server = {}
            return {"error": error_msg}
    
    async def close(self):
        """关闭MCP连接"""
        if self.client:
            try:
                # 检查客户端是否有close方法
                if hasattr(self.client, 'close'):
                    await self.client.close()
                    print("MCP连接已关闭")
                else:
                    print("MCP客户端无需显式关闭")
                # 清理客户端引用
                self.client = None
                self.tools = []
                self.tools_by_server = {}
            except Exception as e:
                print(f"❌ 关闭MCP连接时出错: {e}")
                # 即使出错也要清理引用
                self.client = None
                self.tools = []
                self.tools_by_server = {}
    
    def is_agent_mcp_enabled(self, agent_name: str) -> bool:
        """检查智能体是否启用了MCP工具"""
        return self.agent_permissions.get(agent_name, False)
    
    def get_enabled_agents(self) -> List[str]:
        """获取启用MCP工具的智能体列表"""
        return [agent for agent, enabled in self.agent_permissions.items() if enabled]