import streamlit as st

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="DNV Ship Design Tool", layout="wide")

st.title("⚓ DNV-Based Ship Design Tool")
st.caption("Integrated Rule-Based Ship Arrangement, Corrosion and Compliance Tool")

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

# =========================================================
# CHAPTER 3 - SECTION 3 CORROSION ADDITIONS
# =========================================================
st.sidebar.subheader("🧪 Corrosion Additions (Ch.3 Sec.3)")

material_family = st.sidebar.selectbox(
    "Material Family",
    ["Carbon-manganese steel", "Stainless steel", "Stainless clad steel", "Aluminium"]
)

member_kind = st.sidebar.selectbox(
    "Member Type for Corrosion Calculation",
    ["Compartment boundary", "Internal member", "Stiffener"]
)

compartment_1 = st.sidebar.selectbox(
    "Compartment / Exposure Side 1",
    [
        "Cargo oil / liquid chemicals tank",
        "Dry cargo hold - lower part",
        "Dry cargo hold - other members",
        "External surface",
        "Ballast / sea water tank",
        "Potable water / fuel oil / lube oil tank",
        "Brine / urea / bilge water / drain storage / chain locker tank",
        "Other tank",
        "Accommodation space",
        "Void / dry space - upper deck or bottom plate",
        "Void / dry space - elsewhere",
        "Stainless steel / aluminium independent of compartment"
    ]
)

compartment_2 = st.sidebar.selectbox(
    "Compartment / Exposure Side 2 (for boundaries)",
    [
        "Cargo oil / liquid chemicals tank",
        "Dry cargo hold - lower part",
        "Dry cargo hold - other members",
        "External surface",
        "Ballast / sea water tank",
        "Potable water / fuel oil / lube oil tank",
        "Brine / urea / bilge water / drain storage / chain locker tank",
        "Other tank",
        "Accommodation space",
        "Void / dry space - upper deck or bottom plate",
        "Void / dry space - elsewhere",
        "Stainless steel / aluminium independent of compartment"
    ]
)

grab_3x = st.sidebar.checkbox("Grab(3-X) notation for dry cargo hold lower part")
tc_max_override_mm = st.sidebar.number_input(
    "Optional tc max from Sec.3 [1.2.5] (mm, 0 = ignore)",
    min_value=0.0,
    value=0.0,
    step=0.1
)

# ---- Net scantling input using Sec.2 + Sec.3 ----
st.sidebar.subheader("📏 Net / Gross Thickness Check")

t_net_required = st.sidebar.number_input("Net required thickness t (mm)", min_value=0.0, value=10.0)
t_as_built = st.sidebar.number_input("As-built thickness tas_built (mm)", min_value=0.0, value=12.0)
t_vol_add = st.sidebar.number_input("Voluntary addition tvol_add (mm)", min_value=0.0, value=0.0)

# =========================================================
# CHAPTER 3 - SECTION 4 CORROSION PROTECTION
# =========================================================
st.sidebar.subheader("🛡️ Corrosion Protection (Ch.3 Sec.4)")

corrosive_tank_or_hold = st.sidebar.radio(
    "Tank / hold exposed to corrosive environment?",
    ["No", "Yes"]
)

pspc_vessel = st.sidebar.radio(
    "Vessel follows PSPC requirements?",
    ["No", "Yes"]
)

dedicated_seawater_ballast = st.sidebar.radio(
    "Dedicated seawater ballast tank?",
    ["No", "Yes"]
)

crude_oil_cargo_tank = st.sidebar.radio(
    "Cargo oil tank of crude oil carrier?",
    ["No", "Yes"]
)

narrow_space = st.sidebar.radio(
    "Narrow space present?",
    ["No", "Yes"]
)

efficient_protection_product = st.sidebar.radio(
    "Efficient protective product / prevention system provided?",
    ["No", "Yes"]
)

# =========================================================
# CHAPTER 3 - SECTION 5, 6, 7
# =========================================================
st.sidebar.subheader("🧩 Ch.3 Sec.5-7 Structural Design")

# Section 5
structural_continuity_ok = st.sidebar.radio(
    "Structural continuity provided?",
    ["Yes", "No"]
)

longitudinal_stiffeners_aligned = st.sidebar.radio(
    "Longitudinal stiffeners aligned / continuous?",
    ["Yes", "No"]
)

transverse_stiffeners_supported = st.sidebar.radio(
    "Transverse stiffeners properly supported?",
    ["Yes", "No"]
)

