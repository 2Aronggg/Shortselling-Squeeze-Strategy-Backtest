"""
Helper Functions for Short Interest Backtesting

Functions:
- load_and_merge_data(): 데이터 로드 및 병합
- generate_signals(): 팩터 신호 생성
- calculate_metrics(): 성과 지표 계산
- plot_results(): 시각화
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import yaml
import os


def load_config(config_path="config/config.yaml"):
    """
    설정 파일 로드
    
    Args:
        config_path: config.yaml 파일 경로
    
    Returns:
        dict: 설정값
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def load_and_merge_data(short_interest_path, price_path, pbr_path):
    """
    데이터 로드 및 병합
    
    Args:
        short_interest_path: 공매도 CSV 경로
        price_path: 가격 CSV 경로
        pbr_path: PBR CSV 경로
    
    Returns:
        pd.DataFrame: 병합된 데이터프레임
    """
    print("📊 데이터 로드 중...")
    
    # 데이터 로드
    df_short = pd.read_csv(short_interest_path)
    df_price = pd.read_csv(price_path)
    df_pbr = pd.read_csv(pbr_path)
    
    # 날짜 형식 변환
    df_short['date'] = pd.to_datetime(df_short['date'])
    df_price['date'] = pd.to_datetime(df_price['date'])
    df_pbr['date'] = pd.to_datetime(df_pbr['date'])
    
    # 가격과 공매도 병합 (inner join - 둘 다 있는 데이터만)
    df = df_price.merge(df_short, on=['date', 'ticker'], how='inner')
    
    # PBR 추가 (left join - 가격 데이터 기준)
    df = df.merge(df_pbr, on=['date', 'ticker'], how='left')
    
    # 정렬
    df = df.sort_values(['date', 'ticker']).reset_index(drop=True)
    
    # 결측치 처리 (forward fill)
    df['pbr'] = df.groupby('ticker')['pbr'].fillna(method='ffill')
    df['short_ratio'] = df.groupby('ticker')['short_ratio'].fillna(method='ffill')
    
    # 필수 컬럼만 선택
    required_cols = ['date', 'ticker', 'price', 'return', 'short_ratio', 'pbr']
    df = df[required_cols].dropna()
    
    print(f"✅ 데이터 로드 완료: {len(df)} 행, {df['ticker'].nunique()} 종목")
    print(f"   기간: {df['date'].min()} ~ {df['date'].max()}")
    
    return df


def generate_short_signal(df):
    """
    공매도 신호 생성 (-1 ~ +1)
    
    Cross-sectional rank를 사용하여 각 날짜별로 신호 생성
    공매도 낮음 = +1 (좋음)
    공매도 높음 = -1 (나쁨)
    
    Args:
        df: 데이터프레임
    
    Returns:
        pd.Series: 공매도 신호
    """
    signals = []
    
    for date in df['date'].unique():
        date_data = df[df['date'] == date].copy()
        
        # Cross-sectional rank (낮을수록 좋음)
        rank = date_data['short_ratio'].rank(method='average')
        
        # Min-Max 정규화 (0 ~ 1)
        min_rank = rank.min()
        max_rank = rank.max()
        
        if max_rank == min_rank:
            normalized = pd.Series(0.5, index=rank.index)
        else:
            normalized = (rank - min_rank) / (max_rank - min_rank)
        
        # -1 ~ +1로 변환 (공매도 낮음 = +1)
        signal = 1 - 2 * normalized
        
        signals.append(signal)
    
    return pd.concat(signals)


def generate_value_signal(df):
    """
    밸류 신호 생성 (-1 ~ +1)
    
    1/PBR (역수)를 사용
    PBR 낮음(저평가) = +1 (좋음)
    PBR 높음(고평가) = -1 (나쁨)
    
    Args:
        df: 데이터프레임
    
    Returns:
        pd.Series: 밸류 신호
    """
    signals = []
    
    for date in df['date'].unique():
        date_data = df[df['date'] == date].copy()
        
        # PBR 역수 (0으로 나누기 방지)
        pbr_inv = 1 / (date_data['pbr'] + 1e-6)
        
        # Cross-sectional rank
        rank = pbr_inv.rank(method='average')
        
        # Min-Max 정규화
        min_rank = rank.min()
        max_rank = rank.max()
        
        if max_rank == min_rank:
            normalized = pd.Series(0.5, index=rank.index)
        else:
            normalized = (rank - min_rank) / (max_rank - min_rank)
        
        # -1 ~ +1로 변환
        signal = 1 - 2 * normalized
        
        signals.append(signal)
    
    return pd.concat(signals)


