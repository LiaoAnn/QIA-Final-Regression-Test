# 策略四: 布林軌道 + 趨勢過濾
# 這是一個結合了趨勢判斷的均值回歸策略，旨在避免逆勢交易。
# 核心思想：順大勢（長期趨勢），逆小勢（短期回檔）。
# 進場條件:
#   - 計算一條長期均線 (如 MA50) 來判斷主要趨勢。
#   - 當處於上升趨勢 (收盤價 > MA50) 時，若價格回檔觸及布林下軌，則做多。
#   - 當處於下降趨勢 (收盤價 < MA50) 時，若價格反彈觸及布林上軌，則做空。
# 出場條件: (與前一版相同)
#   - 停損: 持有多單時，K線開收盤價皆破下軌；持有空單時，K線開收盤價皆破上軌。
#   - 停利: 持有多單時觸及上軌；持有空單時觸及下軌。

from lib.technical_indicators import calc_Bollinger

def backtest_strategy_four(df, bb_period=5, bb_std=2, ma_long_period=10):
    """
    執行策略四（含趨勢過濾）的回測。

    Args:
        df (pd.DataFrame): 包含開、高、低、收價格的時間序列資料。
        bb_period (int): 計算布林通道的週期。
        bb_std (int): 計算布林通道時使用的標準差倍數。
        ma_long_period (int): 用於判斷長期趨勢的移動平均線週期。

    Returns:
        pd.DataFrame: 附帶回測結果的 DataFrame。
    """
    # 複製一份 DataFrame 以免修改到原始傳入的資料
    df = df.copy()

    # --- 步驟一：計算所需技術指標 ---
    df = calc_Bollinger(df, n=bb_period, k=bb_std).copy()

    # 加入 BB_MA 欄位（布林中線 = MA(bb_period)）
    bb_ma_col = f"BB_MA{bb_period}"
    df[bb_ma_col] = df["收盤價"].rolling(bb_period).mean()

    # 計算長期趨勢線
    ma_long_col = f'MA{ma_long_period}'
    df[ma_long_col] = df['收盤價'].rolling(ma_long_period).mean()

    L = len(df)
    if L < ma_long_period: # 確保有足夠資料計算長期均線
        return df

    # --- 步驟二：初始化回測所需的欄位與變數 ---
    df["ret"] = 0.0
    df["cus"] = 0.0
    df["position"] = 0  # 記錄每日的持倉狀態 (0: 空手, 1: 持有多單, -1: 持有空單)

    position = 0
    avg_cost = 0.0
    cum_ret = 0.0

    # --- 步驟三：遍歷所有交易日，執行回測邏輯 ---
    for i in range(L):
        idx = df.index[i]
        row = df.iloc[i]

        # --- 出場邏輯 (優先處理) ---
        if position != 0:
            exit_price = 0
            ret = 0

            # 持有多單時的出場條件
            if position == 1:
                # 停損: 開盤與收盤價皆低於下軌
                if row["開盤價"] < row["BB_Lower"] and row["收盤價"] < row["BB_Lower"]:
                    exit_price = row["收盤價"]
                    ret = exit_price - avg_cost
                # 停利: 價格觸及上軌
                elif row["最高價"] >= row["BB_Upper"]:
                    exit_price = row["BB_Upper"]
                    ret = exit_price - avg_cost

            # 持有空單時的出場條件
            elif position == -1:
                # 停損: 開盤與收盤價皆高於上軌
                if row["開盤價"] > row["BB_Upper"] and row["收盤價"] > row["BB_Upper"]:
                    exit_price = row["收盤價"]
                    ret = avg_cost - exit_price
                # 停利: 價格觸及下軌
                elif row["最低價"] <= row["BB_Lower"]:
                    exit_price = row["BB_Lower"]
                    ret = avg_cost - exit_price

            # 如果觸發了出場條件
            if exit_price > 0:
                df.at[idx, "ret"] = ret
                cum_ret += ret
                position = 0
                avg_cost = 0.0

        # --- 進場邏輯 (當日無持倉且未觸發出場時才檢查) ---
        if position == 0:
            # 趨勢過濾條件
            is_uptrend = row['收盤價'] > row[ma_long_col]
            is_downtrend = row['收盤價'] < row[ma_long_col]

            # 做多信號: 上升趨勢中的回檔
            if is_uptrend and row["最低價"] <= row["BB_Lower"]:
                avg_cost = row["BB_Lower"]
                position = 1
            # 做空信號: 下降趨勢中的反彈
            elif is_downtrend and row["最高價"] >= row["BB_Upper"]:
                avg_cost = row["BB_Upper"]
                position = -1

        # --- 每日結算與記錄 ---
        if position == 1:
            df.at[idx, "cus"] = cum_ret + (row["收盤價"] - avg_cost)
        elif position == -1:
            df.at[idx, "cus"] = cum_ret + (avg_cost - row["收盤價"])
        else:
            df.at[idx, "cus"] = cum_ret

        df.at[idx, "position"] = position

    # --- 步驟四：計算買入並持有策略的報酬作為比較基準 ---
    df["BH"] = df["收盤價"] - df["收盤價"].iloc[0]

    return df
