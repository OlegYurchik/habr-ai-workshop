import os
from datetime import datetime, date
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Expense Tracker", layout="wide")
st.title("Expense Tracker")

page = st.sidebar.radio("Navigation", ["Transactions", "Report", "Categories"])


def get_categories() -> list[dict]:
    try:
        response = requests.get(f"{API_URL}/categories", timeout=5)
        return response.json() if response.ok else []
    except requests.RequestException:
        return []


if page == "Categories":
    st.header("Categories")

    with st.form("add_category"):
        name = st.text_input("Category name")
        if st.form_submit_button("Add") and name:
            response = requests.post(f"{API_URL}/categories", json={"name": name})
            if response.status_code == 201:
                st.success(f"Category '{name}' added.")
                st.rerun()
            elif response.status_code == 409:
                st.error("Category already exists.")
            else:
                st.error("Error adding category.")

    categories = get_categories()
    if categories:
        st.dataframe(
            [{"ID": c["id"], "Name": c["name"]} for c in categories],
            use_container_width=True,
        )
    else:
        st.info("No categories yet.")


elif page == "Transactions":
    st.header("Transactions")

    categories = get_categories()
    category_map = {c["name"]: c["id"] for c in categories}

    with st.form("add_transaction"):
        col1, col2 = st.columns(2)
        amount = col1.number_input("Amount", min_value=0.01, step=0.01, value=0.01)
        category_name = col2.selectbox("Category", options=list(category_map.keys()) or ["—"])
        description = st.text_input("Description (optional)")
        transaction_date = st.date_input("Date", value=date.today())
        if st.form_submit_button("Add") and category_map:
            created_at = datetime.combine(transaction_date, datetime.min.time()).isoformat()
            response = requests.post(f"{API_URL}/transactions", json={
                "amount": amount,
                "description": description or None,
                "category_id": category_map[category_name],
                "created_at": created_at,
            })
            if response.status_code == 201:
                st.success("Transaction added.")
                st.rerun()
            else:
                st.error("Error adding transaction.")

    st.subheader("Filter")
    col1, col2, col3 = st.columns(3)
    filter_category = col1.selectbox("Category", options=["All"] + list(category_map.keys()))
    from_date = col2.date_input("From", value=None, key="tx_from")
    to_date = col3.date_input("To", value=None, key="tx_to")

    params: dict = {"limit": 100}
    if filter_category != "All":
        params["category_id"] = category_map[filter_category]
    if from_date:
        params["from_date"] = datetime.combine(from_date, datetime.min.time()).isoformat()
    if to_date:
        params["to_date"] = datetime.combine(to_date, datetime.max.time()).isoformat()

    response = requests.get(f"{API_URL}/transactions", params=params, timeout=5)
    if response.ok:
        data = response.json()
        st.caption(f"Total: {data['total']}")
        if data["items"]:
            category_id_map = {c["id"]: c["name"] for c in categories}
            st.dataframe(
                [
                    {
                        "ID": t["id"],
                        "Amount": t["amount"],
                        "Description": t["description"] or "",
                        "Category": category_id_map.get(t["category_id"], "Unknown"),
                        "Date": t["created_at"][:10],
                    }
                    for t in data["items"]
                ],
                use_container_width=True,
            )
        else:
            st.info("No transactions found.")


elif page == "Report":
    st.header("Report")

    col1, col2 = st.columns(2)
    from_date = col1.date_input("From", value=None, key="rep_from")
    to_date = col2.date_input("To", value=None, key="rep_to")

    params = {}
    if from_date:
        params["from_date"] = datetime.combine(from_date, datetime.min.time()).isoformat()
    if to_date:
        params["to_date"] = datetime.combine(to_date, datetime.max.time()).isoformat()

    response = requests.get(f"{API_URL}/report", params=params, timeout=5)
    if response.ok:
        items = response.json()
        if items:
            st.bar_chart({item["category"]: item["total"] for item in items})
            st.dataframe(
                [{"Category": item["category"], "Total": item["total"]} for item in items],
                use_container_width=True,
            )
        else:
            st.info("No data for the selected period.")
