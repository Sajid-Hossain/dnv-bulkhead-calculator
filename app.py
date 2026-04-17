from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="DNV Ship Design Tool",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "DNV-based ship design and compliance tool (advanced prototype)"},
)


TRES = 0.5
YES_NO = ("Yes", "No")
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
SERVICE_RESTRICTIONS = ["Unrestricted", "R2", "R3", "R4", "RE"]
ENGINE_ROOM_LOCATIONS = ["Aft", "Amidships", "Forward / other"]

TC_TABLE: dict[str, float] = {
    "Cargo oil / liquid chemicals tank": 1.0,
    "Dry cargo hold - lower part (standard)": 1.0,
    "Dry cargo hold - lower part (Grab 3-X)": 2.5,
    "Dry cargo hold - other members": 0.5,
    "External surface": 0.5,
    "Ballast / sea water tank": 1.0,
    "Potable water / fuel oil / lube oil tank": 0.0,
    "Brine / urea / bilge water / drain storage / chain locker tank": 1.0,
    "Other tank": 0.5,
    "Accommodation space": 0.0,
    "Void / dry space - upper deck or bottom plate": 0.5,
    "Void / dry space - elsewhere": 0.0,
    "Stainless steel / aluminium independent of compartment": 0.0,
}


@dataclass
class ArrangementInputs:
    L: float
    propulsion: str
    damage_stability: str
    second_deck: str
    draught_cond: str
    quarter_deck: str
    ship_type: str
    freeboard_to_ap: str
    engine_room_location: str
    service_restriction: str
    aft_space_usage: str
    double_bottom_fitted: str
    fuel_next_to_fw: str


@dataclass
class BowInputs:
    LLL: float
    TLL: float
    B: float
    displacement: float
    Awf: float
    actual_fb: float


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
    structural_continuity_ok: str
    longitudinal_stiffeners_aligned: str
    transverse_stiffeners_supported: str
    sheer_strake_continuity: str
    stringer_plate_continuity: str
    deckhouse_connection_good: str
    tripping_brackets_fitted: str
    face_plate_width: float
    free_flange_outstand: float
    tripping_bracket_height: float
    tripping_bracket_arm: float
    openings_in_stiffeners_ok: str
    openings_in_psm_ok: str
    openings_in_shell_deck_ok: str
    effective_span: float
    stiffener_spacing: float
    attached_plate_b1: float
    attached_plate_b2: float
    web_thickness: float
    flange_thickness: float
    hw: float
    bf: float
    tp: float


@dataclass
class AppInputs:
    arrangement: ArrangementInputs
    bow: BowInputs
    collision: CollisionInputs
    corrosion: CorrosionInputs
    protection: ProtectionInputs
    structural: StructuralInputs


@dataclass
class BulkheadScreening:
    applicable: bool
    special_consideration: bool
    min_aft_region: int | None
    min_elsewhere: int | None
    note: str


@dataclass
class BowHeightResult:
    cb: float
    cwf: float
    required_fb: float
    actual_fb: float
    margin: float
    compliant: bool


@dataclass
class CollisionResult:
    xf: float
    xc_min: float
    xc_max: float
    openings_ok: bool
    pipes_ok: bool
    single_pipe_requires_valve: bool
    superstructure_extension_required: bool


@dataclass
class CorrosionResult:
    tc1: float
    tc2: float
    tc_total: float
    detail: str
    gross_required: float
    gross_offered: float
    net_offered: float
    gross_margin: float
    net_margin: float
    gross_ok: bool
    net_ok: bool


@dataclass
class DetailDesignResult:
    bracket_arm_min: float
    bracket_arm_ok: bool
    face_plate_brackets_required: bool
    free_flange_support_required: bool


@dataclass
class IdealizationResult:
    beff_mm: float
    a_stiffener_mm2: float
    a_web_mm2: float
    a_flange_mm2: float
    a_plate_mm2: float
    a_total_mm2: float
    y_na_mm: float
    i_total_mm4: float
    z_top_mm3: float
    z_bot_mm3: float


@dataclass
class AppResults:
    bulkheads: BulkheadScreening
    bow: BowHeightResult
    collision: CollisionResult
    corrosion: CorrosionResult
    detail: DetailDesignResult
    idealization: IdealizationResult
    double_bottom_height_mm: float


def yes_no_index(default: str) -> int:
    return 0 if default == "Yes" else 1


def yes_no_radio(label: str, default: str = "No") -> str:
    return st.radio(label, YES_NO, index=yes_no_index(default), horizontal=True)


def render_messages(messages: list[tuple[str, str]]) -> None:
    for level, message in messages:
        if level == "success":
            st.success(message)
        elif level == "warning":
            st.warning(message)
        elif level == "error":
            st.error(message)
        else:
            st.info(message)


def min_bulkheads_lookup(length_m: float) -> tuple[int, int] | None:
    thresholds = [
        (65.0, 3, 4),
        (85.0, 4, 4),
        (105.0, 4, 5),
        (125.0, 5, 6),
        (145.0, 6, 7),
        (165.0, 7, 8),
        (190.0, 8, 9),
        (225.0, 9, 10),
    ]
    for threshold, aft_region, elsewhere in thresholds:
        if length_m <= threshold:
            return aft_region, elsewhere
    return None


def calculate_cb(length_m: float, breadth_m: float, draught_m: float, displacement_m3: float) -> float:
    denominator = length_m * breadth_m * draught_m
    return displacement_m3 / denominator if denominator > 0 else 0.0


def calculate_cwf(length_m: float, breadth_m: float, awf_m2: float) -> float:
    denominator = 0.5 * length_m * breadth_m
    return awf_m2 / denominator if denominator > 0 else 0.0


