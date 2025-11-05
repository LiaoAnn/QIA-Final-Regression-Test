# 回測策略（隔天開盤進場版）
from lib.technical_indicators import calc_Bollinger, calc_MA5, calc_prev_gain


def backtest_strategy(df):
    df = df.copy()
    df = calc_MA5(df).copy()
    df = calc_Bollinger(df).copy()
    df = calc_prev_gain(df).copy()

    L = len(df)
    if L < 2:  # 需要至少兩天資料來執行進場邏輯
        return df

    # 初始化欄位
    df["ret"] = 0.0
    df["cus"] = 0.0
    df["position"] = 0

    position = 0
    avg_cost = 0.0
    cum_ret = 0.0
    yesterday_triggered_bb = False  # 紀錄前一天收盤是否觸發BB上軌
    prev_close = 0.0
    prev_gain = 0.0

    for i in range(L):  # 循環遍歷所有日期
        idx = df.index[i]
        row = df.iloc[i]

        # 處理進場邏輯 (適用於今天)
        if yesterday_triggered_bb and position == 0:
            # 檢查今天開盤是否滿足第二階段訊號
            if row["開盤價"] >= prev_close - prev_gain / 2:
                # 使用今天的開盤價進場，並重置訊號
                avg_cost = row["開盤價"]
                position = 1
            yesterday_triggered_bb = False  # 訊號已處理，重置

        # --- 出場條件（當日收盤） ---
        if position == 1 and row["收盤價"] < row["MA5"]:
            exit_price = row["收盤價"]
            ret = exit_price - avg_cost
            df.at[idx, "ret"] = ret
            cum_ret += ret
            position = 0
            avg_cost = 0.0

        # --- 計算浮動盈虧 ---
        if position == 1:
            df.at[idx, "cus"] = cum_ret + (row["收盤價"] - avg_cost)
        else:
            df.at[idx, "cus"] = cum_ret

        # --- 記錄持倉 ---
        df.at[idx, "position"] = position

        # --- 判斷今天收盤是否觸發進場訊號 (供明天使用) ---
        if position == 0:  # 只有在目前沒有持倉時才考慮進場
            if row["收盤價"] > row["BB_Upper"]:
                yesterday_triggered_bb = True  # 為明天設置訊號
                prev_close = row["收盤價"]
                prev_gain = row.get("prev_gain", 0.0)

    # --- Buy & Hold ---
    df["BH"] = df["收盤價"] - df["收盤價"].iloc[0]

    return df
