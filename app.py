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
ATTENDANCE_SHEET = "Attendance"
LOGIN_SHEET = "Login_Log"

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
book = client.open(SHEET_NAME)

# ================= AUTO CREATE SHEETS =================
def get_or_create(title, headers):
    try:
        ws = book.worksheet(title)
    except:
        ws = book.add_worksheet(title=title, rows="1000", cols="10")
        ws.append_row(headers)
    return ws

attendance_ws = get_or_create(
    ATTENDANCE_SHEET,
    ["Date", "Time", "Name", "Status", "Banana"]
)

login_ws = get_or_create(
    LOGIN_SHEET,
    ["Date", "Time", "User"]
)

# ================= SESSION =================
if "role" not in st.session_state:
    st.session_state.role = None

# ================= LOGIN =================
if st.session_state.role is None:

    st.title("🔐 Login")
    password = st.text_input("Enter password", type="password")

    if st.button("Login"):

        now = datetime.now()
        date_str = now.strftime("%d-%m-%Y")
        time_str = now.strftime("%I:%M %p")

        if password == ADMIN_PASS:
            st.session_state.role = "admin"
            login_ws.append_row([date_str, time_str, "admin"])
            st.rerun()

        elif password == PAPA_PASS:
            st.session_state.role = "papa"
            login_ws.append_row([date_str, time_str, "papa"])
            st.rerun()

        else:
            st.error("Wrong password")

# ================= DASHBOARD =================
else:

    st.sidebar.success(f"Logged in as: {st.session_state.role}")

    if st.sidebar.button("Logout"):
        st.session_state.role = None
        st.rerun()

    now = datetime.now()
    today = now.strftime("%d-%m-%Y")
    time_now = now.strftime("%I:%M %p")

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
            attendance_ws.append_row(row)
        st.success("✅ Attendance saved successfully")

    # ================= HISTORY =================
    st.divider()
    st.subheader("📅 Attendance History")

    df = pd.DataFrame(attendance_ws.get_all_records())

    if not df.empty:

        if st.session_state.role == "papa":
            df_show = df[["Date", "Name", "Status", "Banana"]]
        else:
            df_show = df[["Date", "Time", "Name", "Status", "Banana"]]

        def color_status(val):
            if val == "Present":
                return "background-color: #90EE90"
            elif val == "Absent":
                return "background-color: #FF9999"
            return ""

        styled = df_show.style.applymap(color_status, subset=["Status"])
        st.dataframe(styled, use_container_width=True)

        output = BytesIO()
        df_show.to_excel(output, index=False)

        st.download_button(
            "⬇ Download Excel",
            data=output.getvalue(),
            file_name="attendance.xlsx"
        )

    # ================= ADMIN LOGIN LOG =================
    if st.session_state.role == "admin":
        st.divider()
        st.subheader("👑 Login Activity")

        log_df = pd.DataFrame(login_ws.get_all_records())
        st.dataframe(log_df, use_container_width=True)
