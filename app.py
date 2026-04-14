import streamlit as st
import math
from dataclasses import dataclass, field
from typing import Optional
import pandas as pd

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="DNV Ship Design Tool",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "DNV-based ship design and compliance tool (advanced prototype)"}
)

# -----------------------------
# CONSTANTS
# -----------------------------
TRES = 0.5  # Residual corrosion addition (mm)

COMPARTMENT_OPTIONS = [
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
    "Stainless steel / aluminium independent of compartment",
]

TC_TABLE: dict[str, float] = {
    "Cargo oil / liquid chemicals tank":                          1.0,
    "Dry cargo hold - lower part (standard)":                    1.0,
    "Dry cargo hold - lower part (Grab 3-X)":                    2.5,
    "Dry cargo hold - other members":                            0.5,
    "External surface":                                          0.5,
    "Ballast / sea water tank":                                  1.0,
    "Potable water / fuel oil / lube oil tank":                  0.0,
    "Brine / urea / bilge water / drain storage / chain locker tank": 1.0,
    "Other tank":                                                0.5,
    "Accommodation space":                                       0.0,
    "Void / dry space - upper deck or bottom plate":             0.5,
    "Void / dry space - elsewhere":                              0.0,
    "Stainless steel / aluminium independent of compartment":    0.0,
}

# -----------------------------
# DATA CLASSES
# -----------------------------
@dataclass
class ShipInputs:
    L: float
    propulsion: str
    damage_stability: str
    second_deck: str
    draught_cond: str
    quarter_deck: str
    ship_type: str
    freeboard_to_ap: str

@dataclass
class BowInputs:
    LLL: float
    TLL: float
    B: float
    disp: float
    Awf: float
    actual_Fb: float

@dataclass
class CollisionInputs:
    bulbous_bow: str
    xbe: float
    openings_below_freeboard: str
    num_pipes: int
    long_superstructure: str

@dataclass
class CorrosionInputs:
    material_family: str
    member_kind: str
    compartment_1: str
    compartment_2: str
    grab_3x: bool
    tc_max_override_mm: float
    t_net_required: float
    t_as_built: float
    t_vol_add: float

@dataclass
class ProtectionInputs:
    corrosive_tank_or_hold: str
    pspc_vessel: str
    dedicated_seawater_ballast: str
    crude_oil_cargo_tank: str
    narrow_space: str
    efficient_protection_product: str

@dataclass
class StructuralInputs:
    # Section 5
    structural_continuity_ok: str
    longitudinal_stiffeners_aligned: str
    transverse_stiffeners_supported: str
    sheer_strake_continuity: str
    stringer_plate_continuity: str
    deckhouse_connection_good: str
    # Section 6
    tripping_brackets_fitted: str
    face_plate_width: float
    free_flange_outstand: float
    tripping_bracket_height: float
    tripping_bracket_arm: float
    openings_in_stiffeners_ok: str
    openings_in_psm_ok: str
    openings_in_shell_deck_ok: str
    # Section 7
    effective_span: float
    stiffener_spacing: float
    attached_plate_b1: float
    attached_plate_b2: float
    web_thickness: float
    flange_thickness: float
    hw: float
    bf: float
    tp: float

# -----------------------------
# CALCULATION FUNCTIONS
# -----------------------------

# --- Bulkheads ---
def min_bulkheads(L: float) -> Optional[dict]:
    thresholds = [
        (65,  3, 4),
        (85,  4, 4),
        (105, 4, 5),
        (125, 5, 6),
        (145, 6, 7),
        (165, 7, 8),
        (190, 8, 9),
        (225, 9, 10),
    ]
    for threshold, aft, elsewhere in thresholds:
        if L <= threshold:
            return {"aft": aft, "elsewhere": elsewhere}
    return None


# --- Bow Height ---
def calculate_cb(LLL: float, B: float, TLL: float, disp: float) -> float:
    denom = LLL * B * TLL
    return disp / denom if denom > 0 else 0.0


def calculate_cwf(LLL: float, B: float, Awf: float) -> float:
    denom = 0.5 * LLL * B
    return Awf / denom if denom > 0 else 0.0


def calculate_fb(LLL: float, TLL: float, CB: float, Cwf: float) -> float:
    if TLL <= 0:
        return 0.0
    x = LLL / 100
    return (
        (6075 * x - 1875 * x**2 + 200 * x**3)
        * (2.08 + 0.609 * CB - 1.603 * Cwf - 0.0129 * (LLL / TLL))
    )


