import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import gspread
from google.oauth2.service_account import Credentials
from io import BytesIO
import requests

def eng_to_marathi(text):
    try:
        url = "https://inputtools.google.com/request"
        params = {
            "text": text,
            "itc": "mr-t-i0-und"
        }
        res = requests.get(url, params=params, timeout=3)
        data = res.json()

        if data[0] == "SUCCESS":
            return data[1][0][1][0]
        return text
    except:
        return text


# ================= PASSWORDS =================
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

india = pytz.timezone("Asia/Kolkata")

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
        ws = book.add_worksheet(title=title, rows="3000", cols="10")
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

    # ================= TODAY ENTRY =================
    st.markdown("### 📝 Today Attendance")

    existing = pd.DataFrame(attendance_ws.get_all_records())
    today_names = []

    if not existing.empty:

        # 🔒 safety for old data
        if "Deleted" not in existing.columns:
            existing["Deleted"] = "NO"

        today_names = existing[
            (existing["Date"] == today) &
            (existing["Deleted"] == "NO")
        ]["Name"].tolist()

    data = []

    for name in NAMES:
        c1, c2, c3 = st.columns([3,2,2])

        with c1:
            st.write(name)

        with c2:
            present = st.checkbox("Present", key=name)

        with c3:
            banana = st.number_input("Banana", 0, step=1, key=name+"_b")

        status = "Present" if present else "Absent"
        data.append([today, time_now, name, status, banana, "NO"])

    if st.button("💾 Save Today Data"):

        for row in data:
            if row[2] not in today_names:
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

        # 🔍 name search
        search = st.text_input("Search name")
        if search:
            df = df[df["Name"].str.contains(search, case=False)]

        # 📅 date filter
        date_filter = st.selectbox(
            "Select Date",
            ["All"] + sorted(df["Date"].unique(), reverse=True)
        )

        if date_filter != "All":
            df = df[df["Date"] == date_filter]
            st.info(f"🍌 Total Banana: {df['Banana'].sum()}")

        # papa vs admin view
        if st.session_state.role == "papa":
            df_show = df[["Date", "Name", "Status", "Banana"]]
        else:
            df_show = df[["Date", "Time", "Name", "Status", "Banana"]]

        def color(val):
            if val == "Present":
                return "background-color:#90EE90"
            if val == "Absent":
                return "background-color:#FF9999"
            return ""

        st.dataframe(
            df_show.style.applymap(color, subset=["Status"]),
            use_container_width=True
        )

        output = BytesIO()
        df_show.to_excel(output, index=False)

        st.download_button(
            "⬇ Download Excel",
            data=output.getvalue(),
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
                    attendance_ws.update_cell(i + 1, 6, "YES")

            st.success("Record deleted safely ✅")