def calculate_fb(length_m: float, draught_m: float, cb: float, cwf: float) -> float:
    if draught_m <= 0:
        return 0.0
    scaled_length = length_m / 100.0
    return (
        (6075.0 * scaled_length - 1875.0 * scaled_length**2 + 200.0 * scaled_length**3)
        * (2.08 + 0.609 * cb - 1.603 * cwf - 0.0129 * (length_m / draught_m))
    )


def calculate_xf(bulbous_bow: str, xbe_m: float, length_m: float) -> float:
    if bulbous_bow == "No":
        return 0.0
    return min(0.5 * xbe_m, 0.015 * length_m, 3.0)


def collision_limits(length_m: float, xf_m: float) -> tuple[float, float]:
    xc_min = (0.05 * length_m if length_m < 200.0 else 10.0) - xf_m
    xc_max = (0.05 * length_m + 3.0 if length_m < 100.0 else 0.08 * length_m) - xf_m
    return xc_min, xc_max


def double_bottom_height(breadth_m: float) -> float:
    height_mm = 1000.0 * breadth_m / 20.0
    return min(max(height_mm, 760.0), 2000.0)


def tc_one_side(compartment_name: str, grab_3x: bool) -> float:
    if compartment_name == "Dry cargo hold - lower part":
        key = "Dry cargo hold - lower part (Grab 3-X)" if grab_3x else "Dry cargo hold - lower part (standard)"
    else:
        key = compartment_name
    return TC_TABLE.get(key, 0.0)


def total_corrosion_addition(inputs: CorrosionInputs) -> tuple[float, float, float, str]:
    tc1 = tc_one_side(inputs.compartment_1, inputs.grab_3x)
    tc2 = tc_one_side(inputs.compartment_2, inputs.grab_3x)

    if inputs.material_family in {"Stainless steel", "Aluminium"}:
        tc_total = TRES
        detail = "tc = t_res (stainless steel / aluminium)"
    elif inputs.material_family == "Stainless clad steel":
        tc_total = tc1 + TRES
        detail = "tc = tc1 + t_res (stainless clad steel)"
    else:
        if inputs.member_kind in {"Internal member", "Stiffener"}:
            tc_total = 2.0 * tc1 + TRES
            detail = "tc = 2*tc1 + t_res (internal member / stiffener)"
        else:
            tc_total = tc1 + tc2 + TRES
            detail = "tc = tc1 + tc2 + t_res (compartment boundary)"

    if inputs.tc_max_override_mm > 0 and tc_total > inputs.tc_max_override_mm:
        detail += f" -> capped at {inputs.tc_max_override_mm:.2f} mm"
        tc_total = inputs.tc_max_override_mm

    return tc1, tc2, tc_total, detail


def round_to_nearest_half(value: float) -> float:
    return round(value * 2.0) / 2.0


def corrosion_protection_messages(inputs: ProtectionInputs) -> list[tuple[str, str]]:
    messages: list[tuple[str, str]] = []

    checks = [
        (
            inputs.corrosive_tank_or_hold == "Yes",
            inputs.efficient_protection_product == "Yes",
            "Corrosive tank/hold: efficient corrosion prevention system indicated.",
            "Corrosive tank/hold requires an efficient corrosion prevention system.",
            "error",
        ),
        (
            inputs.pspc_vessel == "Yes" and inputs.dedicated_seawater_ballast == "Yes",
            inputs.efficient_protection_product == "Yes",
            "Dedicated seawater ballast tank: protection indicated for PSPC scope.",
            "Dedicated seawater ballast tank requires PSPC-compliant protection.",
            "error",
        ),
        (
            inputs.pspc_vessel == "Yes" and inputs.crude_oil_cargo_tank == "Yes",
            inputs.efficient_protection_product == "Yes",
            "Crude oil cargo tank: corrosion prevention indicated.",
            "Crude oil cargo tank requires efficient corrosion prevention under the applicable PSPC regime.",
            "error",
        ),
        (
            inputs.narrow_space == "Yes",
            inputs.efficient_protection_product == "Yes",
            "Narrow space: protection indicated.",
            "Narrow spaces should generally be protected by an efficient protective product.",
            "warning",
        ),
    ]

    for condition, is_ok, ok_message, fail_message, fail_level in checks:
        if condition:
            messages.append(("success", ok_message) if is_ok else (fail_level, fail_message))

    if not messages:
        messages.append(("info", "No specific corrosion protection triggers were selected."))

    return messages


def section5_messages(inputs: StructuralInputs) -> list[tuple[str, str]]:
    checks = [
        (
            inputs.structural_continuity_ok,
            "Structural continuity indicated.",
            "Structural continuity is not satisfactory; review required.",
            "error",
        ),
        (
            inputs.longitudinal_stiffeners_aligned,
            "Longitudinal stiffeners are continuous/aligned.",
            "Longitudinal stiffener discontinuity requires review.",
            "warning",
        ),
        (
            inputs.transverse_stiffeners_supported,
            "Transverse stiffeners are properly supported.",
            "Transverse stiffener support requires review.",
            "warning",
        ),
        (
            inputs.sheer_strake_continuity,
            "Sheer strake continuity is satisfactory.",
            "Sheer strake continuity requires attention.",
            "warning",
        ),
        (
            inputs.stringer_plate_continuity,
            "Stringer plate continuity is satisfactory.",
            "Stringer plate continuity requires attention.",
            "warning",
        ),
        (
            inputs.deckhouse_connection_good,
            "Deckhouse/superstructure connection is satisfactory.",
            "Deckhouse/superstructure connection should be reviewed for stress concentration.",
            "warning",
        ),
    ]

    messages: list[tuple[str, str]] = []
    for value, ok_message, fail_message, fail_level in checks:
        messages.append(("success", ok_message) if value == "Yes" else (fail_level, fail_message))
    return messages


