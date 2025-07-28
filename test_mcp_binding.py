#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试MCP工具绑定的简单脚本
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# 修复导入问题
sys.path.insert(0, str(Path(__file__).parent))

from src.mcp_manager import MCPManager
from src.base_agent import BaseAgent
from src.agent_states import AgentState

class SimpleTestAgent(BaseAgent):
    """简单测试智能体"""
    
    def get_system_prompt(self, state) -> str:
        return """
你是一个金融数据分析助手。当用户询问需要实时数据的问题时，你应该主动调用相应的MCP工具获取信息。

可用的工具包括：
- current_timestamp: 获取当前时间戳
- index_data: 获取指数数据
- company_performance: 获取公司业绩数据

请根据用户的问题，判断是否需要调用工具，并提供准确的分析。
        """
    
    async def process(self, state) -> AgentState:
        """处理用户查询"""
        user_query = state.user_query if hasattr(state, 'user_query') else state.get('user_query', '')
        
        # 调用LLM处理
        result = await self.call_llm_with_context(state, user_query)
        
        # 更新状态
        if hasattr(state, 'result'):
            state.result = result
        else:
            state['result'] = result
            
        return state

async def test_mcp_binding():
    """测试MCP工具绑定"""
    print("🔧 测试MCP工具绑定...")
    
    try:
        # 1. 初始化MCP管理器
        print("\n📋 初始化MCP管理器...")
        mcp_manager = MCPManager()
        
        success = await mcp_manager.initialize()
        if not success:
            print("❌ MCP管理器初始化失败")
            return False
            
        print(f"✅ MCP管理器初始化成功，发现 {len(mcp_manager.tools)} 个工具")
        
        # 2. 创建测试智能体
        print("\n📋 创建测试智能体...")
        
        # 确保测试智能体有MCP权限
        os.environ['SIMPLE_TEST_AGENT_MCP_ENABLED'] = 'true'
        mcp_manager.agent_permissions['simple_test_agent'] = True
        
        test_agent = SimpleTestAgent(
            agent_name="simple_test_agent",
            mcp_manager=mcp_manager,
            role_description="简单的MCP工具测试智能体"
        )
        
        print(f"✅ 测试智能体创建成功，MCP状态: {test_agent.mcp_enabled}")
        
        # 3. 测试工具调用
        print("\n📋 测试工具调用...")
        
        test_queries = [
            "请帮我查询当前的时间戳",
            "我想了解一下股票市场的基本情况"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🤖 测试查询 {i}: {query}")
            
            # 创建测试状态
            test_state = {
                'user_query': query,
                'result': ''
            }
            
            print("⏳ 正在处理...")
            
            # 处理查询
            result_state = await test_agent.process(test_state)
            result = result_state.get('result', '')
            
            print(f"\n📊 响应结果 {i}:")
            print("=" * 50)
            print(result)
            print("=" * 50)
            
            # 简单检查是否包含工具调用的迹象
            has_data = any(keyword in result.lower() for keyword in ['timestamp', '时间戳', 'data', '数据', '结果'])
            print(f"🔍 包含数据信息: {'✅' if has_data else '❌'}")
        
        print("\n🎯 测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理资源
        if 'mcp_manager' in locals():
            await mcp_manager.close()
            print("\n🔧 资源清理完成")

async def main():
    """主函数"""
    print("🚀 MCP工具绑定测试")
    print("=" * 40)
    
    success = await test_mcp_binding()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 测试完成！")
    else:
        print("⚠️ 测试中出现问题")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())