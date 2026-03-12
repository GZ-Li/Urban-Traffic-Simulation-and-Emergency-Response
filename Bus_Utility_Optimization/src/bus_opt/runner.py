"""
算法三运行器 - 公交车利用率提升的对比实验
"""
import asyncio
import copy
import json
import logging
import os
import time
import random
from typing import Dict, Any, Optional, List, Tuple

import numpy as np
import pymongo

from trafficlight_rl.engine import SimulatorConfig
from ..runtime.sim_runner import SimulationRunner
from ..metrics.evaluator import MetricsEvaluator, BusUtilizationEvaluator
from .bus_selector import BusSelector
from .weighted_pressure import WeightedPressureController
from ..road_opt.fixed_timing import FixedTimingDeployer, generate_avg_split_timing
from ..road_opt.phase_collector import PhaseDurationCollector
from ..road_opt.phase_ratio import PhaseRatioEstimator


def normalize_person_for_add(person: Dict[str, Any]) -> Dict[str, Any]:
    """清洗Person字段，确保符合AddPerson的schema（保留所有字段，只去除base和id）"""
    field_map = {
        "vehicle_attribute": "vehicleAttribute",
        "bus_attribute": "busAttribute",
        "pedestrian_attribute": "pedestrianAttribute",
        "bike_attribute": "bikeAttribute",
        "output_when_sleep": "outputWhenSleep",
    }
    # import pdb; pdb.set_trace()
    # print(person)
    
    normalized: Dict[str, Any] = {}
    for key, value in person.items():
        if key in field_map:
            normalized[field_map[key]] = value
        else:
            normalized[key] = value

    # AddPerson要求不设置id，并且不接受base字段（其他字段全部保留）
    normalized.pop("id", None)
    normalized.pop("base", None)

    return normalized


def load_person_template_from_mongo(
    mongo_uri: str, agent_db: str, agent_coll: str
) -> Optional[Dict[str, Any]]:
    """从Mongo读取一条静态person配置（data字段）"""
    logger = logging.getLogger(__name__)
    client = pymongo.MongoClient(mongo_uri)
    try:
        db = client[agent_db]
        coll = db[agent_coll]
        doc = coll.find_one({}, {"_id": 0})
        if not doc:
            logger.warning("Mongo中未找到person模板")
            return None
        data = doc.get("data")
        if not isinstance(data, dict):
            logger.warning("Mongo模板缺少data字段")
            return None
        return data
    finally:
        client.close()


async def add_bus_persons(
    runner: SimulationRunner,
    count: int,
    config: SimulatorConfig,
    post_wait_steps: int = 50,
) -> List[int]:
    """通过AddPerson新增车辆，并返回新车辆ID列表（用AddPersonResponse.person_id验证）"""
    logger = logging.getLogger(__name__)
    if count <= 0:
        return []

    # 从Mongo读取静态模板
    template = load_person_template_from_mongo(
        config.mongo_uri, config.agent_db, config.agent_coll
    )
    if not template:
        logger.warning("无法从Mongo读取person模板，AddPerson失败")
        return []

    person = normalize_person_for_add(copy.deepcopy(template))
    if not person:
        logger.warning("模板person清洗后为空，AddPerson失败")
        return []

    # 调用AddPerson并收集person_id（不依赖GetAllVehicles）
    logger.info(f"开始新增 {count} 辆公交车...")
    added_ids: List[int] = []
    for _ in range(count):
        resp = await runner.engine.client.person_service.AddPerson(
            {"person": copy.deepcopy(person)}
        )
        pid = resp.get("person_id") if isinstance(resp, dict) else None
        if isinstance(pid, int):
            added_ids.append(pid)

    logger.info(f"AddPerson返回person_id数量: {len(added_ids)}")
    if added_ids:
        logger.info(f"新增公交车ID示例: {added_ids[:5]}")

    # 推进一些step，让新增person有机会"出生"
    if post_wait_steps > 0:
        logger.info(f"推进 {post_wait_steps} 步，等待新增公交车生效...")
        for _ in range(post_wait_steps):
            runner.step(1)
            await asyncio.sleep(0)
    return added_ids


