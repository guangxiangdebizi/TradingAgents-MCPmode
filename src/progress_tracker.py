from datetime import datetime
from typing import Dict, Any, Optional


class ProgressTracker:
    """简化的进度跟踪器 - 只输出核心agent结果"""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_stage = ""
        self.current_agent = ""
        print(f"🚀 会话开始: {self.session_id}")
    
    def update_user_query(self, query: str):
        """更新用户查询"""
        print(f"📝 用户查询: {query}")
    
    def start_stage(self, stage_name: str, description: str = ""):
        """开始新阶段"""
        self.current_stage = stage_name
        print(f"📍 阶段开始: {stage_name}")
        if description:
            print(f"   描述: {description}")
    
    def start_agent(self, agent_name: str, action: str = ""):
        """开始智能体工作"""
        self.current_agent = agent_name
        print(f"🤖 智能体开始工作: {agent_name}")
        if action:
            print(f"   执行: {action}")
    
    def complete_agent(self, agent_name: str, result: str = "", success: bool = True):
        """完成智能体工作"""
        status = "✅ 成功" if success else "❌ 失败"
        print(f"🏁 智能体完成: {agent_name} - {status}")
        
        # 输出完整的agent结果内容
        if result:
            print(f"\n📋 {agent_name} 输出结果:")
            print("=" * 50)
            print(result)
            print("=" * 50)
    
    def add_agent_action(self, agent_name: str, action: str, details: Dict[str, Any] = None):
        """添加智能体行动记录"""
        print(f"🔄 {agent_name}: {action}")
    
    def add_mcp_tool_call(self, agent_name: str, tool_name: str, tool_args: Dict, tool_result: Any):
        """记录MCP工具调用"""
        print(f"🔧 {agent_name} 调用工具: {tool_name}")
    
    def update_global_state(self, state_key: str, state_value: Any):
        """更新全局状态"""
        pass  # 简化：不再保存状态
    
    def update_debate_state(self, debate_type: str, debate_data: Dict[str, Any]):
        """更新辩论状态"""
        print(f"🗣️ 辩论更新: {debate_type} - 轮次 {debate_data.get('count', 0)}")
    
    def add_error(self, error_msg: str, agent_name: str = None):
        """添加错误记录"""
        if agent_name:
            print(f"❌ {agent_name} 错误: {error_msg}")
        else:
            print(f"❌ 错误: {error_msg}")
    
    def add_warning(self, warning_msg: str, agent_name: str = None):
        """添加警告记录"""
        if agent_name:
            print(f"⚠️ {agent_name} 警告: {warning_msg}")
        else:
            print(f"⚠️ 警告: {warning_msg}")
    
    def set_final_results(self, results: Dict[str, Any]):
        """设置最终结果"""
        print(f"🏁 会话完成")
        print("\n📊 最终结果:")
        print("=" * 60)
        for key, value in results.items():
            print(f"{key}: {value}")
        print("=" * 60)
    
    def log_workflow_start(self, workflow_info: Dict[str, Any]):
        """记录工作流开始"""
        print(f"🚀 工作流开始: {workflow_info.get('user_query', '')}")
    
    def log_workflow_completion(self, completion_info: Dict[str, Any]):
        """记录工作流完成"""
        status = "成功" if completion_info.get("success", False) else "失败"
        print(f"🏁 工作流完成: {status}")
    
    def log_agent_start(self, agent_name: str, context: Dict[str, Any] = None):
        """记录智能体开始工作"""
        self.start_agent(agent_name, context.get("action", "") if context else "")
    
    def log_agent_complete(self, agent_name: str, result: Any = None, context: Dict[str, Any] = None):
        """记录智能体完成工作"""
        result_str = str(result) if result else ""
        success = context.get("success", True) if context else True
        self.complete_agent(agent_name, result_str, success)
    
    def log_llm_call(self, agent_name: str, prompt_preview: str, context: Dict[str, Any] = None):
        """记录LLM调用"""
        self.add_agent_action(agent_name, "LLM调用")
    
    def log_error(self, agent_name: str, error: str, context: Dict[str, Any] = None):
        """记录错误"""
        self.add_error(error, agent_name)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """获取会话摘要"""
        return {"session_id": self.session_id}