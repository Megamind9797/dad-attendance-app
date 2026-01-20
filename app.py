import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import gspread
import requests
from google.oauth2.service_account import Credentials
from io import BytesIO

# ==================================================
# PASSWORDS
# ==================================================
ADMIN_PASS = "tushar07_"
PAPA_PASS = "lalitnemade"

# ==================================================
# SETTINGS
# ==================================================
SHEET_NAME = "DadBusinessAttendance"
ATTENDANCE_SHEET = "Attendance"
LOGIN_SHEET = "Login_Log"
WORKERS_SHEET = "Workers"

india = pytz.timezone("Asia/Kolkata")

# ==================================================
# OLD NAMES (IMPORT ONLY ONCE)
# ==================================================
OLD_NAMES = [
    "पंडितबाबा","हिरामणदेव","विमलबाई","राधे","संजय वांझरे","अजय महाजन",
    "नांदेड आई","राधाबाई","राधेश्याम","पप्पू भानू","नवीन","भाऊराव",
    "समर्थ","ईश्वरराव","गायत्री पखाले","काडोदे","निखिल डोंगरे","गिरी",
    "सुनील सावळे","सुनील घाडगे","मोरे","कोकणे","मोतीलाल मढव",
    "राजू पिस्तको","अक्कल","मनोहर","बालासाहेब","अर्जुन",
    "विष्णू पाटील","सुनील लोणारे","केदारनाथ","माळे साई",
    "कृष्णा केशव","सोमनाथ","गोपाल सोनार","कुमुद आराख","केशवकर",
    "सुनील वाणी","मोहन","अरुण","चंदन","दादा","विजयाबाई","मला",
    "गोपाल बोंगावी","संतोष पवार","केलासन पवार","अर्पिता जंगरे",
    "फुले","पल्लवी ताई","राजू कोंढे","आशिष","ईश्वरनाथ शिंदे",
    "हिराबाई","मुकेश जोशी","साईसिद्धी","समर्थराव","रामदास पाटील",
    "पप्पू शिंदे","के. के. वाघ","खलील शेख","अशोक","सुनील",
    "सुषमा गुप्ता",
    "आरिफ बागवान","चिंताबाई","पप्पू डिंगराव","सागर काळे","गोरख केदार",
    "सरपंच","संदीप कोरे","कमलबाई","डोंगरसिंग","बालूबा",
    "भिंगाजी पप्पा","महादेव","अनिता देवकर","हिराबाई नाथराव",
    "लक्ष्मीनारायण","गायकवाड","रेश्मा माई","आयुब खानबी","जिलेटा",
    "अजय कपलेश्वर","शिला जाधव","आशा महाजन","सागर त्रिवेदी",
    "कुशारे","महाले","उज्वला गवळे","हनुमंत","गोविंद मोरे",
    "शंकर लोखंडे","योगेश काकडी","गणेश सावळपूर","विठ्ठलाधवारे",
    "मेघा ताटी","ज्ञानेश्वर","मधु येवाले","अनिक तायडे","सविता काशिद",
    "लिलाबाई","शंकराऊ","बकुलाबाई माने","विजाबाई","सुनिलराम कदम",
    "सुदाम यादव","राकेश कांबळे","विनायक कोरे","यशवंत राठोड",
    "गंगाधर माळी","पालवाडी","काळे","वालाजी लांडे","अशोक कुंभार",
    "श्यामर गामा","संजय पाटील","गितुनी तांबोळी","गोपाल माने",
    "राजू शेटे","शंकरदास","वसंत चव्हाण","योगेश पवार",
    "जलेलकर","अशोक गवळा","देवेंद्र"
]

# ==================================================
# TRANSLITERATION
# ==================================================
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

# ==================================================
# GOOGLE AUTH
# ==================================================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["google"], scopes=scope
)

client = gspread.authorize(creds)
book = client.open(SHEET_NAME)

def get_or_create(title, headers):
    try:
        ws = book.worksheet(title)
    except:
        ws = book.add_worksheet(title=title, rows="6000", cols="10")
        ws.append_row(headers)
    return ws

attendance_ws = get_or_create(
    ATTENDANCE_SHEET,
    ["Date", "Time", "Name", "Status", "Banana", "Deleted"]
)

login_ws = get_or_create(
    LOGIN_SHEET,
    ["Date", "Time", "User"]
)

workers_ws = get_or_create(
    WORKERS_SHEET,
    ["Name"]
)

# ==================================================
# HELPERS
# ==================================================
def get_workers():
    df = pd.DataFrame(workers_ws.get_all_records())
    if df.empty:
        return []
    return df["Name"].dropna().tolist()

def auto_import_workers(name_list):
    existing = workers_ws.get_all_values()
    existing_names = [r[0] for r in existing[1:]]
    count = 0

    for n in name_list:
        if n not in existing_names:
            workers_ws.append_row([n])
            count += 1
    return count

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

# ==================================================
# SESSION
# ==================================================
if "role" not in st.session_state:
    st.session_state.role = None

# ==================================================
# LOGIN
# ==================================================
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

# ==================================================
# DASHBOARD
# ==================================================
else:

    st.sidebar.success(f"Logged in as: {st.session_state.role}")

    if st.sidebar.button("Logout"):
        st.session_state.role = None
        st.rerun()

    now = datetime.now(india)
    today = now.strftime("%d-%m-%Y")
    time_now = now.strftime("%I:%M %p")

    workers = get_workers()

    # ========= AUTO IMPORT (ADMIN ONLY) =========
    if st.session_state.role == "admin":

        st.warning("⚠️ One-time setup: Import old worker names")

        if st.button("🚀 Import Old Names"):
            added = auto_import_workers(OLD_NAMES)
            st.success(f"✅ {added} workers imported")
            st.rerun()

    # ========= SIDEBAR DOWNLOAD =========
    st.sidebar.markdown("## 📥 Download Data")

    all_df = pd.DataFrame(attendance_ws.get_all_records())

    if not all_df.empty:
        date_dl = st.sidebar.selectbox(
            "Select Date",
            sorted(all_df["Date"].unique(), reverse=True)
        )

        dl_df = all_df[all_df["Date"] == date_dl]

        excel = BytesIO()
        dl_df.to_excel(excel, index=False)

        st.sidebar.download_button(
            "⬇ Download Excel",
            data=excel.getvalue(),
            file_name=f"{date_dl}_attendance.xlsx"
        )

    # ========= ADD WORKER =========
    st.markdown("### ➕ Add New Worker")

    new_worker = st.text_input("Enter worker name (English or Marathi)")

    if st.button("Add Worker"):
        mar_name = eng_to_marathi(new_worker.strip())
        existing = workers_ws.get_all_values()
        names = [r[0] for r in existing[1:]]

        if mar_name in names:
            st.warning("Worker already exists")
        else:
            workers_ws.append_row([mar_name])
            st.success(f"✅ {mar_name} added")
            st.rerun()

    # ========= ATTENDANCE =========
    st.divider()
    st.markdown("### 📝 Today Attendance")

    search = st.text_input("Search name (English or Marathi)")

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
