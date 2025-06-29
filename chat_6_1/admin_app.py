import streamlit as st
import pandas as pd
from datetime import datetime
from utils import (
    verify_admin, get_all_users, get_all_token_usage,
    get_token_usage_by_user, get_monthly_token_usage, get_chats_by_user
)

COST_PER_1K_TOKENS = 0.001  # Adjust based on model pricing

# Set page config
st.set_page_config(page_title="📊 Admin Dashboard", layout="wide")

# Hide Streamlit menu and footer
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- Admin Login ---
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

if not st.session_state.admin_logged_in:
    st.title("🔒 Admin Login")
    email = st.text_input("Admin Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if verify_admin(email, password):
            st.session_state.admin_logged_in = True
            st.success("Logged in as Admin")
            st.rerun()
        else:
            st.error("Invalid admin credentials")
    st.stop()

# --- Admin Dashboard ---
st.title("📊 Admin Dashboard — AI Chat Usage Analytics")
st.markdown("---")

# Select user
user_emails = [u["email"] for u in get_all_users()]
selected_email = st.selectbox("Select User", options=user_emails)

if selected_email:
    st.subheader(f"User: {selected_email}")

    # Get token records
    token_records = get_token_usage_by_user(selected_email)

    if token_records:
        df = pd.DataFrame(token_records)
        df["date"] = pd.to_datetime(df["timestamp"]).dt.date
        df["cost"] = (df["total_tokens"] / 1000) * COST_PER_1K_TOKENS

        st.markdown("### 📊 Token Usage Over Time")
        st.line_chart(df.set_index("date")["total_tokens"])

        st.markdown("### 💰 Estimated Cost Over Time")
        st.line_chart(df.set_index("date")["cost"])

        st.markdown("### 📄 Raw Token Logs")
        st.dataframe(df[["date", "prompt_tokens", "completion_tokens", "total_tokens", "cost"]])

        st.markdown("### 📆 Monthly Summary")
        current_year = datetime.now().year
        monthly_data = []
        for m in range(1, 13):
            usage = get_monthly_token_usage(selected_email, current_year, m)
            monthly_data.append({
                "Month": f"{current_year}-{m:02d}",
                "Prompt Tokens": usage["total_prompt_tokens"],
                "Completion Tokens": usage["total_completion_tokens"],
                "Total Tokens": usage["total_tokens"],
                "Estimated Cost": round((usage["total_tokens"] / 1000) * COST_PER_1K_TOKENS, 6)
            })

        st.dataframe(pd.DataFrame(monthly_data))

        st.markdown("### 💬 Chat Sessions")
        chats = get_chats_by_user(selected_email)
        for chat in chats:
            st.markdown(f"#### 🧠 {chat['title']}")
            for msg in chat.get("messages", []):
                role = msg["role"].capitalize()
                content = msg["content"]
                st.markdown(f"**{role}:** {content}")
            st.markdown("---")

    else:
        st.info("No usage data found for this user.")

# Global stats
if st.checkbox("Show Global Analytics"):
    all_usage = get_all_token_usage()
    if all_usage:
        df_global = pd.DataFrame(all_usage)
        df_global["date"] = pd.to_datetime(df_global["timestamp"]).dt.strftime("%Y-%m-%d")
        st.markdown("### 🌐 Daily Total Token Usage")
        st.line_chart(df_global.groupby("date")["total_tokens"].sum())

        st.markdown("### 📊 Total Token Usage Per User")
        user_usage = {}
        for record in all_usage:
            email = record["email"]
            user_usage[email] = user_usage.get(email, 0) + record["total_tokens"]

        usage_df = pd.DataFrame(list(user_usage.items()), columns=["User", "Total Tokens"])
        st.bar_chart(usage_df.set_index("User")["Total Tokens"])

    else:
        st.info("No global token data found.")

# Footer from knowledge base
st.markdown("---")
st.markdown("""
**Your-Site.Com / Fluidsoft, Inc.**  
P.O. Box 535 | Funkstown, MD 21734  
[📧 info@your-site.com](mailto:info@your-site.com)  
Copyright © 1996–2025 Your-Site.Com  
[Privacy Statement](https://your-site.com/privacy )
""")