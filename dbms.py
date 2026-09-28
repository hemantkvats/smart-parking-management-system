import streamlit as st
import sqlite3
from datetime import datetime
import time
import html as htmllib


# ============================================================
# HTML RENDER HELPER
# ============================================================

def render_html(markup):
    """
    Strips leading whitespace from EVERY line and removes blank lines.
    Markdown treats lines indented 4+ spaces (or HTML broken by blank
    lines) as code blocks, which is what caused raw HTML to show up.
    """
    cleaned = "\n".join(
        line.strip() for line in markup.splitlines() if line.strip()
    )
    st.markdown(cleaned, unsafe_allow_html=True)


def esc(value):
    """Escape user-provided text before placing it in HTML."""
    return htmllib.escape(str(value))


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="ParkEase | Smart Parking",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# CONSTANTS
# ============================================================

TOTAL_SLOTS = 10
RATE_PER_HOUR = 20


# ============================================================
# DATABASE
# ============================================================

def get_db():
    conn = sqlite3.connect("parking.db", check_same_thread=False)
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
    conn.commit()
    return conn


conn = get_db()


def get_currently_parked():
    return conn.execute("""
        SELECT * FROM parking
        WHERE time_out IS NULL
        ORDER BY slot
    """).fetchall()


def get_history():
    return conn.execute("""
        SELECT * FROM parking
        WHERE time_out IS NOT NULL
        ORDER BY id DESC
        LIMIT 10
    """).fetchall()


def get_total_earnings():
    result = conn.execute(
        "SELECT COALESCE(SUM(fee), 0) FROM parking"
    ).fetchone()
    return result[0]


