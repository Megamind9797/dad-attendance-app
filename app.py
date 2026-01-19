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

# ---------------- LOGIN ----------------
st.title("🍌 Daily Attendance System")

password = st.text_input("Enter password (admin only)", type="password")

is_admin = password == st.secrets["admin_password"]

if is_admin:
    st.success("Admin mode enabled 👑")
else:
    st.info("User mode (Papa)")

# ---------------- COMMON ----------------
today = datetime.now().strftime("%d-%m-%Y")
time_now = datetime.now().strftime("%H:%M:%S")

st.subheader(f"Date: {today}")

data = []

# ---------------- ATTENDANCE ENTRY ----------------
st.markdown("### 📝 Today Attendance")

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

if st.button("💾 Save Today Data"):
    for row in data:
        sheet.append_row(row)
    st.success("Data saved successfully ✅")

# ---------------- HISTORY ----------------
st.divider()
st.subheader("📅 History")

records = sheet.get_all_records()
df = pd.DataFrame(records)

if not df.empty:

    dates = sorted(df["Date"].unique(), reverse=True)
    selected_date = st.selectbox("Select Date", dates)

    show_df = df[df["Date"] == selected_date]

    st.dataframe(show_df)

    # Excel download allowed for both
    output = BytesIO()
    show_df.to_excel(output, index=False)

    st.download_button(
        "⬇ Download Excel",
        data=output.getvalue(),
        file_name=f"{selected_date}.xlsx"
    )

# ---------------- ADMIN PANEL ----------------
if is_admin:
    st.divider()
    st.subheader("👑 Admin Panel")

    st.write("📊 Monthly Summary")

    df["Month"] = pd.to_datetime(df["Date"], dayfirst=True).dt.strftime("%B %Y")

    month = st.selectbox("Select Month", df["Month"].unique())

    mdf = df[df["Month"] == month]

    summary = mdf.groupby("Name").agg(
        Total_Days=("Status", "count"),
        Present_Days=("Status", lambda x: (x == "Present").sum()),
        Total_Banana=("Banana", "sum")
    )

    st.dataframe(summary)

    out = BytesIO()
    summary.to_excel(out)

    st.download_button(
        "⬇ Download Monthly Report",
        data=out.getvalue(),
        file_name=f"{month}_report.xlsx"
    )