# --- Collision Bulkhead ---
def calculate_xf(bulbous_bow: str, xbe: float, LLL: float) -> float:
    if bulbous_bow == "No":
        return 0.0
    return min(0.5 * xbe, 0.015 * LLL, 3.0)


def collision_limits(LLL: float, xf: float) -> tuple[float, float]:
    xc_min = (0.05 * LLL if LLL < 200 else 10.0) - xf
    xc_max = (0.05 * LLL + 3 if LLL < 100 else 0.08 * LLL) - xf
    return xc_min, xc_max


# --- Double Bottom ---
def double_bottom_height(B: float) -> float:
    h = 1000 * B / 20
    return min(max(h, 760), 2000)


# --- Corrosion Additions ---
def tc_one_side(compartment_name: str, grab_3x_flag: bool) -> float:
    if compartment_name == "Dry cargo hold - lower part":
        key = "Dry cargo hold - lower part (Grab 3-X)" if grab_3x_flag else "Dry cargo hold - lower part (standard)"
    else:
        key = compartment_name
    return TC_TABLE.get(key, 0.0)


def total_corrosion_addition(
    material: str,
    member_type: str,
    comp1: str,
    comp2: str,
    grab_flag: bool,
    tc_cap: float
) -> tuple[float, float, float, str]:

    tc1 = tc_one_side(comp1, grab_flag)
    tc2 = tc_one_side(comp2, grab_flag)

    if material in ["Stainless steel", "Aluminium"]:
        tc = TRES
        detail = "tc = t_res (stainless/aluminium)"
    elif material == "Stainless clad steel":
        tc = tc1 + TRES
        detail = "tc = tc1 + t_res (clad steel)"
    else:
        # Carbon-manganese steel
        if member_type in ["Internal member", "Stiffener"]:
            tc = 2.0 * tc1 + TRES
            detail = "tc = 2·tc1 + t_res (internal/stiffener)"
        else:
            tc = tc1 + tc2 + TRES
            detail = "tc = tc1 + tc2 + t_res (boundary)"

    if tc_cap > 0:
        if tc > tc_cap:
            detail += f" → capped at {tc_cap:.2f} mm"
            tc = tc_cap

    return tc1, tc2, tc, detail


def round_to_nearest_half(x: float) -> float:
    return round(x * 2) / 2.0


# --- Corrosion Protection ---
def corrosion_protection_messages(p: ProtectionInputs) -> list[tuple[str, str]]:
    msgs = []

    checks = [
        (
            p.corrosive_tank_or_hold == "Yes",
            p.efficient_protection_product == "Yes",
            "Corrosive tank/hold — efficient corrosion prevention system provided.",
            "Corrosive tank/hold requires an efficient corrosion prevention system.",
        ),
        (
            p.pspc_vessel == "Yes" and p.dedicated_seawater_ballast == "Yes",
            p.efficient_protection_product == "Yes",
            "Dedicated seawater ballast tank protected under PSPC.",
            "Dedicated seawater ballast tank requires PSPC-compliant protection.",
        ),
        (
            p.pspc_vessel == "Yes" and p.crude_oil_cargo_tank == "Yes",
            p.efficient_protection_product == "Yes",
            "Crude-oil cargo tank corrosion prevention indicated.",
            "Crude-oil cargo tank requires efficient corrosion prevention under applicable PSPC regime.",
        ),
        (
            p.narrow_space == "Yes",
            p.efficient_protection_product == "Yes",
            "Narrow space protection indicated.",
            "Narrow spaces should generally be protected by an efficient protective product.",
        ),
    ]

    for condition, passing, ok_msg, fail_msg in checks:
        if condition:
            msgs.append(("success" if passing else ("error" if "requires" in fail_msg else "warning"), ok_msg if passing else fail_msg))

    if not msgs:
        msgs.append(("info", "No specific corrosion protection triggers selected."))

    return msgs


# --- Section 5: Structural Arrangement ---
def section5_messages(s: StructuralInputs) -> list[tuple[str, str]]:
    checks = [
        (s.structural_continuity_ok,        "error",   "Structural continuity indicated.",             "Structural continuity insufficient — review required."),
        (s.longitudinal_stiffeners_aligned,  "warning", "Longitudinal stiffeners continuous/aligned.",  "Longitudinal stiffener discontinuity — review required."),
        (s.transverse_stiffeners_supported,  "warning", "Transverse stiffeners properly supported.",    "Transverse stiffener support — review required."),
        (s.sheer_strake_continuity,          "warning", "Sheer strake continuity satisfactory.",        "Sheer strake continuity requires attention."),
        (s.stringer_plate_continuity,        "warning", "Stringer plate continuity satisfactory.",      "Stringer plate continuity requires attention."),
        (s.deckhouse_connection_good,        "warning", "Deckhouse/superstructure connection satisfactory.", "Deckhouse/superstructure connection — review for stress concentration."),
    ]
    return [("success" if val == "Yes" else sev, ok if val == "Yes" else fail) for val, sev, ok, fail in checks]


