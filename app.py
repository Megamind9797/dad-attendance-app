import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import gspread
import requests
from google.oauth2.service_account import Credentials
from io import BytesIO

# =====================================================
# BASIC CONFIG
# =====================================================
ADMIN_PASS = "tushar07_"
PAPA_PASS = "lalitnemade"

SHEET_NAME = "DadBusinessAttendance"
ATTENDANCE_SHEET = "Attendance"
WORKERS_SHEET = "Workers"
LOGIN_SHEET = "Login_Log"

india = pytz.timezone("Asia/Kolkata")

# =====================================================
# TRANSLITERATION
# =====================================================
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

# =====================================================
# GOOGLE AUTH
# =====================================================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["google"], scopes=scope
)

client = gspread.authorize(creds)
book = client.open(SHEET_NAME)

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

# =====================================================
# HELPERS
# =====================================================
def get_workers():
    df = pd.DataFrame(workers_ws.get_all_records())
    if df.empty:
        return []
    return sorted(df["Name"].dropna().tolist())

def upsert_attendance(date, time, name, status, banana):
    rows = attendance_ws.get_all_values()
    for i in range(1, len(rows)):
        if rows[i][0] == date and rows[i][2] == name:
            attendance_ws.update(
                f"A{i+1}:F{i+1}",
                [[date, time, name, status, banana, "NO"]]
            )
            return
    attendance_ws.append_row([date, time, name, status, banana, "NO"])

# =====================================================
# SESSION
# =====================================================
if "role" not in st.session_state:
    st.session_state.role = None

# =====================================================
# LOGIN PAGE
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
# DASHBOARD
# =====================================================
else:

    now = datetime.now(india)
    today = now.strftime("%d-%m-%Y")
    time_now = now.strftime("%I:%M %p")

    st.sidebar.success(f"Logged in as: {st.session_state.role}")

    if st.sidebar.button("Logout"):
        st.session_state.role = None
        st.rerun()

    # =================================================
    # SIDEBAR DOWNLOAD (PAPA + ADMIN)
    # =================================================
    st.sidebar.markdown("## 📥 Download Attendance")

    df_all = pd.DataFrame(attendance_ws.get_all_records())

    if not df_all.empty:
        date_sel = st.sidebar.selectbox(
            "Select date",
            sorted(df_all["Date"].unique(), reverse=True)
        )

        down_df = df_all[df_all["Date"] == date_sel]

        excel = BytesIO()
        down_df.to_excel(excel, index=False)

        st.sidebar.download_button(
            "⬇ Download Excel",
            data=excel.getvalue(),
            file_name=f"{date_sel}_attendance.xlsx"
        )

    # =================================================
    # ADMIN PANEL (RIGHT SIDE)
    # =================================================
    if st.session_state.role == "admin":

        st.sidebar.markdown("## 👑 Admin Panel")

        # Login logs
        log_df = pd.DataFrame(login_ws.get_all_records())
        if not log_df.empty:
            st.sidebar.markdown("### 🔐 Login History")
            st.sidebar.dataframe(log_df.tail(10), use_container_width=True)

    # =================================================
    # ADD WORKER (PAPA + ADMIN)
    # =================================================
    st.markdown("### ➕ Add Worker")

    new_worker = st.text_input("Type name (English or Marathi)")

    if st.button("Add Worker"):
        mar = eng_to_marathi(new_worker.strip())

        existing = workers_ws.get_all_values()
        names = [r[0] for r in existing[1:]]

        if mar in names:
            st.warning("Worker already exists")
        else:
            workers_ws.append_row([mar])
            st.success(f"✅ {mar} added")
            st.rerun()

    # =================================================
    # ATTENDANCE
    # =================================================
    st.divider()
    st.markdown("### 📝 Today Attendance")

    workers = get_workers()

    if not workers:
        st.info("No workers found.")
    else:

        search = st.text_input("Search name (English / Marathi)")

        filtered = workers
        if search:
            mar = eng_to_marathi(search)
            filtered = [n for n in workers if mar in n]

        for name in filtered:
            c1, c2, c3 = st.columns([3,2,2])

            with c1:
                st.write(name)

            with c2:
                st.checkbox(
                    "Present",
                    key=f"p_{name}",
                    on_change=upsert_attendance,
                    args=(
                        today,
                        time_now,
                        name,
                        "Present" if st.session_state.get(f"p_{name}") else "Absent",
                        st.session_state.get(f"b_{name}", 0)
                    )
                )

            with c3:
                st.number_input(
                    "Banana",
                    min_value=0,
                    step=1,
                    key=f"b_{name}",
                    on_change=upsert_attendance,
                    args=(
                        today,
                        time_now,
                        name,
                        "Present" if st.session_state.get(f"p_{name}") else "Absent",
                        st.session_state.get(f"b_{name}", 0)
                    )
                )
