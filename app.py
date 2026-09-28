import streamlit as st
import sqlite3
from datetime import datetime

TOTAL_SLOTS = 10
RATE_PER_HOUR = 20   # rupees

st.set_page_config(page_title="Smart Parking System", page_icon="🚗")


# ---------- database part ----------
def get_db():
    conn = sqlite3.connect("parking.db")
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS parking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot INTEGER,
            vehicle_no TEXT,
            owner TEXT,
            vehicle_type TEXT,
            time_in TEXT,
            time_out TEXT,
            fee INTEGER
        )
    """)
    return conn


conn = get_db()

# cars parked right now
parked = conn.execute("SELECT * FROM parking WHERE time_out IS NULL ORDER BY slot").fetchall()
history = conn.execute("SELECT * FROM parking WHERE time_out IS NOT NULL ORDER BY id DESC LIMIT 10").fetchall()
earnings = conn.execute("SELECT COALESCE(SUM(fee), 0) FROM parking").fetchone()[0]

taken = [p["slot"] for p in parked]
free = [s for s in range(1, TOTAL_SLOTS + 1) if s not in taken]

# ---------- page ----------
st.title("🚗 Smart Parking Management System")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Slots", TOTAL_SLOTS)
col2.metric("Free", len(free))
col3.metric("Occupied", len(taken))
col4.metric("Earnings", f"Rs. {earnings}")

# show messages saved from the last action
if "msg" in st.session_state:
    st.info(st.session_state.pop("msg"))

# slots
st.subheader("Parking Slots")
cols = st.columns(5)
for i in range(1, TOTAL_SLOTS + 1):
    if i in taken:
        cols[(i - 1) % 5].error(f"Slot {i}: Full")
    else:
        cols[(i - 1) % 5].success(f"Slot {i}: Free")

# park a vehicle
st.subheader("Park a Vehicle")
if len(free) == 0:
    st.warning("Parking is full!")
else:
    with st.form("park_form", clear_on_submit=True):
        vehicle_no = st.text_input("Vehicle Number (e.g. KA01AB1234)")
        owner = st.text_input("Owner Name")
        vehicle_type = st.selectbox("Vehicle Type", ["Car", "Bike", "Truck"])
        slot = st.selectbox("Slot", free)
        submit = st.form_submit_button("Park")

    if submit:
        vehicle_no = vehicle_no.strip().upper()
        if vehicle_no == "" or owner.strip() == "":
            st.session_state["msg"] = "Please fill all the details!"
        else:
            already = conn.execute("SELECT id FROM parking WHERE vehicle_no=? AND time_out IS NULL",
                                   (vehicle_no,)).fetchone()
            if already:
                st.session_state["msg"] = "This vehicle is already parked!"
            else:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn.execute("INSERT INTO parking (slot, vehicle_no, owner, vehicle_type, time_in) VALUES (?,?,?,?,?)",
                             (slot, vehicle_no, owner.strip(), vehicle_type, now))
                conn.commit()
                st.session_state["msg"] = f"{vehicle_no} parked in slot {slot}."
        st.rerun()

st.caption(f"Rate: Rs. {RATE_PER_HOUR} per hour (part of an hour counts as a full hour)")

# currently parked + checkout
st.subheader("Currently Parked")
if len(parked) == 0:
    st.write("No vehicles parked right now.")
else:
    st.table([{"Slot": p["slot"], "Vehicle No": p["vehicle_no"], "Owner": p["owner"],
               "Type": p["vehicle_type"], "Time In": p["time_in"]} for p in parked])

    choice = st.selectbox("Select vehicle to check out", [p["vehicle_no"] for p in parked])
    if st.button("Check Out"):
        rec = conn.execute("SELECT * FROM parking WHERE vehicle_no=? AND time_out IS NULL", (choice,)).fetchone()
        time_in = datetime.strptime(rec["time_in"], "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        hours = int((now - time_in).total_seconds() // 3600) + 1
        fee = hours * RATE_PER_HOUR
        conn.execute("UPDATE parking SET time_out=?, fee=? WHERE id=?",
                     (now.strftime("%Y-%m-%d %H:%M:%S"), fee, rec["id"]))
        conn.commit()
        st.session_state["msg"] = f"{choice} checked out. Fee: Rs. {fee} ({hours} hr)"
        st.rerun()

# history
st.subheader("Recent History")
if len(history) == 0:
    st.write("No history yet.")
else:
    st.table([{"Vehicle No": h["vehicle_no"], "Owner": h["owner"], "Slot": h["slot"],
               "In": h["time_in"], "Out": h["time_out"], "Fee": f"Rs. {h['fee']}"} for h in history])