# --- Section 6: Detail Design ---
def section6_messages(s: StructuralInputs) -> list[tuple[str, str]]:
    msgs = []

    msgs.append(
        ("success", "Tripping brackets fitted where required.")
        if s.tripping_brackets_fitted == "Yes"
        else ("warning", "Tripping bracket locations should be verified against rule requirements.")
    )

    if s.face_plate_width > 400:
        msgs.append(("warning", f"bf = {s.face_plate_width:.0f} mm > 400 mm — backing brackets required at tripping bracket locations."))

    if s.free_flange_outstand > 180:
        msgs.append(("warning", f"Outstand = {s.free_flange_outstand:.0f} mm > 180 mm — connect to tripping bracket or add rib plate."))

    d_min = 0.6 * s.tripping_bracket_height
    msgs.append(
        ("success", f"Tripping bracket arm d = {s.tripping_bracket_arm:.3f} m ≥ minimum {d_min:.3f} m ✓")
        if s.tripping_bracket_arm >= d_min
        else ("error", f"Tripping bracket arm d = {s.tripping_bracket_arm:.3f} m < minimum {d_min:.3f} m — non-compliant.")
    )

    for val, label in [
        (s.openings_in_stiffeners_ok, "Openings/scallops in stiffeners"),
        (s.openings_in_psm_ok, "Openings in primary supporting members"),
        (s.openings_in_shell_deck_ok, "Openings in decks/shell/longitudinal bulkheads"),
    ]:
        msgs.append(
            ("success", f"{label} — acceptable.")
            if val == "Yes"
            else ("warning", f"{label} — requires review.")
        )

    return msgs


# --- Section 7: Structural Idealization ---
def section7_results(s: StructuralInputs) -> dict:
    beff = min(s.attached_plate_b1 + s.attached_plate_b2, s.stiffener_spacing)
    A_web = s.hw * s.web_thickness
    A_flange = s.bf * s.flange_thickness
    A_stiffener = A_web + A_flange
    A_plate = beff * s.tp
    A_total = A_stiffener + A_plate

    # Neutral axis (from bottom of plate)
    y_web = s.tp + s.hw / 2
    y_flange = s.tp + s.hw + s.flange_thickness / 2
    y_plate = s.tp / 2

    y_na = (A_web * y_web + A_flange * y_flange + A_plate * y_plate) / A_total if A_total > 0 else 0

    # Second moment of area about neutral axis
    I_web = (s.web_thickness * s.hw**3) / 12 + A_web * (y_web - y_na)**2
    I_flange = (s.bf * s.flange_thickness**3) / 12 + A_flange * (y_flange - y_na)**2
    I_plate = (beff * s.tp**3) / 12 + A_plate * (y_plate - y_na)**2
    I_total = I_web + I_flange + I_plate

    y_top = s.tp + s.hw + s.flange_thickness - y_na
    y_bot = y_na
    Z_top = I_total / y_top if y_top > 0 else 0
    Z_bot = I_total / y_bot if y_bot > 0 else 0

    return {
        "beff_mm": beff,
        "A_stiffener_mm2": A_stiffener,
        "A_web_mm2": A_web,
        "A_flange_mm2": A_flange,
        "A_plate_mm2": A_plate,
        "A_total_mm2": A_total,
        "y_na_mm": y_na,
        "I_total_mm4": I_total,
        "Z_top_mm3": Z_top,
        "Z_bot_mm3": Z_bot,
    }


# --- Render helpers ---
def render_messages(msgs: list[tuple[str, str]]):
    for level, msg in msgs:
        getattr(st, level)(msg)


def compliance_badge(passed: bool) -> str:
    return "✅ PASS" if passed else "❌ FAIL"


# =============================================================
# SIDEBAR — INPUTS
# =============================================================