sheer_strake_continuity = st.sidebar.radio(
    "Sheer strake continuity satisfactory?",
    ["Yes", "No"]
)

stringer_plate_continuity = st.sidebar.radio(
    "Stringer plate continuity satisfactory?",
    ["Yes", "No"]
)

deckhouse_connection_good = st.sidebar.radio(
    "Deckhouse / superstructure connection satisfactory?",
    ["Yes", "No"]
)

# Section 6
tripping_brackets_fitted = st.sidebar.radio(
    "Tripping brackets fitted where required?",
    ["Yes", "No"]
)

face_plate_width = st.sidebar.number_input(
    "Face plate width bf (mm)",
    min_value=0.0,
    value=300.0
)

free_flange_outstand = st.sidebar.number_input(
    "Free flange outstand bf-out (mm)",
    min_value=0.0,
    value=120.0
)

tripping_bracket_height = st.sidebar.number_input(
    "Tripping bracket height h (m)",
    min_value=0.0,
    value=0.30
)

tripping_bracket_arm = st.sidebar.number_input(
    "Tripping bracket arm length d (m)",
    min_value=0.0,
    value=0.18
)

openings_in_stiffeners_ok = st.sidebar.radio(
    "Openings/scallops in stiffeners acceptable?",
    ["Yes", "No"]
)

openings_in_psm_ok = st.sidebar.radio(
    "Openings in primary supporting members acceptable?",
    ["Yes", "No"]
)

openings_in_shell_deck_ok = st.sidebar.radio(
    "Openings in decks/shell/longitudinal bulkheads acceptable?",
    ["Yes", "No"]
)

# Section 7
effective_span = st.sidebar.number_input(
    "Effective span l (mm)",
    min_value=0.0,
    value=2500.0
)

stiffener_spacing = st.sidebar.number_input(
    "Stiffener spacing s (mm)",
    min_value=0.0,
    value=700.0
)

attached_plate_b1 = st.sidebar.number_input(
    "Attached plating breadth b1 (mm)",
    min_value=0.0,
    value=350.0
)

attached_plate_b2 = st.sidebar.number_input(
    "Attached plating breadth b2 (mm)",
    min_value=0.0,
    value=350.0
)

web_thickness = st.sidebar.number_input(
    "Web thickness tw (mm)",
    min_value=0.0,
    value=10.0
)

flange_thickness = st.sidebar.number_input(
    "Flange thickness tf (mm)",
    min_value=0.0,
    value=12.0
)

hw = st.sidebar.number_input(
    "Web height hw (mm)",
    min_value=0.0,
    value=200.0
)

bf = st.sidebar.number_input(
    "Flange width bf (mm)",
    min_value=0.0,
    value=90.0
)

tp = st.sidebar.number_input(
    "Attached plate thickness tp (mm)",
    min_value=0.0,
    value=12.0
)

st.sidebar.divider()

# -----------------------------
# FUNCTIONS
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


def calculate_cb():
    denom = LLL * B * TLL
    return disp / denom if denom > 0 else 0.0


def calculate_cwf():
    denom = 0.5 * LLL * B
    return Awf / denom if denom > 0 else 0.0


def calculate_fb(CB, Cwf):
    if TLL <= 0:
        return 0.0
    x = LLL / 100
    return (6075 * x - 1875 * x**2 + 200 * x**3) * (
        2.08 + 0.609 * CB - 1.603 * Cwf - 0.0129 * (LLL / TLL)
    )


def calculate_xf():
    if bulbous_bow == "No":
        return 0.0
    return min(0.5 * xbe, 0.015 * LLL, 3.0)


def collision_limits(xf):
    if LLL < 200:
        xc_min = 0.05 * LLL - xf
    else:
        xc_min = 10 - xf

    if LLL < 100:
        xc_max = 0.05 * LLL + 3 - xf
    else:
        xc_max = 0.08 * LLL - xf

    return xc_min, xc_max


def double_bottom_height():
    h = 1000 * B / 20
    return min(max(h, 760), 2000)


# =========================================================
# SECTION 3 - CORROSION ADDITIONS
# =========================================================
TRES = 0.5