def park_vehicle(slot, vehicle_no, owner, vehicle_type):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        INSERT INTO parking
        (slot, vehicle_no, owner, vehicle_type, time_in, time_out, fee)
        VALUES (?, ?, ?, ?, ?, NULL, 0)
    """, (slot, vehicle_no, owner, vehicle_type, now))
    conn.commit()


def remove_vehicle(record_id):
    row = conn.execute(
        "SELECT * FROM parking WHERE id = ?", (record_id,)
    ).fetchone()

    if row is None:
        return 0

    time_in = datetime.strptime(row["time_in"], "%Y-%m-%d %H:%M:%S")
    time_out = datetime.now()
    seconds = (time_out - time_in).total_seconds()

    # Minimum parking charge = 1 hour
    hours = max(1, int((seconds + 3599) // 3600))
    fee = hours * RATE_PER_HOUR

    conn.execute("""
        UPDATE parking SET time_out = ?, fee = ? WHERE id = ?
    """, (time_out.strftime("%Y-%m-%d %H:%M:%S"), fee, record_id))
    conn.commit()
    return fee


# ============================================================
# CURRENT DATA
# ============================================================

parked = get_currently_parked()
history = get_history()

occupied_slots = {row["slot"] for row in parked}
free_slots = [s for s in range(1, TOTAL_SLOTS + 1) if s not in occupied_slots]

occupied_count = len(occupied_slots)
free_count = TOTAL_SLOTS - occupied_count
earnings = get_total_earnings()


# ============================================================
# CSS
# ============================================================

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #f5f7f4; color: #17201b; }
.block-container { padding-top: 1rem; padding-bottom: 4rem; max-width: 1250px; }

#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }

/* NAVBAR */
.navbar {
    width: 100%; background: rgba(255,255,255,0.96);
    border: 1px solid #e4e9e5; border-radius: 18px;
    padding: 14px 22px; display: flex; align-items: center;
    justify-content: space-between; margin-bottom: 28px;
    box-shadow: 0 8px 30px rgba(20,40,25,0.05);
}
.logo { font-family: 'Space Grotesk', sans-serif; font-size: 25px; font-weight: 700; color: #18221c; }
.logo span { color: #19a765; }
.nav-links { display: flex; gap: 30px; font-size: 14px; font-weight: 600; }
.nav-links a { text-decoration: none; color: #647067; }
.nav-links a:hover { color: #19a765; }
.nav-button {
    background: #19a765; color: white !important; padding: 10px 17px;
    border-radius: 11px; text-decoration: none; font-weight: 600;
}

/* HERO */
.hero {
    min-height: 460px; border-radius: 30px; overflow: hidden;
    position: relative; margin-bottom: 35px;
    background: linear-gradient(90deg, rgba(247,250,247,0.98) 0%, rgba(247,250,247,0.95) 39%, rgba(247,250,247,0.15) 75%), url('https://images.unsplash.com/photo-1506521781263-d8422e82f27a?auto=format&fit=crop&w=1600&q=85');
    background-size: cover; background-position: center;
    display: flex; align-items: center; padding: 60px;
    box-shadow: 0 15px 45px rgba(20,40,25,0.08);
}
.hero-content { max-width: 570px; }
.hero-tag {
    display: inline-block; background: #e2f6eb; color: #148853;
    padding: 8px 13px; border-radius: 50px; font-size: 12px;
    font-weight: 700; letter-spacing: 0.7px; margin-bottom: 18px;
}
.hero h1 {
    font-family: 'Space Grotesk', sans-serif; font-size: 62px;
    line-height: 0.98; letter-spacing: -3px; margin: 0 0 22px 0; color: #17201b;
}
.hero h1 span { color: #18a665; }
.hero p { font-size: 17px; line-height: 1.65; color: #647067; max-width: 490px; margin-bottom: 28px; }
.hero-small { display: flex; gap: 35px; margin-top: 35px; }
.hero-stat strong { display: block; font-family: 'Space Grotesk', sans-serif; font-size: 25px; color: #17201b; }
.hero-stat span { font-size: 12px; color: #718078; }

/* SECTION HEADINGS */
.section-label { color: #19a765; font-weight: 700; font-size: 12px; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 8px; }
.section-title { font-family: 'Space Grotesk', sans-serif; font-size: 38px; letter-spacing: -1.5px; margin-bottom: 8px; color: #17201b; }
.section-description { color: #6d786f; font-size: 15px; margin-bottom: 25px; }

/* METRICS */
.metric-card {
    background: white; border: 1px solid #e5eae6; border-radius: 20px;
    padding: 22px 24px; min-height: 155px; box-sizing: border-box;
    box-shadow: 0 8px 25px rgba(20,40,25,0.04);
}
}
.metric-icon { font-size: 20px; margin-bottom: 8px; }
.metric-number { font-family: 'Space Grotesk', sans-serif; font-size: 29px; font-weight: 700; color: #17201b; }
.metric-label { color: #758078; font-size: 12px; margin-top: 3px; }

/* SLOTS */
.slot-card {
    background: white; border-radius: 18px; padding: 18px;
    border: 1px solid #e5eae6; min-height: 145px;
    box-shadow: 0 8px 24px rgba(20,40,25,0.04); transition: 0.2s;
}
.slot-card:hover { transform: translateY(-3px); box-shadow: 0 12px 30px rgba(20,40,25,0.08); }
.slot-number { font-family: 'Space Grotesk', sans-serif; font-size: 23px; font-weight: 700; color: #17201b; }
.slot-status-free {
    display: inline-block; background: #e3f7eb; color: #15905a;
    border-radius: 50px; padding: 5px 9px; font-size: 10px; font-weight: 700; margin-top: 12px;
}
.slot-status-busy {
    display: inline-block; background: #fff0ed; color: #d6533d;
    border-radius: 50px; padding: 5px 9px; font-size: 10px; font-weight: 700; margin-top: 12px;
}
.slot-car { font-size: 31px; margin-top: 10px; }

/* FEATURES */
.feature-card {
    background: white; border: 1px solid #e5eae6; border-radius: 22px;
    padding: 27px; min-height: 190px; box-shadow: 0 8px 25px rgba(20,40,25,0.04);
}
.feature-icon {
    width: 45px; height: 45px; background: #e4f7ed; border-radius: 13px;
    display: flex; align-items: center; justify-content: center;
    font-size: 21px; margin-bottom: 18px;
}
.feature-card h3 { font-family: 'Space Grotesk', sans-serif; margin: 0 0 8px 0; font-size: 19px; }
.feature-card p { color: #727d75; font-size: 13px; line-height: 1.6; }

/* BOOKING */
.booking-box {
    background: #17201b; color: white; border-radius: 28px;
    padding: 35px; margin-top: 25px; margin-bottom: 30px;
}
.booking-box h2 { font-family: 'Space Grotesk', sans-serif; font-size: 32px; margin-bottom: 8px; color: white; }
.booking-box p { color: #aeb9b1; }

/* PARKED */
.parked-card {
    background: white; border: 1px solid #e5eae6; border-radius: 18px;
    padding: 20px; margin-bottom: 12px;
}
.parked-title { font-family: 'Space Grotesk', sans-serif; font-size: 18px; font-weight: 700; }
.parked-detail { color: #758078; font-size: 13px; margin-top: 5px; }

/* BUTTONS */
.stButton > button {
    background: white !important;
    color: #17201b !important;
    border: 1px solid #dce4df !important;
    border-radius: 11px !important;
    min-height: 42px;
    font-weight: 600 !important;
    transition: 0.2s;
}
.stButton > button p {
    color: #17201b !important;
}
.stButton > button:hover {
    background: #f0faf5 !important;
    border-color: #19a765 !important;
    color: #19a765 !important;
}
.stButton > button:hover p {
    color: #19a765 !important;
}

/* Green submit button inside the form */
div[data-testid="stFormSubmitButton"] button {
    background: #19a765 !important;
    color: white !important;
    border: none !important;
}
div[data-testid="stFormSubmitButton"] button p {
    color: white !important;
}

/* INPUTS */
div[data-baseweb="input"] { border-radius: 10px; }
div[data-baseweb="select"] { border-radius: 10px; }

/* FOOTER */
.footer {
    border-top: 1px solid #dde4df; margin-top: 60px; padding: 28px 0;
    color: #7a857e; font-size: 12px; text-align: center;
}

/* MOBILE */
@media (max-width: 768px) {
    .hero { padding: 35px; min-height: 500px; }
    .hero h1 { font-size: 44px; }
    .nav-links { display: none; }
    .nav-button { font-size: 12px; }
}
</style>
"""