with st.sidebar:
    st.header("⚙️ Ship Inputs")

    with st.expander("📦 General", expanded=True):
        L    = st.number_input("Ship Length L (m)", 10.0, 400.0, 120.0)
        propulsion       = st.selectbox("Propulsion Type", ["Conventional", "Electric"])
        damage_stability = st.radio("Damage Stability Available?", ["No", "Yes"], horizontal=True)

    with st.expander("🏗️ Deck Configuration"):
        second_deck      = st.radio("Second Deck Below Freeboard?",       ["No", "Yes"], horizontal=True)
        draught_cond     = st.radio("Draught < Depth to Second Deck?",    ["No", "Yes"], horizontal=True)
        quarter_deck     = st.radio("Raised Quarter Deck?",               ["No", "Yes"], horizontal=True)
        ship_type        = st.selectbox("Ship Type", ["Cargo Ship", "Other"])
        freeboard_to_ap  = st.radio("Freeboard Deck Extends to AP?",      ["Yes", "No"], horizontal=True)

    with st.expander("🌊 Bow Height"):
        LLL       = st.number_input("Freeboard Length LLL (m)",             value=120.0)
        TLL       = st.number_input("Load Line Draught TLL (m)",            value=8.0)
        B         = st.number_input("Breadth B (m)",                        value=20.0)
        disp      = st.number_input("Displacement ∇ (m³)",                  value=15000.0)
        Awf       = st.number_input("Forward Waterplane Area Awf (m²)",     value=800.0)
        actual_Fb = st.number_input("Actual Bow Height Provided (mm)",      value=3000.0)

    with st.expander("🚢 Collision Bulkhead"):
        bulbous_bow              = st.radio("Bulbous Bow Present?",             ["No", "Yes"], horizontal=True)
        xbe                      = st.number_input("Bulb Extension xbe (m)",    value=5.0)
        openings_below_freeboard = st.radio("Openings below freeboard deck?",   ["No", "Yes"], horizontal=True)
        num_pipes                = st.number_input("Pipes through collision bulkhead", 0, 5, 0)
        long_superstructure      = st.radio("Forward superstructure ≥ 0.25L?",  ["No", "Yes"], horizontal=True)
        aft_space_usage          = st.selectbox("Aft Space Usage", ["Machinery", "Cargo/Passengers"])

    with st.expander("🧱 Double Bottom & Cofferdam"):
        double_bottom_fitted = st.radio("Double Bottom Fitted?",             ["Yes", "No"], horizontal=True)
        fuel_next_to_fw      = st.radio("Fuel tank adjacent to fresh water?", ["Yes", "No"], horizontal=True)

    with st.expander("🧪 Corrosion Additions (Ch.3 Sec.3)"):
        material_family  = st.selectbox("Material Family", ["Carbon-manganese steel", "Stainless steel", "Stainless clad steel", "Aluminium"])
        member_kind      = st.selectbox("Member Type", ["Compartment boundary", "Internal member", "Stiffener"])
        compartment_1    = st.selectbox("Exposure Side 1", COMPARTMENT_OPTIONS)
        compartment_2    = st.selectbox("Exposure Side 2 (boundary)", COMPARTMENT_OPTIONS)
        grab_3x          = st.checkbox("Grab(3-X) notation for dry cargo hold lower part")
        tc_max_override  = st.number_input("tc cap from Sec.3 [1.2.5] (mm, 0 = off)", min_value=0.0, value=0.0, step=0.1)

        st.markdown("**Net / Gross Thickness**")
        t_net_required = st.number_input("Net required thickness t (mm)",  min_value=0.0, value=10.0)
        t_as_built     = st.number_input("As-built thickness tas_built (mm)", min_value=0.0, value=12.0)
        t_vol_add      = st.number_input("Voluntary addition tvol (mm)",  min_value=0.0, value=0.0)

    with st.expander("🛡️ Corrosion Protection (Ch.3 Sec.4)"):
        corrosive_tank_or_hold       = st.radio("Tank/hold exposed to corrosive environment?", ["No", "Yes"], horizontal=True)
        pspc_vessel                  = st.radio("Vessel follows PSPC?",                          ["No", "Yes"], horizontal=True)
        dedicated_seawater_ballast   = st.radio("Dedicated seawater ballast tank?",              ["No", "Yes"], horizontal=True)
        crude_oil_cargo_tank         = st.radio("Cargo oil tank — crude oil carrier?",           ["No", "Yes"], horizontal=True)
        narrow_space                 = st.radio("Narrow space present?",                         ["No", "Yes"], horizontal=True)
        efficient_protection_product = st.radio("Efficient protective system provided?",         ["No", "Yes"], horizontal=True)

    with st.expander("🧩 Structural Arrangement (Ch.3 Sec.5)"):
        structural_continuity_ok         = st.radio("Structural continuity?",                ["Yes", "No"], horizontal=True)
        longitudinal_stiffeners_aligned  = st.radio("Longitudinal stiffeners aligned?",     ["Yes", "No"], horizontal=True)
        transverse_stiffeners_supported  = st.radio("Transverse stiffeners supported?",     ["Yes", "No"], horizontal=True)
        sheer_strake_continuity          = st.radio("Sheer strake continuity OK?",          ["Yes", "No"], horizontal=True)
        stringer_plate_continuity        = st.radio("Stringer plate continuity OK?",        ["Yes", "No"], horizontal=True)
        deckhouse_connection_good        = st.radio("Deckhouse connection OK?",             ["Yes", "No"], horizontal=True)

    with st.expander("🔧 Detail Design (Ch.3 Sec.6)"):
        tripping_brackets_fitted  = st.radio("Tripping brackets fitted?",              ["Yes", "No"], horizontal=True)
        face_plate_width          = st.number_input("Face plate width bf (mm)",        min_value=0.0, value=300.0)
        free_flange_outstand      = st.number_input("Free flange outstand bf-out (mm)",min_value=0.0, value=120.0)
        tripping_bracket_height   = st.number_input("Tripping bracket height h (m)",   min_value=0.0, value=0.30)
        tripping_bracket_arm      = st.number_input("Tripping bracket arm d (m)",      min_value=0.0, value=0.18)
        openings_in_stiffeners_ok = st.radio("Openings in stiffeners OK?",             ["Yes", "No"], horizontal=True)
        openings_in_psm_ok        = st.radio("Openings in PSM OK?",                   ["Yes", "No"], horizontal=True)
        openings_in_shell_deck_ok = st.radio("Openings in shell/deck/bulkheads OK?",  ["Yes", "No"], horizontal=True)

    with st.expander("📐 Structural Idealization (Ch.3 Sec.7)"):
        effective_span     = st.number_input("Effective span l (mm)",         min_value=0.0, value=2500.0)
        stiffener_spacing  = st.number_input("Stiffener spacing s (mm)",      min_value=0.0, value=700.0)
        attached_plate_b1  = st.number_input("Attached plating b1 (mm)",      min_value=0.0, value=350.0)
        attached_plate_b2  = st.number_input("Attached plating b2 (mm)",      min_value=0.0, value=350.0)
        web_thickness      = st.number_input("Web thickness tw (mm)",         min_value=0.0, value=10.0)
        flange_thickness   = st.number_input("Flange thickness tf (mm)",      min_value=0.0, value=12.0)
        hw_input           = st.number_input("Web height hw (mm)",            min_value=0.0, value=200.0)
        bf_input           = st.number_input("Flange width bf (mm)",          min_value=0.0, value=90.0)
        tp_input           = st.number_input("Attached plate thickness tp (mm)", min_value=0.0, value=12.0)

    run = st.button("🚀 Run Full Calculation", use_container_width=True, type="primary")

