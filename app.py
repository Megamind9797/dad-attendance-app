import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import gspread
import requests
from google.oauth2.service_account import Credentials
from io import BytesIO

# ================= CONFIG =================
ADMIN_PASS = "tushar07_"
PAPA_PASS = "lalitnemade"

SHEET_NAME = "DadBusinessAttendance"
ATTENDANCE_SHEET = "Attendance"
WORKERS_SHEET = "Workers"
LOGIN_SHEET = "Login_Log"

india = pytz.timezone("Asia/Kolkata")

# ================= TRANSLITERATION =================
def eng_to_marathi(text):
    try:
        url = "https://inputtools.google.com/request"
        params = {"text": text, "itc": "mr-t-i0-und"}
        r = requests.get(url, params=params, timeout=3)
        data = r.json()
        if data[0] == "SUCCESS":
            return data[1][0][1][0]
        return text
    except:
        return text

# ================= GOOGLE AUTH =================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["google"], scopes=scope
)

client = gspread.authorize(creds)

try:
    book = client.open(SHEET_NAME)
except:
    st.error("❌ Sheet not shared with service account")
    st.stop()

def get_or_create(sheet, headers):
    try:
        ws = book.worksheet(sheet)
    except:
        ws = book.add_worksheet(sheet, rows="5000", cols="10")
        ws.append_row(headers)
    return ws

attendance_ws = get_or_create(
    ATTENDANCE_SHEET,
    ["Date","Time","Name","Status","Banana","Deleted"]
)

workers_ws = get_or_create(WORKERS_SHEET, ["Name"])
login_ws = get_or_create(LOGIN_SHEET, ["Date","Time","User"])

# ================= SESSION =================
if "role" not in st.session_state:
    st.session_state.role = None

if "attendance_today" not in st.session_state:
    st.session_state.attendance_today = {}

# ================= LOGIN =================
if st.session_state.role is None:

    st.title("🔐 Login")
    password = st.text_input("Enter password", type="password")

    if st.button("Login"):
        now = datetime.now(india)
        d = now.strftime("%d-%m-%Y")
        t = now.strftime("%I:%M %p")

        if password == ADMIN_PASS:
            st.session_state.role = "admin"
            login_ws.append_row([d, t, "admin"])
            st.rerun()

        elif password == PAPA_PASS:
            st.session_state.role = "papa"
            login_ws.append_row([d, t, "papa"])
            st.rerun()
        else:
            st.error("Wrong password")

# ================= DASHBOARD =================
else:

    now = datetime.now(india)
    today = now.strftime("%d-%m-%Y")
    time_now = now.strftime("%I:%M %p")

    st.sidebar.success(f"Logged in as: {st.session_state.role}")

    if st.sidebar.button("Logout"):
        st.session_state.role = None
        st.rerun()

    # ================= LOAD WORKERS =================
    df_workers = pd.DataFrame(workers_ws.get_all_records())
    workers = df_workers["Name"].tolist() if not df_workers.empty else []

    # ================= ATTENDANCE UI =================
    st.markdown("### 📝 Today Attendance")

    search = st.text_input("Search name")

    if search:
        mar = eng_to_marathi(search)
        workers = [n for n in workers if mar in n]

    for name in workers:

        if name not in st.session_state.attendance_today:
            st.session_state.attendance_today[name] = {
                "status": "Absent",
                "banana": 0
            }

        col1, col2, col3, col4 = st.columns([4,2,2,2])

        with col1:
            st.write(name)

        with col2:
            present = st.checkbox(
                "",
                key=f"p_{name}",
                value=st.session_state.attendance_today[name]["status"] == "Present"
            )

        status = "Present" if present else "Absent"
        st.session_state.attendance_today[name]["status"] = status

        with col3:
            st.markdown("🟢 Present" if present else "🔴 Absent")

        with col4:
            banana = st.number_input(
                "",
                min_value=0,
                step=1,
                key=f"b_{name}",
                value=st.session_state.attendance_today[name]["banana"]
            )

        st.session_state.attendance_today[name]["banana"] = banana

    # ================= SAVE BUTTON =================
    st.divider()

    if st.button("💾 Save Attendance"):
        for name, data in st.session_state.attendance_today.items():
            attendance_ws.append_row([
                today,
                time_now,
                name,
                data["status"],
                data["banana"],
                "NO"
            ])
        st.success("✅ Attendance saved successfully")
