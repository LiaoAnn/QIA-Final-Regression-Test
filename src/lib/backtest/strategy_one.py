# 策略一：結合布林通道與隔日開盤價濾網的回測策略
# 這是一個兩階段的進場策略：
# 1. 第一階段（T日收盤）：當日收盤價突破布林通道上軌，觸發進場觀察信號。
# 2. 第二階段（T+1日開盤）：隔天開盤時，若股價沒有大幅低開（由 drop_threshold 控制），則以開盤價進場。
# 出場條件：當持倉時，若收盤價回落到布林通道上軌以下，則於收盤價出場。

from lib.technical_indicators import calc_Bollinger, calc_MA5, calc_prev_gain

def backtest_strategy(df, ma_period=5, bb_period=20, bb_std=2, drop_threshold=0.5):
    """
    執行策略一的回測。

    Args:
        df (pd.DataFrame): 包含開、高、低、收價格的時間序列資料。
        ma_period (int): 計算移動平均線的週期。
        bb_period (int): 計算布林通道的週期。
        bb_std (int): 計算布林通道時使用的標準差倍數。
        drop_threshold (float): 隔日開盤價的跌幅容忍閾值。
                                用於判斷前一日觸發信號後，隔天開盤是否因跌幅過大而放棄進場。
                                例如 0.5 表示開盤價 > (前日收盤價 - 前日漲幅 * 0.5)。

    Returns:
        pd.DataFrame: 附帶回測結果（如每日報酬、持倉狀態、累計報酬等）的 DataFrame。
    """
    # 複製一份 DataFrame 以免修改到原始傳入的資料
    df = df.copy()
    
    # --- 步驟一：計算所需技術指標 ---
    # 雖然 MA5 在此策略邏輯中未使用，但保留以便未來擴展或分析
    df = calc_MA5(df, period=ma_period).copy()
    # 計算布林通道，這是策略的核心指標
    df = calc_Bollinger(df, n=bb_period, k=bb_std).copy()
    # 計算前一日的絕對漲跌幅，用於隔日開盤的濾網
    df = calc_prev_gain(df).copy()

    L = len(df)
    if L < 2:  # 至少需要兩天資料才能執行進出場邏輯
        return df

    # --- 步驟二：初始化回測所需的欄位與變數 ---
    df["ret"] = 0.0       # 記錄每筆已實現交易的報酬
    df["cus"] = 0.0       # 記錄每日的累計報酬（包含未實現的浮動盈虧）
    df["position"] = 0    # 記錄每日的持倉狀態 (0: 空手, 1: 持有多單)

    position = 0          # 當前的持倉狀態
    avg_cost = 0.0        # 持倉的平均成本
    cum_ret = 0.0         # 已實現的累計報酬
    
    # 策略狀態變數
    yesterday_triggered_bb = False  # 標記前一天收盤是否已觸發布林通道突破信號
    prev_close = 0.0                # 觸發信號當天的收盤價
    prev_gain = 0.0                 # 觸發信號當天的漲跌幅

    # --- 步驟三：遍歷所有交易日，執行回測邏輯 ---
    for i in range(L):
        idx = df.index[i]
        row = df.iloc[i]

        # --- T+1日開盤進場邏輯 ---
        # 如果前一天觸發了BB突破信號，並且當前是空手狀態
        if yesterday_triggered_bb and position == 0:
            # 檢查今天的開盤價是否滿足第二階段的濾網條件（沒有大幅低開）
            if row["開盤價"] >= prev_close - prev_gain * drop_threshold:
                # 條件滿足，使用今天的開盤價進場
                avg_cost = row["開盤價"]
                position = 1
            
            # 無論是否進場，這個信號在今天處理完畢後都應重置
            yesterday_triggered_bb = False

        # --- 當日收盤出場邏輯 ---
        # 如果當前持有多單，並且當日收盤價已回落至布林通道上軌之下
        if position == 1 and row["收盤價"] < row["BB_Upper"]:
            exit_price = row["收盤價"]
            ret = exit_price - avg_cost  # 計算這筆交易的報酬
            df.at[idx, "ret"] = ret      # 記錄報酬
            cum_ret += ret               # 累加到已實現報酬中
            
            # 平倉，重置持倉狀態
            position = 0
            avg_cost = 0.0

        # --- 每日結算與記錄 ---
        # 計算每日的浮動盈虧
        if position == 1:
            # 若仍持倉，總權益 = 已實現報酬 + (當前價格 - 持倉成本)
            df.at[idx, "cus"] = cum_ret + (row["收盤價"] - avg_cost)
        else:
            # 若空手，總權益 = 已實現報酬
            df.at[idx, "cus"] = cum_ret

        # 記錄當日結束時的持倉狀態
        df.at[idx, "position"] = position

        # --- T日收盤進場信號觸發 ---
        # 判斷今天收盤是否觸發第一階段的進場信號 (供明天使用)
        if position == 0:  # 只有在目前沒有持倉時才考慮新的進場信號
            if row["收盤價"] > row["BB_Upper"]:
                # 觸發信號，設置標記為 True
                yesterday_triggered_bb = True
                # 記錄下今天的收盤價和漲跌幅，供明天開盤時判斷
                prev_close = row["收盤價"]
                prev_gain = row.get("prev_gain", 0.0)

    # --- 步驟四：計算買入並持有策略的報酬作為比較基準 ---
    df["BH"] = df["收盤價"] - df["收盤價"].iloc[0]

    return df