# =============================================================
# MAIN AREA — HEADER
# =============================================================

st.title("⚓ DNV-Based Ship Design Tool")
st.caption("Integrated Rule-Based Ship Arrangement, Corrosion and Compliance Tool · Preliminary design use only")
st.divider()

if not run:
    st.info("Configure inputs in the sidebar, then press **Run Full Calculation**.")
    st.stop()

# =============================================================
# ASSEMBLE DATA OBJECTS
# =============================================================

ship   = ShipInputs(L, propulsion, damage_stability, second_deck, draught_cond, quarter_deck, ship_type, freeboard_to_ap)
bow    = BowInputs(LLL, TLL, B, disp, Awf, actual_Fb)
coll   = CollisionInputs(bulbous_bow, xbe, openings_below_freeboard, num_pipes, long_superstructure)
corr   = CorrosionInputs(material_family, member_kind, compartment_1, compartment_2, grab_3x, tc_max_override, t_net_required, t_as_built, t_vol_add)
prot   = ProtectionInputs(corrosive_tank_or_hold, pspc_vessel, dedicated_seawater_ballast, crude_oil_cargo_tank, narrow_space, efficient_protection_product)
struct = StructuralInputs(
    structural_continuity_ok, longitudinal_stiffeners_aligned,
    transverse_stiffeners_supported, sheer_strake_continuity,
    stringer_plate_continuity, deckhouse_connection_good,
    tripping_brackets_fitted, face_plate_width, free_flange_outstand,
    tripping_bracket_height, tripping_bracket_arm,
    openings_in_stiffeners_ok, openings_in_psm_ok, openings_in_shell_deck_ok,
    effective_span, stiffener_spacing, attached_plate_b1, attached_plate_b2,
    web_thickness, flange_thickness, hw_input, bf_input, tp_input
)

# =============================================================
# RUN CALCULATIONS UP FRONT
# =============================================================

# Bulkheads
bulkhead_res = min_bulkheads(ship.L)

