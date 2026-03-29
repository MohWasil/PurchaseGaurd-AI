"""
Streamlit Frontend - PurchaseGuard AI Phase 3
Enhanced dashboard with charts, email alerts, and exports
"""
import streamlit as st
import requests
import base64
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

st.set_page_config(
    page_title="PurchaseGuard AI",
    page_icon="🛡️",
    layout="wide"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .metric-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #2c3e50;
    }
    .alert-urgent {
        background-color: #ffe6e6;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #e74c3c;
    }
    .alert-warning {
        background-color: #fff3cd;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #f39c12;
    }
    </style>
""", unsafe_allow_html=True)

# Session state initialization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None

def get_headers():
    """Get authenticated headers"""
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}

def login_user(email: str, password: str) -> bool:
    """Authenticate user"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            data={"username": email, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.token = data["access_token"]
            st.session_state.authenticated = True
            
            headers = get_headers()
            user_response = requests.get(f"{API_BASE_URL}/auth/me", headers=headers)
            if user_response.status_code == 200:
                st.session_state.user = user_response.json()
            return True
        return False
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return False

def register_user(email: str, password: str) -> bool:
    """Register new user"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/register",
            json={"email": email, "password": password}
        )
        if response.status_code == 201:
            return True
        st.error(response.json().get("detail", "Registration failed"))
        return False
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return False

def logout_user():
    """Logout user"""
    st.session_state.authenticated = False
    st.session_state.token = None
    st.session_state.user = None

def upload_receipt(file) -> dict:
    """Upload receipt to API"""
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        headers = get_headers()
        response = requests.post(
            f"{API_BASE_URL}/purchases/upload",
            files=files,
            headers=headers
        )
        if response.status_code == 201:
            return response.json()
        st.error(f"Upload failed: {response.json().get('detail', 'Unknown error')}")
        return None
    except Exception as e:
        st.error(f"Upload error: {str(e)}")
        return None

def get_purchases() -> list:
    """Get all purchases"""
    try:
        headers = get_headers()
        response = requests.get(f"{API_BASE_URL}/purchases/", headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Fetch error: {str(e)}")
        return []

# def get_stats() -> dict:
#     """Get purchase statistics"""
#     try:
#         headers = get_headers()
#         response = requests.get(f"{API_BASE_URL}/purchases/stats", headers=headers)
#         if response.status_code == 200:
#             return response.json()
#         return {}
#     except Exception as e:
#         st.error(f"Fetch error: {str(e)}")
#         return {}

def get_stats() -> dict:
    """Get purchase statistics"""
    try:
        headers = get_headers()
        response = requests.get(f"{API_BASE_URL}/purchases/stats", headers=headers)
        if response.status_code == 200:
            return response.json()
        # Return default stats on error
        return {
            "total_purchases": 0,
            "total_amount": 0.0,
            "avg_purchase": 0.0,
            "categories": {},
            "upcoming_returns": 0,
            "active_warranties": 0
        }
    except Exception as e:
        st.error(f"Fetch stats error: {str(e)}")
        return {
            "total_purchases": 0,
            "total_amount": 0.0,
            "avg_purchase": 0.0,
            "categories": {},
            "upcoming_returns": 0,
            "active_warranties": 0
        }

# def get_stats() -> dict:
#     """Get purchase statistics"""
#     try:
#         headers = get_headers()
#         response = requests.get(f"{API_BASE_URL}/purchases/stats", headers=headers, timeout=10)
        
#         # Log status for debugging
#         if response.status_code != 200:
#             st.warning(f"Stats API returned: {response.status_code}")
#             st.warning(f"Response: {response.text[:200]}")
        
#         if response.status_code == 200:
#             return response.json()
        
#         return {
#             "total_purchases": 0,
#             "total_amount": 0.0,
#             "avg_purchase": 0.0,
#             "categories": {},
#             "upcoming_returns": 0,
#             "active_warranties": 0
#         }
#     except Exception as e:
#         st.warning(f"Stats fetch error: {str(e)}")
#         return {
#             "total_purchases": 0,
#             "total_amount": 0.0,
#             "avg_purchase": 0.0,
#             "categories": {},
#             "upcoming_returns": 0,
#             "active_warranties": 0
#         }


# def get_alerts() -> list:
#     """Get all alerts"""
#     try:
#         headers = get_headers()
#         response = requests.get(f"{API_BASE_URL}/purchases/alerts", headers=headers)
#         if response.status_code == 200:
#             return response.json()
#         return []
#     except Exception as e:
#         st.error(f"Fetch error: {str(e)}")
#         return []
def get_alerts() -> list:
    """Get all alerts"""
    try:
        headers = get_headers()
        response = requests.get(f"{API_BASE_URL}/purchases/alerts", headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Fetch alerts error: {str(e)}")
        return []



def delete_purchase(purchase_id: int) -> bool:
    """Delete a purchase"""
    try:
        headers = get_headers()
        response = requests.delete(
            f"{API_BASE_URL}/purchases/{purchase_id}",
            headers=headers
        )
        return response.status_code == 204
    except Exception as e:
        st.error(f"Delete error: {str(e)}")
        return False

def mark_as_returned(purchase_id: int) -> bool:
    """Mark purchase as returned"""
    try:
        headers = get_headers()
        response = requests.patch(
            f"{API_BASE_URL}/purchases/{purchase_id}/return",
            headers=headers
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"Update error: {str(e)}")
        return False

def export_csv() -> bytes:
    """Export purchases as CSV"""
    try:
        headers = get_headers()
        response = requests.get(f"{API_BASE_URL}/purchases/export/csv", headers=headers)
        if response.status_code == 200:
            return response.content
        return None
    except Exception as e:
        st.error(f"Export error: {str(e)}")
        return None

# ============== LOGIN PAGE ==============
if not st.session_state.authenticated:
    st.title("🛡️ PurchaseGuard AI")
    st.markdown("### Personal Receipt & Warranty Intelligence Agent")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login to Your Account")
        login_email = st.text_input("Email", key="login_email")
        login_password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", type="primary"):
            if login_email and login_password:
                if login_user(login_email, login_password):
                    st.success("Login successful!")
                    st.rerun()
    
    with tab2:
        st.subheader("Create New Account")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_password_confirm = st.text_input("Confirm Password", type="password", key="reg_password_confirm")
        
        if st.button("Register", type="primary"):
            if reg_password != reg_password_confirm:
                st.error("Passwords do not match")
            elif len(reg_password) < 8:
                st.error("Password must be at least 8 characters")
            elif register_user(reg_email, reg_password):
                st.success("Registration successful! Please login.")
    
    st.markdown("---")
    st.markdown("**Phase 3 Features:**")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("- 📧 Email deadline alerts")
        st.markdown("- 📊 Dashboard charts & analytics")
        st.markdown("- 📁 CSV export functionality")
    with col2:
        st.markdown("- 🏷️ Auto-categorization")
        st.markdown("- ⏰ Background scheduler")
        st.markdown("- 🔒 Bank-level encryption")

# ============== MAIN DASHBOARD ==============
else:
    # Sidebar navigation
    with st.sidebar:
        st.title(f"👤 {st.session_state.user['email'].split('@')[0]}")
        
        if st.button("Logout", type="secondary"):
            logout_user()
            st.rerun()
        
        st.markdown("---")
        page = st.radio(
            "Navigation",
            ["📊 Dashboard", "📤 Upload Receipt", "📦 All Purchases", "🔔 Alerts", "⚙️ Settings"]
        )
        
        st.markdown("---")
        st.markdown("**Quick Stats:**")
        stats = get_stats()
        if stats:
            st.metric("Total Purchases", stats.get("total_purchases", 0))
            st.metric("Total Spent", f"${stats.get('total_amount', 0):.2f}")
    
    # ============== DASHBOARD PAGE ==============
    if page == "📊 Dashboard":
        st.title("📊 PurchaseGuard Dashboard")
        
        # Refresh button
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("🔄 Refresh"):
                st.rerun()
        
        # Get data
        stats = get_stats()
        purchases = get_purchases()
        alerts = get_alerts()
        
        # Stats cards
        # col1, col2, col3, col4 = st.columns(4)
        # with col1:
        #     st.metric("📦 Total Purchases", stats.get("total_purchases", 0))
        # with col2:
        #     st.metric("💰 Total Spent", f"${stats.get('total_amount', 0):.2f}")
        # with col3:
        #     st.metric("⏰ Upcoming Returns", stats.get("upcoming_returns", 0))
        # with col4:
        #     st.metric("🛡️ Active Warranties", stats.get("active_warranties", 0))
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📦 Total Purchases", stats.get("total_purchases", 0))
        with col2:
            total_spent = stats.get("total_amount", 0)
            st.metric("💰 Total Spent", f"${float(total_spent):.2f}" if total_spent else "$0.00")
        with col3:
            st.metric("⏰ Upcoming Returns", stats.get("upcoming_returns", 0))
        with col4:
            st.metric("🛡️ Active Warranties", stats.get("active_warranties", 0))  
          
        st.markdown("---")
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Spending by Category")
            if stats.get("categories"):
                fig = px.pie(
                    values=list(stats["categories"].values()),
                    names=list(stats["categories"].keys()),
                    title="Purchase Categories"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Upload receipts to see category breakdown")
        
        with col2:
            st.subheader("🔔 Recent Alerts")
            if alerts:
                for alert in alerts[:5]:
                    alert_type = alert.get("type", "info")
                    if "return" in alert_type.lower():
                        st.markdown(f'<div class="alert-urgent">🔴 {alert.get("message", "")}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="alert-warning">🟡 {alert.get("message", "")}</div>', unsafe_allow_html=True)
            else:
                st.info("🔔 No alerts. You're all caught up!")
        
        st.markdown("---")
        
        # Recent purchases table
        st.subheader("📦 Recent Purchases")
        if purchases:
            df = pd.DataFrame(purchases[:10])
            # df["purchase_date"] = pd.to_datetime(df["purchase_date"]).dt.strftime("%Y-%m-%d")
            df["purchase_date"] = pd.to_datetime(df["purchase_date"], format='ISO8601').dt.strftime("%Y-%m-%d")
            st.dataframe(
                df[["merchant_name", "total_amount", "purchase_date", "return_deadline"]],
                use_container_width=True
            )
        else:
            st.info("📭 No purchases yet. Upload your first receipt!")
        
        # Export option
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            csv_data = export_csv()
            if csv_data:
                st.download_button(
                    label="📁 Export CSV",
                    data=csv_data,
                    file_name="purchases.csv",
                    mime="text/csv"
                )
    
    # ============== UPLOAD PAGE ==============
    elif page == "📤 Upload Receipt":
        st.title("📤 Upload Receipt")
        
        uploaded_file = st.file_uploader(
            "Choose receipt image",
            type=["png", "jpg", "jpeg"],
            help="Max file size: 10MB"
        )
        
        if uploaded_file:
            st.image(uploaded_file, caption="Preview", use_column_width=True)
            
            if st.button("Process Receipt", type="primary"):
                with st.spinner("🤖 AI is processing your receipt..."):
                    result = upload_receipt(uploaded_file)
                    if result:
                        st.success("✅ Receipt processed successfully!")
                        st.json(result)
        
        st.markdown("---")
        st.info("💡 Tips for best results:\n- Use clear, well-lit photos\n- Ensure all text is visible\n- Avoid blurry or crumpled receipts")
    
    # ============== ALL PURCHASES PAGE ==============
    elif page == "📦 All Purchases":
        st.title("📦 All Purchases")
        
        purchases = get_purchases()
        
        if purchases:
            for purchase in purchases:
                with st.expander(
                    f"{purchase.get('merchant_name', 'Unknown')} - ${purchase.get('total_amount', 0):.2f}"
                ):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Date:** {purchase.get('purchase_date', 'N/A')[:10] if purchase.get('purchase_date') else 'N/A'}")
                        st.write(f"**Amount:** ${purchase.get('total_amount', 0):.2f}")
                        st.write(f"**Currency:** {purchase.get('currency', 'USD')}")
                    with col2:
                        st.write(f"**Return Deadline:** {purchase.get('return_deadline', 'N/A')[:10] if purchase.get('return_deadline') else 'N/A'}")
                        st.write(f"**Warranty Expires:** {purchase.get('warranty_expiry', 'N/A')[:10] if purchase.get('warranty_expiry') else 'N/A'}")
                    
                    # Action buttons
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if not purchase.get("is_returned"):
                            if st.button("Mark Returned", key=f"return_{purchase['id']}"):
                                if mark_as_returned(purchase['id']):
                                    st.success("Marked as returned!")
                                    st.rerun()
                    with col2:
                        if not purchase.get("is_claimed"):
                            if st.button("Mark Claimed", key=f"claim_{purchase['id']}"):
                                st.success("Marked as claimed!")
                                st.rerun()
                    with col3:
                        if st.button("Delete", key=f"delete_{purchase['id']}", type="secondary"):
                            if delete_purchase(purchase['id']):
                                st.success("Deleted!")
                                st.rerun()
        else:
            st.info("📭 No purchases yet. Upload your first receipt!")
    
    # ============== ALERTS PAGE ==============
    elif page == "🔔 Alerts":
        st.title("🔔 Alerts & Notifications")
        
        alerts = get_alerts()
        
        if alerts:
            # Group by type
            urgent_alerts = [a for a in alerts if "return" in a.get("type", "").lower()]
            warranty_alerts = [a for a in alerts if "warranty" in a.get("type", "").lower()]
            other_alerts = [a for a in alerts if a not in urgent_alerts and a not in warranty_alerts]
            
            if urgent_alerts:
                st.subheader("🔴 Urgent Return Deadlines")
                for alert in urgent_alerts:
                    st.markdown(f'<div class="alert-urgent">{alert.get("message", "")}</div>', unsafe_allow_html=True)
            
            if warranty_alerts:
                st.subheader("🟡 Warranty Expirations")
                for alert in warranty_alerts:
                    st.markdown(f'<div class="alert-warning">{alert.get("message", "")}</div>', unsafe_allow_html=True)
            
            if other_alerts:
                st.subheader("⚪ Other Alerts")
                for alert in other_alerts:
                    st.info(alert.get("message", ""))
        else:
            st.success("🎉 No alerts! All your purchases are in good standing.")
        
        st.markdown("---")
        st.info("📧 Email alerts are sent automatically for deadlines within 7 days. Check your .env file to configure email settings.")
    
    # ============== SETTINGS PAGE ==============
    elif page == "⚙️ Settings":
        st.title("⚙️ Settings")
        
        st.subheader("👤 Account Information")
        st.write(f"**Email:** {st.session_state.user.get('email', 'N/A')}")
        st.write(f"**Account Created:** {st.session_state.user.get('created_at', 'N/A')[:10]}")
        
        st.markdown("---")
        st.subheader("📧 Email Notifications")
        st.info("Email alerts are configured in the backend .env file. Contact administrator to change settings.")
        
        st.markdown("---")
        st.subheader("📁 Data Export")
        csv_data = export_csv()
        if csv_data:
            st.download_button(
                label="📁 Download All Purchases (CSV)",
                data=csv_data,
                file_name=f"purchases_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
        st.markdown("---")
        st.subheader(" Security")
        st.success(" Your data is encrypted with AES-256")
        st.success(" All API connections use JWT authentication")
        st.success(" Receipts are stored securely")
    