def evaluate_detail_design(inputs: StructuralInputs) -> DetailDesignResult:
    return DetailDesignResult(
        bracket_arm_min=0.6 * inputs.tripping_bracket_height,
        bracket_arm_ok=inputs.tripping_bracket_arm >= 0.6 * inputs.tripping_bracket_height,
        face_plate_brackets_required=inputs.face_plate_width > 400.0,
        free_flange_support_required=inputs.free_flange_outstand > 180.0,
    )


def section6_messages(inputs: StructuralInputs, result: DetailDesignResult) -> list[tuple[str, str]]:
    messages: list[tuple[str, str]] = []

    messages.append(
        ("success", "Tripping brackets fitted where required.")
        if inputs.tripping_brackets_fitted == "Yes"
        else ("warning", "Tripping bracket locations should be verified against rule requirements.")
    )

    if result.face_plate_brackets_required:
        messages.append(
            ("warning", f"Face plate width = {inputs.face_plate_width:.0f} mm > 400 mm; backing brackets are required at tripping bracket locations.")
        )

    if result.free_flange_support_required:
        messages.append(
            ("warning", f"Free flange outstand = {inputs.free_flange_outstand:.0f} mm > 180 mm; connect to a tripping bracket or add a rib plate.")
        )

    messages.append(
        ("success", f"Tripping bracket arm d = {inputs.tripping_bracket_arm:.3f} m >= minimum {result.bracket_arm_min:.3f} m.")
        if result.bracket_arm_ok
        else ("error", f"Tripping bracket arm d = {inputs.tripping_bracket_arm:.3f} m < minimum {result.bracket_arm_min:.3f} m.")
    )

    for value, label in [
        (inputs.openings_in_stiffeners_ok, "Openings/scallops in stiffeners"),
        (inputs.openings_in_psm_ok, "Openings in primary supporting members"),
        (inputs.openings_in_shell_deck_ok, "Openings in shell/deck/longitudinal bulkheads"),
    ]:
        messages.append(
            ("success", f"{label}: acceptable.")
            if value == "Yes"
            else ("warning", f"{label}: review required.")
        )

    return messages


def section7_results(inputs: StructuralInputs) -> IdealizationResult:
    beff = min(inputs.attached_plate_b1 + inputs.attached_plate_b2, inputs.stiffener_spacing)
    a_web = inputs.hw * inputs.web_thickness
    a_flange = inputs.bf * inputs.flange_thickness
    a_stiffener = a_web + a_flange
    a_plate = beff * inputs.tp
    a_total = a_stiffener + a_plate

    y_web = inputs.tp + inputs.hw / 2.0
    y_flange = inputs.tp + inputs.hw + inputs.flange_thickness / 2.0
    y_plate = inputs.tp / 2.0

    y_na = 0.0
    if a_total > 0:
        y_na = (a_web * y_web + a_flange * y_flange + a_plate * y_plate) / a_total

    i_web = (inputs.web_thickness * inputs.hw**3) / 12.0 + a_web * (y_web - y_na) ** 2
    i_flange = (inputs.bf * inputs.flange_thickness**3) / 12.0 + a_flange * (y_flange - y_na) ** 2
    i_plate = (beff * inputs.tp**3) / 12.0 + a_plate * (y_plate - y_na) ** 2
    i_total = i_web + i_flange + i_plate

    y_top = inputs.tp + inputs.hw + inputs.flange_thickness - y_na
    y_bot = y_na
    z_top = i_total / y_top if y_top > 0 else 0.0
    z_bot = i_total / y_bot if y_bot > 0 else 0.0

    return IdealizationResult(
        beff_mm=beff,
        a_stiffener_mm2=a_stiffener,
        a_web_mm2=a_web,
        a_flange_mm2=a_flange,
        a_plate_mm2=a_plate,
        a_total_mm2=a_total,
        y_na_mm=y_na,
        i_total_mm4=i_total,
        z_top_mm3=z_top,
        z_bot_mm3=z_bot,
    )


