# app/main.py
import os
import requests
import pandas as pd
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")

st.set_page_config(
    page_title="Customer Sales Dashboard",
    page_icon="📊",
    layout="wide",
)

# ── Sidebar navigation ────────────────────────────────────
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Customer Chatbot"],
    index=0,
)

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

# ── Page: Dashboard ───────────────────────────────────────
if page == "Dashboard":
    st.title("Customer Sales Dashboard")

    @st.cache_data(ttl=60)
    def fetch_customers():
        r = requests.get(f"{BACKEND_URL}/customers", timeout=10)
        r.raise_for_status()
        return r.json()

    data      = fetch_customers()
    customers = data["customers"]
    df        = pd.DataFrame(customers)

    st.subheader("Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total customers", data["count"])
    col2.metric("Highest sales",   f"${df['total_sales'].max():,.2f}")
    col3.metric("Total revenue",   f"${df['total_sales'].sum():,.2f}")

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

# ── Page: Chatbot ─────────────────────────────────────────
elif page == "Customer Chatbot":
    st.title("Customer Sales Chatbot")
    st.caption("Ask anything about your customer sales data")

    # Initialise session state for message history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role":    "assistant",
                "content": "Hi! I can answer questions about your customer sales data. Try asking: *Who is the top customer?* or *What is the total revenue?*"
            }
        ]

    # Render existing message history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input box — appears at the bottom
    if prompt := st.chat_input("Ask about your customer data..."):

        # Show user message immediately
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Call backend /chat route
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/chat",
                        json={"question": prompt},
                        timeout=60,    # LLM can be slow on CPU
                    )
                    if response.status_code == 200:
                        answer = response.json()["answer"]
                    else:
                        answer = f"Backend error: {response.status_code}"
                except requests.exceptions.Timeout:
                    answer = "The model took too long to respond. Please try again."
                except requests.exceptions.ConnectionError:
                    answer = "Cannot reach the backend. Please check the service."

            st.markdown(answer)

        # Save assistant reply to history
        st.session_state.messages.append({"role": "assistant", "content": answer})

    # Clear chat button
    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()