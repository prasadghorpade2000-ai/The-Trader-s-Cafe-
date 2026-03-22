import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import os

# --- CONFIG ---
CAFE_NAME = "The Trader's Cafe"
ADMIN_PASSWORD = "Prasad@123" 
DB_FILE = 'cafe_sales.csv'
STOCK_FILE = 'inventory.csv'

st.set_page_config(page_title=CAFE_NAME, layout="wide")

# --- INITIAL SETUP ---
if not os.path.isfile('menu.csv'):
    pd.DataFrame([['🍕 Pizza', 'Golden Corn', 59], ['🍔 Burger', 'Classic', 39]], 
                 columns=['Category', 'Item', 'Price']).to_csv('menu.csv', index=False)

if not os.path.isfile(DB_FILE):
    pd.DataFrame(columns=['Date', 'Item', 'Qty', 'Total', 'Phone', 'Status']).to_csv(DB_FILE, index=False)

# Inventory Setup (Pizza Base, Burger Bun, etc.)
if not os.path.isfile(STOCK_FILE):
    pd.DataFrame([['Pizza Base', 50], ['Burger Bun', 50], ['Paneer (Portions)', 30]], 
                 columns=['Raw_Material', 'Current_Stock']).to_csv(STOCK_FILE, index=False)

menu_df = pd.read_csv('menu.csv')
stock_df = pd.read_csv(STOCK_FILE)

if 'cart' not in st.session_state:
    st.session_state.cart = {}

# --- SIDEBAR: ADMIN & STOCK MANAGEMENT ---
st.sidebar.title("🔐 Admin & Inventory")
input_pass = st.sidebar.text_input("Admin Password", type="password")

if input_pass == ADMIN_PASSWORD:
    st.sidebar.success("Owner Access")
    admin_tab = st.sidebar.radio("Go To:", ["Sales Report", "Manage Stock", "Edit Menu"])

    if admin_tab == "Manage Stock":
        st.header("📦 Inventory Management")
        new_stock_data = st.data_editor(stock_df, num_rows="dynamic", use_container_width=True)
        if st.button("Update Stock"):
            new_stock_data.to_csv(STOCK_FILE, index=False)
            st.success("Stock Updated!")
            st.rerun()

    if admin_tab == "Sales Report":
        st.header("🏁 Day Closing")
        sales_df = pd.read_csv(DB_FILE)
        st.metric("Total Sale Today", f"₹{sales_df[sales_df['Status']=='Completed']['Total'].sum()}")
        st.dataframe(sales_df.tail(20), use_container_width=True)

# --- LOW STOCK ALERTS ---
for _, row in stock_df.iterrows():
    if row['Current_Stock'] <= 5:
        st.warning(f"⚠️ Low Stock: {row['Raw_Material']} (Sirf {row['Current_Stock']} bache hain!)")

# --- MAIN BILLING ---
st.title(f"☕ {CAFE_NAME}")
col1, col2 = st.columns()

with col1:
    tabs = st.tabs(list(menu_df['Category'].unique()))
    for i, cat in enumerate(menu_df['Category'].unique()):
        with tabs[i]:
            items = menu_df[menu_df['Category'] == cat]
            cols = st.columns(2)
            for idx, row in items.iterrows():
                with cols[idx % 2]:
                    if st.button(f"{row['Item']} - ₹{row['Price']}", key=f"add_{row['Item']}", use_container_width=True):
                        st.session_state.cart[row['Item']] = st.session_state.cart.get(row['Item'], 0) + 1
                        st.rerun()

with col2:
    st.header("🧾 Cart")
    phone = st.text_input("Customer Phone", value="91")
    
    if st.session_state.cart:
        total_bill = 0
        for item, qty in list(st.session_state.cart.items()):
            price = menu_df[menu_df['Item'] == item]['Price'].values
            total_bill += price * qty
            st.write(f"**{item}** x {qty} = ₹{price*qty}")
        
        st.subheader(f"Total: ₹{total_bill}")

        if st.button("✅ Confirm Order & Send Bill", type="primary", use_container_width=True):
            # 1. Update Stock (Logic: Pizza uses Pizza Base, Burger uses Bun)
            for item, qty in st.session_state.cart.items():
                if "Pizza" in item:
                    stock_df.loc[stock_df['Raw_Material'] == 'Pizza Base', 'Current_Stock'] -= qty
                if "Burger" in item:
                    stock_df.loc[stock_df['Raw_Material'] == 'Burger Bun', 'Current_Stock'] -= qty
            stock_df.to_csv(STOCK_FILE, index=False)

            # 2. Save Sales
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            new_sales = [[now, i, q, (menu_df[menu_df['Item'] == i]['Price'].values * q), phone, 'Completed'] for i, q in st.session_state.cart.items()]
            pd.DataFrame(new_sales).to_csv(DB_FILE, mode='a', header=False, index=False)
            
            st.success("Order Placed & Stock Deducted!")
            st.session_state.cart = {}
            st.rerun()
