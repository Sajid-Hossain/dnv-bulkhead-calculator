import streamlit as st

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="DNV Ship Design Tool", layout="wide")

st.title("⚓ DNV-Based Ship Design Tool")
st.caption("Integrated Rule-Based Ship Arrangement & Compliance Tool")

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

# ---- Deck Rules ----
st.sidebar.subheader("🏗️ Deck Configuration")

second_deck = st.sidebar.radio("Second Deck Below Freeboard?", ["No", "Yes"])
draught_cond = st.sidebar.radio("Draught < Depth to Second Deck?", ["No", "Yes"])
quarter_deck = st.sidebar.radio("Raised Quarter Deck?", ["No", "Yes"])

ship_type = st.sidebar.selectbox("Ship Type", ["Cargo Ship", "Other"])
freeboard_to_ap = st.sidebar.radio("Freeboard Deck Extends to AP?", ["Yes", "No"])

# ---- Bow Height ----
st.sidebar.subheader("🌊 Bow Height Inputs")

LLL = st.sidebar.number_input("Freeboard Length LLL (m)", value=120.0)
TLL = st.sidebar.number_input("Load Line Draught TLL (m)", value=8.0)
B = st.sidebar.number_input("Breadth B (m)", value=20.0)
disp = st.sidebar.number_input("Displacement ∇ (m³)", value=15000.0)
Awf = st.sidebar.number_input("Forward Waterplane Area Awf (m²)", value=800.0)
actual_Fb = st.sidebar.number_input("Actual Bow Height Provided (mm)", value=3000.0)

# ---- Collision Bulkhead ----
st.sidebar.subheader("🚢 Collision Bulkhead")

bulbous_bow = st.sidebar.radio("Bulbous Bow Present?", ["No", "Yes"])
xbe = st.sidebar.number_input("Bulb Extension Length xbe (m)", value=5.0)

# ---- Additional Arrangement Inputs ----
st.sidebar.subheader("📐 Arrangement Checks")

openings_below_freeboard = st.sidebar.radio("Openings below freeboard deck?", ["No", "Yes"])
num_pipes = st.sidebar.number_input("Pipes through collision bulkhead", 0, 5, 0)
long_superstructure = st.sidebar.radio("Forward superstructure ≥ 0.25L?", ["No", "Yes"])

aft_space_usage = st.sidebar.selectbox("Aft Space Usage", ["Machinery", "Cargo/Passengers"])

# ---- Double Bottom ----
st.sidebar.subheader("🧱 Double Bottom")

double_bottom_fitted = st.sidebar.radio("Double Bottom Fitted?", ["Yes", "No"])

# ---- Cofferdam ----
st.sidebar.subheader("🛢️ Cofferdam")

fuel_next_to_fw = st.sidebar.radio("Fuel tank adjacent to fresh water?", ["Yes", "No"])

# -----------------------------
# FUNCTIONS
# -----------------------------
def min_bulkheads(L):
    if L <= 65: return {"aft": 3, "elsewhere": 4}
    elif L <= 85: return {"aft": 4, "elsewhere": 4}
    elif L <= 105: return {"aft": 4, "elsewhere": 5}
    elif L <= 125: return {"aft": 5, "elsewhere": 6}
    elif L <= 145: return {"aft": 6, "elsewhere": 7}
    elif L <= 165: return {"aft": 7, "elsewhere": 8}
    elif L <= 190: return {"aft": 8, "elsewhere": 9}
    elif L <= 225: return {"aft": 9, "elsewhere": 10}
    else: return None


def calculate_cb():
    return disp / (LLL * B * TLL)


def calculate_cwf():
    return Awf / (0.5 * LLL * B)


def calculate_fb(CB, Cwf):
    x = LLL / 100
    return (6075*x - 1875*x**2 + 200*x**3) * (2.08 + 0.609*CB - 1.603*Cwf - 0.0129*(LLL/TLL))