# Bow height
CB  = calculate_cb(bow.LLL, bow.B, bow.TLL, bow.disp)
Cwf = calculate_cwf(bow.LLL, bow.B, bow.Awf)
Fb  = calculate_fb(bow.LLL, bow.TLL, CB, Cwf)
bow_compliant = bow.actual_Fb >= Fb

# Collision bulkhead
xf = calculate_xf(coll.bulbous_bow, coll.xbe, bow.LLL)
xc_min, xc_max = collision_limits(bow.LLL, xf)

# Double bottom
hdb = double_bottom_height(bow.B)

# Corrosion additions
tc1, tc2, tc_total, tc_detail = total_corrosion_addition(
    corr.material_family, corr.member_kind,
    corr.compartment_1, corr.compartment_2,
    corr.grab_3x, corr.tc_max_override_mm
)
tgr     = round_to_nearest_half(corr.t_net_required + tc_total)
tgr_off = corr.t_as_built - corr.t_vol_add
toff    = tgr_off - tc_total
gross_ok = tgr_off >= tgr
net_ok   = toff >= corr.t_net_required

# Section 7
ideal = section7_results(struct)

# =============================================================
# SUMMARY SCORECARD
# =============================================================

st.header("📊 Compliance Summary")

# Build a quick pass/fail table
summary_rows = [
    ("Bulkhead count",          bulkhead_res is not None or L > 225),
    ("Bow height",              bow_compliant),
    ("Collision bulkhead — openings", coll.openings_below_freeboard == "No"),
    ("Collision bulkhead — pipes",    coll.num_pipes <= 1),
    ("Cofferdam",               fuel_next_to_fw == "No"),
    ("Gross thickness",         gross_ok),
    ("Net thickness",           net_ok),
    ("Structural continuity",   struct.structural_continuity_ok == "Yes"),
    ("Tripping bracket arm",    struct.tripping_bracket_arm >= 0.6 * struct.tripping_bracket_height),
]

pass_count = sum(1 for _, v in summary_rows if v)
fail_count = len(summary_rows) - pass_count

col_a, col_b, col_c = st.columns(3)
col_a.metric("Total Checks", len(summary_rows))
col_b.metric("✅ Passing", pass_count)
col_c.metric("❌ Failing", fail_count, delta=f"-{fail_count}" if fail_count else "0", delta_color="inverse")

summary_df = pd.DataFrame(
    [{"Check": name, "Result": "✅ PASS" if passed else "❌ FAIL"} for name, passed in summary_rows]
)
st.dataframe(summary_df, use_container_width=True, hide_index=True)

st.divider()

# =============================================================
# DETAILED RESULTS — TABS
# =============================================================

tabs = st.tabs([
    "🧱 Arrangement",
    "🌊 Bow & Collision",
    "🧪 Corrosion",
    "🛡️ Protection",
    "🧩 Structure Sec.5",
    "🔧 Detail Sec.6",
    "📐 Idealization Sec.7",
    "📘 Notes",
])

# ─── TAB 0: ARRANGEMENT ───────────────────────────────────────
with tabs[0]:
    st.subheader("🧱 Bulkhead Arrangement")

    if bulkhead_res:
        c1, c2 = st.columns(2)
        c1.metric("Min. Bulkheads — Aft region",       bulkhead_res["aft"])
        c2.metric("Min. Bulkheads — Elsewhere",         bulkhead_res["elsewhere"])
        st.success("Bulkhead table lookup successful.")
    else:
        st.warning("L > 225 m — special consideration required per rule table.")

    st.divider()
    st.subheader("🛢️ Cofferdam")

    if fuel_next_to_fw == "Yes":
        st.error("Cofferdam REQUIRED between fuel oil and fresh water tanks.")
    else:
        st.success("No cofferdam required — fuel and fresh water tanks not adjacent.")

    st.divider()
    st.subheader("🧱 Double Bottom")

    if double_bottom_fitted == "Yes":
        st.metric("Minimum Height (mm)", f"{hdb:.0f}")
        st.success("Double bottom provided.")
    else:
        st.warning("Double bottom not fitted — damage stability justification must be provided.")

    st.divider()
    st.subheader("🚢 Compartment Rules")

    rules = [
        "No fuel oil in compartments forward of the collision bulkhead.",
        "Stern tube must be enclosed in a watertight space.",
        "Shaft tunnel required when engine room is located amidships.",
        "Steering gear compartment must be separated and remain accessible.",
    ]
    for r in rules:
        st.write(f"• {r}")

    st.divider()
    st.subheader("🚪 Access Requirements")

    access = [
        "All tanks must be accessible for inspection.",
        "Double bottom must be fitted with manholes.",
        "Closed spaces must be accessible or specially approved.",
    ]
    for a in access:
        st.write(f"• {a}")


