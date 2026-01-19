import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from io import BytesIO

# ---------------- SETTINGS ----------------
SHEET_NAME = "DadBusinessAttendance"
WORKSHEET = "Data"

NAMES = [
    "पंडितबाबा", "हिरामणदेव", "विमलबाई", "शाहिद",
    "संजय वाघुळे", "उषा भालेराव", "नावदेव आई"
]

# ---------------- GOOGLE AUTH ----------------
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

# ---------------- UI ----------------
st.set_page_config(page_title="Attendance", layout="wide")
st.title("🍌 Daily Attendance System")

today = datetime.now().strftime("%d-%m-%Y")
time_now = datetime.now().strftime("%H:%M:%S")

st.subheader(f"Date: {today}")

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
    data.append([today, time_now, name, status, banana])

# ---------------- SAVE ----------------
if st.button("💾 Save Today Data"):
    for row in data:
        sheet.append_row(row)
    st.success("✅ Data saved successfully")

# ---------------- HISTORY ----------------
st.divider()
st.subheader("📅 View Old Records")

records = sheet.get_all_records()
df = pd.DataFrame(records)

if not df.empty:
    selected_date = st.selectbox(
        "Select Date",
        sorted(df["Date"].unique(), reverse=True)
    )

    view_df = df[df["Date"] == selected_date]
    st.dataframe(view_df)

    output = BytesIO()
    view_df.to_excel(output, index=False)

    st.download_button(
        "⬇ Download Excel",
        data=output.getvalue(),
        file_name=f"{selected_date}.xlsx"
    )