def generate_momentum_signal(df, lookback=252):
    """
    모멘텀 신호 생성 (-1 ~ +1)
    
    12개월(252거래일) 누적 수익률 사용
    
    Args:
        df: 데이터프레임
        lookback: 로드백 기간 (기본 252일 = 12개월)
    
    Returns:
        pd.Series: 모멘텀 신호
    """
    # 종목별 모멘텀 계산
    df = df.copy()
    df['momentum'] = df.groupby('ticker')['return'].rolling(lookback).sum().values
    
    signals = []
    
    for date in df['date'].unique():
        date_data = df[df['date'] == date].copy()
        
        # 결측치 처리
        momentum = date_data['momentum'].fillna(0)
        
        # Cross-sectional rank
        rank = momentum.rank(method='average')
        
        # Min-Max 정규화
        min_rank = rank.min()
        max_rank = rank.max()
        
        if max_rank == min_rank:
            normalized = pd.Series(0.5, index=rank.index)
        else:
            normalized = (rank - min_rank) / (max_rank - min_rank)
        
        # -1 ~ +1로 변환
        signal = 1 - 2 * normalized
        
        signals.append(signal)
    
    return pd.concat(signals)


def generate_all_signals(df):
    """
    모든 신호 생성 (공매도, 밸류, 모멘텀)
    
    Args:
        df: 데이터프레임
    
    Returns:
        pd.DataFrame: 신호가 추가된 데이터프레임
    """
    print("\n🧮 팩터 신호 생성 중...")
    
    df = df.copy()
    
    # 신호 생성
    df['f_short'] = generate_short_signal(df)
    print("   ✅ 공매도 신호 완료")
    
    df['f_value'] = generate_value_signal(df)
    print("   ✅ 밸류 신호 완료")
    
    df['f_momentum'] = generate_momentum_signal(df)
    print("   ✅ 모멘텀 신호 완료")
    
    # NaN 처리 (신호 생성 과정에서 발생한 NaN)
    df[['f_short', 'f_value', 'f_momentum']] = df[['f_short', 'f_value', 'f_momentum']].fillna(0)
    
    print("✅ 팩터 신호 생성 완료")
    
    return df


def calculate_sharpe_ratio(daily_returns, risk_free_rate=0.035):
    """
    샤프 비율 계산
    
    Args:
        daily_returns: 일간 수익률 (pandas Series)
        risk_free_rate: 무위험율 (연 기준, 기본 3.5%)
    
    Returns:
        float: 샤프 비율
    """
    annual_return = daily_returns.mean() * 252
    annual_std = daily_returns.std() * np.sqrt(252)
    
    if annual_std == 0:
        return 0
    
    sharpe = (annual_return - risk_free_rate) / annual_std
    
    return sharpe


def calculate_max_drawdown(cumulative_values):
    """
    최대 낙폭 (MDD) 계산
    
    Args:
        cumulative_values: 누적 수익 (pandas Series)
    
    Returns:
        float: 최대 낙폭 (음수)
    """
    running_max = cumulative_values.cummax()
    drawdown = (cumulative_values - running_max) / running_max
    mdd = drawdown.min()
    
    return mdd


def calculate_win_rate(daily_returns):
    """
    승률 계산
    
    Args:
        daily_returns: 일간 수익률 (pandas Series)
    
    Returns:
        float: 승률 (0 ~ 1)
    """
    if len(daily_returns) == 0:
        return 0
    
    win_rate = (daily_returns > 0).sum() / len(daily_returns)
    
    return win_rate


def calculate_metrics(daily_returns, risk_free_rate=0.035):
    """
    모든 성과 지표 계산
    
    Args:
        daily_returns: 일간 수익률 (pandas Series)
        risk_free_rate: 무위험율 (기본 3.5%)
    
    Returns:
        dict: 성과 지표 {'sharpe': ..., 'return': ..., 'mdd': ..., 'win_rate': ...}
    """
    cumulative = (1 + daily_returns).cumprod()
    
    metrics = {
        'sharpe': calculate_sharpe_ratio(daily_returns, risk_free_rate),
        'total_return': cumulative.iloc[-1] - 1,
        'mdd': calculate_max_drawdown(cumulative),
        'win_rate': calculate_win_rate(daily_returns),
        'cumulative': cumulative
    }
    
    return metrics


