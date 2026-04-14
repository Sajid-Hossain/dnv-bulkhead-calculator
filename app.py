import streamlit as st

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="DNV Design Tool", layout="wide")

st.title("⚓ DNV-Based Ship Design Tool")
st.caption("Bulkhead Arrangement + Minimum Bow Height (Preliminary Design)")

st.divider()

# -----------------------------
# SIDEBAR INPUTS
# -----------------------------
st.sidebar.header("⚙️ General Inputs")

L = st.sidebar.number_input("Ship Length L (m)", 10.0, 400.0, 120.0)

propulsion = st.sidebar.selectbox(
    "Propulsion Type", ["Conventional", "Electric"]
)

damage_stability = st.sidebar.radio(
    "Damage Stability Available?", ["No", "Yes"]
)

# ---- Deck Rules Inputs ----
st.sidebar.subheader("🏗️ Deck Configuration")

second_deck = st.sidebar.radio("Second Deck Below Freeboard?", ["No", "Yes"])
draught_cond = st.sidebar.radio("Draught < Depth to Second Deck?", ["No", "Yes"])
quarter_deck = st.sidebar.radio("Raised Quarter Deck?", ["No", "Yes"])

ship_type = st.sidebar.selectbox("Ship Type", ["Cargo Ship", "Other"])
freeboard_to_ap = st.sidebar.radio(
    "Freeboard Deck Extends to AP?", ["Yes", "No"]
)

# ---- Bow Height Inputs ----
st.sidebar.subheader("🌊 Bow Height Inputs")

LLL = st.sidebar.number_input("Freeboard Length LLL (m)", value=120.0)
TLL = st.sidebar.number_input("Load Line Draught TLL (m)", value=8.0)
B = st.sidebar.number_input("Breadth B (m)", value=20.0)
disp = st.sidebar.number_input("Displacement ∇ (m³)", value=15000.0)
Awf = st.sidebar.number_input("Forward Waterplane Area Awf (m²)", value=800.0)

actual_Fb = st.sidebar.number_input("Actual Bow Height Provided (mm)", value=3000.0)

st.sidebar.divider()

# -----------------------------
# CORE FUNCTIONS
# -----------------------------
def min_bulkheads(L):
    if L <= 65:
        return {"aft": 3, "elsewhere": 4}
    elif L <= 85:
        return {"aft": 4, "elsewhere": 4}
    elif L <= 105:
        return {"aft": 4, "elsewhere": 5}
    elif L <= 125:
        return {"aft": 5, "elsewhere": 6}
    elif L <= 145:
        return {"aft": 6, "elsewhere": 7}
    elif L <= 165:
        return {"aft": 7, "elsewhere": 8}
    elif L <= 190:
        return {"aft": 8, "elsewhere": 9}
    elif L <= 225:
        return {"aft": 9, "elsewhere": 10}
    else:
        return None


def mandatory_bulkheads(propulsion):
    items = [
        "Collision bulkhead",
        "Aft peak bulkhead",
        "Engine room forward bulkhead",
        "Engine room aft bulkhead"
    ]
    if propulsion == "Electric":
        items.append("Generator room watertight bulkhead")
    return items


def deck_logic():
    notes = []

    notes.append("All watertight bulkheads extend to bulkhead deck.")

    if second_deck == "Yes" and draught_cond == "Yes":
        notes += [
            "Bulkheads (except collision) may terminate at second deck.",
            "Engine casing must be watertight.",
            "Second deck must be watertight outside casing."
        ]

    if quarter_deck == "Yes":
        notes.append("Bulkheads in quarter deck region extend to that deck.")

    if ship_type == "Cargo Ship" and quarter_deck == "Yes" and freeboard_to_ap == "No":
        notes += [
            "Aft peak bulkhead may terminate below freeboard deck.",
            "Rudder stock must be in watertight compartment.",
            "No open connection forward of aft peak bulkhead."
        ]

    return notes


def calculate_cb():
    return disp / (LLL * B * TLL)


def calculate_cwf():
    return Awf / (0.5 * LLL * B)


def calculate_fb(CB, Cwf):
    x = LLL / 100
    return (
        (6075*x - 1875*x**2 + 200*x**3)
        * (2.08 + 0.609*CB - 1.603*Cwf - 0.0129*(LLL/TLL))
    )

# -----------------------------
# MAIN BUTTON
# -----------------------------
if st.button("🚀 Run Full Calculation"):

    # ---------------- BULKHEADS ----------------
    st.header("🧱 Bulkhead Arrangement")

    for b in mandatory_bulkheads(propulsion):
        st.write("✔️", b)

    if damage_stability == "No":
        res = min_bulkheads(L)
        if res:
            st.success(f"Aft: {res['aft']} | Elsewhere: {res['elsewhere']}")
        else:
            st.error("Special consideration required (L > 225 m)")
    else:
        st.warning("Damage stability governs arrangement.")

    st.subheader("🏗️ Deck Rules")
    for note in deck_logic():
        st.write("✔️", note)

    st.divider()

    # ---------------- BOW HEIGHT ----------------
    st.header("🌊 Minimum Bow Height")

    CB = calculate_cb()
    Cwf = calculate_cwf()
    Fb = calculate_fb(CB, Cwf)

    col1, col2, col3 = st.columns(3)
    col1.metric("CB", f"{CB:.3f}")
    col2.metric("Cwf", f"{Cwf:.3f}")
    col3.metric("Required Fb (mm)", f"{Fb:.1f}")

    # Compliance
    st.subheader("✔ Compliance Check")

    if actual_Fb >= Fb:
        st.success("Complies with minimum bow height requirement")
    else:
        st.error("Does NOT comply with minimum bow height requirement")

    # Validation
    if CB < 0.5 or CB > 0.85:
        st.warning("CB outside typical ship design range")

    st.divider()

    st.subheader("📘 Design Notes")
    st.info("""
    - Based on DNV Pt.3 Ch.2 Sec.2 and Load Line Convention
    - Combines structural arrangement and hydrostatic requirements
    - For preliminary design only
    """)

# -----------------------------
# FOOTER
# -----------------------------
st.caption("DNV-based preliminary ship design software prototype")
