import random
import uuid
from datetime import datetime

import streamlit as st


APP_TITLE = "PulmoVision AI"
APP_SUBTITLE = "FastViT Diagnostic System"
MENU_ITEMS = ["Dashboard", "Patient Details", "History & Cases", "Settings"]


def init_session_state() -> None:
    defaults = {
        "is_authenticated": False,
        "active_page": "Dashboard",
        "dark_mode": True,
        "captcha_a": random.randint(1, 9),
        "captcha_b": random.randint(1, 9),
        "patients": [],
        "partner_id": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def apply_global_styles(dark_mode: bool) -> None:
    if dark_mode:
        bg_grad = "linear-gradient(135deg, #0f172a 0%, #1e293b 40%, #0b1220 100%)"
        text_color = "#e5f1ff"
        card_bg = "rgba(255, 255, 255, 0.08)"
        border_color = "rgba(255, 255, 255, 0.15)"
    else:
        bg_grad = "linear-gradient(135deg, #dbeafe 0%, #eff6ff 45%, #e0f2fe 100%)"
        text_color = "#0f172a"
        card_bg = "rgba(255, 255, 255, 0.55)"
        border_color = "rgba(255, 255, 255, 0.45)"

    st.markdown(
        f"""
        <style>
        .stApp {{
            background: {bg_grad};
            color: {text_color};
        }}

        .glass-card {{
            background: {card_bg};
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid {border_color};
            border-radius: 18px;
            padding: 1.2rem 1.2rem 1rem 1.2rem;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.20);
            margin-bottom: 1rem;
        }}

        .login-shell {{
            min-height: 80vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .login-card {{
            width: 100%;
            max-width: 520px;
            margin: 0 auto;
            background: {card_bg};
            border: 1px solid {border_color};
            border-radius: 20px;
            padding: 1.25rem;
            box-shadow: 0 14px 40px rgba(15, 23, 42, 0.25);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
        }}

        .pv-title {{
            font-size: 1.9rem;
            font-weight: 700;
            margin: 0;
            color: {text_color};
        }}

        .pv-subtitle {{
            font-size: 0.95rem;
            opacity: 0.92;
            margin-top: 0.35rem;
            margin-bottom: 0.3rem;
            color: {text_color};
        }}

        .hero-title {{
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }}

        .hero-subtitle {{
            font-size: 1rem;
            opacity: 0.92;
            margin-bottom: 1rem;
        }}

        .stButton > button {{
            border-radius: 12px;
            border: 0;
            color: white;
            font-weight: 600;
            background: linear-gradient(90deg, #2563eb 0%, #06b6d4 100%);
            box-shadow: 0 8px 20px rgba(37, 99, 235, 0.35);
            padding: 0.6rem 1rem;
        }}

        .stButton > button:hover {{
            filter: brightness(1.05);
            transform: translateY(-1px);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def regenerate_captcha() -> None:
    st.session_state["captcha_a"] = random.randint(1, 9)
    st.session_state["captcha_b"] = random.randint(1, 9)


def generate_patient_id() -> str:
    short_uuid = str(uuid.uuid4()).split("-")[0].upper()
    return f"PV-{datetime.utcnow().strftime('%y%m%d')}-{short_uuid}"


def validate_patient_form(data: dict) -> tuple[bool, str]:
    required_fields = ["full_name", "age", "gender", "address", "contact", "reason"]
    for field in required_fields:
        if not str(data.get(field, "")).strip():
            return False, f"{field.replace('_', ' ').title()} is required."

    try:
        age = int(str(data["age"]).strip())
        if age <= 0 or age > 130:
            return False, "Age must be between 1 and 130."
    except ValueError:
        return False, "Age must be numeric."

    if not str(data["contact"]).replace("+", "").replace("-", "").replace(" ", "").isdigit():
        return False, "Contact Number must contain only digits (plus optional +, spaces, hyphens)."

    return True, "Validated"


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(f"### 🫁 {APP_TITLE}")
        st.caption(APP_SUBTITLE)
        st.divider()

        selected = st.radio("Navigation", MENU_ITEMS, index=MENU_ITEMS.index(st.session_state["active_page"]))
        st.session_state["active_page"] = selected

        st.divider()
        st.session_state["dark_mode"] = st.toggle("Dark Mode", value=st.session_state["dark_mode"])

        if st.button("Logout", use_container_width=True):
            st.session_state["is_authenticated"] = False
            st.session_state["partner_id"] = ""
            regenerate_captcha()
            st.rerun()


def render_login_page() -> None:
    st.markdown('<div class="login-shell">', unsafe_allow_html=True)
    st.markdown('<div class="login-card">', unsafe_allow_html=True)

    st.markdown(f'<p class="pv-title">{APP_TITLE}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="pv-subtitle">{APP_SUBTITLE}</p>', unsafe_allow_html=True)
    st.write("Secure access for lab partners")

    partner_id = st.text_input("Username / Partner ID", placeholder="e.g., LP-2026-001")
    password = st.text_input("Password", type="password")

    a = st.session_state["captcha_a"]
    b = st.session_state["captcha_b"]
    captcha_input = st.text_input(f"Captcha: What is {a} + {b}?")

    col1, col2 = st.columns(2)
    with col1:
        login_clicked = st.button("Secure Login", use_container_width=True)
    with col2:
        if st.button("Refresh Captcha", use_container_width=True):
            regenerate_captcha()
            st.rerun()

    if login_clicked:
        if not partner_id.strip() or not password.strip():
            st.error("Please enter both Partner ID and Password.")
        else:
            try:
                captcha_ok = int(captcha_input.strip()) == (a + b)
            except ValueError:
                captcha_ok = False

            if not captcha_ok:
                st.error("Captcha validation failed. Please try again.")
                regenerate_captcha()
            else:
                st.session_state["is_authenticated"] = True
                st.session_state["partner_id"] = partner_id.strip()
                st.success("Login successful.")
                st.rerun()

    st.markdown('</div></div>', unsafe_allow_html=True)


def render_dashboard_home() -> None:
    st.markdown('<div class="hero-title">Welcome, Lab Partner</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-subtitle">Register patient and upload imaging data for PulmoVision AI analysis</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Registered Patients", len(st.session_state["patients"]))
    c2.metric("Active Partner", st.session_state.get("partner_id", "-"))
    c3.metric("System", "Online")


def render_patient_registration() -> None:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Patient Registration")

    search_term = st.text_input("Search Existing Patient (Name / ID)")
    if search_term.strip():
        matches = [
            p
            for p in st.session_state["patients"]
            if search_term.lower() in p["patient_id"].lower() or search_term.lower() in p["full_name"].lower()
        ]
        if matches:
            st.success(f"Found {len(matches)} matching patient(s).")
            st.dataframe(matches, use_container_width=True)
        else:
            st.warning("No matching patient found.")

    patient_id = generate_patient_id()
    st.text_input("Patient ID (auto-generated)", value=patient_id, disabled=True)

    col1, col2 = st.columns(2)
    with col1:
        full_name = st.text_input("Full Name *")
        age = st.text_input("Age *", placeholder="e.g., 45")
        gender = st.selectbox("Gender *", ["", "Male", "Female", "Other"])
        contact = st.text_input("Contact Number *")

    with col2:
        address = st.text_area("Address *", height=100)
        known_diseases = st.text_area("Known Diseases (Optional)", height=100)
        reason = st.text_area("Reason for Diagnosis *", height=100)

    payload = {
        "patient_id": patient_id,
        "full_name": full_name,
        "age": age,
        "gender": gender,
        "address": address,
        "contact": contact,
        "known_diseases": known_diseases,
        "reason": reason,
        "registered_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    }

    if st.button("Proceed to Upload", use_container_width=True):
        valid, msg = validate_patient_form(payload)
        if not valid:
            st.error(msg)
        else:
            payload["age"] = int(payload["age"])
            st.session_state["patients"].append(payload)
            st.success(f"Patient {payload['full_name']} registered successfully. Proceed to imaging upload workflow.")

    st.markdown('</div>', unsafe_allow_html=True)


def render_history() -> None:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("History & Cases")
    if st.session_state["patients"]:
        st.dataframe(st.session_state["patients"], use_container_width=True)
    else:
        st.info("No registered patients yet.")
    st.markdown('</div>', unsafe_allow_html=True)


def render_settings() -> None:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Settings")
    st.write("Customize dashboard preferences for PulmoVision AI.")
    st.checkbox("Enable notifications", value=True)
    st.checkbox("Auto-save patient drafts", value=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render_dashboard() -> None:
    render_sidebar()

    page = st.session_state["active_page"]
    if page == "Dashboard":
        render_dashboard_home()
        render_patient_registration()
    elif page == "Patient Details":
        render_patient_registration()
    elif page == "History & Cases":
        render_history()
    elif page == "Settings":
        render_settings()


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="expanded")
    init_session_state()
    apply_global_styles(st.session_state["dark_mode"])

    if not st.session_state["is_authenticated"]:
        render_login_page()
    else:
        render_dashboard()


if __name__ == "__main__":
    main()