def save_bus_ids(log_dir: str, bus_ids: List[int]):
    """保存公交车ID列表"""
    bus_file = os.path.join(log_dir, "bus_ids.json")
    with open(bus_file, "w") as f:
        json.dump({"bus_ids": bus_ids, "count": len(bus_ids)}, f, indent=2)


async def run_fixed_random_scenario(
    config: SimulatorConfig,
    log_dir: str,
    total_steps: int,
    interval: int,
    bus_ids: List[int],
    add_bus_count: int,
    bus_speed_threshold: float,
    cycle_seconds: float,
    seed: Optional[int] = None,
    sample_interval: int = 10
) -> Dict[str, Any]:
    """
    Scenario: 随机固定配时（无优化baseline）
    
    Args:
        config: 仿真配置
        log_dir: 日志目录
        total_steps: 总步数
        interval: 间隔（秒）
        bus_ids: 公交车ID列表
        add_bus_count: 通过AddPerson新增公交数量
        bus_speed_threshold: 速度阈值（m/s）
        cycle_seconds: 周期时长（秒）
        seed: 随机种子
        sample_interval: 采样间隔（步）
        
    Returns:
        指标字典
    """
    logger = logging.getLogger(__name__)
    logger.info(f"开始运行 FixedRandom scenario (周期={cycle_seconds}s, 种子={seed})")
    
    if seed is not None:
        random.seed(seed)
    
    with SimulationRunner(config, log_dir) as runner:
        if add_bus_count > 0:
            added_bus_ids = await add_bus_persons(runner, add_bus_count, config, post_wait_steps=10)
            if added_bus_ids:
                bus_ids = bus_ids + added_bus_ids
                logger.info(f"新增公交车合并后总数: {len(bus_ids)}")
        save_bus_ids(log_dir, bus_ids)

        evaluator = MetricsEvaluator(runner)
        bus_evaluator = BusUtilizationEvaluator(runner, bus_ids, bus_speed_threshold)
        
        # 获取路口信息
        map_data = runner.get_map_data()
        
        # 生成随机固定配时方案
        fixed_timings = {}
        for junction in map_data.junctions:
            num_phases = len(junction.phases) if junction.phases else len(junction.fixed_program.phases)
            if num_phases > 0:
                # 平均分配作为"随机"baseline（可扩展为真随机）
                fixed_timings[junction.id] = generate_avg_split_timing(cycle_seconds, num_phases)
        
        # 保存配时方案
        timing_file = os.path.join(log_dir, "fixed_timing_random.json")
        with open(timing_file, "w") as f:
            json.dump(fixed_timings, f, indent=2)
        
        # 部署固定配时
        deployer = FixedTimingDeployer(runner, fixed_timings)
        await deployer.initialize()
        
        for step in range(total_steps):
            # 更新固定配时
            await deployer.update(interval)
            
            # 定期采样
            if step % sample_interval == 0:
                await evaluator.sample_metrics()
                await bus_evaluator.sample(interval * sample_interval)
            
            runner.step(1)
            
            if (step + 1) % 100 == 0:
                logger.info(f"FixedRandom进度: {step + 1}/{total_steps}")
        
        # 收集指标
        metrics = await evaluator.compute_final_metrics()
        bus_metrics = bus_evaluator.get_metrics()
        metrics.update(bus_metrics)
        
        logger.info(f"FixedRandom完成: 公交利用率={bus_metrics['bus_utilization']:.3f}")
        
        return metrics


