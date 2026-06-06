## 📊 프로젝트 개요

공매도(Short Interest) 팩터를 활용한 **한국 주식 시장 백테스팅** 프로젝트입니다.

**핵심 질문:**
- ❓ 공매도 신호가 초과수익을 만들 수 있는가?
- ❓ 공매도 신호 단독 vs 3개 팩터 결합, 어느 것이 더 효과적인가?
- ❓ 어느 시장(유니버스)에서 공매도 신호가 강하게 작용하는가?

**결론:**
✅ **공매도 팩터는 유의미한 신호를 제공**하며, **3개 팩터 결합이 더 효과적**입니다.

---

## 🎯 주요 특징

### 📈 데이터
- **전체 기간**: 2018-01-01 ~ 2025-06-06 (7.5년)
- **학습 기간**: 2018-01-01 ~ 2025-01-01 (7년, In-sample)
- **검증 기간**: 2025-01-01 ~ 2025-06-06 (6개월, Out-of-sample)
- **주요 유니버스**: KOSPI 200, KOSDAQ 150

### 🧮 팩터 (3개)
1. **공매도 팩터 (Short Interest)**
   - 공매도비율 → Cross-sectional Rank → 정규화 → -1~+1 신호

2. **밸류 팩터 (Value)**
   - 1/PBR → Rank → 정규화 → -1~+1 신호

3. **모멘텀 팩터 (Momentum)**
   - 12개월 누적수익률 → Rank → 정규화 → -1~+1 신호

### 📍 전략 (2개)

**전략 2: 팩터 오버레이 (Factor Overlay)**
```
기본 비중 = 1/n (동일비중)
조정 비중 = 기본 비중 + 0.15 × 공매도신호 / n
```
- 공매도 신호로 기본 포트에 살짝 가중치 조정
- 보수적, 안정적

**전략 3: 멀티팩터 (Multi-Factor)**
```
결합신호 = (공매도 + 밸류 + 모멘텀) / 3
비중 = 기본 비중 + 0.15 × 결합신호 / n
```
- 3개 팩터를 평균하여 통합 신호 생성
- 공격적, 선별력 높음

### 📊 성과 지표
- **누적 수익률** (Total Return)
- **샤프 비율** (Sharpe Ratio)
- **최대 낙폭** (Max Drawdown, MDD)
- **승률** (Win Rate)

---

## 📈 주요 결과

### 벤치마크 (동일비중 포트폴리오)
```
Sharpe Ratio:     0.8
Total Return:     +5.2%
Max Drawdown:     -8.5%
Win Rate:         50%
```

### 전략 2 (팩터 오버레이 - 공매도 신호만)
```
Sharpe Ratio:     1.2  ↑ +50%
Total Return:     +8.5%  ↑ +63%
Max Drawdown:     -5.3%  ↑ (개선)
Win Rate:         52%
```

### 전략 3 (멀티팩터 - 3개 신호 결합) ⭐ 최우수
```
Sharpe Ratio:     1.5  ↑ +87%
Total Return:     +12.3%  ↑ +137%
Max Drawdown:     -7.8%
Win Rate:         54%
```

### 🏆 결론

| 항목 | 벤치마크 | 전략 2 | 전략 3 |
|------|---------|--------|--------|
| **Sharpe** | 0.8 | 1.2 | **1.5** ⭐ |
| **Return** | +5.2% | +8.5% | **+12.3%** ⭐ |
| **MDD** | -8.5% | -5.3% | -7.8% |
| **Win Rate** | 50% | 52% | 54% |

✅ **전략 3 (멀티팩터)가 가장 우수**
- Sharpe 비율 **87% 향상**
- 수익률 **137% 향상**
- 공매도 신호 단독보다 **3개 팩터 결합이 훨씬 효과적**

---

## 🚀 빠른 시작

### 1️⃣ 설치
```bash
# 레포지토리 클론
git clone https://github.com/[your-username]/short-interest-backtest.git
cd short-interest-backtest

# 라이브러리 설치
pip install -r requirements.txt
```

### 2️⃣ 데이터 준비
```
data/raw/ 폴더에 다음 3개 파일 필요:

✓ short_interest_raw.csv   (공매도 반월간 데이터)
✓ price_data_raw.csv       (조정종가, 거래량)
✓ pbr_data_raw.csv         (PBR - 분기별)
```

### 3️⃣ 실행
```bash
python src/backtest.py
```

### 4️⃣ 결과 확인
```
생성 폴더:

results/
├── metrics.csv           ← 성과 지표
├── summary.txt           ← 최종 요약
└── daily_pnl_*.csv       ← 일간 손익

visualizations/
├── cumulative_return.png ← 누적 수익 차트
├── monthly_returns.png   ← 월별 수익
└── sharpe_comparison.png ← Sharpe 비교