# ─── TAB 1: BOW & COLLISION ───────────────────────────────────
with tabs[1]:
    st.subheader("🌊 Minimum Bow Height")

    c1, c2, c3 = st.columns(3)
    c1.metric("CB (block coefficient)", f"{CB:.4f}")
    c2.metric("Cwf (waterplane coeff.)", f"{Cwf:.4f}")
    c3.metric("Required Fb (mm)", f"{Fb:.1f}")

    c4, c5 = st.columns(2)
    c4.metric("Actual Bow Height (mm)", f"{bow.actual_Fb:.1f}")
    c5.metric("Margin (mm)", f"{bow.actual_Fb - Fb:+.1f}")

    if bow_compliant:
        st.success(f"Bow height compliant — actual {bow.actual_Fb:.0f} mm ≥ required {Fb:.0f} mm.")
    else:
        st.error(f"Bow height NON-COMPLIANT — shortfall of {Fb - bow.actual_Fb:.0f} mm.")

    st.divider()
    st.subheader("🚢 Collision Bulkhead Position")

    cb1, cb2 = st.columns(2)
    cb1.metric("xc_min (m)", f"{xc_min:.3f}")
    cb2.metric("xc_max (m)", f"{xc_max:.3f}")

    if xf > 0:
        st.info(f"Bulbous bow credit xf = {xf:.3f} m applied.")

    if coll.openings_below_freeboard == "Yes":
        st.error("Openings below freeboard deck — NOT permitted through or below the collision bulkhead.")
    else:
        st.success("No openings below freeboard deck.")

    if coll.num_pipes > 1:
        st.error(f"{coll.num_pipes} pipes through collision bulkhead — maximum 1 pipe permitted.")
    elif coll.num_pipes == 1:
        st.warning("1 pipe through collision bulkhead — must be fitted with a screw-down valve operable from above the freeboard deck.")
    else:
        st.success("No pipes through collision bulkhead.")

    if coll.long_superstructure == "Yes":
        st.info("Forward superstructure ≥ 0.25L — collision bulkhead must extend weathertight to the next deck.")

    st.divider()
    st.subheader("⚓ Aft Peak Bulkhead")

    st.write("• Must enclose the stern tube and rudder trunk.")
    if aft_space_usage == "Machinery":
        st.info("Aft machinery space — termination above the deepest draught is permitted.")
    else:
        st.write("• Aft space used for cargo/passengers — verify full height enclosure.")


# ─── TAB 2: CORROSION ADDITIONS ───────────────────────────────
with tabs[2]:
    st.subheader("🧪 Corrosion Additions (Ch.3 Sec.3)")

    d1, d2, d3, d4 = st.columns(4)
    d1.metric("tc₁ (mm)", f"{tc1:.2f}")
    d2.metric("tc₂ (mm)", f"{tc2:.2f}")
    d3.metric("t_res (mm)", f"{TRES:.2f}")
    d4.metric("Total tc (mm)", f"{tc_total:.2f}")

    st.info(f"Rule logic: {tc_detail}")

    if corr.member_kind == "Stiffener":
        st.write("• Stiffener tc follows the location of connection to attached plating.")
        st.write("• Where more than one corrosion value applies, use the largest.")

    st.divider()
    st.subheader("📏 Net / Gross Thickness Check")

    g1, g2, g3, g4 = st.columns(4)
    g1.metric("Net required t (mm)",      f"{corr.t_net_required:.2f}")
    g2.metric("Gross required tgr (mm)",  f"{tgr:.1f}")
    g3.metric("Gross offered tgr_off (mm)", f"{tgr_off:.1f}")
    g4.metric("Net offered toff (mm)",    f"{toff:.1f}")

    # Visual margin bars
    gross_margin = tgr_off - tgr
    net_margin   = toff - corr.t_net_required

    r1, r2 = st.columns(2)
    with r1:
        if gross_ok:
            st.success(f"Gross thickness OK — margin: +{gross_margin:.2f} mm")
        else:
            st.error(f"Gross thickness FAILS — shortfall: {gross_margin:.2f} mm")
    with r2:
        if net_ok:
            st.success(f"Net thickness OK — margin: +{net_margin:.2f} mm")
        else:
            st.error(f"Net thickness FAILS — shortfall: {net_margin:.2f} mm")

    # Breakdown table
    st.markdown("**Thickness Breakdown**")
    breakdown = pd.DataFrame({
        "Parameter":  ["t_net required", "tc total", "Gross required (tgr)", "As-built (t_as-built)", "Voluntary addition (tvol)", "Gross offered (tgr_off)", "Net offered (toff)"],
        "Value (mm)": [corr.t_net_required, tc_total, tgr, corr.t_as_built, corr.t_vol_add, tgr_off, toff],
    })
    st.dataframe(breakdown, use_container_width=True, hide_index=True)


