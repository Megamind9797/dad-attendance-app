import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from io import BytesIO

# ================= LOGIN PASSWORDS =================
ADMIN_PASS = "tushar07_"
PAPA_PASS = "lalitnemade"

# ================= SETTINGS =================
SHEET_NAME = "DadBusinessAttendance"
WORKSHEET = "Data"

NAMES = [
    "पंडितबाबा", "हिरामणदेव", "विमलबाई", "शाहिद",
    "संजय वाघुळे", "उषा भालेराव", "नावदेव आई"
]

# ================= GOOGLE AUTH =================
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

# ================= SESSION =================
if "role" not in st.session_state:
    st.session_state.role = None

# ================= LOGIN =================
if st.session_state.role is None:

    st.title("🔐 Login")
    password = st.text_input("Enter password", type="password")

    if st.button("Login"):
        now = datetime.now()
        d = now.strftime("%d-%m-%Y")
        t = now.strftime("%H:%M:%S")

        if password == ADMIN_PASS:
            st.session_state.role = "admin"
            sheet.append_row([d, t, "admin", "LOGIN", 0])
            st.rerun()

        elif password == PAPA_PASS:
            st.session_state.role = "papa"
            sheet.append_row([d, t, "papa", "LOGIN", 0])
            st.rerun()

        else:
            st.error("Wrong password")

# ================= DASHBOARD =================
else:

    st.sidebar.success(f"Logged in as: {st.session_state.role}")

    if st.sidebar.button("Logout"):
        st.session_state.role = None
        st.rerun()

    today = datetime.now().strftime("%d-%m-%Y")
    time_now = datetime.now().strftime("%H:%M:%S")

    st.title("🍌 Daily Attendance System")
    st.subheader(f"Date: {today}")

    # ================= ATTENDANCE =================
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
        st.success("✅ Data saved")

    # ================= HISTORY =================
    st.divider()
    st.subheader("📅 History")

    records = sheet.get_all_records()
    df = pd.DataFrame(records)

    if not df.empty:

        attendance_df = df[df["Status"].isin(["Present", "Absent"])]

        if st.session_state.role == "papa":
            attendance_df = attendance_df[["Date", "Name", "Status", "Banana"]]
        else:
            attendance_df = attendance_df[["Date", "Time", "Name", "Status", "Banana"]]

        def color_status(val):
            if val == "Present":
                return "background-color: #90EE90"
            elif val == "Absent":
                return "background-color: #FF9999"
            return ""

        styled = attendance_df.style.applymap(color_status, subset=["Status"])

        st.dataframe(styled, use_container_width=True)

        output = BytesIO()
        attendance_df.to_excel(output, index=False)

        st.download_button(
            "⬇ Download Excel",
            data=output.getvalue(),
            file_name="attendance.xlsx"
        )

    # ================= ADMIN PANEL =================
    if st.session_state.role == "admin" and not df.empty:
        st.divider()
        st.subheader("👑 Admin Activity Log")

        log_df = df[df["Status"] == "LOGIN"]
        st.dataframe(log_df, use_container_width=True)
