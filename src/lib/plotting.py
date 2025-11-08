# === Step 0: 載入必要模組 ===
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import platform


# 通用中文字體設定函數
def get_chinese_font(size=12):
    system = platform.system()
    if system == "Windows":
        font_path = "C:/Windows/Fonts/msjh.ttc"
    elif system == "Darwin":
        font_path = "/System/Library/Fonts/PingFang.ttc"
    else:  # Linux
        font_path = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
    try:
        return fm.FontProperties(fname=font_path, size=size)
    except FileNotFoundError:
        return fm.FontProperties(size=size)


# === 1️⃣ 繪製收盤價 + 技術指標 ===
def plot_price_indicators(df: pd.DataFrame, title: str, indicators: list):
    font = get_chinese_font(12)
    plt.figure(figsize=(20, 15))
    plt.plot(df.index, df["收盤價"], label="收盤價")
    for ind in indicators:
        if ind in df.columns:
            plt.plot(df.index, df[ind], label=ind)
    plt.title(f"{title} - 技術指標", fontproperties=font)
    plt.xlabel("日期", fontproperties=font)
    plt.legend(prop=font)
    plt.grid(True)
    plt.tight_layout()
    plt.show()


# === 2️⃣ 繪製累積報酬率 ===
def plot_cumulative_returns(df: pd.DataFrame, title: str):
    font = get_chinese_font(12)
    plt.figure(figsize=(20, 15))
    plt.plot(df.index, df["cus"], label="策略累積報酬")
    plt.plot(df.index, df["BH"], label="買進持有累積報酬")
    plt.title(f"{title} - 累積報酬率", fontproperties=font)
    plt.xlabel("日期", fontproperties=font)
    plt.legend(prop=font)
    plt.grid(True)
    plt.tight_layout()
    plt.show()


# === 3️⃣ 繪製持倉狀態 ===
def plot_position(df: pd.DataFrame, title: str):
    font = get_chinese_font(12)
    plt.figure(figsize=(20, 3))  # 高度小一點
    plt.plot(df.index, df["position"], label="Position", drawstyle="steps-post")
    plt.fill_between(df.index, 0, df["position"], alpha=0.3, step="post")
    plt.title(f"{title} - 持倉狀態", fontproperties=font)
    plt.xlabel("日期", fontproperties=font)
    plt.yticks([0, 1])
    plt.ylim(-0.1, 1.1)
    plt.legend(prop=font)
    plt.grid(True)
    plt.tight_layout()
    plt.show()


# === 4️⃣ 繪製綜合圖表 ===
def plot_strategy_results(df: pd.DataFrame, title: str, indicators: list):
    """
    繪製策略的回測結果，包含價格、技術指標、累積報酬率和持倉狀態。
    Position 放在最下面，每張圖高度縮小。
    """
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    import platform

    # 設定中文字體
    system = platform.system()
    if system == "Windows":
        font_path = "C:/Windows/Fonts/msjh.ttc"
    elif system == "Darwin":
        font_path = "/System/Library/Fonts/PingFang.ttc"
    else:
        font_path = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"

    try:
        font = fm.FontProperties(fname=font_path, size=12)
    except FileNotFoundError:
        font = fm.FontProperties(size=12)

    # 調整總高度，讓每張圖小一點
    fig, (ax1, ax2, ax3) = plt.subplots(
        3, 1, figsize=(20, 10), sharex=True, gridspec_kw={"height_ratios": [3, 3, 1]}
    )

    # Subplot 1: 收盤價 + 技術指標
    ax1.set_title(f"{title} - 技術指標", fontproperties=font)
    ax1.plot(df.index, df["收盤價"], label="收盤價")
    for indicator in indicators:
        if indicator in df.columns:
            ax1.plot(df.index, df[indicator], label=indicator)
    ax1.legend(prop=font)
    ax1.grid(True)

    # Subplot 2: 累積報酬率
    ax2.set_title(f"{title} - 累積報酬率", fontproperties=font)
    ax2.plot(df.index, df["cus"], label="策略累積報酬")
    ax2.plot(df.index, df["BH"], label="買進持有累積報酬")
    ax2.legend(prop=font)
    ax2.grid(True)

    # Subplot 3: 持倉狀態
    ax3.set_title(f"{title} - 持倉狀態", fontproperties=font)
    ax3.plot(df.index, df["position"], label="Position", drawstyle="steps-post")
    ax3.fill_between(df.index, 0, df["position"], alpha=0.3, step="post")
    ax3.set_yticks([0, 1])
    ax3.set_ylim(-0.1, 1.1)  # y 軸縮窄，讓 0~1 看起來更緊湊
    ax3.grid(True)

    plt.xlabel("日期", fontproperties=font)
    plt.tight_layout()
    plt.show()

    # return fig
