"""
扫雪策略模块
包含不同的扫雪路径规划策略
"""

from .greedy_strategy import GreedyStrategy
from .random_strategy import RandomStrategy

__all__ = ['GreedyStrategy', 'RandomStrategy']

# 策略注册表
STRATEGY_REGISTRY = {
    'greedy': GreedyStrategy,
    'random': RandomStrategy,
}


def get_strategy(strategy_name):
    """
    获取指定的策略类
    
    Args:
        strategy_name: 策略名称 ('greedy' 或 'random')
    
    Returns:
        策略类
    """
    if strategy_name not in STRATEGY_REGISTRY:
        raise ValueError(f"未知策略: {strategy_name}. 可用策略: {list(STRATEGY_REGISTRY.keys())}")
    return STRATEGY_REGISTRY[strategy_name]
