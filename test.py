#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP工具绑定测试脚本
用于测试大模型与MCP工具的连接和调用是否正常
"""

import os
import json
import asyncio
from typing import Dict, Any, List
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv


class MCPTestAgent:
    """MCP测试代理 - 简化版本用于测试MCP连接和工具调用"""
    
    def __init__(self, config_file="mcp_config.json"):
        # 加载环境变量
        load_dotenv()
        
        # 加载配置文件
        self.config = self._load_config(config_file)
        
        # 获取模型配置（优先使用环境变量）
        api_key = os.getenv("LLM_API_KEY")
        base_url = os.getenv("LLM_BASE_URL")
        model_name = os.getenv("LLM_MODEL", "deepseek-chat")
        
        print(f"🔧 模型配置:")
        print(f"   API Key: {api_key[:10]}...{api_key[-4:] if api_key else 'None'}")
        print(f"   Base URL: {base_url}")
        print(f"   Model: {model_name}")
        
        # 初始化大模型
        self.llm = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4000"))
        )
        
        self.client = None
        self.tools = []
        self.agent = None
        self.conversation_history = []
        
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✅ 配置文件加载成功: {config_file}")
            return config
        except FileNotFoundError:
            print(f"❌ 配置文件未找到: {config_file}")
            return {"servers": {}}
        except json.JSONDecodeError as e:
            print(f"❌ 配置文件格式错误: {e}")
            return {"servers": {}}
    
    async def initialize(self, mcp_config=None):
        """初始化MCP客户端和工具"""
        try:
            # 使用配置创建MCP客户端
            config = mcp_config or self.config.get("servers", {})
            print(f"🔧 MCP服务器配置: {config}")
            
            if not config:
                print("❌ 未找到MCP服务器配置")
                return False
            
            self.client = MultiServerMCPClient(config)
            print("✅ MCP客户端创建成功")
            
            # 获取所有可用工具
            print("🔍 正在获取MCP工具...")
            self.tools = await self.client.get_tools()
            print(f"✅ 成功连接到MCP服务器，发现 {len(self.tools)} 个工具")
            
            # 按服务器组织工具
            self.tools_by_server = await self._organize_tools_by_server()
            
            # 创建React智能体
            print("🤖 创建React智能体...")
            self.agent = create_react_agent(self.llm, self.tools)
            print("✅ React智能体创建成功")
            
            return True
            
        except Exception as e:
            print(f"❌ MCP客户端初始化失败: {e}")
            import traceback
            traceback.print_exc()
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
    
    def get_tools_info(self) -> Dict[str, Any]:
        """获取工具信息列表，按MCP服务器分组"""
        if not hasattr(self, 'tools_by_server') or not self.tools_by_server:
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
            "server_count": len(servers_info)
        }
    
    async def chat(self, message: str, verbose: bool = True) -> str:
        """与AI助手对话，支持工具调用"""
        if not self.agent:
            return "❌ MCP代理未初始化，请先调用 initialize() 方法"
        
        try:
            # 添加用户消息到历史
            self.conversation_history.append({"role": "user", "content": message})
            
            if verbose:
                print(f"\n🔵 用户: {message}")
            
            # 调用智能体处理
            print("🤖 正在调用智能体处理...")
            response = await self.agent.ainvoke({
                "messages": self.conversation_history
            })
            
            # 处理响应消息
            messages = response.get("messages", [])
            
            if verbose:
                print("\n📋 对话流程:")
                for i, msg in enumerate(messages, 1):
                    if hasattr(msg, 'type'):
                        if msg.type == 'human':
                            print(f"  {i}. 👤 用户: {msg.content}")
                        elif msg.type == 'ai':
                            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                print(f"  {i}. 🤖 AI调用工具:")
                                for tool_call in msg.tool_calls:
                                    print(f"     🔧 工具: {tool_call.get('name', 'unknown')}")
                                    print(f"     📝 参数: {tool_call.get('args', {})}")
                            else:
                                print(f"  {i}. 🤖 AI: {msg.content}")
                        elif msg.type == 'tool':
                            content_preview = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                            print(f"  {i}. 🛠️ 工具返回: {content_preview}")
            
            # 获取最终回复
            final_message = messages[-1] if messages else None
            if final_message and hasattr(final_message, 'content'):
                final_response = final_message.content
                
                # 添加AI回复到历史
                self.conversation_history.append({"role": "assistant", "content": final_response})
                
                if verbose:
                    print(f"\n✅ 最终回复: {final_response}")
                
                return final_response
            else:
                return "❌ 未收到有效回复"
                
        except Exception as e:
            error_msg = f"❌ 对话处理失败: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return error_msg
    
    async def test_tool_call(self, tool_name: str, tool_args: dict) -> Any:
        """直接测试工具调用"""
        if not self.tools:
            return {"error": "未找到可用工具"}
        
        # 查找工具
        target_tool = None
        for tool in self.tools:
            if tool.name == tool_name:
                target_tool = tool
                break
        
        if not target_tool:
            return {"error": f"未找到工具: {tool_name}"}
        
        try:
            print(f"🔧 直接调用工具: {tool_name}")
            print(f"📝 参数: {tool_args}")
            result = await target_tool.ainvoke(tool_args)
            print(f"✅ 工具调用成功")
            return result
        except Exception as e:
            error_msg = f"工具调用失败: {e}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return {"error": error_msg}
    
    async def close(self):
        """关闭MCP连接"""
        if self.client:
            try:
                if hasattr(self.client, 'close'):
                    await self.client.close()
                    print("✅ MCP连接已关闭")
            except Exception as e:
                print(f"❌ 关闭MCP连接时出错: {e}")


async def main():
    """主测试函数"""
    print("🚀 开始MCP工具绑定测试")
    print("=" * 50)
    
    agent = MCPTestAgent()
    
    try:
        # 1. 初始化测试
        print("\n📋 步骤1: 初始化MCP客户端")
        success = await agent.initialize()
        
        if not success:
            print("❌ 初始化失败，退出测试")
            return
        
        # 2. 工具信息测试
        print("\n📋 步骤2: 获取工具信息")
        tools_info = agent.get_tools_info()
        print(f"📊 工具统计:")
        print(f"   服务器数量: {tools_info['server_count']}")
        print(f"   工具总数: {tools_info['total_tools']}")
        
        for server_name, server_info in tools_info['servers'].items():
            print(f"\n🖥️ 服务器: {server_name}")
            print(f"   工具数量: {server_info['tool_count']}")
            for tool in server_info['tools']:
                print(f"   - {tool['name']}: {tool['description']}")
        
        # 3. 直接工具调用测试
        if agent.tools:
            print("\n📋 步骤3: 直接工具调用测试")
            first_tool = agent.tools[0]
            print(f"🔧 测试工具: {first_tool.name}")
            
            # 尝试调用第一个工具（使用空参数或最小参数）
            test_args = {}
            if hasattr(first_tool, 'args_schema') and first_tool.args_schema:
                try:
                    if hasattr(first_tool.args_schema, 'model_json_schema'):
                        schema = first_tool.args_schema.model_json_schema()
                        if 'properties' in schema:
                            # 为必需参数提供默认值
                            required = schema.get('required', [])
                            for req_param in required:
                                if req_param in schema['properties']:
                                    prop = schema['properties'][req_param]
                                    if prop.get('type') == 'string':
                                        test_args[req_param] = "test"
                                    elif prop.get('type') == 'number':
                                        test_args[req_param] = 1
                                    elif prop.get('type') == 'boolean':
                                        test_args[req_param] = True
                except Exception as e:
                    print(f"⚠️ 解析工具参数失败: {e}")
            
            result = await agent.test_tool_call(first_tool.name, test_args)
            print(f"🔍 工具调用结果: {result}")
        
        # 4. 交互式对话模式
        print("\n📋 步骤4: 进入交互式对话模式")
        print("💡 提示: 输入 'quit' 或 'exit' 退出对话")
        print("💡 提示: 输入 'tools' 查看可用工具列表")
        print("-" * 50)
        
        while True:
            try:
                # 获取用户输入
                user_input = input("\n🔵 你: ").strip()
                
                # 检查退出命令
                if user_input.lower() in ['quit', 'exit', '退出', 'q']:
                    print("👋 再见！")
                    break
                
                # 检查工具列表命令
                if user_input.lower() in ['tools', '工具', 'tool']:
                    tools_info = agent.get_tools_info()
                    print(f"\n🛠️ 可用工具列表 (共{tools_info['total_tools']}个):")
                    for server_name, server_info in tools_info['servers'].items():
                        print(f"\n📡 服务器: {server_name}")
                        for tool in server_info['tools']:
                            print(f"   • {tool['name']}: {tool['description']}")
                    continue
                
                # 跳过空输入
                if not user_input:
                    continue
                
                # 处理用户问题
                print("🤖 正在思考...")
                response = await agent.chat(user_input, verbose=True)
                print(f"\n🤖 AI: {response}")
                print("-" * 50)
                
            except KeyboardInterrupt:
                print("\n\n👋 检测到 Ctrl+C，退出对话")
                break
            except EOFError:
                print("\n\n👋 检测到 EOF，退出对话")
                break
            except Exception as e:
                print(f"\n❌ 对话过程中出现错误: {e}")
                continue
        
        print("\n✅ 对话结束")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理资源
        await agent.close()


if __name__ == "__main__":
    asyncio.run(main())