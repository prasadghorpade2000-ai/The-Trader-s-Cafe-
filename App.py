import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import os

# --- CONFIG ---
CAFE_NAME = "The Trader's Cafe"
ADMIN_PASSWORD = "Prasad@123" 
DB_FILE = 'cafe_sales.csv'

st.set_page_config(page_title=CAFE_NAME, layout="wide")

# --- DATABASE SETUP ---
if not os.path.isfile('menu.csv'):
    pd.DataFrame([['🍕 Pizza', 'Golden Corn', 59], ['🍔 Burger', 'Classic', 39]], 
                 columns=['Category', 'Item', 'Price']).to_csv('menu.csv', index=False)

if not os.path.isfile(DB_FILE):
    pd.DataFrame(columns=['Date', 'Item', 'Qty', 'Total', 'Phone', 'Status']).to_csv(DB_FILE, index=False)

menu_df = pd.read_csv('menu.csv')

if 'cart' not in st.session_state:
    st.session_state.cart = {}

# --- SIDEBAR: ADMIN & DAY CLOSING ---
st.sidebar.title("🔐 Admin & Reports")
input_pass = st.sidebar.text_input("Admin Password", type="password")

if input_pass == ADMIN_PASSWORD:
    show_reports = st.sidebar.checkbox("📊 Day Closing & Analytics")
    if show_reports:
        st.header("🏁 Day Closing Report")
        sales_df = pd.read_csv(DB_FILE)
        if not sales_df.empty:
            # Summary Metrics
            col_m1, col_m2, col_m3 = st.columns(3)
            active_sales = sales_df[sales_df['Status'] == 'Completed']
            cancelled_sales = sales_df[sales_df['Status'] == 'Cancelled']
            
            col_m1.metric("Total Sale (Net)", f"₹{active_sales['Total'].sum()}")
            col_m2.metric("Orders Completed", len(active_sales))
            col_m3.metric("Orders Cancelled", len(cancelled_sales), delta_color="inverse")

            # Cancellation Details
            st.subheader("Order Logs")
            st.dataframe(sales_df.tail(20), use_container_width=True)
            
            # Cancel an Order functionality
            order_to_cancel = st.selectbox("Select Order Date/Time to Cancel", sales_df['Date'].unique())
            if st.button("❌ Mark Order as Cancelled"):
                sales_df.loc[sales_df['Date'] == order_to_cancel, 'Status'] = 'Cancelled'
                sales_df.to_csv(DB_FILE, index=False)
                st.success(f"Order {order_to_cancel} cancelled!")
                st.rerun()
        else:
            st.info("No sales yet.")

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
    st.header("🧾 Live Bill")
    phone = st.text_input("Customer Phone", value="91")
    
    if st.session_state.cart:
        total_bill = 0
        bill_msg = ""
        for item, qty in list(st.session_state.cart.items()):
            price = menu_df[menu_df['Item'] == item]['Price'].values
            subtotal = price * qty
            total_bill += subtotal
            
            # --- EDIT OPTIONS (Add/Remove/Cancel individual item) ---
            c_item, c_minus, c_plus, c_del = st.columns()
            c_item.write(f"**{item}** (₹{subtotal})")
            if c_minus.button("➖", key=f"min_{item}"):
                if qty > 1: st.session_state.cart[item] -= 1
                else: st.session_state.cart.pop(item)
                st.rerun()
            if c_plus.button("➕", key=f"pls_{item}"):
                st.session_state.cart[item] += 1
                st.rerun()
            if c_del.button("🗑️", key=f"del_{item}"):
                st.session_state.cart.pop(item)
                st.rerun()
            
            bill_msg += f"- {item} (x{qty}): ₹{subtotal}\n"

        st.divider()
        st.subheader(f"Grand Total: ₹{total_bill}")

        if st.button("✅ Complete & Send WhatsApp", type="primary", use_container_width=True):
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            new_data = [[now, i, q, (menu_df[menu_df['Item'] == i]['Price'].values * q), phone, 'Completed'] 
                        for i, q in st.session_state.cart.items()]
            pd.DataFrame(new_data).to_csv(DB_FILE, mode='a', header=False, index=False)
            
            wa_text = f"Thanks for visiting *{CAFE_NAME}*!\n\n*Bill Summary:*\n{bill_msg}\n*Total: ₹{total_bill}*\n\nSee you again! ✨"
            wa_url = f"https://wa.me/{phone}?text={urllib.parse.quote(wa_text)}"
            st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:12px; border-radius:5px; font-weight:bold;">📲 Send WhatsApp Bill</button></a>', unsafe_allow_html=True)
            st.session_state.cart = {}
