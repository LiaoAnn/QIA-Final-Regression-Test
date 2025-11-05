import pandas as pd


# 計算策略績效
def result_F(df):
    last = df["cus"].iloc[-1]
    count = df["sign"][df["sign"] != 0].count()

    def maxdrawdown(s):
        s = s.cummax() - s
        return s.max()

    mdd = maxdrawdown(df["cus"])
    w = df["ret"][df["ret"] > 0].count() / count if count > 0 else 0
    result = pd.DataFrame(
        {"最後報酬": [last], "交易次數": [count], "最大回損": [mdd], "勝率": [w]}
    )
    return result


def calculate_strategy_one_performance(df_backtest_output: pd.DataFrame) -> dict:
    """
    從 backtest_strategy 函數的輸出 DataFrame 中計算詳細的績效指標。

    Args:
        df_backtest_output (pd.DataFrame): 已經執行過 backtest_strategy 的 DataFrame

    Returns:
        dict: 包含策略績效指標的字典
    """

    # 1. 提取已實現的交易列表 (來自 'ret' 欄位)
    # 這些是您策略中 "一進一出" 的所有已實現損益
    trades = df_backtest_output["ret"][df_backtest_output["ret"] != 0].dropna()

    # 2. 提取 'cus' 欄位 (市值型權益曲線)
    cus_series = df_backtest_output["cus"]

    # --- 計算最大回撤 (MDD) ---
    def maxdrawdown(s):
        s = s.cummax() - s
        return s.max()

    mdd = maxdrawdown(cus_series)

    # --- 績效計算 (來自 calculate_strategy_performance 的統計邏輯) ---
    total_trades = len(trades)

    # 如果沒有任何已實現的交易
    if total_trades == 0:
        return {
            "最終權益 (Mark-to-Market)": (
                cus_series.iloc[-1] if not cus_series.empty else 0
            ),
            "淨利或淨損 (已實現)": 0,
            "最大回撤 (MDD)": mdd,
            "總交易次數": 0,
            "勝率": "0.00%",
            "總獲利 (已實現)": 0,
            "總損失 (已實現)": 0,
            "賺錢交易次數": 0,
            "虧錢交易次數": 0,
            "單次交易最大獲利": 0,
            "單次交易最大損失": 0,
            "獲利交易中的平均獲利": 0,
            "損失交易中的平均損失": 0,
            "賺賠比": 0,
            "最長的連續性獲利的次數": 0,
            "最長的連續性損失的次數": 0,
        }

    # 分別計算獲利交易與虧損交易
    winning_trades = trades[trades > 0]
    losing_trades = trades[trades < 0]

    total_profit = winning_trades.sum()
    total_loss = losing_trades.sum()
    num_winning_trades = len(winning_trades)
    num_losing_trades = len(losing_trades)

    win_rate = num_winning_trades / total_trades
    max_profit_trade = winning_trades.max() if not winning_trades.empty else 0
    max_loss_trade = losing_trades.min() if not losing_trades.empty else 0
    avg_profit = total_profit / num_winning_trades if num_winning_trades > 0 else 0
    # 注意：avg_loss 會是負值
    avg_loss = total_loss / num_losing_trades if num_losing_trades > 0 else 0

    if avg_loss == 0:
        profit_loss_ratio = float("inf")  # 如果沒有虧損交易
    else:
        profit_loss_ratio = abs(avg_profit / avg_loss)

    # 計算最長連續獲利/虧損
    longest_win_streak = longest_loss_streak = 0
    current_win_streak = current_loss_streak = 0
    for trade_return in trades:
        if trade_return > 0:
            current_win_streak += 1
            current_loss_streak = 0
        elif trade_return < 0:
            current_loss_streak += 1
            current_win_streak = 0
        longest_win_streak = max(longest_win_streak, current_win_streak)
        longest_loss_streak = max(longest_loss_streak, current_loss_streak)

    metrics = {
        "最終權益 (Mark-to-Market)": cus_series.iloc[-1],  # 'cus' 的最後值
        "淨利或淨損 (已實現)": trades.sum(),  # 'ret' 的總和
        "最大回撤 (MDD)": mdd,  # 'cus' 的最大回撤
        "總獲利 (已實現)": total_profit,
        "總損失 (已實現)": total_loss,
        "總交易次數": total_trades,
        "賺錢交易次數": num_winning_trades,
        "虧錢交易次數": num_losing_trades,
        "勝率": f"{win_rate:.2%}",
        "單次交易最大獲利": max_profit_trade,
        "單次交易最大損失": max_loss_trade,
        "獲利交易中的平均獲利": avg_profit,
        "損失交易中的平均損失": avg_loss,
        "賺賠比": profit_loss_ratio,
        "最長的連續性獲利的次數": longest_win_streak,
        "最長的連續性損失的次數": longest_loss_streak,
    }

    return metrics
