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
        ws = book.add_worksheet(title=sheet, rows="5000", cols="10")
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

if "today_data" not in st.session_state:
    st.session_state.today_data = {}

# =====================================================
# 🔐 LOGIN PAGE (ONLY THIS SHOWS FIRST)
# =====================================================
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

# =====================================================
# 🏠 DASHBOARD (AFTER LOGIN)
# =====================================================
else:

    st.title("📋 जय भोले फ्रूट्स")

    now = datetime.now(india)
    today = now.strftime("%d-%m-%Y")
    time_now = now.strftime("%I:%M %p")

    st.sidebar.success(f"Logged in as: {st.session_state.role}")

    if st.sidebar.button("Logout"):
        st.session_state.role = None
        st.rerun()

    # ---------------- TODAY TOTAL ----------------
    total_banana = sum(
        v.get("banana", 0) for v in st.session_state.today_data.values()
    )

    st.sidebar.markdown("## 🍌 Today Total")
    st.sidebar.success(str(total_banana))

    # ---------------- ADMIN RESET ----------------
    if st.session_state.role == "admin":
        if st.sidebar.button("🔄 Refresh Today"):
            st.session_state.today_data = {}
            st.success("✅ Today reset")
            st.rerun()

    # ---------------- DOWNLOAD ----------------
    df_att = pd.DataFrame(attendance_ws.get_all_records())
    if not df_att.empty:
        date_sel = st.sidebar.selectbox(
            "Download date",
            sorted(df_att["Date"].unique(), reverse=True)
        )

        excel = BytesIO()
        df_att[df_att["Date"] == date_sel].to_excel(excel, index=False)

        st.sidebar.download_button(
            "⬇ Download Excel",
            data=excel.getvalue(),
            file_name=f"{date_sel}.xlsx"
        )

    # ---------------- ADMIN LOGS ----------------
    if st.session_state.role == "admin":
        st.sidebar.markdown("## 🔐 Login Logs")
        logs_df = pd.DataFrame(login_ws.get_all_records())
        if not logs_df.empty:
            st.sidebar.dataframe(logs_df.tail(10), use_container_width=True)

    # ---------------- ADD WORKER ----------------
    st.subheader("➕ Add Customer")

    new_worker = st.text_input("Name (English or Marathi)")

    if st.button("Add Worker"):
        mar = eng_to_marathi(new_worker.strip())
        if mar not in workers_ws.get_all_values():
            workers_ws.append_row([mar])
            st.success(f"Added: {mar}")
            st.rerun()
        else:
            st.warning("Already exists")

    # ---------------- ATTENDANCE ----------------
    st.divider()
    st.subheader("📝 Today Attendance")

    workers_df = pd.DataFrame(workers_ws.get_all_records())
    workers = workers_df["Name"].tolist() if not workers_df.empty else []

    search = st.text_input("Search name")

    if search:
        mar = eng_to_marathi(search)
        workers = [n for n in workers if mar in n]

    st.markdown("""
<style>
.box {
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 10px;
    margin-bottom: 10px;
}
.head {
    font-weight: bold;
    text-align: center;
}
.center {
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

for name in workers:

    if name not in st.session_state.today_data:
        st.session_state.today_data[name] = {
            "status": "Absent",
            "banana": 0
        }

    st.markdown("<div class='box'>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns([4,2,2,2])

    # -------- NAME --------
    with col1:
        st.markdown("<div class='head'>Name</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='center'>{name}</div>", unsafe_allow_html=True)

    # -------- TICK --------
    with col2:
        st.markdown("<div class='head'>Tick</div>", unsafe_allow_html=True)
        present = st.checkbox(
            "",
            key=f"p_{name}",
            value=st.session_state.today_data[name]["status"] == "Present"
        )

    status = "Present" if present else "Absent"
    st.session_state.today_data[name]["status"] = status

    # -------- STATUS --------
    with col3:
        st.markdown("<div class='head'>Status</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='center'>{'🟢 Present' if present else '🔴 Absent'}</div>",
            unsafe_allow_html=True
        )

    # -------- BANANA --------
    with col4:
        st.markdown("<div class='head'>🍌 Quantity</div>", unsafe_allow_html=True)
        banana = st.number_input(
            "",
            min_value=0,
            step=1,
            key=f"b_{name}",
            value=st.session_state.today_data[name]["banana"]
        )

    st.session_state.today_data[name]["banana"] = banana

    st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- SAVE ----------------
    st.divider()

    if st.button("💾 Save Attendance"):
        for name, data in st.session_state.today_data.items():
            attendance_ws.append_row([
                today,
                time_now,
                name,
                data["status"],
                data["banana"],
                "NO"
            ])
        st.success("✅ Attendance saved")
