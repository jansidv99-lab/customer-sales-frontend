# app/main.py
import os
import requests
import pandas as pd
import streamlit as st

# Backend URL — injected as env var in Kubernetes, default for local dev
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")

st.set_page_config(
    page_title="Customer Sales Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("Customer Sales Dashboard")
st.caption(f"Data source: {BACKEND_URL}")

# ── Health check ──────────────────────────────────────────
def check_backend():
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return r.status_code == 200
    except requests.exceptions.ConnectionError:
        return False

if not check_backend():
    st.error("Cannot reach backend API. Is it running?")
    st.stop()

st.success("Backend connected")

# ── Fetch all customers ───────────────────────────────────
@st.cache_data(ttl=60)   # cache for 60 seconds — avoids hammering BigQuery
def fetch_customers():
    r = requests.get(f"{BACKEND_URL}/customers", timeout=10)
    r.raise_for_status()
    return r.json()

data = fetch_customers()
customers = data["customers"]
df = pd.DataFrame(customers)

# ── Summary metrics ───────────────────────────────────────
st.subheader("Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Total customers", data["count"])
col2.metric("Highest sales",   f"${df['total_sales'].max():,.2f}")
col3.metric("Total revenue",   f"${df['total_sales'].sum():,.2f}")

# ── Customer table ────────────────────────────────────────
st.subheader("All customers")
st.dataframe(
    df.rename(columns={
        "customer_id":   "ID",
        "customer_name": "Name",
        "total_sales":   "Total Sales (USD)",
    }),
    use_container_width=True,
    hide_index=True,
)

# ── Single customer lookup ────────────────────────────────
st.subheader("Customer lookup")
customer_id = st.text_input("Enter customer ID (e.g. C004)").strip().upper()

if customer_id:
    r = requests.get(f"{BACKEND_URL}/customers/{customer_id}", timeout=10)
    if r.status_code == 200:
        c = r.json()
        st.success(f"Found: {c['customer_name']}")
        st.json(c)
    elif r.status_code == 404:
        st.warning(f"Customer {customer_id} not found")
    else:
        st.error("Unexpected error from backend")