def tc_one_side(compartment_name: str, grab_3x_flag: bool) -> float:
    if compartment_name == "Cargo oil / liquid chemicals tank":
        return 1.0
    elif compartment_name == "Dry cargo hold - lower part":
        return 2.5 if grab_3x_flag else 1.0
    elif compartment_name == "Dry cargo hold - other members":
        return 0.5
    elif compartment_name == "External surface":
        return 0.5
    elif compartment_name == "Ballast / sea water tank":
        return 1.0
    elif compartment_name == "Potable water / fuel oil / lube oil tank":
        return 0.0
    elif compartment_name == "Brine / urea / bilge water / drain storage / chain locker tank":
        return 1.0
    elif compartment_name == "Other tank":
        return 0.5
    elif compartment_name == "Accommodation space":
        return 0.0
    elif compartment_name == "Void / dry space - upper deck or bottom plate":
        return 0.5
    elif compartment_name == "Void / dry space - elsewhere":
        return 0.0
    elif compartment_name == "Stainless steel / aluminium independent of compartment":
        return 0.0
    return 0.0


def total_corrosion_addition(material, member_type, comp1, comp2, grab_flag, tc_cap):
    tc1 = tc_one_side(comp1, grab_flag)
    tc2 = tc_one_side(comp2, grab_flag)

    if material in ["Stainless steel", "Aluminium"]:
        tc = TRES
        detail = "tc = tres"
    elif material == "Stainless clad steel":
        if member_type == "Internal member":
            tc = tc1 + TRES
            detail = "tc = tc1 + tres"
        else:
            tc = tc1 + 0.0 + TRES
            detail = "tc = tc1 + 0 + tres"
    else:
        if member_type in ["Internal member", "Stiffener"]:
            tc = 2.0 * tc1 + TRES
            detail = "tc = 2*tc1 + tres"
        else:
            tc = tc1 + tc2 + TRES
            detail = "tc = tc1 + tc2 + tres"

    if tc_cap > 0:
        tc = min(tc, tc_cap)
        detail += f" ; capped at {tc_cap:.2f} mm"

    return tc1, tc2, tc, detail


def round_to_nearest_half(x):
    return round(x * 2) / 2.0


def gross_required_thickness(t_net, tc):
    return round_to_nearest_half(t_net + tc)


def gross_offered_thickness(t_asbuilt, t_voluntary):
    return t_asbuilt - t_voluntary


def net_offered_thickness(tgr_off, tc):
    return tgr_off - tc


# =========================================================
# SECTION 4 - CORROSION PROTECTION
# =========================================================
def corrosion_protection_messages():
    msgs = []

    if corrosive_tank_or_hold == "Yes":
        if efficient_protection_product == "Yes":
            msgs.append(("success", "Efficient corrosion prevention system indicated for corrosive tank/hold."))
        else:
            msgs.append(("error", "Corrosive tank/hold requires an efficient corrosion prevention system."))

    if pspc_vessel == "Yes" and dedicated_seawater_ballast == "Yes":
        if efficient_protection_product == "Yes":
            msgs.append(("success", "Dedicated seawater ballast tank appears protected under PSPC requirement."))
        else:
            msgs.append(("error", "Dedicated seawater ballast tank requires PSPC-compliant corrosion prevention."))

    if pspc_vessel == "Yes" and crude_oil_cargo_tank == "Yes":
        if efficient_protection_product == "Yes":
            msgs.append(("success", "Crude-oil cargo tank appears protected under applicable corrosion prevention requirement."))
        else:
            msgs.append(("error", "Crude-oil cargo tank requires efficient corrosion prevention under the applicable PSPC regime."))

    if narrow_space == "Yes":
        if efficient_protection_product == "Yes":
            msgs.append(("success", "Narrow space protection indicated."))
        else:
            msgs.append(("warning", "Narrow spaces should generally be protected by an efficient protective product."))

    if not msgs:
        msgs.append(("info", "No specific corrosion protection trigger selected."))

    return msgs