def build_sidebar_inputs() -> tuple[AppInputs, bool]:
    with st.sidebar:
        st.header("Ship Inputs")

        with st.form("dnv_ship_inputs"):
            with st.expander("General", expanded=True):
                L = st.number_input("Ship length L (m)", min_value=10.0, max_value=400.0, value=120.0)
                propulsion = st.selectbox("Propulsion type", ["Conventional", "Electric"])
                damage_stability = st.radio("Damage stability available?", ["No", "Yes"], horizontal=True)
                engine_room_location = st.selectbox("Engine room location", ENGINE_ROOM_LOCATIONS)
                service_restriction = st.selectbox("Service restriction notation", SERVICE_RESTRICTIONS)

            with st.expander("Deck configuration"):
                second_deck = yes_no_radio("Second deck below freeboard deck?", default="No")
                draught_cond = yes_no_radio("Draught < depth to second deck?", default="No")
                quarter_deck = yes_no_radio("Raised quarter deck?", default="No")
                ship_type = st.selectbox("Ship type", ["Cargo Ship", "Other"])
                freeboard_to_ap = yes_no_radio("Freeboard deck extends to AP?", default="Yes")

            with st.expander("Bow height"):
                LLL = st.number_input("Freeboard length LLL (m)", min_value=0.0, value=120.0)
                TLL = st.number_input("Load line draught TLL (m)", min_value=0.0, value=8.0)
                B = st.number_input("Breadth B (m)", min_value=0.0, value=20.0)
                displacement = st.number_input("Displacement nabla (m^3)", min_value=0.0, value=15000.0)
                Awf = st.number_input("Forward waterplane area Awf (m^2)", min_value=0.0, value=800.0)
                actual_fb = st.number_input("Actual bow height provided (mm)", min_value=0.0, value=3000.0)

            with st.expander("Collision bulkhead"):
                bulbous_bow = st.radio("Bulbous bow present?", ["No", "Yes"], horizontal=True)
                xbe = st.number_input("Bulb extension xbe (m)", min_value=0.0, value=5.0)
                openings_below_freeboard = yes_no_radio("Openings below freeboard deck?", default="No")
                num_pipes = st.number_input("Pipes through collision bulkhead", min_value=0, max_value=5, value=0)
                long_superstructure = yes_no_radio("Forward superstructure >= 0.25L?", default="No")
                aft_space_usage = st.selectbox("Aft space usage", ["Machinery", "Cargo/Passengers"])

            with st.expander("Double bottom and cofferdam"):
                double_bottom_fitted = yes_no_radio("Double bottom fitted?", default="Yes")
                fuel_next_to_fw = yes_no_radio("Fuel tank adjacent to fresh water?", default="No")

            with st.expander("Corrosion additions (Ch.3 Sec.3)"):
                material_family = st.selectbox(
                    "Material family",
                    ["Carbon-manganese steel", "Stainless steel", "Stainless clad steel", "Aluminium"],
                )
                member_kind = st.selectbox(
                    "Member type",
                    ["Compartment boundary", "Internal member", "Stiffener"],
                )
                compartment_1 = st.selectbox("Exposure side 1", COMPARTMENT_OPTIONS)
                compartment_2 = st.selectbox("Exposure side 2 (boundary)", COMPARTMENT_OPTIONS)
                grab_3x = st.checkbox("Grab(3-X) notation for dry cargo hold lower part")
                tc_max_override_mm = st.number_input(
                    "tc cap from Sec.3 [1.2.5] (mm, 0 = off)",
                    min_value=0.0,
                    value=0.0,
                    step=0.1,
                )
                t_net_required = st.number_input("Net required thickness t (mm)", min_value=0.0, value=10.0)
                t_as_built = st.number_input("As-built thickness tas_built (mm)", min_value=0.0, value=12.0)
                t_vol_add = st.number_input("Voluntary addition tvol (mm)", min_value=0.0, value=0.0)

            with st.expander("Corrosion protection (Ch.3 Sec.4)"):
                corrosive_tank_or_hold = yes_no_radio("Tank/hold exposed to corrosive environment?", default="No")
                pspc_vessel = yes_no_radio("Vessel follows PSPC?", default="No")
                dedicated_seawater_ballast = yes_no_radio("Dedicated seawater ballast tank?", default="No")
                crude_oil_cargo_tank = yes_no_radio("Cargo oil tank - crude oil carrier?", default="No")
                narrow_space = yes_no_radio("Narrow space present?", default="No")
                efficient_protection_product = yes_no_radio("Efficient protective system provided?", default="No")

            with st.expander("Structural arrangement (Ch.3 Sec.5)"):
                structural_continuity_ok = yes_no_radio("Structural continuity?", default="Yes")
                longitudinal_stiffeners_aligned = yes_no_radio("Longitudinal stiffeners aligned?", default="Yes")
                transverse_stiffeners_supported = yes_no_radio("Transverse stiffeners supported?", default="Yes")
                sheer_strake_continuity = yes_no_radio("Sheer strake continuity OK?", default="Yes")
                stringer_plate_continuity = yes_no_radio("Stringer plate continuity OK?", default="Yes")
                deckhouse_connection_good = yes_no_radio("Deckhouse connection OK?", default="Yes")

            with st.expander("Detail design (Ch.3 Sec.6)"):
                tripping_brackets_fitted = yes_no_radio("Tripping brackets fitted?", default="Yes")
                face_plate_width = st.number_input("Face plate width bf (mm)", min_value=0.0, value=300.0)
                free_flange_outstand = st.number_input("Free flange outstand (mm)", min_value=0.0, value=120.0)
                tripping_bracket_height = st.number_input("Tripping bracket height h (m)", min_value=0.0, value=0.30)
                tripping_bracket_arm = st.number_input("Tripping bracket arm d (m)", min_value=0.0, value=0.18)
                openings_in_stiffeners_ok = yes_no_radio("Openings in stiffeners OK?", default="Yes")
                openings_in_psm_ok = yes_no_radio("Openings in PSM OK?", default="Yes")
                openings_in_shell_deck_ok = yes_no_radio("Openings in shell/deck/bulkheads OK?", default="Yes")

            with st.expander("Structural idealization (Ch.3 Sec.7)"):
                effective_span = st.number_input("Effective span l (mm)", min_value=0.0, value=2500.0)
                stiffener_spacing = st.number_input("Stiffener spacing s (mm)", min_value=0.0, value=700.0)
                attached_plate_b1 = st.number_input("Attached plating b1 (mm)", min_value=0.0, value=350.0)
                attached_plate_b2 = st.number_input("Attached plating b2 (mm)", min_value=0.0, value=350.0)
                web_thickness = st.number_input("Web thickness tw (mm)", min_value=0.0, value=10.0)
                flange_thickness = st.number_input("Flange thickness tf (mm)", min_value=0.0, value=12.0)
                hw = st.number_input("Web height hw (mm)", min_value=0.0, value=200.0)
                bf = st.number_input("Flange width bf (mm)", min_value=0.0, value=90.0)
                tp = st.number_input("Attached plate thickness tp (mm)", min_value=0.0, value=12.0)

            submitted = st.form_submit_button("Run full calculation", use_container_width=True, type="primary")

    inputs = AppInputs(
        arrangement=ArrangementInputs(
            L=L,
            propulsion=propulsion,
            damage_stability=damage_stability,
            second_deck=second_deck,
            draught_cond=draught_cond,
            quarter_deck=quarter_deck,
            ship_type=ship_type,
            freeboard_to_ap=freeboard_to_ap,
            engine_room_location=engine_room_location,
            service_restriction=service_restriction,
            aft_space_usage=aft_space_usage,
            double_bottom_fitted=double_bottom_fitted,
            fuel_next_to_fw=fuel_next_to_fw,
        ),
        bow=BowInputs(
            LLL=LLL,
            TLL=TLL,
            B=B,
            displacement=displacement,
            Awf=Awf,
            actual_fb=actual_fb,
        ),
        collision=CollisionInputs(
            bulbous_bow=bulbous_bow,
            xbe=xbe,
            openings_below_freeboard=openings_below_freeboard,
            num_pipes=num_pipes,
            long_superstructure=long_superstructure,
        ),
        corrosion=CorrosionInputs(
            material_family=material_family,
            member_kind=member_kind,
            compartment_1=compartment_1,
            compartment_2=compartment_2,
            grab_3x=grab_3x,
            tc_max_override_mm=tc_max_override_mm,
            t_net_required=t_net_required,
            t_as_built=t_as_built,
            t_vol_add=t_vol_add,
        ),
        protection=ProtectionInputs(
            corrosive_tank_or_hold=corrosive_tank_or_hold,
            pspc_vessel=pspc_vessel,
            dedicated_seawater_ballast=dedicated_seawater_ballast,
            crude_oil_cargo_tank=crude_oil_cargo_tank,
            narrow_space=narrow_space,
            efficient_protection_product=efficient_protection_product,
        ),
        structural=StructuralInputs(
            structural_continuity_ok=structural_continuity_ok,
            longitudinal_stiffeners_aligned=longitudinal_stiffeners_aligned,
            transverse_stiffeners_supported=transverse_stiffeners_supported,
            sheer_strake_continuity=sheer_strake_continuity,
            stringer_plate_continuity=stringer_plate_continuity,
            deckhouse_connection_good=deckhouse_connection_good,
            tripping_brackets_fitted=tripping_brackets_fitted,
            face_plate_width=face_plate_width,
            free_flange_outstand=free_flange_outstand,
            tripping_bracket_height=tripping_bracket_height,
            tripping_bracket_arm=tripping_bracket_arm,
            openings_in_stiffeners_ok=openings_in_stiffeners_ok,
            openings_in_psm_ok=openings_in_psm_ok,
            openings_in_shell_deck_ok=openings_in_shell_deck_ok,
            effective_span=effective_span,
            stiffener_spacing=stiffener_spacing,
            attached_plate_b1=attached_plate_b1,
            attached_plate_b2=attached_plate_b2,
            web_thickness=web_thickness,
            flange_thickness=flange_thickness,
            hw=hw,
            bf=bf,
            tp=tp,
        ),
    )
    return inputs, submitted