async def run_bus_weighted_mp_scenario(
    config: SimulatorConfig,
    log_dir: str,
    total_steps: int,
    interval: int,
    bus_ids: List[int],
    add_bus_count: int,
    bus_speed_threshold: float,
    bus_weight_alpha: float,
    cycle_seconds: float,
    min_green_seconds: float,
    sample_interval: int = 5
) -> Dict[str, Any]:
    """
    Scenario: 公交车加权MaxPressure
    
    Args:
        config: 仿真配置
        log_dir: 日志目录
        total_steps: 总步数
        interval: 间隔（秒）
        bus_ids: 公交车ID列表
        add_bus_count: 通过AddPerson新增公交数量
        bus_speed_threshold: 速度阈值（m/s）
        bus_weight_alpha: 公交权重系数
        cycle_seconds: 周期时长（秒）
        min_green_seconds: 最小绿灯（秒）
        sample_interval: 采样间隔（步）
        
    Returns:
        指标字典
    """
    logger = logging.getLogger(__name__)
    logger.info(f"开始运行 BusWeightedMP scenario (alpha={bus_weight_alpha})")
    
    with SimulationRunner(config, log_dir) as runner:
        if add_bus_count > 0:
            added_bus_ids = await add_bus_persons(runner, add_bus_count, config, post_wait_steps=10)
            if added_bus_ids:
                bus_ids = bus_ids + added_bus_ids
                logger.info(f"新增公交车合并后总数: {len(bus_ids)}")
        save_bus_ids(log_dir, bus_ids)

        evaluator = MetricsEvaluator(runner)
        bus_evaluator = BusUtilizationEvaluator(runner, bus_ids, bus_speed_threshold)
        
        # 获取路口信息
        map_data = runner.get_map_data()
        junction_ids = [j.id for j in map_data.junctions]
        
        # 初始化公交加权MP控制器
        controller = WeightedPressureController(
            sim_runner=runner,
            junction_ids=junction_ids,
            bus_ids=bus_ids,
            bus_weight_alpha=bus_weight_alpha,
            cycle_seconds=cycle_seconds,
            min_green_seconds=min_green_seconds,
            decision_interval=interval
        )
        
        for step in range(total_steps):
            print(f"step: {step}")
            if step >=5:
                import pdb
                pdb.set_trace()
                metrics = await evaluator.compute_final_metrics()
                bus_metrics = bus_evaluator.get_metrics()
                metrics.update(bus_metrics)

                logger.info(f"BusWeightedMP完成: 公交利用率={bus_metrics['bus_utilization']:.3f}")
                return metrics

                # import pdb; pdb.set_trace()
                # print(step)
            # 更新公交加权MP
            await controller.update(interval)
            
            # 定期采样
            if step % sample_interval == 0:
                await evaluator.sample_metrics()
                await bus_evaluator.sample(interval * sample_interval)
            
            runner.step(1)
            
            if (step + 1) % 100 == 0:
                logger.info(f"BusWeightedMP进度: {step + 1}/{total_steps}")
        
        # 收集指标
        metrics = await evaluator.compute_final_metrics()
        bus_metrics = bus_evaluator.get_metrics()
        metrics.update(bus_metrics)
        
        logger.info(f"BusWeightedMP完成: 公交利用率={bus_metrics['bus_utilization']:.3f}")
        
        return metrics


