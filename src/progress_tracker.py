import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from loguru import logger


class ProgressTracker:
    """进度跟踪器 - 实时保存智能体工作进度和数据到JSON文件"""
    
    def __init__(self, session_id: str = None):
        # 创建进度保存目录
        self.progress_dir = "progress_logs"
        os.makedirs(self.progress_dir, exist_ok=True)
        
        # 生成会话ID
        if session_id is None:
            self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        else:
            self.session_id = session_id
            
        # 进度文件路径
        self.progress_file = os.path.join(self.progress_dir, f"session_{self.session_id}.json")
        
        # 初始化进度数据
        self.progress_data = {
            "session_id": self.session_id,
            "start_time": datetime.now().isoformat(),
            "status": "running",
            "user_query": "",
            "current_stage": "",
            "current_agent": "",
            "agents_progress": {},
            "global_state": {},
            "timeline": [],
            "errors": [],
            "warnings": [],
            "mcp_tool_calls": [],
            "debate_states": {
                "investment_debate": {},
                "risk_debate": {}
            },
            "final_results": {}
        }
        
        # 保存初始状态
        self._save_progress()
        logger.info(f"📊 进度跟踪器初始化完成，会话ID: {self.session_id}")
    
    def _save_progress(self):
        """保存进度到JSON文件"""
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存进度失败: {e}")
    
    def update_user_query(self, query: str):
        """更新用户查询"""
        self.progress_data["user_query"] = query
        self._add_timeline_event("user_query_set", {"query": query})
        self._save_progress()
    
    def start_stage(self, stage_name: str, description: str = ""):
        """开始新阶段"""
        self.progress_data["current_stage"] = stage_name
        self._add_timeline_event("stage_start", {
            "stage": stage_name,
            "description": description
        })
        logger.info(f"📍 阶段开始: {stage_name}")
        self._save_progress()
    
    def start_agent(self, agent_name: str, action: str = ""):
        """开始智能体工作"""
        self.progress_data["current_agent"] = agent_name
        
        if agent_name not in self.progress_data["agents_progress"]:
            self.progress_data["agents_progress"][agent_name] = {
                "status": "running",
                "start_time": datetime.now().isoformat(),
                "actions": [],
                "results": [],
                "mcp_calls": [],
                "errors": []
            }
        
        self.progress_data["agents_progress"][agent_name]["status"] = "running"
        self.progress_data["agents_progress"][agent_name]["start_time"] = datetime.now().isoformat()
        
        if action:
            self.progress_data["agents_progress"][agent_name]["actions"].append({
                "action": action,
                "timestamp": datetime.now().isoformat()
            })
        
        self._add_timeline_event("agent_start", {
            "agent": agent_name,
            "action": action
        })
        
        logger.info(f"🤖 智能体开始工作: {agent_name} - {action}")
        self._save_progress()
    
    def complete_agent(self, agent_name: str, result: str = "", success: bool = True):
        """完成智能体工作"""
        if agent_name in self.progress_data["agents_progress"]:
            self.progress_data["agents_progress"][agent_name]["status"] = "completed" if success else "failed"
            self.progress_data["agents_progress"][agent_name]["end_time"] = datetime.now().isoformat()
            
            if result:
                self.progress_data["agents_progress"][agent_name]["results"].append({
                    "result": result[:500] + "..." if len(result) > 500 else result,  # 限制长度
                    "timestamp": datetime.now().isoformat(),
                    "success": success
                })
        
        self._add_timeline_event("agent_complete", {
            "agent": agent_name,
            "success": success,
            "result_length": len(result) if result else 0
        })
        
        logger.info(f"✅ 智能体完成工作: {agent_name} - {'成功' if success else '失败'}")
        self._save_progress()
    
    def add_agent_action(self, agent_name: str, action: str, details: Dict[str, Any] = None):
        """添加智能体行动记录"""
        if agent_name not in self.progress_data["agents_progress"]:
            self.start_agent(agent_name)
        
        action_record = {
            "action": action,
            "timestamp": datetime.now().isoformat()
        }
        
        if details:
            action_record["details"] = details
        
        self.progress_data["agents_progress"][agent_name]["actions"].append(action_record)
        self._save_progress()
    
    def add_mcp_tool_call(self, agent_name: str, tool_name: str, tool_args: Dict, tool_result: Any):
        """记录MCP工具调用"""
        tool_call_record = {
            "agent": agent_name,
            "tool_name": tool_name,
            "tool_args": tool_args,
            "tool_result": str(tool_result)[:1000] + "..." if len(str(tool_result)) > 1000 else str(tool_result),
            "timestamp": datetime.now().isoformat()
        }
        
        self.progress_data["mcp_tool_calls"].append(tool_call_record)
        
        if agent_name in self.progress_data["agents_progress"]:
            self.progress_data["agents_progress"][agent_name]["mcp_calls"].append(tool_call_record)
        
        self._add_timeline_event("mcp_tool_call", {
            "agent": agent_name,
            "tool": tool_name
        })
        
        logger.info(f"🔧 MCP工具调用: {agent_name} -> {tool_name}")
        self._save_progress()
    
    def update_global_state(self, state_key: str, state_value: Any):
        """更新全局状态"""
        # 对于复杂对象，只保存关键信息
        if isinstance(state_value, dict):
            self.progress_data["global_state"][state_key] = state_value
        elif hasattr(state_value, '__dict__'):
            # 对象转换为字典
            self.progress_data["global_state"][state_key] = vars(state_value)
        else:
            self.progress_data["global_state"][state_key] = str(state_value)
        
        self._save_progress()
    
    def update_debate_state(self, debate_type: str, debate_data: Dict[str, Any]):
        """更新辩论状态"""
        if debate_type in self.progress_data["debate_states"]:
            self.progress_data["debate_states"][debate_type] = debate_data
            self._add_timeline_event("debate_update", {
                "type": debate_type,
                "round": debate_data.get("count", 0)
            })
            self._save_progress()
    
    def add_error(self, error_msg: str, agent_name: str = None):
        """添加错误记录"""
        error_record = {
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }
        
        if agent_name:
            error_record["agent"] = agent_name
            if agent_name in self.progress_data["agents_progress"]:
                self.progress_data["agents_progress"][agent_name]["errors"].append(error_record)
        
        self.progress_data["errors"].append(error_record)
        self._add_timeline_event("error", error_record)
        
        logger.error(f"❌ 错误记录: {error_msg}")
        self._save_progress()
    
    def add_warning(self, warning_msg: str, agent_name: str = None):
        """添加警告记录"""
        warning_record = {
            "warning": warning_msg,
            "timestamp": datetime.now().isoformat()
        }
        
        if agent_name:
            warning_record["agent"] = agent_name
        
        self.progress_data["warnings"].append(warning_record)
        self._add_timeline_event("warning", warning_record)
        
        logger.warning(f"⚠️ 警告记录: {warning_msg}")
        self._save_progress()
    
    def set_final_results(self, results: Dict[str, Any]):
        """设置最终结果"""
        self.progress_data["final_results"] = results
        self.progress_data["status"] = "completed"
        self.progress_data["end_time"] = datetime.now().isoformat()
        
        self._add_timeline_event("session_complete", {
            "total_agents": len(self.progress_data["agents_progress"]),
            "total_mcp_calls": len(self.progress_data["mcp_tool_calls"]),
            "total_errors": len(self.progress_data["errors"])
        })
        
        logger.info(f"🏁 会话完成，最终结果已保存")
        self._save_progress()
    
    def _add_timeline_event(self, event_type: str, event_data: Dict[str, Any]):
        """添加时间线事件"""
        timeline_event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": event_data
        }
        
        self.progress_data["timeline"].append(timeline_event)
    
    def get_progress_file_path(self) -> str:
        """获取进度文件路径"""
        return self.progress_file
    
    def log_workflow_start(self, workflow_info: Dict[str, Any]):
        """记录工作流开始"""
        self.progress_data["workflow_info"] = workflow_info
        self._add_timeline_event("workflow_start", workflow_info)
        logger.info(f"🚀 工作流开始: {workflow_info.get('user_query', '')}")
        self._save_progress()
    
    def log_workflow_completion(self, completion_info: Dict[str, Any]):
        """记录工作流完成"""
        self.progress_data["completion_info"] = completion_info
        if completion_info.get("success", False):
            self.progress_data["status"] = "completed"
        else:
            self.progress_data["status"] = "failed"
        
        self.progress_data["end_time"] = completion_info.get("completion_time", datetime.now().isoformat())
        self._add_timeline_event("workflow_completion", completion_info)
        
        status = "成功" if completion_info.get("success", False) else "失败"
        logger.info(f"🏁 工作流完成: {status}")
        self._save_progress()
    
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
        self.add_agent_action(agent_name, "LLM调用", {
            "prompt_preview": prompt_preview[:200] + "..." if len(prompt_preview) > 200 else prompt_preview,
            "context": context
        })
    
    def log_error(self, agent_name: str, error: str, context: Dict[str, Any] = None):
        """记录错误"""
        self.add_error(error, agent_name)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """获取会话摘要"""
        return {
            "session_id": self.session_id,
            "status": self.progress_data["status"],
            "start_time": self.progress_data["start_time"],
            "end_time": self.progress_data.get("end_time"),
            "total_agents": len(self.progress_data["agents_progress"]),
            "total_timeline_events": len(self.progress_data["timeline"]),
            "total_mcp_calls": len(self.progress_data["mcp_tool_calls"]),
            "total_errors": len(self.progress_data["errors"]),
            "total_warnings": len(self.progress_data["warnings"]),
            "progress_file": self.progress_file
        }