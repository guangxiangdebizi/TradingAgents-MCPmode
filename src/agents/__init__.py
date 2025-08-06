# 智能体模块
# 包含所有交易决策智能体的实现

from .analysts import (
    MarketAnalyst,
    SentimentAnalyst, 
    NewsAnalyst,
    FundamentalsAnalyst,
    ProductAnalyst
)

from .researchers import (
    BullResearcher,
    BearResearcher
)

from .managers import (
    ResearchManager,
    Trader
)

from .risk_management import (
    AggressiveRiskAnalyst,
    SafeRiskAnalyst,
    NeutralRiskAnalyst,
    RiskManager
)

__all__ = [
    # 分析师
    'MarketAnalyst',
    'SentimentAnalyst',
    'NewsAnalyst', 
    'FundamentalsAnalyst',
    'ProductAnalyst',
    
    # 研究员
    'BullResearcher',
    'BearResearcher',
    
    # 管理层
    'ResearchManager',
    'Trader',
    
    # 风险管理
    'AggressiveRiskAnalyst',
    'SafeRiskAnalyst',
    'NeutralRiskAnalyst',
    'RiskManager'
]