# =========================================================
# SECTION 5 - STRUCTURAL ARRANGEMENT
# =========================================================
def section5_arrangement_messages():
    msgs = []

    if structural_continuity_ok == "Yes":
        msgs.append(("success", "Structural continuity indicated."))
    else:
        msgs.append(("error", "Structural continuity should be improved."))

    if longitudinal_stiffeners_aligned == "Yes":
        msgs.append(("success", "Longitudinal stiffeners appear continuous/aligned."))
    else:
        msgs.append(("warning", "Longitudinal stiffener discontinuity should be reviewed."))

    if transverse_stiffeners_supported == "Yes":
        msgs.append(("success", "Transverse stiffeners appear properly supported."))
    else:
        msgs.append(("warning", "Transverse stiffener support should be reviewed."))

    if sheer_strake_continuity == "Yes":
        msgs.append(("success", "Sheer strake continuity satisfactory."))
    else:
        msgs.append(("warning", "Sheer strake continuity requires attention."))

    if stringer_plate_continuity == "Yes":
        msgs.append(("success", "Stringer plate continuity satisfactory."))
    else:
        msgs.append(("warning", "Stringer plate continuity requires attention."))

    if deckhouse_connection_good == "Yes":
        msgs.append(("success", "Deckhouse/superstructure connection satisfactory."))
    else:
        msgs.append(("warning", "Deckhouse/superstructure connection should be reviewed for stress concentration."))

    return msgs


# =========================================================
# SECTION 6 - DETAIL DESIGN
# =========================================================
def min_tripping_bracket_arm(h):
    return 0.6 * h


def section6_detail_messages():
    msgs = []

    if tripping_brackets_fitted == "Yes":
        msgs.append(("success", "Tripping brackets fitted where required."))
    else:
        msgs.append(("warning", "Tripping brackets should be checked against required locations."))

    if face_plate_width > 400:
        msgs.append(("warning", "bf > 400 mm: backing brackets should be fitted in way of tripping bracket."))

    if free_flange_outstand > 180:
        msgs.append(("warning", "bf-out > 180 mm: flange outstand should be connected to tripping bracket or additional rib."))

    d_min = min_tripping_bracket_arm(tripping_bracket_height)
    if tripping_bracket_arm >= d_min:
        msgs.append(("success", f"Provided tripping bracket arm satisfies d ≥ {d_min:.3f} m"))
    else:
        msgs.append(("error", f"Provided tripping bracket arm is below d ≥ {d_min:.3f} m"))

    if openings_in_stiffeners_ok == "Yes":
        msgs.append(("success", "Openings/scallops in stiffeners marked acceptable."))
    else:
        msgs.append(("warning", "Openings/scallops in stiffeners should be reviewed."))

    if openings_in_psm_ok == "Yes":
        msgs.append(("success", "Openings in primary supporting members marked acceptable."))
    else:
        msgs.append(("warning", "Openings in primary supporting members should be reviewed."))

    if openings_in_shell_deck_ok == "Yes":
        msgs.append(("success", "Openings in decks/shell/longitudinal bulkheads marked acceptable."))
    else:
        msgs.append(("warning", "Openings in decks/shell/longitudinal bulkheads should be reviewed."))

    return msgs


# =========================================================
# SECTION 7 - STRUCTURAL IDEALIZATION
# =========================================================
def effective_breadth_simple(b1, b2, spacing):
    return min(b1 + b2, spacing)


def stiffener_area(hw, tw, bf, tf):
    return hw * tw + bf * tf


def attached_plate_area(beff, tp):
    return beff * tp


def total_stiffener_plus_plate_area(hw, tw, bf, tf, beff, tp):
    return stiffener_area(hw, tw, bf, tf) + attached_plate_area(beff, tp)


def section7_idealization_results():
    beff = effective_breadth_simple(attached_plate_b1, attached_plate_b2, stiffener_spacing)
    a_stf = stiffener_area(hw, web_thickness, bf, flange_thickness)
    a_plate = attached_plate_area(beff, tp)
    a_total = total_stiffener_plus_plate_area(hw, web_thickness, bf, flange_thickness, beff, tp)

    return {
        "beff": beff,
        "A_stiffener": a_stf,
        "A_plate": a_plate,
        "A_total": a_total
    }