# ─── TAB 3: CORROSION PROTECTION ──────────────────────────────
with tabs[3]:
    st.subheader("🛡️ Corrosion Protection (Ch.3 Sec.4)")
    render_messages(corrosion_protection_messages(prot))


# ─── TAB 4: STRUCTURAL ARRANGEMENT ────────────────────────────
with tabs[4]:
    st.subheader("🧩 Structural Arrangement (Ch.3 Sec.5)")
    render_messages(section5_messages(struct))
    st.caption("Rule-screening module for continuity, stiffener arrangement and major structural connections.")


# ─── TAB 5: DETAIL DESIGN ─────────────────────────────────────
with tabs[5]:
    st.subheader("🔧 Detail Design (Ch.3 Sec.6)")
    render_messages(section6_messages(struct))
    st.caption("Simplified checks for tripping brackets and openings.")


# ─── TAB 6: STRUCTURAL IDEALIZATION ───────────────────────────
with tabs[6]:
    st.subheader("📐 Structural Idealization (Ch.3 Sec.7)")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Effective breadth beff (mm)",  f"{ideal['beff_mm']:.1f}")
    c2.metric("A_stiffener (mm²)",            f"{ideal['A_stiffener_mm2']:.1f}")
    c3.metric("A_plate (mm²)",                f"{ideal['A_plate_mm2']:.1f}")
    c4.metric("A_total (mm²)",                f"{ideal['A_total_mm2']:.1f}")

    st.divider()

    e1, e2, e3, e4 = st.columns(4)
    e1.metric("A_web (mm²)",              f"{ideal['A_web_mm2']:.1f}")
    e2.metric("A_flange (mm²)",           f"{ideal['A_flange_mm2']:.1f}")
    e3.metric("Neutral axis y_NA (mm)",   f"{ideal['y_na_mm']:.2f}")
    e4.metric("I_total (mm⁴)",            f"{ideal['I_total_mm4']:.1f}")

    s1, s2 = st.columns(2)
    s1.metric("Z_top (mm³)", f"{ideal['Z_top_mm3']:.1f}")
    s2.metric("Z_bot (mm³)", f"{ideal['Z_bot_mm3']:.1f}")

    st.caption(
        "Neutral axis measured from bottom of attached plate. "
        "Z_top = section modulus to top fibre (flange), Z_bot = to bottom fibre (plate underside). "
        "Effective breadth uses simple min(b1+b2, s) rule — shear lag not applied."
    )

    # Cross-section summary table
    st.markdown("**Section Property Summary**")
    props = pd.DataFrame({
        "Property": list(ideal.keys()),
        "Value": [f"{v:.2f}" for v in ideal.values()],
    })
    st.dataframe(props, use_container_width=True, hide_index=True)


# ─── TAB 7: NOTES ─────────────────────────────────────────────
with tabs[7]:
    st.subheader("📘 Scope & Limitations")

    st.markdown("""
    **Scope**

    | Chapter | Section | Topic |
    |---------|---------|-------|
    | Ch.2 | — | Arrangement & subdivision |
    | Ch.3 | Sec.3 | Corrosion additions |
    | Ch.3 | Sec.4 | Corrosion protection |
    | Ch.3 | Sec.5 | Structural arrangement |
    | Ch.3 | Sec.6 | Detail design |
    | Ch.3 | Sec.7 | Structural idealization |

    **Known Simplifications**
    - Bow height formula uses DNV simplified expression; slamming loads not computed.
    - Effective breadth uses simple $$b_{eff} = \\min(b_1+b_2,\\,s)$$ — shear lag effects not modelled.
    - Section modulus assumes uniform rectangular web and flange; no fillet welds modelled.
    - Tripping bracket arm check uses rule-of-thumb $$d \\geq 0.6h$$.
    - Corrosion addition rule logic covers the main material/member/compartment matrix; specialist notations beyond Grab(3-X) are not included.
    - No wave loads, fatigue, or buckling checks are performed.

    **Intended Use**

    Preliminary design screening and rule orientation only. Results must be verified
    against the current DNV Rules for Ships before submission or fabrication.
    """)

# =============================================================
# FOOTER
# =============================================================

st.divider()
st.caption("DNV-based ship design and compliance tool · Advanced prototype · For preliminary design use only")
