import os
import pandas as pd
import plotly.express as px
import streamlit as st

DATA_DIR = "data"
TRANSACTIONS_FILE = os.path.join(DATA_DIR, "account_transactions.csv")
TRANSACTION_CODES_FILE = os.path.join(DATA_DIR, "transaction_codes.csv")

st.set_page_config(page_title="Banking Analytics Portfolio", layout="wide")

@st.cache_data
def load_transactions(path):
    if not os.path.exists(path):
        return None
    return pd.read_csv(path, parse_dates=["created_time"], low_memory=False)

@st.cache_data
def load_transaction_codes(path):
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)

st.title("🏦 Banking Transaction Analytics Dashboard")
st.subheader("Transaction volume, channel mix, and activity trends")

st.markdown(
    """
    This app analyzes banking transaction activity using the available transaction dataset.
    You can filter by transaction type, channel, and account type, then explore volume and trend metrics.
    """
)

transactions = load_transactions(TRANSACTIONS_FILE)
code_map = load_transaction_codes(TRANSACTION_CODES_FILE)

if transactions is None:
    st.error(f"Veri dosyası bulunamadı: {TRANSACTIONS_FILE}")
    st.stop()

if code_map is not None:
    transactions = transactions.merge(
        code_map.drop_duplicates(subset=["transaction_code"]),
        on="transaction_code",
        how="left",
        suffixes=("", "_code")
    )

transactions["amount"] = pd.to_numeric(transactions["amount"], errors="coerce")
transactions["created_time"] = pd.to_datetime(transactions["created_time"], errors="coerce")

st.sidebar.title("Filters")

transaction_types = sorted(transactions["transaction_type"].dropna().unique())
channels = sorted(transactions["channel"].dropna().unique())
account_types = sorted(
    transactions["account_type"].dropna().unique()
) if "account_type" in transactions.columns else []

selected_types = st.sidebar.multiselect(
    "Transaction Type",
    transaction_types,
    default=transaction_types,
)
selected_channels = st.sidebar.multiselect(
    "Channel",
    channels,
    default=channels,
)
selected_account_types = None
if account_types:
    selected_account_types = st.sidebar.multiselect(
        "Account Type",
        account_types,
        default=account_types,
    )

filtered = transactions[
    transactions["transaction_type"].isin(selected_types)
    & transactions["channel"].isin(selected_channels)
]
if selected_account_types is not None:
    filtered = filtered[filtered["account_type"].isin(selected_account_types)]

st.markdown("## 📈 Key Metrics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Transactions", f"{len(filtered):,}")
col2.metric("Total Volume", f"${filtered['amount'].sum():,.2f}")
col3.metric("Avg Amount", f"${filtered['amount'].mean():,.2f}")
col4.metric("Unique Accounts", f"{filtered['account_id'].nunique():,}")

st.markdown("## 📊 Transaction Mix")
fig1 = px.histogram(
    filtered,
    x="transaction_type",
    color="transaction_type",
    title="Transaction Type Distribution",
    labels={"transaction_type": "Transaction Type", "count": "Count"},
)
st.plotly_chart(fig1, use_container_width=True)

st.markdown("## 💳 Amount by Channel")
fig2 = px.box(
    filtered,
    x="channel",
    y="amount",
    color="channel",
    title="Amount Distribution by Channel",
    labels={"channel": "Channel", "amount": "Amount"},
)
st.plotly_chart(fig2, use_container_width=True)

if filtered["created_time"].notna().any():
    time_data = (
        filtered
        .dropna(subset=["created_time"])
        .assign(month=lambda df: df["created_time"].dt.to_period("M").dt.to_timestamp())
        .groupby("month")["amount"].sum()
        .reset_index()
    )
    st.markdown("## 📅 Monthly Transaction Volume")
    fig3 = px.line(
        time_data,
        x="month",
        y="amount",
        markers=True,
        title="Monthly Transaction Volume",
        labels={"month": "Month", "amount": "Amount"},
    )
    st.plotly_chart(fig3, use_container_width=True)

st.markdown("## 🔎 Top Transaction Codes")
code_summary = (
    filtered
    .groupby("transaction_code")
    ["amount"]
    .agg(["count", "sum"])
    .reset_index()
    .sort_values(by="sum", ascending=False)
    .head(10)
)
st.dataframe(code_summary.style.format({"sum": "${:,.2f}"}))

st.markdown("---")
st.markdown("📌 Built with Python • Streamlit • Pandas • Plotly")