async def run_bus_weighted_mp_then_fixed_scenario(
    config: SimulatorConfig,
    log_dir: str,
    total_steps: int,
    interval: int,
    bus_ids: List[int],
    add_bus_count: int,
    bus_speed_threshold: float,
    bus_weight_alpha: float,
    cycle_seconds: float,
    min_green_seconds: float,
    mp_warmup_cycles: int,
    mp_collect_cycles: int,
    min_phase_seconds: float,
    sample_interval: int = 10
) -> Dict[str, Any]:
    """
    Scenario: 公交加权MP后固定配时 - 两次仿真
    第一次: 运行公交加权MP并统计相位占比
    第二次: 使用固化配时运行并评估公交利用率
    
    Args:
        config: 仿真配置
        log_dir: 日志目录
        total_steps: 第二次仿真的总步数
        interval: 间隔（秒）
        bus_ids: 公交车ID列表
        add_bus_count: 通过AddPerson新增公交数量
        bus_speed_threshold: 公交速度阈值（m/s）
        bus_weight_alpha: 公交权重系数
        cycle_seconds: 周期时长（秒）
        min_green_seconds: 最小绿灯（秒）
        mp_warmup_cycles: MP热身周期数
        mp_collect_cycles: MP统计周期数
        min_phase_seconds: 相位最小时长（秒）
        sample_interval: 采样间隔（步）
        
    Returns:
        指标字典
    """
    logger = logging.getLogger(__name__)
    logger.info("开始运行 BusWeightedMP-then-Fixed scenario")
    
    # ===== 第一次仿真: 运行公交加权MP并统计 =====
    logger.info(f"第一次仿真: 公交加权MP统计 (热身={mp_warmup_cycles}周期, 统计={mp_collect_cycles}周期)")
    
    mp_log_dir = os.path.join(log_dir, "phase1_mp_collection")
    os.makedirs(mp_log_dir, exist_ok=True)
    
    # 计算第一次仿真需要的步数
    total_cycles = mp_warmup_cycles + mp_collect_cycles
    mp_steps = int((total_cycles * cycle_seconds) / interval)
    
    with SimulationRunner(config, mp_log_dir) as runner:
        # AddPerson 新增公交（第一次仿真）
        phase1_bus_ids = bus_ids.copy()
        if add_bus_count > 0:
            added_ids = await add_bus_persons(runner, add_bus_count, config, post_wait_steps=10)
            if added_ids:
                phase1_bus_ids = phase1_bus_ids + added_ids
                logger.info(f"第一次仿真新增公交: {len(added_ids)} 辆")
        
        # 获取路口信息并过滤有效路口
        map_data = runner.get_map_data()
        valid_junction_ids = []
        num_phases_per_junction = {}
        for junction in map_data.junctions:
            num_phases = len(junction.phases) if junction.phases else len(junction.fixed_program.phases)
            if num_phases > 0:
                valid_junction_ids.append(junction.id)
                num_phases_per_junction[junction.id] = num_phases
        
        junction_ids = valid_junction_ids
        logger.info(f"找到 {len(junction_ids)} 个有效信控路口")
        
        # 初始化公交加权MP控制器
        controller = WeightedPressureController(
            sim_runner=runner,
            junction_ids=junction_ids,
            bus_ids=phase1_bus_ids,
            bus_weight_alpha=bus_weight_alpha,
            cycle_seconds=cycle_seconds,
            min_green_seconds=min_green_seconds,
            decision_interval=interval
        )
        
        # 初始化相位收集器
        collector = PhaseDurationCollector(
            junction_ids=junction_ids,
            cycle_seconds=cycle_seconds,
            num_phases_per_junction=num_phases_per_junction
        )
        
        # 运行公交加权MP
        for step in range(mp_steps):
            # 更新控制器
            await controller.update(interval)
            
            # 收集相位统计
            for jid in junction_ids:
                current_phase = controller.get_current_phase(jid)
                collector.update(jid, current_phase, interval)
            
            # 推进时间
            collector.advance_time(interval)
            runner.step(1)
            
            if (step + 1) % 100 == 0:
                logger.info(f"公交加权MP统计进度: {step + 1}/{mp_steps}")
        
        # 获取统计结果
        stats = collector.get_statistics(warmup_cycles=mp_warmup_cycles)
        logger.info(f"收集到 {len(stats)} 个路口的相位统计")
    
    # 生成固定配时方案
    estimator = PhaseRatioEstimator(
        cycle_seconds=cycle_seconds,
        min_phase_seconds=min_phase_seconds
    )
    fixed_timings = estimator.estimate_all_junctions(stats)
    
    # 保存固定配时方案
    timing_file = os.path.join(log_dir, "fixed_timing_bus_weighted_mp.json")
    with open(timing_file, "w") as f:
        json.dump(fixed_timings, f, indent=2)
    logger.info(f"固定配时方案保存到: {timing_file}")
    
    # ===== 第二次仿真: 使用固定配时运行并评估 =====
    logger.info(f"第二次仿真: 固定配时评估 (总步数={total_steps})")
    
    eval_log_dir = os.path.join(log_dir, "phase2_evaluation")
    os.makedirs(eval_log_dir, exist_ok=True)
    
    with SimulationRunner(config, eval_log_dir) as runner:
        # AddPerson 新增公交（第二次仿真，重新生成ID）
        phase2_bus_ids = bus_ids.copy()
        if add_bus_count > 0:
            added_ids = await add_bus_persons(runner, add_bus_count, config, post_wait_steps=10)
            if added_ids:
                phase2_bus_ids = phase2_bus_ids + added_ids
                logger.info(f"第二次仿真新增公交: {len(added_ids)} 辆")
        
        # 保存第二次仿真的公交ID列表
        save_bus_ids(log_dir, phase2_bus_ids)
        
        evaluator = MetricsEvaluator(runner)
        bus_evaluator = BusUtilizationEvaluator(runner, phase2_bus_ids, bus_speed_threshold)
        
        # 部署固定配时
        deployer = FixedTimingDeployer(runner, fixed_timings)
        await deployer.initialize()
        
        for step in range(total_steps):
            print(f"step: {step}")
            if step>90:
                
                metrics = await evaluator.compute_final_metrics()
                bus_metrics = bus_evaluator.get_metrics()
                metrics.update(bus_metrics)

                logger.info(f"BusWeightedMP-then-Fixed完成: 公交利用率={bus_metrics['bus_utilization']:.3f}")

                return metrics
                
            
            # 更新固定配时
            await deployer.update(interval)
            
            # 定期采样
            if step % sample_interval == 0:
                await evaluator.sample_metrics()
                await bus_evaluator.sample(interval * sample_interval)
            
            runner.step(1)
            
            if (step + 1) % 100 == 0:
                logger.info(f"固定配时评估进度: {step + 1}/{total_steps}")
        
        # 收集指标
        metrics = await evaluator.compute_final_metrics()
        bus_metrics = bus_evaluator.get_metrics()
        metrics.update(bus_metrics)
        
        logger.info(f"BusWeightedMP-then-Fixed完成: 公交利用率={bus_metrics['bus_utilization']:.3f}")
        
        return metrics


