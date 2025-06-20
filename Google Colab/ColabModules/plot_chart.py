# plot_chart.py
import mplfinance as mpf
import matplotlib.pyplot as plt
from matplotlib import font_manager

jp_font = font_manager.FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")

def plot_stock_chart(df, symbol, name, flags, today_str):
    df_recent = df.dropna().copy()[-60:]
    if df_recent.empty:
        raise ValueError(f"{symbol}: データが不足しています")

    add_plots = []
    panel_ratios = [2]
    panel_id = 1
    if flags.SHOW_PRICE_MA:
        add_plots += [
            mpf.make_addplot(df_recent["MA5"], panel=0, color="black"),
            mpf.make_addplot(df_recent["MA25"], panel=0, color="green"),
            mpf.make_addplot(df_recent["MA75"], panel=0, color="red"),
            mpf.make_addplot(df_recent["MA200"], panel=0, color="blue"),
        ]
    if flags.SHOW_VOLUME_MA:
        add_plots += [
            mpf.make_addplot(df_recent["Vol_MA5"], panel=panel_id, color="blue"),
            mpf.make_addplot(df_recent["Vol_MA25"], panel=panel_id, color="orange"),
        ]
        panel_ratios.append(1)
        panel_id += 1
    if flags.SHOW_RSI:
        add_plots.append(mpf.make_addplot(df_recent["RSI"], panel=panel_id, ylabel="RSI"))
        panel_ratios.append(1)
        panel_id += 1

    fig, axlist = mpf.plot(
        df_recent,
        type="candle",
        style="yahoo",
        ylabel="株価（円）",
        volume=True,
        figratio=(16, 9),
        figscale=1.2,
        addplot=add_plots,
        panel_ratios=panel_ratios,
        returnfig=True
    )

    title = f"{name}（{symbol}）株価チャート（直近60日） - {today_str}"
    axlist[0].set_title(title, fontproperties=jp_font)

    chart_path = f"{symbol}_{today_str}.png"
    fig.savefig(chart_path, dpi=150)
    plt.close(fig)
    return chart_path
