"""核心模块 - 包含系统核心功能"""

from .state_manager import StateManager
from .data_persistence import DataPersistence

__all__ = ['StateManager', 'DataPersistence']