# CSS is passed straight to st.markdown (no cleaning needed: <style> blocks are safe)
st.markdown(CSS, unsafe_allow_html=True)


# ============================================================
# NAVIGATION
# ============================================================

render_html("""
<div class="navbar">
    <div class="logo">Park<span>Ease</span></div>
    <div class="nav-links">
        <a href="#home">Home</a>
        <a href="#parking">Parking</a>
        <a href="#services">Services</a>
        <a href="#booking">Reserve</a>
        <a href="#history">History</a>
    </div>
    <a class="nav-button" href="#booking">Reserve a Spot</a>
</div>
""")


# ============================================================
# HERO
# ============================================================

render_html("""
<div id="home" class="hero">
    <div class="hero-content">
        <div class="hero-tag">SMART PARKING MANAGEMENT</div>
        <h1>Parking<br><span>made smarter.</span></h1>
        <p>
            Find your parking space, reserve your spot,
            and manage your vehicle with ease.
            A simple and efficient parking experience
            designed for modern cities.
        </p>
        <div class="hero-small">
            <div class="hero-stat"><strong>10</strong><span>Parking Slots</span></div>
            <div class="hero-stat"><strong>₹20</strong><span>Starting / Hour</span></div>
            <div class="hero-stat"><strong>24/7</strong><span>Management</span></div>
        </div>
    </div>
</div>
""")