def compute_results(inputs: AppInputs) -> AppResults:
    bulkhead_lookup = min_bulkheads_lookup(inputs.arrangement.L)
    if inputs.arrangement.damage_stability == "Yes":
        bulkheads = BulkheadScreening(
            applicable=False,
            special_consideration=False,
            min_aft_region=None,
            min_elsewhere=None,
            note="Damage stability is available; the minimum-bulkhead lookup table is not the governing screening check.",
        )
    elif bulkhead_lookup is None:
        bulkheads = BulkheadScreening(
            applicable=True,
            special_consideration=True,
            min_aft_region=None,
            min_elsewhere=None,
            note="L > 225 m; bulkhead number requires special consideration.",
        )
    else:
        bulkheads = BulkheadScreening(
            applicable=True,
            special_consideration=False,
            min_aft_region=bulkhead_lookup[0],
            min_elsewhere=bulkhead_lookup[1],
            note="Minimum transverse watertight bulkhead screening values from the Chapter 2 table.",
        )

    cb = calculate_cb(inputs.bow.LLL, inputs.bow.B, inputs.bow.TLL, inputs.bow.displacement)
    cwf = calculate_cwf(inputs.bow.LLL, inputs.bow.B, inputs.bow.Awf)
    required_fb = calculate_fb(inputs.bow.LLL, inputs.bow.TLL, cb, cwf)
    bow = BowHeightResult(
        cb=cb,
        cwf=cwf,
        required_fb=required_fb,
        actual_fb=inputs.bow.actual_fb,
        margin=inputs.bow.actual_fb - required_fb,
        compliant=inputs.bow.actual_fb >= required_fb,
    )

    xf = calculate_xf(inputs.collision.bulbous_bow, inputs.collision.xbe, inputs.bow.LLL)
    xc_min, xc_max = collision_limits(inputs.bow.LLL, xf)
    collision = CollisionResult(
        xf=xf,
        xc_min=xc_min,
        xc_max=xc_max,
        openings_ok=inputs.collision.openings_below_freeboard == "No",
        pipes_ok=inputs.collision.num_pipes <= 1,
        single_pipe_requires_valve=inputs.collision.num_pipes == 1,
        superstructure_extension_required=inputs.collision.long_superstructure == "Yes",
    )

    tc1, tc2, tc_total, detail = total_corrosion_addition(inputs.corrosion)
    gross_required = round_to_nearest_half(inputs.corrosion.t_net_required + tc_total)
    gross_offered = inputs.corrosion.t_as_built - inputs.corrosion.t_vol_add
    net_offered = gross_offered - tc_total
    gross_margin = gross_offered - gross_required
    net_margin = net_offered - inputs.corrosion.t_net_required
    corrosion = CorrosionResult(
        tc1=tc1,
        tc2=tc2,
        tc_total=tc_total,
        detail=detail,
        gross_required=gross_required,
        gross_offered=gross_offered,
        net_offered=net_offered,
        gross_margin=gross_margin,
        net_margin=net_margin,
        gross_ok=gross_margin >= 0,
        net_ok=net_margin >= 0,
    )

    detail_result = evaluate_detail_design(inputs.structural)
    idealization = section7_results(inputs.structural)

    return AppResults(
        bulkheads=bulkheads,
        bow=bow,
        collision=collision,
        corrosion=corrosion,
        detail=detail_result,
        idealization=idealization,
        double_bottom_height_mm=double_bottom_height(inputs.bow.B),
    )


