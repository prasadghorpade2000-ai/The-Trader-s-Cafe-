import streamlit as st
import pandas as pd
import qrcode
import plotly.express as px
from io import BytesIO
from datetime import datetime
import urllib.parse
import os

# --- CONFIGURATION ---
CAFE_NAME = "The Trader's Cafe"
TAGLINE = "Bake Your Taste 🥧"
INSTAGRAM_HANDLE = "the_traders_cafe"

st.set_page_config(page_title=CAFE_NAME, layout="wide")

# --- DATABASE SETUP ---
DB_FILE = 'cafe_sales.csv'
if not os.path.isfile(DB_FILE):
    df = pd.DataFrame(columns=['Date', 'Item', 'Qty', 'Total', 'Phone'])
    df.to_csv(DB_FILE, index=False)

# --- MENU DATA ---
menu = {
    "🔥 Combo Offers": {"Student Combo": 99, "Trader's Special": 149, "Party Pack": 199},
    "🍕 Pizza": {"Golden Corn": 59, "Testy Tomato": 49, "Shiney Onion": 49, "Spicy Shezwan": 79, "Mighty Paneer Pizza": 79},
    "🍔 Burger": {"Classic Burger": 39, "Cheese Burger": 55, "Spicy Salsa": 59, "Royal Paneer Grill": 69},
    "🥪 Sandwich": {"Grill Sandwich": 39, "Vegs Cheese Sandwich": 49, "Choklet Sandwich": 59}
}

# --- SIDEBAR & SETTINGS ---
st.sidebar.title("⚙️ Admin Panel")
uploaded_logo = st.sidebar.file_uploader("Upload Logo", type=['png', 'jpg'])
show_analytics = st.sidebar.checkbox("Show Sales Analytics")

if 'cart' not in st.session_state:
    st.session_state.cart = {}

# --- ANALYTICS SECTION ---
if show_analytics:
    st.header("📊 Business Analytics")
    sales_df = pd.read_csv(DB_FILE)
    if not sales_df.empty:
        sales_df['Date'] = pd.to_datetime(sales_df['Date'])
        
        col_a, col_b = st.columns(2)
        with col_a:
            # Daily Sales Graph
            daily_sales = sales_df.groupby(sales_df['Date'].dt.date)['Total'].sum().reset_index()
            fig = px.line(daily_sales, x='Date', y='Total', title="Daily Revenue (₹)")
            st.plotly_chart(fig, use_container_width=True)
        
        with col_b:
            # Top Items Chart
            top_items = sales_df.groupby('Item')['Qty'].sum().sort_values(ascending=False).head(5)
            fig2 = px.bar(top_items, title="Top 5 Selling Items")
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("Abhi tak koi sales data nahi hai.")
    st.divider()

# --- BILLING INTERFACE ---
col_logo, col_title = st.columns()
with col_logo:
    if uploaded_logo: st.image(uploaded_logo, width=100)
    else: st.title("☕")
with col_title:
    st.title(CAFE_NAME)
    st.caption(TAGLINE)

col1, col2 = st.columns()

with col1:
    tabs = st.tabs(list(menu.keys()))
    for i, category in enumerate(menu.keys()):
        with tabs[i]:
            items = menu[category]
            cols = st.columns(2)
            for idx, (item, price) in enumerate(items.items()):
                with cols[idx % 2]:
                    if st.button(f"{item} - ₹{price}", key=f"btn_{item}", use_container_width=True):
                        st.session_state.cart[item] = st.session_state.cart.get(item, 0) + 1
                        st.rerun()

with col2:
    st.header("🧾 New Bill")
    total_bill = 0
    phone = st.text_input("Customer Phone", value="91")
    
    if st.session_state.cart:
        for item, qty in st.session_state.cart.items():
            price = next(p for cat in menu.values() for i, p in cat.items() if i == item)
            subtotal = price * qty
            total_bill += subtotal
            st.write(f"**{item}** x {qty} = ₹{subtotal}")
        
        st.subheader(f"Total: ₹{total_bill}")
        
        if st.button("Complete Order ✅", type="primary", use_container_width=True):
            # Save to CSV
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            new_entries = [[now, i, q, (next(p for cat in menu.values() for it, p in cat.items() if it == i) * q), phone] for i, q in st.session_state.cart.items()]
            pd.DataFrame(new_entries).to_csv(DB_FILE, mode='a', header=False, index=False)
            
            # WhatsApp Link
            wa_msg = f"Thanks for visiting *{CAFE_NAME}*! \nYour bill is *₹{total_bill}*. \nInstagram: instagram.com/{INSTAGRAM_HANDLE}"
            st.markdown(f"[📲 Send WhatsApp Receipt](https://wa.me/{phone}?text={urllib.parse.quote(wa_msg)})")
            st.session_state.cart = {}
            st.success("Order Logged!")
    
    if st.button("Clear Cart 🗑️", use_container_width=True):
        st.session_state.cart = {}
        st.rerun()
