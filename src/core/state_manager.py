from typing import Dict, Any, List, Optional
from datetime import datetime
# from loguru import logger  # 已移除


class StateManager:
    """状态管理器 - 管理智能体状态和工作流进度"""
    
    def __init__(self):
        # 定义智能体执行顺序
        self.agent_order = [
            "market_analyst", "sentiment_analyst", "news_analyst", "fundamentals_analyst",
            "bull_researcher", "bear_researcher", "research_manager", "trader",
            "aggressive_risk_analyst", "safe_risk_analyst", "neutral_risk_analyst", "risk_manager"
        ]
        
        # 智能体状态
        self.agent_states = {}
        for agent in self.agent_order:
            self.agent_states[agent] = {
                "status": "pending",  # pending, running, completed, failed
                "start_time": None,
                "end_time": None,
                "progress": 0.0,
                "current_action": "",
                "results_count": 0,
                "mcp_calls_count": 0
            }
        
        # 工作流状态
        self.workflow_state = {
            "status": "idle",  # idle, running, completed, failed
            "current_agent": None,
            "current_stage": "",
            "overall_progress": 0.0,
            "start_time": None,
            "estimated_completion": None
        }
        
        # 辩论状态
        self.debate_states = {
            "investment_debate": {
                "active": False,
                "round": 0,
                "max_rounds": 3,
                "participants": ["bull_researcher", "bear_researcher"]
            },
            "risk_debate": {
                "active": False,
                "round": 0,
                "max_rounds": 2,
                "participants": ["aggressive_risk_analyst", "safe_risk_analyst", "neutral_risk_analyst"]
            }
        }
        
        print("📊 状态管理器初始化完成")
    
    def start_workflow(self, user_query: str):
        """开始工作流"""
        self.workflow_state.update({
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "user_query": user_query
        })
        print(f"🚀 工作流开始: {user_query}")
    
    def start_agent(self, agent_name: str, action: str = ""):
        """开始智能体工作"""
        if agent_name in self.agent_states:
            self.agent_states[agent_name].update({
                "status": "running",
                "start_time": datetime.now().isoformat(),
                "current_action": action
            })
            
            self.workflow_state["current_agent"] = agent_name
            self._update_overall_progress()
            
            print(f"🤖 智能体开始工作: {agent_name} - {action}")
    
    def complete_agent(self, agent_name: str, success: bool = True):
        """完成智能体工作"""
        if agent_name in self.agent_states:
            self.agent_states[agent_name].update({
                "status": "completed" if success else "failed",
                "end_time": datetime.now().isoformat(),
                "progress": 1.0 if success else 0.0
            })
            
            self._update_overall_progress()
            
            # 检查是否所有智能体都完成了
            if self._all_agents_completed():
                self.workflow_state["status"] = "completed"
                self.workflow_state["current_agent"] = None
                print("🏁 所有智能体工作完成")
            
            status_text = "成功" if success else "失败"
            print(f"✅ 智能体完成工作: {agent_name} - {status_text}")
    
    def update_agent_progress(self, agent_name: str, progress: float, action: str = ""):
        """更新智能体进度"""
        if agent_name in self.agent_states:
            self.agent_states[agent_name]["progress"] = min(max(progress, 0.0), 1.0)
            if action:
                self.agent_states[agent_name]["current_action"] = action
            
            self._update_overall_progress()
    
    def increment_agent_results(self, agent_name: str):
        """增加智能体结果计数"""
        if agent_name in self.agent_states:
            self.agent_states[agent_name]["results_count"] += 1
    
    def increment_agent_mcp_calls(self, agent_name: str):
        """增加智能体MCP调用计数"""
        if agent_name in self.agent_states:
            self.agent_states[agent_name]["mcp_calls_count"] += 1
    
    def start_debate(self, debate_type: str):
        """开始辩论"""
        if debate_type in self.debate_states:
            self.debate_states[debate_type]["active"] = True
            self.debate_states[debate_type]["round"] = 1
            print(f"🗣️ 开始{debate_type}辩论")
    
    def next_debate_round(self, debate_type: str) -> bool:
        """进入下一轮辩论，返回是否继续"""
        if debate_type in self.debate_states:
            debate_state = self.debate_states[debate_type]
            if debate_state["active"]:
                debate_state["round"] += 1
                if debate_state["round"] > debate_state["max_rounds"]:
                    debate_state["active"] = False
                    print(f"🏁 {debate_type}辩论结束")
                    return False
                else:
                    print(f"🔄 {debate_type}辩论第{debate_state['round']}轮")
                    return True
        return False
    
    def end_debate(self, debate_type: str):
        """结束辩论"""
        if debate_type in self.debate_states:
            self.debate_states[debate_type]["active"] = False
            print(f"🏁 {debate_type}辩论结束")
    
    def _update_overall_progress(self):
        """更新整体进度"""
        total_agents = len(self.agent_order)
        completed_count = sum(1 for agent in self.agent_order 
                            if self.agent_states[agent]["status"] == "completed")
        
        # 计算当前运行智能体的部分进度
        running_progress = 0.0
        for agent in self.agent_order:
            if self.agent_states[agent]["status"] == "running":
                running_progress = self.agent_states[agent]["progress"] / total_agents
                break
        
        self.workflow_state["overall_progress"] = (completed_count / total_agents) + running_progress
    
    def _all_agents_completed(self) -> bool:
        """检查是否所有智能体都完成了"""
        return all(self.agent_states[agent]["status"] in ["completed", "failed"] 
                  for agent in self.agent_order)
    
    def get_current_progress(self) -> Dict[str, Any]:
        """获取当前进度信息"""
        completed_count = sum(1 for agent in self.agent_order 
                            if self.agent_states[agent]["status"] == "completed")
        total_count = len(self.agent_order)
        
        # 获取当前运行的智能体
        current_agent = self.workflow_state.get("current_agent")
        
        # 计算预估剩余时间（基于平均每个智能体2分钟）
        remaining_agents = total_count - completed_count
        if current_agent and self.agent_states[current_agent]["status"] == "running":
            remaining_agents -= 0.5  # 当前智能体算作半完成
        
        estimated_minutes = max(0, remaining_agents * 2)
        if estimated_minutes < 1:
            estimated_time = "即将完成"
        elif estimated_minutes < 60:
            estimated_time = f"约{int(estimated_minutes)}分钟"
        else:
            hours = int(estimated_minutes // 60)
            minutes = int(estimated_minutes % 60)
            estimated_time = f"约{hours}小时{minutes}分钟"
        
        # 获取当前任务描述
        agent_names = {
            "market_analyst": "市场分析师",
            "sentiment_analyst": "情绪分析师", 
            "news_analyst": "新闻分析师",
            "fundamentals_analyst": "基本面分析师",
            "bull_researcher": "看涨研究员",
            "bear_researcher": "看跌研究员",
            "research_manager": "研究经理",
            "trader": "交易员",
            "aggressive_risk_analyst": "激进风险分析师",
            "safe_risk_analyst": "保守风险分析师",
            "neutral_risk_analyst": "中性风险分析师",
            "risk_manager": "风险经理"
        }
        
        if current_agent and self.agent_states[current_agent]["status"] == "running":
            current_task = agent_names.get(current_agent, current_agent)
        elif completed_count == total_count:
            current_task = "分析完成"
        else:
            current_task = "准备中"
        
        return {
            "progress": self.workflow_state["overall_progress"],
            "current_task": current_task,
            "estimated_time": estimated_time,
            "agent_status": {agent: state["status"] for agent, state in self.agent_states.items()},
            "completed_count": completed_count,
            "total_count": total_count,
            "workflow_status": self.workflow_state["status"]
        }
    
    def get_agent_status(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """获取特定智能体状态"""
        return self.agent_states.get(agent_name)
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """获取工作流状态"""
        return self.workflow_state.copy()
    
    def get_debate_status(self, debate_type: str) -> Optional[Dict[str, Any]]:
        """获取辩论状态"""
        return self.debate_states.get(debate_type)
    
    def reset(self):
        """重置所有状态"""
        for agent in self.agent_order:
            self.agent_states[agent] = {
                "status": "pending",
                "start_time": None,
                "end_time": None,
                "progress": 0.0,
                "current_action": "",
                "results_count": 0,
                "mcp_calls_count": 0
            }
        
        self.workflow_state = {
            "status": "idle",
            "current_agent": None,
            "current_stage": "",
            "overall_progress": 0.0,
            "start_time": None,
            "estimated_completion": None
        }
        
        for debate_type in self.debate_states:
            self.debate_states[debate_type]["active"] = False
            self.debate_states[debate_type]["round"] = 0
        
        print("🔄 状态管理器已重置")
    
    def get_summary(self) -> Dict[str, Any]:
        """获取状态摘要"""
        return {
            "workflow_state": self.workflow_state,
            "agent_states": self.agent_states,
            "debate_states": self.debate_states,
            "agent_order": self.agent_order
        }