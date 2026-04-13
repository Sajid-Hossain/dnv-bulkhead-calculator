import streamlit as st

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(page_title="DNV Bulkhead Calculator", layout="wide")

# -----------------------------
# Title
# -----------------------------
st.title("⚓ DNV-Based Watertight Bulkhead Calculator")
st.caption("Preliminary ship design tool based on classification logic")

st.divider()

# -----------------------------
# Sidebar Inputs
# -----------------------------
st.sidebar.header("⚙️ Input Parameters")

L = st.sidebar.number_input("Ship Length (L) [m]", 10.0, 400.0, 120.0)

propulsion = st.sidebar.selectbox(
    "Propulsion Type", ["Conventional", "Electric"]
)

damage_stability = st.sidebar.radio(
    "Damage Stability Analysis Available?", ["No", "Yes"]
)

# NEW INPUTS (for 1.1.5–1.1.7)
st.sidebar.subheader("Deck Configuration")

second_deck = st.sidebar.radio(
    "Second Deck Below Freeboard Deck?", ["No", "Yes"]
)

draught_less_than_second_deck = st.sidebar.radio(
    "Draught < Depth to Second Deck?", ["No", "Yes"]
)

raised_quarter_deck = st.sidebar.radio(
    "Raised Quarter Deck Present?", ["No", "Yes"]
)

st.sidebar.divider()

# -----------------------------
# Core Logic Functions
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


def deck_extension_logic(second_deck, draught_cond, quarter_deck):
    notes = []

    # Rule 1.1.5 (default)
    notes.append("All watertight bulkheads shall extend to the bulkhead deck.")

    # Rule 1.1.6 (exception)
    if second_deck == "Yes" and draught_cond == "Yes":
        notes.append(
            "Bulkheads (except collision bulkhead) may terminate at the second deck."
        )
        notes.append(
            "Engine casing between second and bulkhead deck must be watertight."
        )
        notes.append(
            "Second deck must be watertight outside engine casing."
        )

    # Rule 1.1.7 (quarter deck)
    if quarter_deck == "Yes":
        notes.append(
            "Bulkheads within quarter deck region must extend to the quarter deck."
        )

    return notes


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

    # Bulkhead number
    st.subheader("📊 Minimum Transverse Bulkheads")

    if damage_stability == "Yes":
        st.warning("Arrangement governed by damage stability analysis.")
    else:
        result = min_bulkheads(L)

        if result:
            col1, col2 = st.columns(2)
            col1.success(f"Aft Region: {result['aft']} bulkheads")
            col2.success(f"Elsewhere: {result['elsewhere']} bulkheads")
        else:
            st.error("L > 225 m: Special consideration required")

    st.divider()

    # NEW SECTION (Deck Extension Rules)
    st.subheader("🏗️ Bulkhead Vertical Extent (Deck Rules)")

    deck_notes = deck_extension_logic(
        second_deck,
        draught_less_than_second_deck,
        raised_quarter_deck
    )

    for note in deck_notes:
        st.write("✔️", note)

    st.divider()

    # Notes
    st.subheader("📝 Engineering Notes")
    st.info("""
    - Based on DNV Pt.3 Ch.2 Sec.2 (simplified logic)
    - Includes deck termination and extension conditions
    - For preliminary design only
    """)

# -----------------------------
# Footer
# -----------------------------
st.caption("Prototype DNV-based structural arrangement tool")
