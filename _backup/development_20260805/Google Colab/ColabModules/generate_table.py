# generate_table.py
import pandas as pd

def make_styled_table(df, flags, name, symbol, today_str):
    df_recent = df.dropna().copy()[-7:]
    date_labels = [d.strftime("%-m/%-d") for d in df_recent.index]
    table_data = []
    table_data.append(["終値"] + [f"{v:.2f}" for v in df_recent["Close"]])
    if flags.SHOW_RSI:
        table_data.append(["RSI"] + [f"{v:.2f}" for v in df_recent["RSI"]])
    df_table = pd.DataFrame(table_data, columns=["指標"] + date_labels)
    styled = df_table.style.set_properties(**{"text-align": "right"})
    return styled
