"""
Order Delivery Management System
=================================
An interactive Streamlit app for managing and analyzing food-delivery
orders: browse/filter orders, update delivery status, add new orders,
track a delivery in real time, and explore analytics.

Run locally:
    streamlit run app.py
"""

import os
from datetime import datetime, date

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# --------------------------------------------------------------------------- #
# Page config & constants
# --------------------------------------------------------------------------- #

st.set_page_config(
    page_title="Order Delivery Management System",
    page_icon="🛵",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_PATH = os.path.join(os.path.dirname(__file__), "delivery_orders.csv")

STATUS_FLOW = ["Pending", "Preparing", "Out for Delivery", "Delivered", "Cancelled"]
STATUS_COLORS = {
    "Pending": "#94A3B8",
    "Preparing": "#F59E0B",
    "Out for Delivery": "#3B82F6",
    "Delivered": "#22C55E",
    "Cancelled": "#EF4444",
}
CITY_COORDS = {
    "Lagos": (6.5244, 3.3792),
    "Abuja": (9.0765, 7.3986),
    "Nairobi": (-1.2921, 36.8219),
    "Accra": (5.6037, -0.1870),
    "Kampala": (0.3476, 32.5825),
}


# --------------------------------------------------------------------------- #
# Data loading — cached, then handed to session_state so in-app edits
# (status changes, new orders) persist for the length of the session
# without mutating the file on disk.
# --------------------------------------------------------------------------- #

@st.cache_data
def load_base_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["order_date"] = pd.to_datetime(df["order_date"])
    return df


if "orders" not in st.session_state:
    st.session_state.orders = load_base_data(DATA_PATH).copy()

if "next_order_id" not in st.session_state:
    st.session_state.next_order_id = int(st.session_state.orders["order_id"].max()) + 1


def orders_df() -> pd.DataFrame:
    return st.session_state.orders


# --------------------------------------------------------------------------- #
# Sidebar navigation
# --------------------------------------------------------------------------- #

st.sidebar.title("🛵 Delivery Ops")
page = st.sidebar.radio(
    "Navigate",
    ["🏠 Home", "📦 Orders", "➕ New Order", "🚚 Track Delivery", "📊 Analytics"],
    label_visibility="collapsed",
)

st.sidebar.divider()
st.sidebar.caption("Filters apply to Home, Orders & Analytics")
df_all = orders_df()
city_filter = st.sidebar.multiselect("City", sorted(df_all["city"].unique()))
status_filter = st.sidebar.multiselect("Status", STATUS_FLOW)
min_date = df_all["order_date"].min().date()
max_date = df_all["order_date"].max().date()
date_range = st.sidebar.date_input(
    "Order date range", value=(min_date, max_date), min_value=min_date, max_value=max_date
)

st.sidebar.divider()
st.sidebar.caption(
    "Domain Order Delivery Management System · Streamlit demo\n\n"
    f"Data as of {datetime.now():%Y-%m-%d %H:%M}"
)


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if city_filter:
        out = out[out["city"].isin(city_filter)]
    if status_filter:
        out = out[out["status"].isin(status_filter)]
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
        out = out[(out["order_date"].dt.date >= start) & (out["order_date"].dt.date <= end)]
    return out


filtered = apply_filters(df_all)


# --------------------------------------------------------------------------- #
# HOME
# --------------------------------------------------------------------------- #

if page == "🏠 Home":
    st.title("🛵 Domain Order Delivery Management System")
    st.markdown(
        "Live overview of orders across all partner restaurants and cities. "
        "Use the sidebar to filter by **city**, **status**, or **date range**."
    )

    total_orders = len(filtered)
    revenue = filtered["order_amount"].sum()
    delivered = filtered[filtered["status"] == "Delivered"]
    on_time = delivered[delivered["actual_delivery_min"] <= delivered["estimated_delivery_min"]]
    on_time_rate = (len(on_time) / len(delivered) * 100) if len(delivered) else 0.0
    avg_rating = delivered["customer_rating"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Orders", f"{total_orders:,}")
    c2.metric("Revenue", f"₦{revenue:,.0f}")
    c3.metric("On-Time Delivery Rate", f"{on_time_rate:.1f}%")
    c4.metric("Avg. Customer Rating", f"{avg_rating:.2f} ⭐" if not np.isnan(avg_rating) else "—")

    st.divider()

    left, right = st.columns([2, 1])

    with left:
        st.subheader("Orders by status")
        status_counts = filtered["status"].value_counts().reindex(STATUS_FLOW).fillna(0)
        fig = px.bar(
            status_counts,
            x=status_counts.index,
            y=status_counts.values,
            color=status_counts.index,
            color_discrete_map=STATUS_COLORS,
            labels={"x": "Status", "y": "Orders"},
        )
        fig.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Revenue by city")
        rev_city = filtered.groupby("city")["order_amount"].sum().sort_values(ascending=False)
        fig2 = px.pie(rev_city, values=rev_city.values, names=rev_city.index, hole=0.45)
        fig2.update_layout(height=380, showlegend=True)
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Recent orders")
    recent = filtered.sort_values("order_date", ascending=False).head(8)
    st.dataframe(
        recent[["order_id", "customer_name", "city", "restaurant", "status", "order_amount"]],
        use_container_width=True,
        hide_index=True,
    )


# --------------------------------------------------------------------------- #
# ORDERS — browse, filter, inline status editing
# --------------------------------------------------------------------------- #

elif page == "📦 Orders":
    st.title("📦 Order Book")
    st.caption("Search, filter, and update order status inline. Edits apply for this session.")

    search = st.text_input("🔎 Search by customer name, restaurant, or order ID")
    view = filtered.copy()
    if search:
        s = search.strip().lower()
        mask = (
            view["customer_name"].str.lower().str.contains(s)
            | view["restaurant"].str.lower().str.contains(s)
            | view["order_id"].astype(str).str.contains(s)
        )
        view = view[mask]

    sort_col = st.selectbox(
        "Sort by", ["order_date", "order_amount", "distance_km", "customer_rating"], index=0
    )
    view = view.sort_values(sort_col, ascending=False)

    st.write(f"**{len(view)}** orders match your filters")

    edited = st.data_editor(
        view[
            [
                "order_id", "customer_name", "city", "restaurant", "cuisine",
                "order_date", "order_amount", "payment_method", "status",
            ]
        ],
        column_config={
            "status": st.column_config.SelectboxColumn("status", options=STATUS_FLOW, required=True),
            "order_amount": st.column_config.NumberColumn("order_amount", format="₦%.2f"),
            "order_date": st.column_config.DateColumn("order_date"),
        },
        disabled=["order_id", "customer_name", "city", "restaurant", "cuisine", "order_date", "order_amount", "payment_method"],
        hide_index=True,
        use_container_width=True,
        key="orders_editor",
    )

    if st.button("💾 Save status changes"):
        base = st.session_state.orders.set_index("order_id")
        upd = edited.set_index("order_id")["status"]
        base.loc[upd.index, "status"] = upd
        st.session_state.orders = base.reset_index()
        st.success(f"Updated status for {len(upd)} order(s).")
        st.rerun()

    csv = view.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Export filtered orders (CSV)", csv, "filtered_orders.csv", "text/csv")


# --------------------------------------------------------------------------- #
# NEW ORDER — form widgets
# --------------------------------------------------------------------------- #

elif page == "➕ New Order":
    st.title("➕ Place a New Order")

    with st.form("new_order_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            customer_name = st.text_input("Customer name*")
            city = st.selectbox("City*", sorted(CITY_COORDS.keys()))
            restaurant = st.text_input("Restaurant*", value="Mama Put Kitchen")
            cuisine = st.selectbox(
                "Cuisine", ["Local", "Chinese", "Italian", "Indian", "Fast Food", "Continental"]
            )
            payment_method = st.radio(
                "Payment method", ["Cash on Delivery", "Card", "Mobile Money", "Wallet"], horizontal=True
            )
        with col2:
            order_date = st.date_input("Order date", value=date.today())
            item_count = st.slider("Number of items", 1, 15, 3)
            distance_km = st.slider("Distance to customer (km)", 0.5, 20.0, 3.0, step=0.1)
            order_amount = st.number_input("Order amount (₦)", min_value=0.0, value=2500.0, step=50.0)
            express = st.checkbox("Express delivery")

        submitted = st.form_submit_button("Place order", use_container_width=True)

    if submitted:
        if not customer_name or not restaurant:
            st.error("Customer name and restaurant are required.")
        else:
            lat0, lon0 = CITY_COORDS[city]
            new_row = {
                "order_id": st.session_state.next_order_id,
                "customer_name": customer_name,
                "city": city,
                "restaurant": restaurant,
                "cuisine": cuisine,
                "order_date": pd.Timestamp(order_date),
                "order_hour": datetime.now().hour,
                "item_count": item_count,
                "order_amount": order_amount,
                "discount_percent": 0,
                "delivery_fee": round(300 + distance_km * 80, 2),
                "distance_km": distance_km,
                "payment_method": payment_method,
                "delivery_partner": "Unassigned",
                "status": "Pending",
                "estimated_delivery_min": int(15 + distance_km * 4 - (5 if express else 0)),
                "actual_delivery_min": 0,
                "customer_rating": np.nan,
                "lat": lat0 + np.random.default_rng().normal(0, 0.03),
                "lon": lon0 + np.random.default_rng().normal(0, 0.03),
            }
            st.session_state.orders = pd.concat(
                [st.session_state.orders, pd.DataFrame([new_row])], ignore_index=True
            )
            st.success(
                f"Order #{st.session_state.next_order_id} placed for {customer_name} "
                f"— estimated delivery in {new_row['estimated_delivery_min']} min."
            )
            st.session_state.next_order_id += 1


# --------------------------------------------------------------------------- #
# TRACK DELIVERY — single-order detail view
# --------------------------------------------------------------------------- #

elif page == "🚚 Track Delivery":
    st.title("🚚 Track a Delivery")

    ids = orders_df().sort_values("order_id", ascending=False)["order_id"].tolist()
    order_id = st.selectbox("Order ID", ids)
    order = orders_df()[orders_df()["order_id"] == order_id].iloc[0]

    st.subheader(f"Order #{order_id} — {order['customer_name']}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Restaurant", order["restaurant"])
    c2.metric("City", order["city"])
    c3.metric("Amount", f"₦{order['order_amount']:,.2f}")

    current_idx = STATUS_FLOW.index(order["status"]) if order["status"] in STATUS_FLOW else 0
    st.markdown("**Delivery progress**")
    if order["status"] == "Cancelled":
        st.error("❌ This order was cancelled.")
    else:
        progress_steps = ["Pending", "Preparing", "Out for Delivery", "Delivered"]
        step_idx = progress_steps.index(order["status"]) if order["status"] in progress_steps else 0
        st.progress((step_idx + 1) / len(progress_steps))
        cols = st.columns(len(progress_steps))
        for i, (col, step) in enumerate(zip(cols, progress_steps)):
            marker = "✅" if i <= step_idx else "⬜"
            col.markdown(f"{marker}\n\n**{step}**")

    st.divider()
    left, right = st.columns([1, 1])
    with left:
        st.markdown("**Order details**")
        st.write(
            {
                "Cuisine": order["cuisine"],
                "Items": int(order["item_count"]),
                "Distance": f"{order['distance_km']} km",
                "Payment": order["payment_method"],
                "Delivery partner": order["delivery_partner"],
                "Estimated time": f"{order['estimated_delivery_min']} min",
            }
        )
        if order["status"] != "Cancelled" and st.button("➡️ Advance status"):
            base = st.session_state.orders
            idx = base.index[base["order_id"] == order_id][0]
            cur = base.at[idx, "status"]
            flow = ["Pending", "Preparing", "Out for Delivery", "Delivered"]
            if cur in flow and flow.index(cur) < len(flow) - 1:
                base.at[idx, "status"] = flow[flow.index(cur) + 1]
                if base.at[idx, "status"] == "Delivered":
                    base.at[idx, "actual_delivery_min"] = order["estimated_delivery_min"]
                st.rerun()

    with right:
        st.markdown("**Delivery location**")
        st.map(pd.DataFrame({"lat": [order["lat"]], "lon": [order["lon"]]}), size=200, zoom=11)


# --------------------------------------------------------------------------- #
# ANALYTICS
# --------------------------------------------------------------------------- #

elif page == "📊 Analytics":
    st.title("📊 Analytics")
    st.caption("Charts respect the sidebar filters.")

    tab1, tab2, tab3 = st.tabs(["Revenue & Volume", "Delivery Performance", "Geography"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            by_cuisine = filtered.groupby("cuisine")["order_amount"].sum().sort_values()
            fig = px.bar(by_cuisine, orientation="h", labels={"value": "Revenue (₦)", "cuisine": ""})
            fig.update_layout(showlegend=False, height=380, title="Revenue by cuisine")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            daily = filtered.groupby(filtered["order_date"].dt.date)["order_amount"].sum().cumsum()
            fig = px.line(daily, labels={"value": "Cumulative revenue (₦)", "order_date": "Date"})
            fig.update_layout(showlegend=False, height=380, title="Cumulative revenue over time")
            st.plotly_chart(fig, use_container_width=True)

        fig = px.pie(filtered, names="payment_method", title="Payment method share", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            fig = px.histogram(
                filtered[filtered["status"] == "Delivered"],
                x="actual_delivery_min",
                nbins=20,
                title="Delivery time distribution (delivered orders)",
            )
            fig.update_layout(height=380)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            deliv = filtered[filtered["status"] == "Delivered"].copy()
            deliv["late"] = deliv["actual_delivery_min"] > deliv["estimated_delivery_min"]
            fig = px.scatter(
                deliv, x="distance_km", y="actual_delivery_min", color="late",
                title="Distance vs. delivery time",
                labels={"distance_km": "Distance (km)", "actual_delivery_min": "Delivery time (min)"},
            )
            fig.update_layout(height=380)
            st.plotly_chart(fig, use_container_width=True)

        fig = px.box(filtered, x="city", y="order_amount", color="city", title="Order amount spread by city")
        fig.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown("**Delivery locations**")
        st.map(filtered[["lat", "lon"]].dropna(), size=100)
        by_city = filtered.groupby("city").agg(
            orders=("order_id", "count"), revenue=("order_amount", "sum")
        ).reset_index()
        fig = px.bar(by_city, x="city", y="orders", color="revenue", title="Orders & revenue by city")
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True)
