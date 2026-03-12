"""
相位比例估算器 - 根据统计结果计算固化配时方案
"""
import logging
from typing import Dict, List
import numpy as np


class PhaseRatioEstimator:
    """
    相位比例估算器 - 将MP统计结果转化为固定配时方案
    """

    def __init__(
        self,
        cycle_seconds: float,
        min_phase_seconds: float = 3.0,
        max_phase_seconds: float = None
    ):
        """
        Args:
            cycle_seconds: 信号灯周期（秒）
            min_phase_seconds: 相位最小时长（秒）
            max_phase_seconds: 相位最大时长（秒），None表示不限制
        """
        self.cycle_seconds = cycle_seconds
        self.min_phase_seconds = min_phase_seconds
        self.max_phase_seconds = max_phase_seconds if max_phase_seconds else cycle_seconds
        self.logger = logging.getLogger(__name__)

    def estimate_fixed_timing(self, phase_ratios: List[float]) -> List[float]:
        """
        根据相位比例估算固定配时时长
        
        Args:
            phase_ratios: 相位比例列表（和为1）
            
        Returns:
            各相位固定时长（秒）列表
        """
        if not phase_ratios:
            return []
        
        num_phases = len(phase_ratios)
        
        # 步骤1: 按原始比例分配周期
        durations = [ratio * self.cycle_seconds for ratio in phase_ratios]
        
        self.logger.debug(f"初始分配: {[f'{d:.2f}' for d in durations]}")
        
        # 步骤2: 检查是否有 duration < min_phase_seconds
        short_phases = [i for i in range(num_phases) if durations[i] < self.min_phase_seconds]
        
        if short_phases:
            self.logger.info(
                f"发现 {len(short_phases)} 个相位时长 < {self.min_phase_seconds}秒: "
                f"相位索引={short_phases}, 原时长={[f'{durations[i]:.2f}' for i in short_phases]}"
            )
            
            # 步骤3: 把所有短相位强制提升到 min_phase_seconds
            for i in short_phases:
                durations[i] = self.min_phase_seconds
            
            # 计算提升后超出的总时长
            deficit = sum(durations) - self.cycle_seconds
            
            self.logger.debug(f"提升短相位后超支: {deficit:.2f}秒")
            
            # 步骤4: 从其他相位中按原比例扣除 deficit
            normal_phases = [i for i in range(num_phases) if i not in short_phases]
            
            if normal_phases:
                # 计算其他相位的原始比例总和
                normal_ratio_sum = sum(phase_ratios[i] for i in normal_phases)
                
                if normal_ratio_sum > 0:
                    # 按比例扣除
                    for i in normal_phases:
                        reduction = deficit * (phase_ratios[i] / normal_ratio_sum)
                        durations[i] -= reduction
                        
                        # 确保扣除后不会变成负数或过小
                        if durations[i] < self.min_phase_seconds:
                            self.logger.warning(
                                f"相位 {i} 扣除后时长 {durations[i]:.2f}秒 < 最小值 {self.min_phase_seconds}秒, "
                                f"可能需要更大的周期或更少的相位数"
                            )
                            durations[i] = self.min_phase_seconds
            else:
                # 所有相位都 < min_phase_seconds，无法满足约束
                total_min = num_phases * self.min_phase_seconds
                self.logger.error(
                    f"所有相位都需要提升到 {self.min_phase_seconds}秒, "
                    f"总需求 {total_min}秒 > 周期 {self.cycle_seconds}秒, 无法满足约束!"
                )
        
        # 应用最大时长约束
        for i in range(num_phases):
            if durations[i] > self.max_phase_seconds:
                durations[i] = self.max_phase_seconds
        
        # 修正总和为周期时长（处理浮点数误差）
        total = sum(durations)
        diff = self.cycle_seconds - total
        
        if abs(diff) > 0.01:  # 如果误差 > 0.01 秒
            self.logger.debug(f"微调前总和: {total:.2f}, 误差: {diff:.2f}")
            
            # 把误差均匀分配到所有相位（避免只调整一个相位）
            adjustment_per_phase = diff / num_phases
            durations = [d + adjustment_per_phase for d in durations]
        
        # 四舍五入到 0.1 秒
        durations = [round(d, 1) for d in durations]
        
        # 最终修正总和（处理四舍五入误差）
        final_diff = self.cycle_seconds - sum(durations)
        if abs(final_diff) > 0.01:
            # 把剩余误差加到最大的相位上
            max_idx = int(np.argmax(durations))
            durations[max_idx] = round(durations[max_idx] + final_diff, 1)
        
        self.logger.info(
            f"最终固定配时: {[f'{d:.1f}' for d in durations]} "
            f"(总和={sum(durations):.1f}, 目标={self.cycle_seconds})"
        )
        
        return durations

    def estimate_all_junctions(
        self,
        statistics: Dict[int, Dict[str, any]]
    ) -> Dict[int, List[float]]:
        """
        为所有路口估算固定配时
        
        Args:
            statistics: PhaseDurationCollector.get_statistics()的输出
            
        Returns:
            {junction_id: [duration0, duration1, ...]}
        """
        fixed_timings = {}
        
        for junction_id, stats in statistics.items():
            phase_ratios = stats["phase_ratios"]
            durations = self.estimate_fixed_timing(phase_ratios)
            fixed_timings[junction_id] = durations
            
            self.logger.info(
                f"路口 {junction_id}: 比例={[f'{r:.3f}' for r in phase_ratios]}, "
                f"时长={[f'{d:.1f}' for d in durations]}"
            )
        
        return fixed_timings
