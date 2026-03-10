"""
公交车加权压力控制器 - 基于MaxPressure，但给公交车更高权重
"""
import logging
from typing import Dict, List, Tuple, Optional, Set

from ..road_opt.max_pressure import MaxPressureController


class WeightedPressureController(MaxPressureController):
    """
    公交车加权压力控制器 - 继承MaxPressure，重写压力计算
    给包含公交车的车道更高权重
    """

    def __init__(
        self,
        sim_runner,
        junction_ids: List[int],
        bus_ids: List[int],
        bus_weight_alpha: float,
        cycle_seconds: float,
        min_green_seconds: float = 5.0,
        decision_interval: float = 1.0
    ):
        """
        Args:
            sim_runner: SimulationRunner实例
            junction_ids: 路口ID列表
            bus_ids: 公交车ID列表
            bus_weight_alpha: 公交车权重系数
            cycle_seconds: 信号灯周期（秒）
            min_green_seconds: 最小绿灯时间（秒）
            decision_interval: 决策间隔（秒）
        """
        super().__init__(
            sim_runner=sim_runner,
            junction_ids=junction_ids,
            cycle_seconds=cycle_seconds,
            min_green_seconds=min_green_seconds,
            decision_interval=decision_interval
        )
        
        self.bus_ids_set: Set[int] = set(bus_ids)
        self._bus_ids_list: List[int] = list(bus_ids)
        self.bus_weight_alpha = bus_weight_alpha
        self.logger.info(f"公交车加权MP初始化: {len(bus_ids)} 辆公交, alpha={bus_weight_alpha}")

    def compute_weighted_phase_pressures_from_caches(
        self,
        junction_id: int,
        lane_queues: Dict[int, int],
        lane_bus_counts: Dict[int, int],
    ) -> List[float]:
        """
        用缓存的 lane_queues / lane_bus_counts 计算指定路口各相位的加权压力（不发RPC）。
        """
        phase_in_ids = self.phase_in_lane_ids.get(junction_id)
        if not phase_in_ids:
            return []

        # 计算各相位加权压力
        phase_pressures = []
        for in_lane_ids in phase_in_ids:
            # 加权压力 = Σ queue(in_lane) * (1 + alpha * bus_presence(in_lane))
            pressure = 0.0
            for lane_id in in_lane_ids:
                queue = lane_queues.get(lane_id, 0)
                bus_count = lane_bus_counts.get(lane_id, 0)
                
                # 权重：如果有公交，增加权重
                weight = 1.0 + self.bus_weight_alpha * (1.0 if bus_count > 0 else 0.0)
                pressure += queue * weight
            
            phase_pressures.append(pressure)
        
        return phase_pressures

    async def _get_lane_bus_counts_from_buses(self) -> Dict[int, int]:
        """
        通过“查询公交person runtime → 读取其所在lane_id”来统计车道上的公交数量。

        这样避免每步对大量lane调用 GetLane(exclude_person=False) 拉取全量 persons，
        能显著降低后端压力。
        """
        if not self._bus_ids_list:
            return {}
        if not getattr(self.sim_runner, "engine", None):
            return {}

        try:
            res = await self.sim_runner.engine.client.person_service.GetPersons(
                {"person_ids": self._bus_ids_list}
            )
            lane_bus_counts: Dict[int, int] = {}
            for person in res.get("persons", []):
                motion = person.get("motion", {})
                pos = motion.get("position", {}) if isinstance(motion, dict) else {}
                lane_pos = pos.get("lane_position", {}) if isinstance(pos, dict) else {}
                lane_id = lane_pos.get("lane_id") if isinstance(lane_pos, dict) else None
                if isinstance(lane_id, int):
                    lane_bus_counts[lane_id] = lane_bus_counts.get(lane_id, 0) + 1
            return lane_bus_counts
        except Exception as e:
            self.logger.warning(f"获取车道公交数量失败: {e}")
            return {}

    async def update(self, dt: float):
        """
        重写 update：每步批量拉取一次 lane_queues 和一次 lane_bus_counts，再本地算所有路口压力。
        """
        # 1) 每步一次：全量排队数（exclude_person=True）
        lane_queues = await self.sim_runner.get_lane_queue_counts(None)

        # 2) 每步一次：只查询公交本身的位置，再本地聚合到 lane_bus_counts
        lane_bus_counts = await self._get_lane_bus_counts_from_buses()
        for junction_id in self.junction_ids:
            current_phase = self.current_phases[junction_id]

            # 最小绿灯约束
            current_time = self.current_phase_times[junction_id]
            if current_time < self.min_green_seconds:
                self.current_phase_times[junction_id] += dt
                continue

            pressures = self.compute_weighted_phase_pressures_from_caches(
                junction_id=junction_id,
                lane_queues=lane_queues,
                lane_bus_counts=lane_bus_counts,
            )
            if not pressures:
                self.current_phase_times[junction_id] += dt
                continue

            best_phase = int(pressures.index(max(pressures)))

            if best_phase != current_phase:
                await self.sim_runner.set_traffic_light_phase(
                    junction_id=junction_id,
                    phase_index=best_phase,
                    time_remaining=1e99,
                )
                self.current_phases[junction_id] = best_phase
                self.current_phase_times[junction_id] = 0.0
            else:
                self.current_phase_times[junction_id] += dt

    def get_current_phase(self, junction_id: int) -> int:
        """获取指定路口的当前相位索引"""
        return self.current_phases.get(junction_id, 0)