# ============================================================
# LIVE STATUS
# ============================================================

render_html("""
<div class="section-label">LIVE PARKING STATUS</div>
<div class="section-title">Know your space.</div>
<div class="section-description">Real-time overview of the parking facility.</div>
""")

m1, m2, m3, m4 = st.columns(4)

with m1:
    render_html(f"""
    <div class="metric-card">
        <div class="metric-icon">🅿️</div>
        <div class="metric-number">{TOTAL_SLOTS}</div>
        <div class="metric-label">TOTAL SLOTS</div>
    </div>
    """)

with m2:
    render_html(f"""
    <div class="metric-card">
        <div class="metric-icon">✓</div>
        <div class="metric-number">{free_count}</div>
        <div class="metric-label">AVAILABLE NOW</div>
    </div>
    """)

with m3:
    render_html(f"""
    <div class="metric-card">
        <div class="metric-icon">🚗</div>
        <div class="metric-number">{occupied_count}</div>
        <div class="metric-label">OCCUPIED</div>
    </div>
    """)

with m4:
    render_html(f"""
    <div class="metric-card">
        <div class="metric-icon">₹</div>
        <div class="metric-number">₹{earnings}</div>
        <div class="metric-label">TOTAL EARNINGS</div>
    </div>
    """)

st.write("")


# ============================================================
# PARKING SLOTS
# ============================================================

render_html("""
<div id="parking" class="section-label">PARKING AREA</div>
<div class="section-title">Choose your space.</div>
<div class="section-description">
    Green indicates an available space. Red indicates an occupied space.
</div>
""")

# 5 slots per row
for row_start in range(1, TOTAL_SLOTS + 1, 5):
    cols = st.columns(5)
    for index, slot_number in enumerate(
        range(row_start, min(row_start + 5, TOTAL_SLOTS + 1))
    ):
        with cols[index]:
            if slot_number in occupied_slots:
                render_html(f"""
                <div class="slot-card">
                    <div class="slot-number">A{slot_number:02d}</div>
                    <div class="slot-car">🚗</div>
                    <div class="slot-status-busy">OCCUPIED</div>
                </div>
                """)
            else:
                render_html(f"""
                <div class="slot-card">
                    <div class="slot-number">A{slot_number:02d}</div>
                    <div class="slot-car">🅿️</div>
                    <div class="slot-status-free">AVAILABLE</div>
                </div>
                """)
    st.write("")


# ============================================================
# SERVICES
# ============================================================

render_html("""
<div id="services" class="section-label">WHY PARKEASE</div>
<div class="section-title">Simple. Smart. Efficient.</div>
<div class="section-description">Everything you need to manage your parking facility.</div>
""")

f1, f2, f3 = st.columns(3)

with f1:
    render_html("""
    <div class="feature-card">
        <div class="feature-icon">🅿️</div>
        <h3>Easy Parking</h3>
        <p>Quickly check available parking spaces and select the slot that works best for you.</p>
    </div>
    """)

with f2:
    render_html("""
    <div class="feature-card">
        <div class="feature-icon">⚡</div>
        <h3>Quick Reservation</h3>
        <p>Reserve your parking space in seconds without complicated procedures.</p>
    </div>
    """)

with f3:
    render_html("""
    <div class="feature-card">
        <div class="feature-icon">🔒</div>
        <h3>Secure Management</h3>
        <p>Keep track of vehicles, parking duration, payments and parking history in one place.</p>
    </div>
    """)

st.write("")
st.write("")


# ============================================================
# BOOKING SECTION
# ============================================================

render_html("""
<div id="booking" class="booking-box">
    <div class="section-label">RESERVE A SPACE</div>
    <h2>Park without the hassle.</h2>
    <p>Enter your vehicle details and select an available parking slot.</p>
</div>
""")