def calculate_xf():
    if bulbous_bow == "No":
        return 0
    return min(0.5*xbe, 0.015*LLL, 3.0)


def collision_limits(xf):
    if LLL < 200:
        xc_min = 0.05*LLL - xf
    else:
        xc_min = 10 - xf

    if LLL < 100:
        xc_max = 0.05*LLL + 3 - xf
    else:
        xc_max = 0.08*LLL - xf

    return xc_min, xc_max


def double_bottom_height():
    h = 1000 * B / 20
    return min(max(h, 760), 2000)

# -----------------------------
# MAIN EXECUTION
# -----------------------------
if st.button("🚀 Run Full Calculation"):

    # ---------------- BULKHEADS ----------------
    st.header("🧱 Bulkhead Arrangement")

    res = min_bulkheads(L)
    if res:
        st.success(f"Aft: {res['aft']} | Elsewhere: {res['elsewhere']}")

    st.divider()

    # ---------------- BOW HEIGHT ----------------
    st.header("🌊 Minimum Bow Height")

    CB = calculate_cb()
    Cwf = calculate_cwf()
    Fb = calculate_fb(CB, Cwf)

    st.metric("Required Fb (mm)", f"{Fb:.1f}")

    if actual_Fb >= Fb:
        st.success("Bow height compliant")
    else:
        st.error("Bow height NOT compliant")

    st.divider()

    # ---------------- COLLISION BULKHEAD ----------------
    st.header("🚢 Collision Bulkhead")

    xf = calculate_xf()
    xc_min, xc_max = collision_limits(xf)

    st.write(f"xc_min = {xc_min:.2f} m | xc_max = {xc_max:.2f} m")

    if openings_below_freeboard == "Yes":
        st.error("Openings below freeboard deck NOT allowed")

    if num_pipes > 1:
        st.error("More than one pipe NOT allowed")

    if long_superstructure == "Yes":
        st.info("Bulkhead must extend weathertight to next deck")

    st.divider()

    # ---------------- AFT PEAK ----------------
    st.header("⚓ Aft Peak Bulkhead")

    st.write("✔️ Must enclose stern tube and rudder trunk")

    if aft_space_usage == "Machinery":
        st.info("Termination above deepest draught permitted")

    st.divider()

    # ---------------- COFFERDAM ----------------
    st.header("🛢️ Cofferdam Check")

    if fuel_next_to_fw == "Yes":
        st.error("Cofferdam REQUIRED between fuel and fresh water tanks")
    else:
        st.success("No cofferdam required")

    st.divider()

    # ---------------- DOUBLE BOTTOM ----------------
    st.header("🧱 Double Bottom")

    if double_bottom_fitted == "Yes":
        hdb = double_bottom_height()
        st.metric("Minimum Double Bottom Height (mm)", f"{hdb:.0f}")
        st.success("Double bottom provided")
    else:
        st.warning("Must justify bottom damage safety")

    st.divider()

    # ---------------- FORE & AFT COMPARTMENTS ----------------
    st.header("🚢 Compartment Rules")

    st.write("✔️ No fuel oil in compartments forward of collision bulkhead")
    st.write("✔️ Stern tube must be enclosed in watertight space")
    st.write("✔️ Shaft tunnel required if engine room amidships")
    st.write("✔️ Steering gear compartment must be separated and accessible")

    st.divider()

    # ---------------- ACCESS ----------------
    st.header("🚪 Access Requirements")

    st.write("✔️ All tanks must be accessible for inspection")
    st.write("✔️ Double bottom must have manholes")
    st.write("✔️ Closed spaces must be accessible or specially approved")

    st.divider()

    st.subheader("📘 Final Notes")
    st.info("""
    - Based on DNV Pt.3 Ch.2 Sec.2
    - Includes arrangement, safety, and compliance logic
    - Suitable for preliminary ship design
    """)

# -----------------------------
# FOOTER
# -----------------------------
st.caption("DNV-based ship design and compliance tool (advanced prototype)")
