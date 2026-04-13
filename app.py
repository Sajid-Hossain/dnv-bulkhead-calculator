import streamlit as st

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    page_title="DNV Bulkhead Calculator",
    layout="wide"
)

# -----------------------------
# Title Section
# -----------------------------
st.title("⚓ DNV-Based Watertight Bulkhead Calculator")
st.caption("Preliminary ship design tool based on classification logic")

st.divider()

# -----------------------------
# Sidebar Inputs (Professional UI style)
# -----------------------------
st.sidebar.header("⚙️ Input Parameters")

L = st.sidebar.number_input(
    "Ship Length (L) [m]",
    min_value=10.0,
    max_value=400.0,
    value=120.0
)

propulsion = st.sidebar.selectbox(
    "Propulsion Type",
    ["Conventional", "Electric"]
)

damage_stability = st.sidebar.radio(
    "Damage Stability Analysis Available?",
    ["No", "Yes"]
)

st.sidebar.divider()
st.sidebar.info("All calculations are based on preliminary class rule interpretation.")

# -----------------------------
# Core Logic
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


# -----------------------------
# Run Calculation
# -----------------------------
if st.button("🚀 Calculate Bulkhead Arrangement"):

    st.subheader("📌 Input Summary")

    col1, col2, col3 = st.columns(3)
    col1.metric("Length (m)", L)
    col2.metric("Propulsion", propulsion)
    col3.metric("Damage Stability", damage_stability)

    st.divider()

    # Mandatory bulkheads
    st.subheader("🧱 Mandatory Bulkheads")

    for b in mandatory_bulkheads(propulsion):
        st.write("✔️", b)

    st.divider()

    # Rule-based result
    st.subheader("📊 Minimum Transverse Bulkheads")

    if damage_stability == "Yes":
        st.warning("Arrangement governed by damage stability analysis. Table not applicable.")
    else:
        result = min_bulkheads(L)

        if result:
            col1, col2 = st.columns(2)
            col1.success(f"Aft Region: {result['aft']} bulkheads")
            col2.success(f"Elsewhere: {result['elsewhere']} bulkheads")
        else:
            st.error("L > 225 m: Special consideration required by class rules")

    st.divider()

    # Engineering Notes
    st.subheader("📝 Engineering Notes")
    st.info("""
    - Based on simplified interpretation of DNV watertight bulkhead arrangement rules
    - Applicable for preliminary design only
    - Final design must be verified by class-approved calculations
    """)

# -----------------------------
# Footer
# -----------------------------
st.caption("Developed as a prototype engineering design tool (DNV-based logic engine)")
