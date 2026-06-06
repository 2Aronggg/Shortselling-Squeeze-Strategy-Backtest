"""
Short Interest Factor Backtesting
메인 백테스팅 엔진

4가지 Phase:
1. 데이터 로드 & 전처리
2. 팩터 신호 생성
3. 전략 백테스팅 (전략 2, 3)
4. 성과 분석 & 시각화
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

# 같은 디렉토리의 utils.py import
from utils import (
    load_config,
    load_and_merge_data,
    generate_all_signals,
    calculate_metrics,
    plot_cumulative_return,
    plot_monthly_returns,
    plot_sharpe_comparison,
    save_metrics_to_csv,
    save_summary_to_txt
)


def backtest_strategy2(df, alpha=0.15, transaction_cost=0.0005):
    """
    전략 2: 팩터 오버레이 (공매도 신호만 사용)
    
    조정 비중 = 기본 비중 + 0.15 × 공매도신호 / n
    
    Args:
        df: 팩터 신호가 포함된 데이터프레임
        alpha: 팩터 오버레이 강도 (기본 0.15)
        transaction_cost: 거래비용 (기본 0.05%)
    
    Returns:
        dict: {
            'daily_pnl': 일간 손익,
            'daily_return': 일간 수익률,
            'cumulative_return': 누적 수익
        }
    """
    print("\n📈 전략 2 백테스팅 중 (팩터 오버레이)...")
    
    df = df.copy()
    
    # 기본 비중 설정 (동일비중)
    n_stocks = df['ticker'].nunique()
    base_weight = 1 / n_stocks
    
    results = []
    
    for date in sorted(df['date'].unique()):
        date_data = df[df['date'] == date].copy()
        
        # 조정 비중 계산
        # 조정 비중 = 기본 비중 + 0.15 × 공매도신호 / n
        adjusted_weight = base_weight + (alpha * date_data['f_short'] / n_stocks)
        
        # 일간 수익 계산
        daily_return = (adjusted_weight * date_data['return']).sum()
        
        # 거래비용 적용
        daily_return -= transaction_cost
        
        results.append({
            'date': date,
            'daily_return': daily_return
        })
    
    # 결과 정리
    result_df = pd.DataFrame(results)
    result_df['date'] = pd.to_datetime(result_df['date'])
    result_df = result_df.set_index('date')
    result_df['cumulative_return'] = (1 + result_df['daily_return']).cumprod()
    
    print(f"✅ 전략 2 백테스팅 완료: {len(result_df)} 거래일")
    
    return {
        'daily_return': result_df['daily_return'],
        'daily_pnl': result_df['daily_return'],
        'cumulative_return': result_df['cumulative_return']
    }


def backtest_strategy3(df, alpha=0.15, transaction_cost=0.0005):
    """
    전략 3: 멀티팩터 (3개 팩터 결합)
    
    결합신호 = (공매도 + 밸류 + 모멘텀) / 3
    조정 비중 = 기본 비중 + 0.15 × 결합신호 / n
    
    Args:
        df: 팩터 신호가 포함된 데이터프레임
        alpha: 팩터 오버레이 강도 (기본 0.15)
        transaction_cost: 거래비용 (기본 0.05%)
    
    Returns:
        dict: {
            'daily_pnl': 일간 손익,
            'daily_return': 일간 수익률,
            'cumulative_return': 누적 수익
        }
    """
    print("\n📈 전략 3 백테스팅 중 (멀티팩터)...")
    
    df = df.copy()
    
    # 기본 비중 설정 (동일비중)
    n_stocks = df['ticker'].nunique()
    base_weight = 1 / n_stocks
    
    results = []
    
    for date in sorted(df['date'].unique()):
        date_data = df[df['date'] == date].copy()
        
        # 3개 팩터 신호 평균
        combined_signal = (
            date_data['f_short'] +
            date_data['f_value'] +
            date_data['f_momentum']
        ) / 3
        
        # 조정 비중 계산
        adjusted_weight = base_weight + (alpha * combined_signal / n_stocks)
        
        # 일간 수익 계산
        daily_return = (adjusted_weight * date_data['return']).sum()
        
        # 거래비용 적용
        daily_return -= transaction_cost
        
        results.append({
            'date': date,
            'daily_return': daily_return
        })
    
    # 결과 정리
    result_df = pd.DataFrame(results)
    result_df['date'] = pd.to_datetime(result_df['date'])
    result_df = result_df.set_index('date')
    result_df['cumulative_return'] = (1 + result_df['daily_return']).cumprod()
    
    print(f"✅ 전략 3 백테스팅 완료: {len(result_df)} 거래일")
    
    return {
        'daily_return': result_df['daily_return'],
        'daily_pnl': result_df['daily_return'],
        'cumulative_return': result_df['cumulative_return']
    }


def backtest_benchmark(df, transaction_cost=0.0005):
    """
    벤치마크: 동일비중 포트폴리오 (신호 없음)
    
    Args:
        df: 데이터프레임
        transaction_cost: 거래비용
    
    Returns:
        dict: 벤치마크 결과
    """
    print("\n📈 벤치마크 백테스팅 중 (동일비중)...")
    
    df = df.copy()
    
    # 기본 비중 설정 (동일비중, 신호 없음)
    n_stocks = df['ticker'].nunique()
    base_weight = 1 / n_stocks
    
    results = []
    
    for date in sorted(df['date'].unique()):
        date_data = df[df['date'] == date].copy()
        
        # 일간 수익 계산 (조정 없음)
        daily_return = (base_weight * date_data['return']).sum()
        
        # 거래비용 적용
        daily_return -= transaction_cost
        
        results.append({
            'date': date,
            'daily_return': daily_return
        })
    
    # 결과 정리
    result_df = pd.DataFrame(results)
    result_df['date'] = pd.to_datetime(result_df['date'])
    result_df = result_df.set_index('date')
    result_df['cumulative_return'] = (1 + result_df['daily_return']).cumprod()
    
    print(f"✅ 벤치마크 백테스팅 완료: {len(result_df)} 거래일")
    
    return {
        'daily_return': result_df['daily_return'],
        'daily_pnl': result_df['daily_return'],
        'cumulative_return': result_df['cumulative_return']
    }


def save_daily_pnl(result_dict, strategy_name, output_path='results'):
    """
    일간 손익을 CSV로 저장
    
    Args:
        result_dict: 백테스팅 결과 딕셔너리
        strategy_name: 전략명
        output_path: 저장 경로
    """
    import os
    os.makedirs(output_path, exist_ok=True)
    
    df_pnl = result_dict['daily_pnl'].reset_index()
    df_pnl.columns = ['date', 'daily_return']
    df_pnl['date'] = df_pnl['date'].astype(str)
    
    output_file = f"{output_path}/daily_pnl_{strategy_name}.csv"
    df_pnl.to_csv(output_file, index=False)
    print(f"   ✅ 저장: {output_file}")


def print_results(metrics_dict):
    """
    결과를 콘솔에 출력
    
    Args:
        metrics_dict: {전략명: 지표 dict} 형태
    """
    print("\n" + "="*70)
    print("🏆 최종 결과")
    print("="*70)
    
    print(f"\n{'전략':<20} {'Sharpe':<12} {'Return':<12} {'MDD':<12} {'Win Rate':<12}")
    print("-"*70)
    
    for strategy, metrics in metrics_dict.items():
        sharpe = metrics['sharpe']
        ret = metrics['total_return'] * 100
        mdd = metrics['mdd'] * 100
        wr = metrics['win_rate'] * 100
        
        print(f"{strategy:<20} {sharpe:>10.2f}  {ret:>9.2f}%  {mdd:>9.2f}%  {wr:>9.1f}%")
    
    print("="*70)
    
    # 최고 Sharpe 전략
    best_strategy = max(metrics_dict.items(), key=lambda x: x[1]['sharpe'])
    print(f"\n✅ 최우수 전략: {best_strategy[0]}")
    print(f"   - Sharpe: {best_strategy[1]['sharpe']:.2f}")
    print(f"   - Return: {best_strategy[1]['total_return']*100:.2f}%")
    print(f"   - MDD: {best_strategy[1]['mdd']*100:.2f}%")
    print("="*70 + "\n")


def main():
    """
    메인 함수: 4가지 Phase 실행
    """
    
    print("\n" + "="*70)
    print("🚀 SHORT INTEREST FACTOR BACKTESTING")
    print("="*70)
    
    # ========== PHASE 1: 데이터 로드 ==========
    print("\n[PHASE 1] 데이터 로드 & 전처리")
    print("-"*70)
    
    try:
        # 데이터 로드 (경로 수정 필요 시 여기서!)
        df = load_and_merge_data(
            short_interest_path='data/raw/short_interest_raw.csv',
            price_path='data/raw/price_data_raw.csv',
            pbr_path='data/raw/pbr_data_raw.csv'
        )
    except FileNotFoundError as e:
        print(f"❌ 데이터 파일을 찾을 수 없습니다: {e}")
        print("   다음 경로에 파일을 배치하세요:")
        print("   - data/raw/short_interest_raw.csv")
        print("   - data/raw/price_data_raw.csv")
        print("   - data/raw/pbr_data_raw.csv")
        return
    
    # ========== PHASE 2: 팩터 신호 생성 ==========
    print("\n[PHASE 2] 팩터 신호 생성")
    print("-"*70)
    
    df = generate_all_signals(df)
    
    # ========== PHASE 3: 백테스팅 ==========
    print("\n[PHASE 3] 백테스팅")
    print("-"*70)
    
    # 설정 로드
    config = load_config('config/config.yaml')
    alpha = config.get('alpha', 0.15)
    transaction_cost = config.get('transaction_cost', 0.0005)
    risk_free_rate = config.get('risk_free_rate', 0.035)
    
    # 벤치마크
    benchmark_result = backtest_benchmark(df, transaction_cost)
    
    # 전략 2
    strategy2_result = backtest_strategy2(df, alpha, transaction_cost)
    
    # 전략 3
    strategy3_result = backtest_strategy3(df, alpha, transaction_cost)
    
    # ========== PHASE 4: 성과 분석 ==========
    print("\n[PHASE 4] 성과 분석 & 시각화")
    print("-"*70)
    
    # 성과 지표 계산
    metrics_benchmark = calculate_metrics(benchmark_result['daily_return'], risk_free_rate)
    metrics_s2 = calculate_metrics(strategy2_result['daily_return'], risk_free_rate)
    metrics_s3 = calculate_metrics(strategy3_result['daily_return'], risk_free_rate)
    
    metrics_dict = {
        'Benchmark': metrics_benchmark,
        'Strategy 2': metrics_s2,
        'Strategy 3': metrics_s3
    }
    
    # 결과 출력
    print_results(metrics_dict)
    
    # 결과 저장
    print("\n📁 결과 저장 중...")
    
    # CSV 저장
    save_metrics_to_csv(metrics_dict)
    
    # 일간 손익 저장
    save_daily_pnl(benchmark_result, 'benchmark')
    save_daily_pnl(strategy2_result, 'strategy2')
    save_daily_pnl(strategy3_result, 'strategy3')
    
    # 요약 저장
    save_summary_to_txt(metrics_dict)
    
    # 시각화
    print("\n📊 시각화 생성 중...")
    
    # 누적 수익 차트
    cumulative_dict = {
        'Benchmark': metrics_benchmark['cumulative'],
        'Strategy 2': metrics_s2['cumulative'],
        'Strategy 3': metrics_s3['cumulative']
    }
    plot_cumulative_return(cumulative_dict, list(cumulative_dict.keys()))
    
    # 월별 수익 차트
    daily_pnl_dict = {
        'Strategy 2': strategy2_result['daily_pnl'],
        'Strategy 3': strategy3_result['daily_pnl']
    }
    plot_monthly_returns(daily_pnl_dict)
    
    # Sharpe 비교 차트
    plot_sharpe_comparison(metrics_dict)
    
    print("\n" + "="*70)
    print("✅ 백테스팅 완료!")
    print("="*70)
    print("\n📁 생성된 파일:")
    print("   results/")
    print("   ├── metrics.csv           (성과 지표)")
    print("   ├── summary.txt           (최종 요약)")
    print("   ├── daily_pnl_benchmark.csv")
    print("   ├── daily_pnl_strategy2.csv")
    print("   └── daily_pnl_strategy3.csv")
    print("\n   visualizations/")
    print("   ├── cumulative_return.png")
    print("   ├── monthly_returns.png")
    print("   └── sharpe_comparison.png")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
