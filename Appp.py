import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import datetime
import urllib.parse
import os

# --- CONFIGURATION ---
CAFE_NAME = "The Trader's Cafe"
INSTAGRAM_HANDLE = "the_traders_cafe"
ADMIN_PASSWORD = "Prasad@123"  # <--- Apna man-pasand password yahan change karein

st.set_page_config(page_title=CAFE_NAME, layout="wide")

# --- DATABASE & MENU SYNC ---
if not os.path.isfile('menu.csv'):
    initial_menu = pd.DataFrame([
        ['🍕 Pizza', 'Golden Corn', 59],
        ['🍕 Pizza', 'Mighty Paneer', 79],
        ['🍔 Burger', 'Classic Burger', 39],
        ['🥪 Sandwich', 'Grill Sandwich', 39],
        ['🔥 Combo', 'Student Combo', 99]
    ], columns=['Category', 'Item', 'Price'])
    initial_menu.to_csv('menu.csv', index=False)

menu_df = pd.read_csv('menu.csv')

if not os.path.isfile('cafe_sales.csv'):
    pd.DataFrame(columns=['Date', 'Item', 'Qty', 'Total', 'Phone']).to_csv('cafe_sales.csv', index=False)

if 'cart' not in st.session_state:
    st.session_state.cart = {}

# --- SIDEBAR: SECURE ADMIN DASHBOARD ---
st.sidebar.title("🔐 Admin Panel")
input_pass = st.sidebar.text_input("Enter Admin Password", type="password")

if input_pass == ADMIN_PASSWORD:
    st.sidebar.success("Access Granted!")
    admin_mode = st.sidebar.checkbox("Edit Menu & Rates")
    show_analytics = st.sidebar.checkbox("Show Sales Report")

    if admin_mode:
        st.header("✏️ Edit Menu Items & Rates")
        # Add New Item
        with st.expander("➕ Add New Item / Offer"):
            new_cat = st.selectbox("Category", ["🍕 Pizza", "🍔 Burger", "🥪 Sandwich", "🔥 Combo", "🥤 Drinks"])
            new_item = st.text_input("Item Name")
            new_price = st.number_input("Price (₹)", min_value=1)
            if st.button("Add to Menu"):
                new_row = pd.DataFrame([[new_cat, new_item, new_price]], columns=['Category', 'Item', 'Price'])
                menu_df = pd.concat([menu_df, new_row], ignore_index=True)
                menu_df.to_csv('menu.csv', index=False)
                st.success("Added!")
                st.rerun()

        # Edit/Delete List
        st.subheader("📋 Current Menu")
        edited_menu = st.data_editor(menu_df, num_rows="dynamic", use_container_width=True)
        if st.button("Save Changes"):
            edited_menu.to_csv('menu.csv', index=False)
            st.success("Menu Updated!")
            st.rerun()

    if show_analytics:
        st.header("📊 Sales Report")
        sales_data = pd.read_csv('cafe_sales.csv')
        st.dataframe(sales_data.tail(20), use_container_width=True)
        st.download_button("Download Full Report (CSV)", sales_data.to_csv(index=False), "sales_report.csv")

else:
    if input_pass != "":
        st.sidebar.error("Wrong Password!")

# --- MAIN BILLING INTERFACE ---
st.title(f"☕ {CAFE_NAME}")
st.caption("Bake Your Taste 🥧")

col1, col2 = st.columns()

with col1:
    categories = menu_df['Category'].unique()
    tabs = st.tabs(list(categories))
    for i, cat in enumerate(categories):
        with tabs[i]:
            items_in_cat = menu_df[menu_df['Category'] == cat]
            cols = st.columns(2)
            for idx, row in items_in_cat.iterrows():
                with cols[idx % 2]:
                    if st.button(f"{row['Item']}\n₹{row['Price']}", key=f"btn_{row['Item']}", use_container_width=True):
                        st.session_state.cart[row['Item']] = st.session_state.cart.get(row['Item'], 0) + 1
                        st.rerun()

with col2:
    st.header("🧾 Checkout")
    phone = st.text_input("WhatsApp (91...)", value="91")
    total_bill = 0
    bill_details = ""
    
    if st.session_state.cart:
        for item, qty in st.session_state.cart.items():
            price = menu_df[menu_df['Item'] == item]['Price'].values
            subtotal = price * qty
            total_bill += subtotal
            st.write(f"**{item}** x {qty} = ₹{subtotal}")
            bill_details += f"- {item} (x{qty}): ₹{subtotal}\n"
        
        st.divider()
        st.subheader(f"Total: ₹{total_bill}")
        
        if st.button("✅ Confirm & Send WhatsApp Bill", type="primary", use_container_width=True):
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            sales_entries = [[now, i, q, (menu_df[menu_df['Item'] == i]['Price'].values * q), phone] for i, q in st.session_state.cart.items()]
            pd.DataFrame(sales_entries).to_csv('cafe_sales.csv', mode='a', header=False, index=False)
            
            wa_msg = f"Thanks for visiting *{CAFE_NAME}* ☕\n\n*Order Detail:*\n{bill_details}\n*Total: ₹{total_bill}*\n\nInstagram: instagram.com/{INSTAGRAM_HANDLE}"
            wa_url = f"https://wa.me/{phone}?text={urllib.parse.quote(wa_msg)}"
            st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:12px; border-radius:5px; font-weight:bold; cursor:pointer;">📲 Click to Send Bill</button></a>', unsafe_allow_html=True)
            st.session_state.cart = {}

    if st.button("Clear Cart 🗑️", use_container_width=True):
        st.session_state.cart = {}
        st.rerun()