def build_summary_rows(inputs: AppInputs, results: AppResults) -> list[tuple[str, bool]]:
    return [
        ("Bow height", results.bow.compliant),
        ("Collision bulkhead openings", results.collision.openings_ok),
        ("Collision bulkhead pipe count", results.collision.pipes_ok),
        ("Gross thickness", results.corrosion.gross_ok),
        ("Net thickness", results.corrosion.net_ok),
        ("Structural continuity", inputs.structural.structural_continuity_ok == "Yes"),
        ("Longitudinal stiffeners aligned", inputs.structural.longitudinal_stiffeners_aligned == "Yes"),
        ("Tripping bracket arm", results.detail.bracket_arm_ok),
    ]


def render_summary(results: AppResults, summary_rows: list[tuple[str, bool]]) -> None:
    st.header("Automated Check Summary")

    pass_count = sum(1 for _, passed in summary_rows if passed)
    fail_count = len(summary_rows) - pass_count

    col1, col2, col3 = st.columns(3)
    col1.metric("Total checks", len(summary_rows))
    col2.metric("Passing", pass_count)
    col3.metric("Failing", fail_count)

    summary_df = pd.DataFrame(
        [{"Check": name, "Result": "PASS" if passed else "FAIL"} for name, passed in summary_rows]
    )
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    st.caption("Only direct pass/fail checks with explicit user inputs are included here.")


def render_arrangement_tab(inputs: AppInputs, results: AppResults) -> None:
    st.subheader("Bulkhead arrangement")

    if results.bulkheads.special_consideration:
        st.warning(results.bulkheads.note)
    elif results.bulkheads.applicable:
        col1, col2 = st.columns(2)
        col1.metric("Min. bulkheads - aft region", results.bulkheads.min_aft_region)
        col2.metric("Min. bulkheads - elsewhere", results.bulkheads.min_elsewhere)
        st.info(results.bulkheads.note)
    else:
        st.info(results.bulkheads.note)

    if inputs.arrangement.propulsion == "Electric":
        st.info("Electric propulsion selected: the generator room and engine room should be enclosed by watertight bulkheads.")

    if inputs.arrangement.second_deck == "Yes" and inputs.arrangement.draught_cond == "Yes":
        st.info(
            "Second deck exception selected: bulkheads other than the collision bulkhead may terminate at the second deck if the related engine casing and deck are arranged as watertight."
        )

    if inputs.arrangement.quarter_deck == "Yes":
        st.info("Raised quarter deck selected: watertight bulkheads in the quarter deck region should extend to that deck.")
        if inputs.arrangement.ship_type == "Cargo Ship" and inputs.arrangement.freeboard_to_ap == "No":
            st.info(
                "Cargo ship with raised quarter deck and freeboard deck not extending to AP: the aft peak bulkhead may terminate at a lower watertight deck only with the stated watertight rudder-stock compartment arrangement."
            )

    st.divider()
    st.subheader("Cofferdam")
    if inputs.arrangement.fuel_next_to_fw == "Yes":
        st.warning("Fuel tank adjacent to fresh water: a cofferdam is required between the two spaces.")
    else:
        st.success("No fuel/fresh-water adjacency selected; no cofferdam trigger from this input.")

    st.divider()
    st.subheader("Double bottom")
    st.metric("Minimum double-bottom height hDB (mm)", f"{results.double_bottom_height_mm:.0f}")
    if inputs.arrangement.double_bottom_fitted == "Yes":
        st.success("Double bottom provided.")
    else:
        st.warning("Double bottom not fitted: bottom-damage justification is required.")

    st.divider()
    st.subheader("Shaft tunnel and aft/steering spaces")
    if inputs.arrangement.engine_room_location == "Amidships":
        if inputs.arrangement.service_restriction == "Unrestricted":
            st.warning("Engine room amidships: a watertight shaft tunnel is required.")
        else:
            st.info(
                f"Engine room amidships with service restriction {inputs.arrangement.service_restriction}: shaft tunnel omission may be possible only if the shafting is otherwise effectively protected."
            )
    else:
        st.info("Engine room not set to amidships; the Chapter 2 shaft tunnel trigger is not active from this input set.")

    if inputs.arrangement.aft_space_usage == "Machinery":
        st.info("Aft machinery space selected: the aft peak bulkhead termination allowance above deepest draught may be relevant.")
    else:
        st.info("Aft cargo/passenger use selected: verify that aft peak arrangements remain fully compliant for the chosen use.")

    st.write("- Steering gear compartment should remain readily accessible and separated from machinery spaces.")
    st.write("- Stern tube should be enclosed in a watertight space or accepted equivalent arrangement.")
    st.write("- Spaces forward of the collision bulkhead should not be used for fuel oil or other flammable products.")

    st.divider()
    st.subheader("Access requirements")
    st.write("- All tanks should be accessible for inspection.")
    st.write("- Double-bottom spaces should have manholes in inner bottom, floors and longitudinal girders.")
    st.write("- Closed spaces should be accessible for inspection, or otherwise specially considered.")