def plot_cumulative_return(results_dict, labels, figsize=(14, 7)):
    """
    누적 수익 차트 그리기
    
    Args:
        results_dict: {이름: 누적수익 Series} 형태의 딕셔너리
        labels: 범례 레이블 (리스트)
        figsize: 그림 크기
    
    Returns:
        None (PNG로 저장)
    """
    plt.figure(figsize=figsize)
    
    colors = ['gray', 'blue', 'red']
    
    for (name, cumulative), label, color in zip(results_dict.items(), labels, colors):
        plt.plot(cumulative.index, cumulative.values, 
                label=label, linewidth=2.5, color=color)
    
    plt.axhline(y=1, color='black', linestyle='--', alpha=0.3, linewidth=1)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Cumulative Return', fontsize=12)
    plt.title('Cumulative Return Comparison', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11, loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # 저장
    os.makedirs('visualizations', exist_ok=True)
    plt.savefig('visualizations/cumulative_return.png', dpi=300, bbox_inches='tight')
    print("✅ 차트 저장: visualizations/cumulative_return.png")
    plt.close()


def plot_monthly_returns(daily_pnl_dict, figsize=(14, 7)):
    """
    월별 수익률 비교 차트
    
    Args:
        daily_pnl_dict: {전략명: 일간 수익 Series} 형태
        figsize: 그림 크기
    
    Returns:
        None (PNG로 저장)
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # 월별 수익 계산
    monthly_returns = {}
    for name, daily_pnl in daily_pnl_dict.items():
        monthly = daily_pnl.resample('M').sum()
        monthly_returns[name] = monthly
    
    # 막대 그래프
    x = np.arange(len(monthly_returns[list(monthly_returns.keys())[0]]))
    width = 0.25
    
    colors = ['blue', 'red']
    
    for i, (name, monthly) in enumerate(monthly_returns.items()):
        ax.bar(x + i*width, monthly.values*100, width, label=name, color=colors[i])
    
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('Return (%)', fontsize=12)
    ax.set_title('Monthly Returns Comparison', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    
    # 저장
    os.makedirs('visualizations', exist_ok=True)
    plt.savefig('visualizations/monthly_returns.png', dpi=300, bbox_inches='tight')
    print("✅ 차트 저장: visualizations/monthly_returns.png")
    plt.close()


def plot_sharpe_comparison(metrics_dict, figsize=(10, 6)):
    """
    Sharpe 비율 비교 차트
    
    Args:
        metrics_dict: {전략명: 지표 dict} 형태
        figsize: 그림 크기
    
    Returns:
        None (PNG로 저장)
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    strategies = list(metrics_dict.keys())
    sharpes = [metrics_dict[s]['sharpe'] for s in strategies]
    
    colors = ['gray', 'blue', 'red']
    bars = ax.bar(strategies, sharpes, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    
    # 값 표시
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}', ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax.set_ylabel('Sharpe Ratio', fontsize=12)
    ax.set_title('Sharpe Ratio Comparison', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    
    # 저장
    os.makedirs('visualizations', exist_ok=True)
    plt.savefig('visualizations/sharpe_comparison.png', dpi=300, bbox_inches='tight')
    print("✅ 차트 저장: visualizations/sharpe_comparison.png")
    plt.close()


def save_metrics_to_csv(metrics_dict, output_path='results/metrics.csv'):
    """
    성과 지표를 CSV로 저장
    
    Args:
        metrics_dict: {전략명: 지표 dict} 형태
        output_path: 저장 경로
    
    Returns:
        None
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    data = {
        'Strategy': list(metrics_dict.keys()),
        'Sharpe': [metrics_dict[s]['sharpe'] for s in metrics_dict.keys()],
        'Total Return': [metrics_dict[s]['total_return'] for s in metrics_dict.keys()],
        'Max Drawdown': [metrics_dict[s]['mdd'] for s in metrics_dict.keys()],
        'Win Rate': [metrics_dict[s]['win_rate'] for s in metrics_dict.keys()]
    }
    
    df_metrics = pd.DataFrame(data)
    df_metrics.to_csv(output_path, index=False)
    print(f"✅ 지표 저장: {output_path}")


def save_summary_to_txt(metrics_dict, output_path='results/summary.txt'):
    """
    최종 요약을 텍스트 파일로 저장
    
    Args:
        metrics_dict: {전략명: 지표 dict} 형태
        output_path: 저장 경로
    
    Returns:
        None
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("SHORT INTEREST FACTOR BACKTEST RESULTS\n")
        f.write("=" * 60 + "\n\n")
        
        for strategy, metrics in metrics_dict.items():
            f.write(f"{strategy.upper()}:\n")
            f.write(f"  Sharpe Ratio:      {metrics['sharpe']:.2f}\n")
            f.write(f"  Total Return:      {metrics['total_return']*100:.2f}%\n")
            f.write(f"  Max Drawdown:      {metrics['mdd']*100:.2f}%\n")
            f.write(f"  Win Rate:          {metrics['win_rate']*100:.1f}%\n\n")
        
        f.write("=" * 60 + "\n")
        f.write("CONCLUSION:\n")
        f.write("=" * 60 + "\n")
        
        # 최고 Sharpe 찾기
        best_strategy = max(metrics_dict.items(), key=lambda x: x[1]['sharpe'])
        f.write(f"✅ Best Strategy: {best_strategy[0]}\n")
        f.write(f"   - Highest Sharpe Ratio: {best_strategy[1]['sharpe']:.2f}\n")
        f.write(f"   - Highest Return: {best_strategy[1]['total_return']*100:.2f}%\n")
    
    print(f"✅ 요약 저장: {output_path}")
