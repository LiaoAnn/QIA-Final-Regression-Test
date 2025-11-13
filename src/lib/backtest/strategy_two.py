# 策略二：雙移動平均線黃金交叉策略
# 進場條件：
#   - T-1日發生黃金交叉（短期均線由下往上穿越長期均線）。
#   - T日開盤價進場。
# 出場條件：
#   - 當日持倉時，若當日的（開盤價+收盤價）/ 2 < 當日的短期均線，則於當日收盤價出場。

from lib.technical_indicators import calc_ma

def backtest_strategy_two(df, short_ma_period=5, long_ma_period=20):
    """
    執行策略二（雙移動平均線黃金交叉）的回測。

    Args:
        df (pd.DataFrame): 包含開、高、低、收價格的時間序列資料。
        short_ma_period (int): 短期移動平均線的週期。
        long_ma_period (int): 長期移動平均線的週期。

    Returns:
        pd.DataFrame: 附帶回測結果（如每日報酬、持倉狀態、累計報酬等）的 DataFrame。
    """
    # 複製一份 DataFrame 以免修改到原始傳入的資料
    df = df.copy()

    # --- 步驟一：計算所需技術指標 ---
    # 計算短期和長期移動平均線
    df = calc_ma(df, period=short_ma_period)
    df = calc_ma(df, period=long_ma_period)

    # 為了方便引用，將指標欄位名稱存成變數
    short_ma_col = f'MA{short_ma_period}'
    long_ma_col = f'MA{long_ma_period}'

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
    # 從索引 1 開始循環，因為需要前一天(i-1)的數據來判斷交叉
    for i in range(1, L):
        idx = df.index[i]
        prev_row = df.iloc[i-1] # 前一日(T-1)的數據
        row = df.iloc[i]        # 當日(T)的數據

        # --- 進場邏輯 (使用 T-1 日的信號，在 T 日開盤進場) ---
        # 條件：當前空手，且有足夠歷史數據來判斷交叉 (i > 1 是為了能取得 i-2 的數據)
        if position == 0 and i > 1:
            prev_prev_row = df.iloc[i-2] # 前二日(T-2)的數據
            
            # 判斷 T-1 日是否發生黃金交叉
            # 條件1: T-2日時，短期均線仍在長期均線之下
            # 條件2: T-1日時，短期均線已穿越到長期均線之上
            is_golden_cross = (prev_prev_row[short_ma_col] < prev_prev_row[long_ma_col] and 
                               prev_row[short_ma_col] > prev_row[long_ma_col])
            
            if is_golden_cross:
                # 信號成立，於今天(T日)開盤價進場
                avg_cost = row["開盤價"]
                position = 1
        
        # --- 出場邏輯 (T日盤中判斷，T日收盤出場) ---
        if position == 1:
            # 計算當日的中間價
            mid_price = (row["開盤價"] + row["收盤價"]) / 2
            # 如果中間價跌破了短期均線，視為趨勢轉弱信號
            if mid_price < row[short_ma_col]:
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
