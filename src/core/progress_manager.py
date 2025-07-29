from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from pathlib import Path
from loguru import logger

from .state_manager import StateManager
from .data_persistence import DataPersistence


class ProgressManager:
    """进度管理器 - 整合状态管理和数据持久化"""
    
    def __init__(self, session_id: Optional[str] = None):
        self.state_manager = StateManager()
        self.data_persistence = DataPersistence(session_id)
        
        # 同步会话ID
        self.session_id = self.data_persistence.session_id
        
        logger.info(f"📈 进度管理器初始化完成 - 会话ID: {self.session_id}")
    
    def start_workflow(self, user_query: str):
        """开始工作流"""
        self.state_manager.start_workflow(user_query)
        self.data_persistence.log_workflow_start(user_query)
        
        # 保存初始状态
        self._sync_and_save()
    
    def start_agent(self, agent_name: str, action: str = ""):
        """开始智能体工作"""
        self.state_manager.start_agent(agent_name, action)
        self.data_persistence.log_agent_start(agent_name, action)
        
        self._sync_and_save()
    
    def complete_agent(self, agent_name: str, success: bool = True, results: Optional[Dict[str, Any]] = None):
        """完成智能体工作"""
        self.state_manager.complete_agent(agent_name, success)
        
        # 保存智能体结果
        if results:
            self.data_persistence.save_agent_results(agent_name, results)
            self.state_manager.increment_agent_results(agent_name)
        
        self.data_persistence.log_agent_complete(agent_name, success)
        
        self._sync_and_save()
    
    def update_agent_progress(self, agent_name: str, progress: float, action: str = ""):
        """更新智能体进度"""
        self.state_manager.update_agent_progress(agent_name, progress, action)
        
        if action:
            self.data_persistence.add_agent_action(agent_name, action)
        
        self._sync_and_save()
    
    def add_agent_action(self, agent_name: str, action: str, details: Optional[Dict[str, Any]] = None):
        """添加智能体行动"""
        self.data_persistence.add_agent_action(agent_name, action, details)
        self._sync_and_save()
    
    def save_mcp_tool_call(self, agent_name: str, tool_name: str, tool_input: Dict[str, Any], 
                          tool_output: Any, success: bool = True):
        """保存MCP工具调用"""
        self.data_persistence.save_mcp_tool_call(agent_name, tool_name, tool_input, tool_output, success)
        self.state_manager.increment_agent_mcp_calls(agent_name)
        
        self._sync_and_save()
    
    def save_llm_interaction(self, agent_name: str, prompt: str, response: str, 
                           model: str = "unknown", tokens_used: Optional[int] = None):
        """保存LLM交互"""
        self.data_persistence.save_llm_interaction(agent_name, prompt, response, model, tokens_used)
        self._sync_and_save()
    
    def start_debate(self, debate_type: str):
        """开始辩论"""
        self.state_manager.start_debate(debate_type)
        self.data_persistence.update_debate_state(debate_type, {
            "active": True,
            "round": 1,
            "start_time": datetime.now().isoformat()
        })
        
        self._sync_and_save()
    
    def next_debate_round(self, debate_type: str) -> bool:
        """进入下一轮辩论"""
        should_continue = self.state_manager.next_debate_round(debate_type)
        
        debate_state = self.state_manager.get_debate_status(debate_type)
        if debate_state:
            self.data_persistence.update_debate_state(debate_type, {
                "round": debate_state["round"],
                "active": debate_state["active"]
            })
        
        self._sync_and_save()
        return should_continue
    
    def end_debate(self, debate_type: str, final_decision: Optional[str] = None):
        """结束辩论"""
        self.state_manager.end_debate(debate_type)
        
        debate_update = {
            "active": False,
            "end_time": datetime.now().isoformat()
        }
        if final_decision:
            debate_update["final_decision"] = final_decision
        
        self.data_persistence.update_debate_state(debate_type, debate_update)
        
        self._sync_and_save()
    
    def add_error(self, agent_name: str, error_message: str, error_details: Optional[Dict[str, Any]] = None):
        """添加错误"""
        self.data_persistence.add_error(agent_name, error_message, error_details)
        self._sync_and_save()
    
    def add_warning(self, agent_name: str, warning_message: str, warning_details: Optional[Dict[str, Any]] = None):
        """添加警告"""
        self.data_persistence.add_warning(agent_name, warning_message, warning_details)
        self._sync_and_save()
    
    def set_final_results(self, results: Dict[str, Any]):
        """设置最终结果"""
        self.data_persistence.set_final_results(results)
        
        # 标记工作流完成
        self.state_manager.workflow_state["status"] = "completed"
        
        self._sync_and_save()
    
    def complete_workflow(self, success: bool = True, final_results: Optional[Dict[str, Any]] = None):
        """完成工作流"""
        if final_results:
            self.set_final_results(final_results)
        
        self.state_manager.workflow_state["status"] = "completed" if success else "failed"
        self.data_persistence.log_workflow_completion(success)
        
        self._sync_and_save()
    
    def get_current_progress(self) -> Dict[str, Any]:
        """获取当前进度"""
        return self.state_manager.get_current_progress()
    
    def get_agent_status(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """获取智能体状态"""
        return self.state_manager.get_agent_status(agent_name)
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """获取工作流状态"""
        return self.state_manager.get_workflow_status()
    
    def get_debate_status(self, debate_type: str) -> Optional[Dict[str, Any]]:
        """获取辩论状态"""
        return self.state_manager.get_debate_status(debate_type)
    
    def get_session_data(self) -> Dict[str, Any]:
        """获取完整会话数据"""
        return self.data_persistence.get_session_data()
    
    def get_progress_file_path(self) -> str:
        """获取进度文件路径"""
        return self.data_persistence.get_progress_file_path()
    
    def get_session_summary(self) -> Dict[str, Any]:
        """获取会话摘要"""
        session_data = self.get_session_data()
        progress = self.get_current_progress()
        
        return {
            "session_id": self.session_id,
            "status": progress["workflow_status"],
            "progress": progress["progress"],
            "current_task": progress["current_task"],
            "completed_agents": progress["completed_count"],
            "total_agents": progress["total_count"],
            "start_time": session_data.get("start_time"),
            "user_query": session_data.get("user_query"),
            "errors_count": len(session_data.get("errors", [])),
            "warnings_count": len(session_data.get("warnings", [])),
            "mcp_calls_count": len(session_data.get("mcp_tool_calls", [])),
            "llm_interactions_count": len(session_data.get("llm_interactions", []))
        }
    
    def reset(self):
        """重置进度管理器"""
        self.state_manager.reset()
        self.data_persistence = DataPersistence()  # 创建新会话
        self.session_id = self.data_persistence.session_id
        
        logger.info(f"🔄 进度管理器已重置 - 新会话ID: {self.session_id}")
    
    def _sync_and_save(self):
        """同步状态并保存数据"""
        # 更新数据持久化中的状态信息
        workflow_state = self.state_manager.get_workflow_status()
        agent_states = {agent: self.state_manager.get_agent_status(agent) 
                       for agent in self.state_manager.agent_order}
        
        # 更新全局状态
        global_state_update = {
            "workflow_state": workflow_state,
            "agent_states": agent_states,
            "overall_progress": workflow_state.get("overall_progress", 0.0),
            "current_agent": workflow_state.get("current_agent"),
            "last_updated": datetime.now().isoformat()
        }
        
        self.data_persistence.update_global_state(global_state_update)
    
    def load_session(self, session_id: str) -> bool:
        """加载已存在的会话"""
        try:
            # 尝试加载数据持久化
            self.data_persistence = DataPersistence(session_id)
            session_data = self.data_persistence.get_session_data()
            
            if not session_data:
                logger.warning(f"⚠️ 会话数据不存在: {session_id}")
                return False
            
            # 恢复状态管理器状态
            global_state = session_data.get("global_state", {})
            workflow_state = global_state.get("workflow_state", {})
            agent_states = global_state.get("agent_states", {})
            
            # 恢复工作流状态
            if workflow_state:
                self.state_manager.workflow_state.update(workflow_state)
            
            # 恢复智能体状态
            for agent_name, agent_state in agent_states.items():
                if agent_name in self.state_manager.agent_states:
                    self.state_manager.agent_states[agent_name].update(agent_state)
            
            self.session_id = session_id
            logger.info(f"📂 成功加载会话: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 加载会话失败: {session_id} - {str(e)}")
            return False
    
    def export_session_data(self, export_path: Optional[str] = None) -> str:
        """导出会话数据"""
        session_data = self.get_session_data()
        
        if not export_path:
            export_path = f"session_export_{self.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📤 会话数据已导出: {export_path}")
            return export_path
            
        except Exception as e:
            logger.error(f"❌ 导出会话数据失败: {str(e)}")
            raise