with st.form("parking_form", clear_on_submit=True):

    col1, col2 = st.columns(2)

    with col1:
        vehicle_no = st.text_input(
            "Vehicle Number", placeholder="e.g. KA01AB1234"
        )
        owner = st.text_input(
            "Owner Name", placeholder="Enter owner's name"
        )

    with col2:
        vehicle_type = st.selectbox(
            "Vehicle Type", ["Car", "Bike", "SUV", "EV"]
        )

        if free_slots:
            selected_slot = st.selectbox(
                "Select Parking Slot",
                free_slots,
                format_func=lambda x: f"A{x:02d}",
            )
        else:
            selected_slot = None
            st.selectbox("Select Parking Slot", ["No slots available"])

    st.write("")

    submitted = st.form_submit_button(
        "RESERVE PARKING SPACE", use_container_width=True
    )

    if submitted:
        vehicle_clean = vehicle_no.strip().upper()
        owner_clean = owner.strip()

        if not vehicle_clean:
            st.error("Please enter the vehicle number.")

        elif not owner_clean:
            st.error("Please enter the owner's name.")

        elif selected_slot is None:
            st.error("No parking slots are currently available.")

        else:
            existing = conn.execute("""
                SELECT * FROM parking
                WHERE vehicle_no = ? AND time_out IS NULL
            """, (vehicle_clean,)).fetchone()

            if existing:
                st.error(
                    f"Vehicle {vehicle_clean} is already parked "
                    f"in slot A{existing['slot']:02d}."
                )
            else:
                park_vehicle(
                    selected_slot, vehicle_clean, owner_clean, vehicle_type
                )
                st.success(
                    f"Parking confirmed! Your vehicle is assigned "
                    f"to slot A{selected_slot:02d}."
                )
                time.sleep(0.8)
                st.rerun()


# ============================================================
# CURRENTLY PARKED
# ============================================================

st.write("")
st.write("")

render_html("""
<div class="section-label">LIVE VEHICLES</div>
<div class="section-title">Currently parked.</div>
<div class="section-description">Vehicles currently inside the parking facility.</div>
""")

if not parked:
    st.info("No vehicles are currently parked.")

else:
    for row in parked:
        render_html(f"""
        <div class="parked-card">
            <div class="parked-title">
                🚗 {esc(row["vehicle_no"])} &nbsp;·&nbsp; Slot A{row["slot"]:02d}
            </div>
            <div class="parked-detail">
                Owner: {esc(row["owner"])} &nbsp;|&nbsp;
                Vehicle: {esc(row["vehicle_type"])} &nbsp;|&nbsp;
                Entry: {esc(row["time_in"])}
            </div>
        </div>
        """)

        if st.button(
            f"Exit Vehicle · A{row['slot']:02d}",
            key=f"exit_{row['id']}",
        ):
            fee = remove_vehicle(row["id"])
            st.success(f"Vehicle exited successfully. Parking fee: ₹{fee}")
            time.sleep(0.8)
            st.rerun()


# ============================================================
# HISTORY
# ============================================================

st.write("")
st.write("")

render_html("""
<div id="history" class="section-label">PARKING HISTORY</div>
<div class="section-title">Recent activity.</div>
<div class="section-description">Latest completed parking sessions.</div>
""")

if not history:
    st.info("No parking history yet.")

else:
    history_data = []
    for row in history:
        history_data.append({
            "Slot": f"A{row['slot']:02d}",
            "Vehicle": row["vehicle_no"],
            "Owner": row["owner"],
            "Type": row["vehicle_type"],
            "Entry": row["time_in"],
            "Exit": row["time_out"],
            "Fee": f"₹{row['fee']}",
        })

    st.dataframe(history_data, use_container_width=True, hide_index=True)


# ============================================================
# FOOTER
# ============================================================

render_html("""
<div class="footer">
    <strong>ParkEase</strong> · Smart Parking Management System
    <br><br>
    DBMS Mini Project · Built with Python, Streamlit & SQLite
</div>
""")
