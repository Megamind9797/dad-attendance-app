import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from io import BytesIO

# ==================================================
# LOGIN PASSWORDS (TEMP – GUARANTEED WORKING)
# ==================================================
ADMIN_PASS = "tushar07_"
PAPA_PASS = "lalitnemade"

# ==================================================
# SETTINGS
# ==================================================
SHEET_NAME = "DadBusinessAttendance"
WORKSHEET = "Data"

NAMES = [
    "पंडितबाबा", "हिरामणदेव", "विमलबाई", "शाहिद",
    "संजय वाघुळे", "उषा भालेराव", "नावदेव आई"
]

# ==================================================
# GOOGLE AUTH
# ==================================================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["google"],
    scopes=scope
)

client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).worksheet(WORKSHEET)

# ==================================================
# SESSION
# ==================================================
if "role" not in st.session_state:
    st.session_state.role = None

# ==================================================
# LOGIN PAGE
# ==================================================
if st.session_state.role is None:

    st.title("🔐 Login")

    password = st.text_input("Enter password", type="password")

    if st.button("Login"):

        if password == ADMIN_PASS:
            st.session_state.role = "admin"
            st.experimental_rerun()

        elif password == PAPA_PASS:
            st.session_state.role = "papa"
            st.experimental_rerun()

        else:
            st.error("❌ Wrong password")

# ==================================================
# DASHBOARD
# ==================================================
else:

    st.sidebar.success(f"Logged in as: {st.session_state.role}")

    if st.sidebar.button("Logout"):
        st.session_state.role = None
        st.experimental_rerun()

    today = datetime.now().strftime("%d-%m-%Y")
    time_now = datetime.now().strftime("%H:%M:%S")

    st.title("🍌 Daily Attendance System")
    st.subheader(f"Date: {today}")

    # ================= Attendance =================
    st.markdown("### 📝 Today Attendance")

    data = []

    for name in NAMES:
        c1, c2, c3 = st.columns([3, 2, 2])

        with c1:
            st.write(name)

        with c2:
            present = st.checkbox("Present", key=name)

        with c3:
            banana = st.number_input("Banana", 0, step=1, key=name + "_b")

        status = "Present" if present else "Absent"
        data.append([today, time_now, name, status, banana])

    if st.button("💾 Save Today Data"):
        for row in data:
            sheet.append_row(row)
        st.success("✅ Data saved successfully")

    # ================= History =================
    st.divider()
    st.subheader("📅 History")

    records = sheet.get_all_records()
    df = pd.DataFrame(records)

    if not df.empty:
        dates = sorted(df["Date"].unique(), reverse=True)
        selected_date = st.selectbox("Select Date", dates)

        view_df = df[df["Date"] == selected_date]
        st.dataframe(view_df, use_container_width=True)

        output = BytesIO()
        view_df.to_excel(output, index=False)

        st.download_button(
            "⬇ Download Excel",
            data=output.getvalue(),
            file_name=f"{selected_date}.xlsx"
        )

    # ================= ADMIN ONLY =================
    if st.session_state.role == "admin" and not df.empty:
        st.divider()
        st.subheader("👑 Admin Panel")

        df["Month"] = pd.to_datetime(df["Date"], dayfirst=True).dt.strftime("%B %Y")

        month = st.selectbox("Select Month", df["Month"].unique())

        mdf = df[df["Month"] == month]

        summary = mdf.groupby("Name").agg(
            Total_Days=("Status", "count"),
            Present_Days=("Status", lambda x: (x == "Present").sum()),
            Total_Banana=("Banana", "sum")
        )

        st.dataframe(summary, use_container_width=True)

        out = BytesIO()
        summary.to_excel(out)

        st.download_button(
            "⬇ Download Monthly Report",
            data=out.getvalue(),
            file_name=f"{month}_report.xlsx"
        )