def render_bow_collision_tab(inputs: AppInputs, results: AppResults) -> None:
    st.subheader("Minimum bow height")

    col1, col2, col3 = st.columns(3)
    col1.metric("CB", f"{results.bow.cb:.4f}")
    col2.metric("Cwf", f"{results.bow.cwf:.4f}")
    col3.metric("Required Fb (mm)", f"{results.bow.required_fb:.1f}")

    col4, col5 = st.columns(2)
    col4.metric("Actual Fb (mm)", f"{results.bow.actual_fb:.1f}")
    col5.metric("Margin (mm)", f"{results.bow.margin:+.1f}")

    if results.bow.compliant:
        st.success(f"Bow height compliant: actual {results.bow.actual_fb:.0f} mm >= required {results.bow.required_fb:.0f} mm.")
    else:
        st.error(f"Bow height not compliant: shortfall {abs(results.bow.margin):.0f} mm.")

    st.info(
        "This bow-height implementation uses the standard DNV/Load Line style expression derived from Chapter 2 screening and should be verified against the governing rule edition before final use."
    )

    st.divider()
    st.subheader("Collision bulkhead")

    c1, c2 = st.columns(2)
    c1.metric("xc_min (m)", f"{results.collision.xc_min:.3f}")
    c2.metric("xc_max (m)", f"{results.collision.xc_max:.3f}")

    if results.collision.xf > 0:
        st.info(f"Bulbous bow adjustment xf = {results.collision.xf:.3f} m applied.")

    if results.collision.openings_ok:
        st.success("No openings below the freeboard deck.")
    else:
        st.error("Openings below the freeboard deck are not permitted in this screening check.")

    if not results.collision.pipes_ok:
        st.error(f"{inputs.collision.num_pipes} pipes through collision bulkhead: maximum allowed is 1.")
    elif results.collision.single_pipe_requires_valve:
        st.warning("One pipe selected: provide the required screw-down valve operable from above the freeboard deck.")
    else:
        st.success("No pipes through the collision bulkhead.")

    if results.collision.superstructure_extension_required:
        st.info("Forward superstructure >= 0.25L selected: collision bulkhead should extend weathertight to the next deck above the bulkhead deck.")


def render_corrosion_tab(inputs: AppInputs, results: AppResults) -> None:
    st.subheader("Corrosion additions (Ch.3 Sec.3)")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("tc1 (mm)", f"{results.corrosion.tc1:.2f}")
    col2.metric("tc2 (mm)", f"{results.corrosion.tc2:.2f}")
    col3.metric("t_res (mm)", f"{TRES:.2f}")
    col4.metric("tc_total (mm)", f"{results.corrosion.tc_total:.2f}")

    st.info(f"Rule logic: {results.corrosion.detail}")

    if inputs.corrosion.member_kind == "Stiffener":
        st.write("- Stiffener tc follows the location of connection to attached plating.")
        st.write("- Where more than one corrosion value applies, the largest value should be used.")

    st.divider()
    st.subheader("Net / gross thickness screening")

    g1, g2, g3, g4 = st.columns(4)
    g1.metric("Net required t (mm)", f"{inputs.corrosion.t_net_required:.2f}")
    g2.metric("Gross required tgr (mm)", f"{results.corrosion.gross_required:.1f}")
    g3.metric("Gross offered tgr_off (mm)", f"{results.corrosion.gross_offered:.1f}")
    g4.metric("Net offered toff (mm)", f"{results.corrosion.net_offered:.1f}")

    c1, c2 = st.columns(2)
    if results.corrosion.gross_ok:
        c1.success(f"Gross thickness OK: margin +{results.corrosion.gross_margin:.2f} mm")
    else:
        c1.error(f"Gross thickness fails: margin {results.corrosion.gross_margin:.2f} mm")

    if results.corrosion.net_ok:
        c2.success(f"Net thickness OK: margin +{results.corrosion.net_margin:.2f} mm")
    else:
        c2.error(f"Net thickness fails: margin {results.corrosion.net_margin:.2f} mm")

    breakdown = pd.DataFrame(
        {
            "Parameter": [
                "t_net required",
                "tc total",
                "Gross required (tgr)",
                "As-built (tas_built)",
                "Voluntary addition (tvol)",
                "Gross offered (tgr_off)",
                "Net offered (toff)",
            ],
            "Value (mm)": [
                inputs.corrosion.t_net_required,
                results.corrosion.tc_total,
                results.corrosion.gross_required,
                inputs.corrosion.t_as_built,
                inputs.corrosion.t_vol_add,
                results.corrosion.gross_offered,
                results.corrosion.net_offered,
            ],
        }
    )
    st.dataframe(breakdown, use_container_width=True, hide_index=True)


def render_protection_tab(inputs: AppInputs) -> None:
    st.subheader("Corrosion protection (Ch.3 Sec.4)")
    render_messages(corrosion_protection_messages(inputs.protection))


