# Shortselling-Squeeze-Strategy-Backtest
배경: 공매도 잔고(누적)와 거래대금(일일 흐름)을 활용해 숏 스퀴즈 발생 가능성을 예측하고, 박스권 돌파 시 수익성을 검증함.

핵심 로직:

필터링: 유통 물량 대비 공매도 잔고 비율(Short Interest) 10% 이상 종목 추출.

신호(Signal): 공매도 잔고가 감소 추세이면서 주가가 박스권 상단을 돌파하는 시점 포착.

검증: 과거 특정 기간(예: 2025~2026)의 주가 데이터를 기반으로 위 전략의 수익률을 시뮬레이션.

기술 스택: Python, Pandas, Matplotlib (시각화), FinanceDataReader (주가 데이터), Backtrader (백테스팅 엔진)
