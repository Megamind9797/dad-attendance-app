import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import gspread
import requests
from google.oauth2.service_account import Credentials
from io import BytesIO

# ================= PASSWORDS =================
ADMIN_PASS = "tushar07_"
PAPA_PASS = "lalitnemade"


# ================= SETTINGS =================
SHEET_NAME = "DadBusinessAttendance"
ATTENDANCE_SHEET = "Attendance"
LOGIN_SHEET = "Login_Log"

# 🔤 Master Marathi names
NAMES = [
    "रामदास पाटील",
    "रामेश्वर पाटील",
    "रमेश पवार",
    "संजय वाघुळे",
    "उषा भालेराव",
    "नावदेव आई"
]

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
book = client.open(SHEET_NAME)

def get_or_create(title, headers):
    try:
        ws = book.worksheet(title)
    except:
        ws = book.add_worksheet(title=title, rows="4000", cols="10")
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

# ================= SESSION =================
if "role" not in st.session_state:
    st.session_state.role = None

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

    st.sidebar.success(f"Logged in as: {st.session_state.role}")

    if st.sidebar.button("Logout"):
        st.session_state.role = None
        st.rerun()

    now = datetime.now(india)
    today = now.strftime("%d-%m-%Y")
    time_now = now.strftime("%I:%M %p")

    st.title("🍌 Daily Attendance System")
    st.subheader(f"Date: {today}")

    # ================= TODAY ATTENDANCE =================
    st.markdown("### 📝 Today Attendance")

    search_input = st.text_input(
        "Search name (English or Marathi)",
        placeholder="Example: ram, patil"
    )

    filtered_names = NAMES

    if search_input:
        mar = eng_to_marathi(search_input)
        filtered_names = [n for n in NAMES if mar in n]

    existing = pd.DataFrame(attendance_ws.get_all_records())

    if not existing.empty and "Deleted" not in existing.columns:
        existing["Deleted"] = "NO"

    today_done = []
    if not existing.empty:
        today_done = existing[
            (existing["Date"] == today) &
            (existing["Deleted"] == "NO")
        ]["Name"].tolist()

    data = []

    for name in filtered_names:
        c1, c2, c3 = st.columns([3,2,2])

        with c1:
            st.write(name)

        with c2:
            present = st.checkbox("Present", key=name)

        with c3:
            banana = st.number_input("Banana", 0, step=1, key=name+"_b")

        status = "Present" if present else "Absent"

        if name not in today_done:
            data.append([today, time_now, name, status, banana, "NO"])

    if st.button("💾 Save Today Data"):
        for row in data:
            attendance_ws.append_row(row)
        st.success("✅ Saved (duplicate auto blocked)")

    # ================= HISTORY =================
    st.divider()
    st.subheader("📊 Attendance History")

    df = pd.DataFrame(attendance_ws.get_all_records())

    if not df.empty:

        if "Deleted" not in df.columns:
            df["Deleted"] = "NO"

        df = df[df["Deleted"] == "NO"]

        search = st.text_input("Search history name")

        if search:
            mar = eng_to_marathi(search)
            df = df[df["Name"].str.contains(mar, case=False)]

        date_filter = st.selectbox(
            "Select Date",
            ["All"] + sorted(df["Date"].unique(), reverse=True)
        )

        if date_filter != "All":
            df = df[df["Date"] == date_filter]
            st.info(f"🍌 Total Banana: {df['Banana'].sum()}")

        if st.session_state.role == "papa":
            df_show = df[["Date", "Name", "Status", "Banana"]]
        else:
            df_show = df[["Date", "Time", "Name", "Status", "Banana"]]

        def color(v):
            if v == "Present":
                return "background-color:#90EE90"
            if v == "Absent":
                return "background-color:#FF9999"
            return ""

        st.dataframe(
            df_show.style.applymap(color, subset=["Status"]),
            use_container_width=True
        )

        out = BytesIO()
        df_show.to_excel(out, index=False)

        st.download_button(
            "⬇ Download Excel",
            data=out.getvalue(),
            file_name="attendance.xlsx"
        )

    # ================= ADMIN DELETE =================
    if st.session_state.role == "admin" and not df.empty:

        st.divider()
        st.subheader("🗑️ Admin Delete")

        del_name = st.selectbox("Select Name", df["Name"].unique())
        del_date = st.selectbox("Select Date", df["Date"].unique())

        if st.button("Delete selected record"):
            all_rows = attendance_ws.get_all_values()

            for i in range(1, len(all_rows)):
                if all_rows[i][0] == del_date and all_rows[i][2] == del_name:
                    attendance_ws.update_cell(i+1, 6, "YES")

            st.success("Record deleted safely ✅")
