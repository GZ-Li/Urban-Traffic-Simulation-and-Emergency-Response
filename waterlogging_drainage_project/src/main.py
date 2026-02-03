"""
Main script for waterlogging drainage strategy evaluation
Runs the complete pipeline: generate -> evaluate -> compare
"""

import os
import sys
import subprocess
from datetime import datetime

def run_command(cmd, description):
    """Run a command and check for errors"""
    print(f"\n{'='*80}")
    print(f"  {description}")
    print(f"{'='*80}")
    
    result = subprocess.run(cmd, shell=True, capture_output=False)
    
    if result.returncode != 0:
        print(f"\n[ERROR] {description} failed!")
        sys.exit(1)
    
    return result.returncode

def main():
    print("\n" + "="*80)
    print("  Waterlogging Drainage Evaluation - Full Pipeline")
    print("="*80)
    
    start_time = datetime.now()
    
    # Step 1: Generate strategies
    print("\n[Step 1/4] Generating strategies...")
    run_command("python generate_strategy.py", "Strategy Generation")
    
    # Find the latest strategy folder
    results_dir = "results"
    strategy_folders = [f for f in os.listdir(results_dir) if f.startswith("strategies_")]
    if not strategy_folders:
        print("[ERROR] No strategy folder found!")
        sys.exit(1)
    
    latest_folder = sorted(strategy_folders)[-1]
    strategy_path = os.path.join(results_dir, latest_folder)
    
    best_strategy = os.path.join(strategy_path, "best_strategy.json")
    worst_strategy = os.path.join(strategy_path, "worst_strategy.json")
    
    print(f"\n  Using strategies from: {strategy_path}")
    
    # Step 2: Evaluate best strategy
    print("\n[Step 2/4] Evaluating BEST strategy (high to low traffic flow)...")
    run_command(
        f"python evaluate_strategy.py -s {best_strategy} -o {strategy_path}",
        "Best Strategy Evaluation"
    )
    
    # Step 3: Evaluate worst strategy
    print("\n[Step 3/4] Evaluating WORST strategy (low to high traffic flow)...")
    run_command(
        f"python evaluate_strategy.py -s {worst_strategy} -o {strategy_path}",
        "Worst Strategy Evaluation"
    )
    
    # Step 4: Compare strategies
    print("\n[Step 4/4] Comparing strategies...")
    eval_best = os.path.join(strategy_path, "evaluation_best.json")
    eval_worst = os.path.join(strategy_path, "evaluation_worst.json")
    
    run_command(
        f"python compare_strategies.py -e {eval_best} {eval_worst}",
        "Strategy Comparison"
    )
    
    # Summary
    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()
    
    print("\n" + "="*80)
    print("  PIPELINE COMPLETED SUCCESSFULLY!")
    print("="*80)
    print(f"  Total time: {elapsed:.1f} seconds")
    print(f"  Results saved in: {strategy_path}")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