# -----------------------------
# MAIN EXECUTION
# -----------------------------
if st.button("🚀 Run Full Calculation"):

    # ---------------- BULKHEADS ----------------
    st.header("🧱 Bulkhead Arrangement")

    res = min_bulkheads(L)
    if res:
        st.success(f"Aft: {res['aft']} | Elsewhere: {res['elsewhere']}")
    else:
        st.warning("Special consideration required.")

    st.divider()

    # ---------------- BOW HEIGHT ----------------
    st.header("🌊 Minimum Bow Height")

    CB = calculate_cb()
    Cwf = calculate_cwf()
    Fb = calculate_fb(CB, Cwf)

    c1, c2, c3 = st.columns(3)
    c1.metric("CB", f"{CB:.3f}")
    c2.metric("Cwf", f"{Cwf:.3f}")
    c3.metric("Required Fb (mm)", f"{Fb:.1f}")

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

    # ---------------- SECTION 3 CORROSION ADDITIONS ----------------
    st.header("🧪 Corrosion Additions (Chapter 3 Section 3)")

    tc1, tc2, tc_total, tc_detail = total_corrosion_addition(
        material=material_family,
        member_type=member_kind,
        comp1=compartment_1,
        comp2=compartment_2,
        grab_flag=grab_3x,
        tc_cap=tc_max_override_mm
    )

    d1, d2, d3, d4 = st.columns(4)
    d1.metric("tc1 (mm)", f"{tc1:.2f}")
    d2.metric("tc2 (mm)", f"{tc2:.2f}")
    d3.metric("tres (mm)", f"{TRES:.2f}")
    d4.metric("Total tc (mm)", f"{tc_total:.2f}")

    st.info(f"Applied rule logic: {tc_detail}")

    if member_kind == "Stiffener":
        st.write("✔️ Stiffener corrosion addition should follow the location of connection to attached plating.")
        st.write("✔️ If more than one corrosion value applies, use the largest value.")

    st.subheader("📏 Net / Gross Thickness Check with Corrosion Addition")

    tgr = gross_required_thickness(t_net_required, tc_total)
    tgr_off = gross_offered_thickness(t_as_built, t_vol_add)
    toff = net_offered_thickness(tgr_off, tc_total)

    g1, g2, g3 = st.columns(3)
    g1.metric("Gross required tgr (mm)", f"{tgr:.1f}")
    g2.metric("Gross offered tgr_off (mm)", f"{tgr_off:.1f}")
    g3.metric("Net offered toff (mm)", f"{toff:.1f}")

    if tgr_off >= tgr:
        st.success("Gross offered thickness satisfies rule check")
    else:
        st.error("Gross offered thickness does NOT satisfy rule check")

    if toff >= t_net_required:
        st.success("Net offered thickness satisfies net requirement")
    else:
        st.error("Net offered thickness does NOT satisfy net requirement")

    st.divider()

    # ---------------- SECTION 4 CORROSION PROTECTION ----------------
    st.header("🛡️ Corrosion Protection (Chapter 3 Section 4)")

    for level, msg in corrosion_protection_messages():
        if level == "success":
            st.success(msg)
        elif level == "error":
            st.error(msg)
        elif level == "warning":
            st.warning(msg)
        else:
            st.info(msg)

    st.divider()

    # ---------------- SECTION 5 ----------------
    st.header("🧩 Structural Arrangement (Ch.3 Sec.5)")

    for level, msg in section5_arrangement_messages():
        if level == "success":
            st.success(msg)
        elif level == "error":
            st.error(msg)
        else:
            st.warning(msg)

    st.info(
        "Section 5 is added as a rule-screening module for continuity, stiffener arrangement, and major structural connection quality."
    )

    st.divider()

    # ---------------- SECTION 6 ----------------
    st.header("🔧 Detail Design (Ch.3 Sec.6)")

    for level, msg in section6_detail_messages():
        if level == "success":
            st.success(msg)
        elif level == "error":
            st.error(msg)
        else:
            st.warning(msg)

    st.info(
        "Section 6 is added for practical checking of tripping brackets and openings."
    )

    st.divider()

    # ---------------- SECTION 7 ----------------
    st.header("📐 Structural Idealization (Ch.3 Sec.7)")

    ideal = section7_idealization_results()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Effective breadth beff (mm)", f"{ideal['beff']:.1f}")
    c2.metric("Stiffener area (mm²)", f"{ideal['A_stiffener']:.1f}")
    c3.metric("Attached plate area (mm²)", f"{ideal['A_plate']:.1f}")
    c4.metric("Total idealized area (mm²)", f"{ideal['A_total']:.1f}")

    st.info(
        "Section 7 is added as a simplified idealization helper for attached plate breadth and stiffener area."
    )

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

    # ---------------- FINAL NOTES ----------------
    st.subheader("📘 Final Notes")
    st.info("""
    - Chapter 2 logic is included for arrangement and subdivision checks.
    - Chapter 3 Sections 3, 4, 5, 6 and 7 are merged into this prototype.
    - Section 6 and 7 currently use simplified engineering logic for some checks.
    - Suitable for preliminary ship design and rule-screening only.
    """)

# -----------------------------
# FOOTER
# -----------------------------
st.caption("DNV-based ship design and compliance tool (advanced prototype)")