def run_bus_opt_experiment(
    scenario: str,
    mongo_uri: str,
    map_db: str,
    map_coll: str,
    agent_db: str,
    agent_coll: str,
    start_step: int,
    total_steps: int,
    interval: int,
    output_dir: str,
    bus_ids: List[int],
    add_bus_count: int,
    bus_speed_threshold: float,
    bus_weight_alpha: float = 2.0,
    cycle_seconds: float = 90.0,
    min_green_seconds: float = 5.0,
    seed: Optional[int] = None,
    mp_warmup_cycles: int = 10,
    mp_collect_cycles: int = 50,
    min_phase_seconds: float = 3.0,
    output_sql_dsn: str = "",
    output_job_prefix: str = "bus_opt_",
    output_bbox: Optional[Tuple[float, float, float, float]] = None
) -> Dict[str, Any]:
    """
    运行公交车优化实验
    
    Args:
        scenario: 场景名 ("fixed_random" | "bus_weighted_mp" | "bus_weighted_mp_fixed")
        mongo_uri: MongoDB URI
        map_db: 地图数据库
        map_coll: 地图集合
        agent_db: Agent数据库
        agent_coll: Agent集合
        start_step: 起始步
        total_steps: 总步数
        interval: 间隔（秒）
        output_dir: 输出目录
        bus_ids: 公交车ID列表
        add_bus_count: 通过AddPerson新增公交数量
        bus_speed_threshold: 公交速度阈值（m/s）
        bus_weight_alpha: 公交权重系数
        cycle_seconds: 周期时长（秒）
        min_green_seconds: 最小绿灯（秒）
        seed: 随机种子
        output_sql_dsn: SQL输出DSN
        output_job_prefix: Job名前缀
        output_bbox: 输出边界框
        
    Returns:
        指标字典
    """
    logger = logging.getLogger(__name__)
    os.makedirs(output_dir, exist_ok=True)
    
    # 设置随机种子
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
        logger.info(f"设置随机种子: {seed}")
    
    # 保存实验配置
    exp_config = {
        "scenario": scenario,
        "total_steps": total_steps,
        "interval": interval,
        "bus_ids": bus_ids,
        "num_buses": len(bus_ids),
        "bus_speed_threshold": bus_speed_threshold,
        "add_bus_count": add_bus_count,
        "bus_weight_alpha": bus_weight_alpha,
        "cycle_seconds": cycle_seconds,
        "min_green_seconds": min_green_seconds,
        "mp_warmup_cycles": mp_warmup_cycles,
        "mp_collect_cycles": mp_collect_cycles,
        "min_phase_seconds": min_phase_seconds,
        "seed": seed,
        "timestamp": time.strftime("%Y%m%d-%H%M%S")
    }
    with open(os.path.join(output_dir, "experiment_config.json"), "w") as f:
        json.dump(exp_config, f, indent=2)
    
    # 保存公交车ID列表
    bus_file = os.path.join(output_dir, "bus_ids.json")
    with open(bus_file, "w") as f:
        json.dump({"bus_ids": bus_ids, "count": len(bus_ids)}, f, indent=2)
    
    # 创建配置
    config = SimulatorConfig(
        mongo_uri=mongo_uri,
        map_db=map_db,
        map_coll=map_coll,
        agent_db=agent_db,
        agent_coll=agent_coll,
        start_step=start_step,
        total_step=total_steps,
        interval=interval,
        use_max_pressure=False,  # 我们手动控制
        output_sql_dsn=output_sql_dsn,
        output_job_prefix=f"{output_job_prefix}{scenario}_",
        output_bbox=output_bbox
    )
    
    # 根据scenario选择运行函数
    if scenario == "fixed_random":
        metrics = asyncio.run(run_fixed_random_scenario(
            config=config,
            log_dir=output_dir,
            total_steps=total_steps,
            interval=interval,
            bus_ids=bus_ids,
            add_bus_count=add_bus_count,
            bus_speed_threshold=bus_speed_threshold,
            cycle_seconds=cycle_seconds,
            seed=seed
        ))
    
    elif scenario == "bus_weighted_mp":
        metrics = asyncio.run(run_bus_weighted_mp_scenario(
            config=config,
            log_dir=output_dir,
            total_steps=total_steps,
            interval=interval,
            bus_ids=bus_ids,
            add_bus_count=add_bus_count,
            bus_speed_threshold=bus_speed_threshold,
            bus_weight_alpha=bus_weight_alpha,
            cycle_seconds=cycle_seconds,
            min_green_seconds=min_green_seconds
        ))
    
    elif scenario == "bus_weighted_mp_fixed":
        metrics = asyncio.run(run_bus_weighted_mp_then_fixed_scenario(
            config=config,
            log_dir=output_dir,
            total_steps=total_steps,
            interval=interval,
            bus_ids=bus_ids,
            add_bus_count=add_bus_count,
            bus_speed_threshold=bus_speed_threshold,
            bus_weight_alpha=bus_weight_alpha,
            cycle_seconds=cycle_seconds,
            min_green_seconds=min_green_seconds,
            mp_warmup_cycles=mp_warmup_cycles,
            mp_collect_cycles=mp_collect_cycles,
            min_phase_seconds=min_phase_seconds
        ))
    
    else:
        raise ValueError(f"不支持的scenario: {scenario}")
    
    # 保存最终指标
    metrics_file = os.path.join(output_dir, "metrics.json")
    with open(metrics_file, "w") as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"\n实验完成！结果保存在: {output_dir}")
    
    return metrics
