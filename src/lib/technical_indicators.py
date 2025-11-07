# 計算 MA
def MA(s, l, df):
    df["ma_s"] = df["收盤價"].rolling(s).mean()
    df["ma_l"] = df["收盤價"].rolling(l).mean()
    df["ma_sign"] = 0
    df.loc[
        (df["ma_s"].shift(1) < df["ma_l"].shift(1)) & (df["ma_s"] >= df["ma_l"]),
        "ma_sign",
    ] = 1
    df.loc[
        (df["ma_s"].shift(1) > df["ma_l"].shift(1)) & (df["ma_s"] <= df["ma_l"]),
        "ma_sign",
    ] = -1


# 計算 RSI
def RSI(d, df):
    x = df["收盤價"].diff()
    epsilon = 1e-10
    df["rsi"] = (
        100
        * x.where(x > 0, 0).rolling(d).mean()
        / (x.where(x > 0, -x).rolling(d).mean() + epsilon)
    )
    df["rsi_sign"] = 0
    df.loc[df["rsi"] < 20, "rsi_sign"] = 1
    df.loc[df["rsi"] > 80, "rsi_sign"] = -1


# 1️⃣ 五日均線
def calc_MA5(df, period=5):
    """
    計算五日均線
    """
    df["MA5"] = df["收盤價"].rolling(period).mean()
    return df


# 2️⃣ 布林軌道
def calc_Bollinger(df, n=20, k=2):
    """
    計算布林帶
    """
    df["BB_MA"] = df["收盤價"].rolling(n).mean()
    df["BB_STD"] = df["收盤價"].rolling(n).std()
    df["BB_Upper"] = df["BB_MA"] + k * df["BB_STD"]
    df["BB_Lower"] = df["BB_MA"] - k * df["BB_STD"]
    return df


# 3️⃣ 昨天漲幅
def calc_prev_gain(df):
    """
    計算昨天漲幅
    """
    df["prev_gain"] = (df["收盤價"] - df["收盤價"].shift(1)) / df["收盤價"].shift(1)
    return df


# 4️⃣ 二十日均線
def calc_MA20(df, period=20):
    """
    計算二十日均線
    """
    df["MA20"] = df["收盤價"].rolling(period).mean()
    return df


# 5️⃣ 乖離率 (Bias)
def calc_Bias(df, period=20):
    """
    計算乖離率 (收盤價 vs. N日均線)
    """
    ma_col = f'MA{period}'
    if ma_col not in df.columns:
        # 如果均線不存在，先計算它
        df[ma_col] = df["收盤價"].rolling(period).mean()
    
    df['Bias'] = (df['收盤價'] - df[ma_col]) / df[ma_col] * 100 # 乘以100變成百分比
    return df


# 6️⃣ 三日均線
def calc_MA3(df, period=3):
    """
    計算三日均線
    """
    df["MA3"] = df["收盤價"].rolling(period).mean()
    return df


# 7️⃣ 十日均線
def calc_MA10(df, period=10):
    """
    計算十日均線
    """
    df["MA10"] = df["收盤價"].rolling(period).mean()
    return df


# 8️⃣ 相對強弱指數 (RSI)
def calc_RSI14(df, period=14):
    """
    計算14日RSI
    """
    x = df["收盤價"].diff()
    epsilon = 1e-10
    
    gain = x.where(x > 0, 0)
    loss = -x.where(x < 0, 0)
    
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    
    rs = avg_gain / (avg_loss + epsilon)
    
    df["RSI14"] = 100 - (100 / (1 + rs))
    return df