def render_section5_tab(inputs: AppInputs) -> None:
    st.subheader("Structural arrangement (Ch.3 Sec.5)")
    render_messages(section5_messages(inputs.structural))
    st.caption("Continuity, stiffener arrangement and major structural connection screening.")


def render_section6_tab(inputs: AppInputs, results: AppResults) -> None:
    st.subheader("Detail design (Ch.3 Sec.6)")
    render_messages(section6_messages(inputs.structural, results.detail))
    st.caption("Simplified checks for tripping brackets and openings.")


def render_section7_tab(results: AppResults) -> None:
    st.subheader("Structural idealization (Ch.3 Sec.7)")

    row1 = st.columns(4)
    row1[0].metric("beff (mm)", f"{results.idealization.beff_mm:.1f}")
    row1[1].metric("A_stiffener (mm^2)", f"{results.idealization.a_stiffener_mm2:.1f}")
    row1[2].metric("A_plate (mm^2)", f"{results.idealization.a_plate_mm2:.1f}")
    row1[3].metric("A_total (mm^2)", f"{results.idealization.a_total_mm2:.1f}")

    st.divider()

    row2 = st.columns(4)
    row2[0].metric("A_web (mm^2)", f"{results.idealization.a_web_mm2:.1f}")
    row2[1].metric("A_flange (mm^2)", f"{results.idealization.a_flange_mm2:.1f}")
    row2[2].metric("Neutral axis y_NA (mm)", f"{results.idealization.y_na_mm:.2f}")
    row2[3].metric("I_total (mm^4)", f"{results.idealization.i_total_mm4:.1f}")

    row3 = st.columns(2)
    row3[0].metric("Z_top (mm^3)", f"{results.idealization.z_top_mm3:.1f}")
    row3[1].metric("Z_bot (mm^3)", f"{results.idealization.z_bot_mm3:.1f}")

    st.caption(
        "Neutral axis is measured from the bottom of the attached plate. Effective breadth uses min(b1 + b2, s). Shear lag and weld geometry are not included."
    )

    properties = pd.DataFrame(
        {
            "Property": [
                "beff_mm",
                "a_stiffener_mm2",
                "a_web_mm2",
                "a_flange_mm2",
                "a_plate_mm2",
                "a_total_mm2",
                "y_na_mm",
                "i_total_mm4",
                "z_top_mm3",
                "z_bot_mm3",
            ],
            "Value": [
                f"{results.idealization.beff_mm:.2f}",
                f"{results.idealization.a_stiffener_mm2:.2f}",
                f"{results.idealization.a_web_mm2:.2f}",
                f"{results.idealization.a_flange_mm2:.2f}",
                f"{results.idealization.a_plate_mm2:.2f}",
                f"{results.idealization.a_total_mm2:.2f}",
                f"{results.idealization.y_na_mm:.2f}",
                f"{results.idealization.i_total_mm4:.2f}",
                f"{results.idealization.z_top_mm3:.2f}",
                f"{results.idealization.z_bot_mm3:.2f}",
            ],
        }
    )
    st.dataframe(properties, use_container_width=True, hide_index=True)


def render_notes_tab() -> None:
    st.subheader("Scope and limitations")
    st.markdown(
        """
| Chapter | Section | Topic |
| --- | --- | --- |
| Ch.2 | - | Arrangement and subdivision |
| Ch.3 | Sec.3 | Corrosion additions |
| Ch.3 | Sec.4 | Corrosion protection |
| Ch.3 | Sec.5 | Structural arrangement |
| Ch.3 | Sec.6 | Detail design |
| Ch.3 | Sec.7 | Structural idealization |

Known simplifications:

- Bow height uses the standard DNV/Load Line style screening expression; no slamming assessment is included.
- Effective breadth uses `beff = min(b1 + b2, s)`; shear lag is not modelled.
- Section properties assume simple rectangular web/flange geometry; welds and scallops are not modelled.
- Tripping bracket arm screening uses `d >= 0.6h`.
- Corrosion addition logic covers the main material/member/compartment cases, including Grab(3-X).
- No direct load, buckling, fatigue or ultimate strength checks are performed.

Intended use:

Preliminary design screening and rule orientation only. Results should be verified against the governing DNV rule edition before submission or fabrication.
"""
    )


def main() -> None:
    inputs, submitted = build_sidebar_inputs()
    if submitted:
        st.session_state["run_calculation"] = True

    st.title("DNV-Based Ship Design Tool")
    st.caption("Integrated rule-based ship arrangement, corrosion and compliance tool for preliminary design.")
    st.divider()

    if not st.session_state.get("run_calculation", False):
        st.info("Configure the inputs in the sidebar, then press Run full calculation.")
        st.stop()

    results = compute_results(inputs)
    summary_rows = build_summary_rows(inputs, results)

    render_summary(results, summary_rows)
    st.divider()

    tabs = st.tabs(
        [
            "Arrangement",
            "Bow and collision",
            "Corrosion",
            "Protection",
            "Structure Sec.5",
            "Detail Sec.6",
            "Idealization Sec.7",
            "Notes",
        ]
    )

    with tabs[0]:
        render_arrangement_tab(inputs, results)
    with tabs[1]:
        render_bow_collision_tab(inputs, results)
    with tabs[2]:
        render_corrosion_tab(inputs, results)
    with tabs[3]:
        render_protection_tab(inputs)
    with tabs[4]:
        render_section5_tab(inputs)
    with tabs[5]:
        render_section6_tab(inputs, results)
    with tabs[6]:
        render_section7_tab(results)
    with tabs[7]:
        render_notes_tab()

    st.divider()
    st.caption("DNV-based ship design and compliance tool - advanced prototype - for preliminary design use only.")


main()
