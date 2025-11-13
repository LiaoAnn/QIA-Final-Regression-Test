# 策略三：三移動平均線策略
# 進場條件：
#   - T-1日，三條均線呈「多頭排列」（短期均線 > 中期均線 > 長期均線）。
#   - T日開盤價進場。
# 出場條件：
#   - T日，短期均線向下穿越中期均線，於當日收盤價出場。

from lib.technical_indicators import calc_ma


def backtest_strategy_three(df, ma_short=3, ma_medium=5, ma_long=10):
    """
    執行策略三（三移動平均線）的回測。

    Args:
        df (pd.DataFrame): 包含開、高、低、收價格的時間序列資料。
        ma_short (int): 短期移動平均線的週期。
        ma_medium (int): 中期移動平均線的週期。
        ma_long (int): 長期移動平均線的週期。

    Returns:
        pd.DataFrame: 附帶回測結果（如每日報酬、持倉狀態、累計報酬等）的 DataFrame。
    """
    # 複製一份 DataFrame 以免修改到原始傳入的資料
    df = df.copy()

    # --- 步驟一：計算所需技術指標 ---
    # 計算短、中、長三條移動平均線
    df = calc_ma(df, period=ma_short)
    df = calc_ma(df, period=ma_medium)
    df = calc_ma(df, period=ma_long)

    # 為了方便引用，將指標欄位名稱存成變數
    short_ma_col = f'MA{ma_short}'
    medium_ma_col = f'MA{ma_medium}'
    long_ma_col = f'MA{ma_long}'

    L = len(df)
    if L < 2: # 至少需要兩天資料
        return df

    # --- 步驟二：初始化回測所需的欄位與變數 ---
    df["ret"] = 0.0       # 記錄每筆已實現交易的報酬
    df["cus"] = 0.0       # 記錄每日的累計報酬（包含未實現的浮動盈虧）
    df["position"] = 0    # 記錄每日的持倉狀態 (0: 空手, 1: 持有多單)

    position = 0          # 當前的持倉狀態
    avg_cost = 0.0        # 持倉的平均成本
    cum_ret = 0.0         # 已實現的累計報酬

    # --- 步驟三：遍歷所有交易日，執行回測邏輯 ---
    # 從索引 1 開始循環，因為需要前一天(i-1)的數據來判斷進場信號
    for i in range(1, L):
        idx = df.index[i]
        prev_row = df.iloc[i - 1] # 前一日(T-1)的數據
        row = df.iloc[i]          # 當日(T)的數據

        # --- 進場邏輯 (使用 T-1 日的信號，在 T 日開盤進場) ---
        if position == 0:
            # 檢查前一天(T-1)是否滿足進場條件：均線多頭排列
            is_bullish_alignment = (prev_row[short_ma_col] > prev_row[medium_ma_col] and 
                                    prev_row[medium_ma_col] > prev_row[long_ma_col])
            
            if is_bullish_alignment:
                # 信號成立，於今天(T日)開盤價進場
                avg_cost = row["開盤價"]
                position = 1

        # --- 出場邏輯 (T日判斷，T日收盤出場) ---
        if position == 1:
            # 檢查出場條件：短期均線下穿中期均線，代表短期趨勢轉弱
            if row[short_ma_col] < row[medium_ma_col]:
                exit_price = row["收盤價"]   # 於當日收盤價出場
                ret = exit_price - avg_cost  # 計算報酬
                df.at[idx, "ret"] = ret      # 記錄報酬
                cum_ret += ret               # 累加到已實現報酬

                # 平倉，重置持倉狀態
                position = 0
                avg_cost = 0.0

        # --- 每日結算與記錄 ---
        if position == 1:
            # 若仍持倉，總權益 = 已實現報酬 + (當前價格 - 持倉成本)
            df.at[idx, "cus"] = cum_ret + (row["收盤價"] - avg_cost)
        else:
            # 若空手，總權益 = 已實現報酬
            df.at[idx, "cus"] = cum_ret

        # 記錄當日結束時的持倉狀態
        df.at[idx, "position"] = position

    # --- 步驟四：計算買入並持有策略的報酬作為比較基準 ---
    df["BH"] = df["收盤價"] - df["收盤價"].iloc[0]

    return df
