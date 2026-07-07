import os
import re

import pandas as pd
import streamlit as st
import plotly.express as px
import google.generativeai as genai
from dotenv import load_dotenv

# -----------------------------
# Environment Setup
# -----------------------------

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("GOOGLE_API_KEY is missing. Add it to your .env file.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash")


# -----------------------------
# Demo Test Cases
# -----------------------------

DEMO_CASES = {
    "Approved - Lumbar Spine MRI": {
        "category": "Imaging",
        "expected": "Approved",
        "service": "Lumbar spine MRI",
        "clinical_note": """
Patient is a 52-year-old with chronic lower back pain for 8 weeks.
Pain has not improved after physical therapy and NSAID treatment.
Neurological exam shows radiating pain into the left leg with numbness.
Provider documents no fever, trauma, cancer history, bowel dysfunction, or bladder dysfunction.
Provider requests lumbar spine MRI.
""",
        "policy": """
Lumbar spine MRI may be medically necessary when:
- Patient has back pain lasting more than 6 weeks.
- Conservative treatment such as physical therapy or NSAIDs has failed.
- Neurological symptoms such as radiating leg pain, weakness, or numbness are documented.
- Red flag symptoms are reviewed or ruled out.
- Imaging is requested by a licensed provider.

Lumbar spine MRI may not be medically necessary when:
- Pain duration is less than 6 weeks.
- No conservative treatment has been attempted.
- No neurological symptoms are documented.
- Red flag symptoms are not assessed.
""",
    },
    "Needs Documentation - Lumbar Spine MRI": {
        "category": "Imaging",
        "expected": "Needs More Documentation",
        "service": "Lumbar spine MRI",
        "clinical_note": """
Patient is a 52-year-old with chronic lower back pain for 8 weeks.
Pain has not improved after physical therapy and NSAID treatment.
Patient reports radiating pain into the left leg.
Provider requests lumbar spine MRI.
The note does not document numbness, weakness, reflex findings, or red flag review.
""",
        "policy": """
Lumbar spine MRI may be medically necessary when:
- Patient has back pain lasting more than 6 weeks.
- Conservative treatment such as physical therapy or NSAIDs has failed.
- Neurological symptoms such as radiating leg pain, weakness, or numbness are documented.
- Red flag symptoms are reviewed or ruled out.
- Imaging is requested by a licensed provider.

Lumbar spine MRI may not be medically necessary when:
- Pain duration is less than 6 weeks.
- No conservative treatment has been attempted.
- No neurological symptoms are documented.
- Red flag symptoms are not assessed.
""",
    },
    "Denial Risk - Lumbar Spine MRI": {
        "category": "Imaging",
        "expected": "Denial Risk",
        "service": "Lumbar spine MRI",
        "clinical_note": """
Patient is a 44-year-old with lower back pain for 2 weeks.
Patient has not attempted physical therapy.
Patient has not tried NSAID treatment.
No neurological symptoms are documented.
Provider requests lumbar spine MRI.
""",
        "policy": """
Lumbar spine MRI may be medically necessary when:
- Patient has back pain lasting more than 6 weeks.
- Conservative treatment such as physical therapy or NSAIDs has failed.
- Neurological symptoms such as radiating leg pain, weakness, or numbness are documented.
- Red flag symptoms are reviewed or ruled out.
- Imaging is requested by a licensed provider.

Lumbar spine MRI may not be medically necessary when:
- Pain duration is less than 6 weeks.
- No conservative treatment has been attempted.
- No neurological symptoms are documented.
- Red flag symptoms are not assessed.
""",
    },
    "Approved - Physical Therapy": {
        "category": "Rehabilitation",
        "expected": "Approved",
        "service": "Physical therapy for knee osteoarthritis",
        "clinical_note": """
Patient is a 60-year-old with right knee osteoarthritis for 3 months.
Patient has difficulty walking and climbing stairs.
Provider documents reduced range of motion and functional limitation.
Patient has tried home exercises and acetaminophen with limited improvement.
Provider orders supervised physical therapy with measurable functional goals.
""",
        "policy": """
Physical therapy may be medically necessary when:
- Patient has a documented functional limitation.
- Symptoms persist despite conservative self-care.
- Therapy is ordered by a licensed provider.
- Treatment plan includes measurable functional goals.

Physical therapy may not be medically necessary when:
- No functional limitation is documented.
- No provider order is present.
- Therapy goals are not defined.
""",
    },
    "Denial Risk - CT Head Scan": {
        "category": "Imaging",
        "expected": "Denial Risk",
        "service": "CT scan for headache",
        "clinical_note": """
Patient is a 29-year-old with mild headache for 1 day.
No trauma is documented.
No neurological deficit is documented.
No fever, seizure, cancer history, or altered mental status is documented.
Provider requests CT head scan.
""",
        "policy": """
CT scan for headache may be medically necessary when:
- Severe or sudden-onset headache is documented.
- Neurological deficit is present.
- Recent trauma is documented.
- Red flag symptoms such as fever, seizure, cancer history, or altered mental status are present.
- Imaging is requested by a licensed provider.

CT scan for headache may not be medically necessary when:
- Headache is mild and short duration.
- No neurological deficit is documented.
- No trauma or red flag symptoms are documented.
""",
    },
    "Needs Documentation - Cardiac Stress Test": {
        "category": "Cardiology",
        "expected": "Needs More Documentation",
        "service": "Cardiac stress test",
        "clinical_note": """
Patient is a 58-year-old with intermittent chest discomfort.
Patient has hypertension and family history of coronary artery disease.
Provider requests cardiac stress test.
The note does not clearly describe exertional symptoms, ECG findings, or prior clinical evaluation.
""",
        "policy": """
Cardiac stress testing may be medically necessary when:
- Chest pain or equivalent symptoms suggest possible coronary artery disease.
- Risk factors such as hypertension, diabetes, smoking, or family history are documented.
- Baseline ECG or clinical evaluation supports additional testing.
- Test is ordered by a licensed provider.

Cardiac stress testing may not be medically necessary when:
- Symptoms are not documented.
- Risk factors are absent or unclear.
- No initial clinical evaluation is documented.
""",
    },
    "Approved - Sleep Study": {
        "category": "Sleep Medicine",
        "expected": "Approved",
        "service": "Sleep study for suspected obstructive sleep apnea",
        "clinical_note": """
Patient is a 49-year-old with loud snoring, witnessed apneas, and daytime sleepiness for 6 months.
BMI is elevated.
Provider documents fatigue affecting daily activities.
Provider requests overnight sleep study.
""",
        "policy": """
Sleep study may be medically necessary when:
- Symptoms suggest obstructive sleep apnea, such as loud snoring or witnessed apneas.
- Daytime sleepiness or functional impact is documented.
- Risk factors such as elevated BMI are documented.
- Test is ordered by a licensed provider.

Sleep study may not be medically necessary when:
- Sleep apnea symptoms are not documented.
- No functional impact is documented.
- No provider order is present.
""",
    },
    "Denial Risk - Vitamin D Lab Test": {
        "category": "Laboratory",
        "expected": "Denial Risk",
        "service": "Vitamin D lab test",
        "clinical_note": """
Patient requests vitamin D testing during routine wellness visit.
No bone disease, malabsorption, kidney disease, osteoporosis, or deficiency symptoms are documented.
Provider orders vitamin D lab test.
""",
        "policy": """
Vitamin D testing may be medically necessary when:
- Patient has documented bone disease, osteoporosis, malabsorption, kidney disease, or deficiency symptoms.
- Testing is needed to monitor treatment for a documented condition.
- Test is ordered by a licensed provider.

Vitamin D testing may not be medically necessary when:
- Ordered as routine screening without documented risk factors.
- No related symptoms or qualifying conditions are documented.
""",
    },
}


# -----------------------------
# Agent Functions
# -----------------------------

def policy_retrieval_agent(policy_text):
    return policy_text


def clinical_evidence_agent(clinical_note, requested_service):
    prompt = f"""
You are a Clinical Evidence Agent.

Extract only facts from the clinical note that matter for the requested service.

Requested service:
{requested_service}

Clinical note:
{clinical_note}

Return in this exact format:

Relevant Patient Facts:
- ...

Symptoms:
- ...

Prior Treatment:
- ...

Missing Information:
- ...
"""
    response = model.generate_content(prompt)
    return response.text


def decision_agent(requested_service, policy_evidence, clinical_evidence):
    prompt = f"""
You are a Healthcare Claims Decision Agent.

Compare the clinical evidence against the payer policy.

Decision rules:
- If all required policy criteria are clearly met, return "Approved".
- If some criteria are met but important documentation is missing, return "Needs More Documentation".
- If the claim clearly fails required policy criteria, return "Denial Risk".
- Do not approve a claim if safety-critical documentation is missing.
- Use only the given policy and clinical evidence.

Requested service:
{requested_service}

Full payer policy:
{policy_evidence}

Clinical evidence:
{clinical_evidence}

Return exactly this format:

Decision: Approved / Needs More Documentation / Denial Risk

Reason:
Short explanation based only on the provided policy and clinical evidence.

Matched Criteria:
- List policy criteria that are met.

Missing Documentation:
- List documentation that is still missing. If none, write "None identified."

Risk Score:
Give a number from 0 to 100, where 100 means highest denial risk.
"""
    response = model.generate_content(prompt)
    return response.text


def governance_agent(decision_output):
    prompt = f"""
You are an AI Governance Agent.

Review the claim decision below for safety, auditability, and human oversight.

Claim decision:
{decision_output}

Return exactly this format:

* **Hallucination Risk:** Low / Medium / High
* **Evidence Quality:** Strong / Partial / Weak
* **Human Review Needed:** Yes / No
* **Privacy/PHI Warning:** One sentence
* **Governance Concern:** One sentence
"""
    response = model.generate_content(prompt)
    return response.text


# -----------------------------
# Parsing Helpers
# -----------------------------

def extract_decision(decision_output):
    match = re.search(r"Decision:\s*(.*)", decision_output)
    if match:
        return match.group(1).strip()
    return "Not Available"


def extract_risk_score(decision_output):
    match = re.search(r"Risk Score:\s*(\d+)", decision_output)
    if match:
        return int(match.group(1))
    return None


def extract_human_review(governance_output):
    match = re.search(r"Human Review Needed:\s*(.*)", governance_output)
    if match:
        return match.group(1).strip()
    return "Yes"


def get_decision_badge(decision):
    decision_lower = decision.lower()

    if "approved" in decision_lower:
        return "✅ Approved"
    if "needs" in decision_lower:
        return "🟡 Needs More Documentation"
    if "denial" in decision_lower:
        return "🔴 Denial Risk"

    return "⚪ Review Needed"


def get_risk_label(score):
    if score is None:
        return "Unknown"
    if score <= 30:
        return "Low Risk"
    if score <= 65:
        return "Medium Risk"
    return "High Risk"


# -----------------------------
# Time-Series Anomaly Detection
# -----------------------------

def build_time_series_data(selected_case_name):
    """
    Creates synthetic monthly claim trend data for the demo.
    In a real system, this would come from claims history.
    """
    base_data = {
        "Approved - Lumbar Spine MRI": [18, 20, 21, 19, 22, 24, 23, 25, 24, 26, 27, 29],
        "Needs Documentation - Lumbar Spine MRI": [15, 16, 17, 15, 18, 19, 20, 22, 21, 23, 39, 42],
        "Denial Risk - Lumbar Spine MRI": [9, 10, 11, 10, 12, 13, 12, 14, 16, 18, 35, 41],
        "Approved - Physical Therapy": [25, 27, 28, 29, 31, 30, 32, 33, 34, 35, 36, 38],
        "Denial Risk - CT Head Scan": [8, 9, 8, 10, 11, 10, 12, 11, 13, 15, 31, 37],
        "Needs Documentation - Cardiac Stress Test": [12, 13, 14, 14, 15, 16, 17, 18, 20, 21, 34, 36],
        "Approved - Sleep Study": [14, 15, 16, 16, 17, 18, 18, 19, 20, 21, 22, 24],
        "Denial Risk - Vitamin D Lab Test": [20, 19, 21, 22, 23, 25, 24, 26, 28, 31, 58, 64],
    }

    months = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]

    claim_counts = base_data.get(
        selected_case_name,
        [10, 11, 12, 11, 13, 14, 15, 16, 17, 18, 19, 20]
    )

    return pd.DataFrame({
        "Month": months,
        "Claim Volume": claim_counts
    })


def detect_time_series_anomaly(df):
    """
    Simple anomaly detector using z-score.
    Compares latest month against prior months.
    """
    baseline = df["Claim Volume"].iloc[:-1]
    latest_value = df["Claim Volume"].iloc[-1]

    mean_value = baseline.mean()
    std_value = baseline.std()

    if std_value == 0:
        z_score = 0
    else:
        z_score = (latest_value - mean_value) / std_value

    if z_score >= 2:
        status = "Anomaly Detected"
        explanation = "The latest month is significantly higher than the historical baseline."
    else:
        status = "Normal Trend"
        explanation = "The latest month is within the expected historical range."

    return status, round(z_score, 2), explanation


# -----------------------------
# Page Styling
# -----------------------------

st.set_page_config(
    page_title="PayRight AI",
    layout="wide",
    page_icon="🏥"
)

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1500px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .main {
        background-color: #f5f8fc;
    }

    .hero {
        background: linear-gradient(135deg, #0f2d46 0%, #145c8f 55%, #1c7fb6 100%);
        padding: 34px;
        border-radius: 18px;
        color: white;
        margin-bottom: 26px;
        box-shadow: 0 8px 24px rgba(15, 45, 70, 0.20);
    }

    .hero h1 {
        font-size: 46px;
        margin-bottom: 6px;
        font-weight: 800;
    }

    .hero p {
        font-size: 18px;
        margin-bottom: 0px;
        color: #e8f4ff;
    }

    .info-strip {
        background: #eaf4ff;
        border-left: 5px solid #1c7fb6;
        padding: 14px 18px;
        border-radius: 10px;
        margin-bottom: 20px;
        color: #0f2d46;
    }

    textarea {
        border-radius: 12px !important;
    }

    .stButton > button {
        border-radius: 10px;
        padding: 0.6rem 1.2rem;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="hero">
        <h1>PayRight AI</h1>
        <p>Healthcare Payment Integrity Review Console powered by policy-aware agentic AI.</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="info-strip">
        PayRight AI demonstrates how AI agents can review clinical documentation against payer policy,
        identify missing evidence, estimate denial risk, detect unusual claim-volume trends, and recommend
        human review before payment decisions.
    </div>
    """,
    unsafe_allow_html=True
)


# -----------------------------
# Sidebar
# -----------------------------

with st.sidebar:
    st.header("PayRight AI")
    st.write("Built for healthcare payment integrity, claims review, and policy-aware decision support.")

    st.divider()

    st.subheader("Agent Workflow")
    st.write("① Policy Retrieval Agent")
    st.write("② Clinical Evidence Agent")
    st.write("③ Decision Agent")
    st.write("④ Governance Agent")
    st.write("⑤ Time-Series Anomaly Monitor")

    st.divider()

    st.subheader("What it demonstrates")
    st.write("- Agentic AI")
    st.write("- Policy-grounded reasoning")
    st.write("- Clinical evidence extraction")
    st.write("- Decision classification")
    st.write("- Risk scoring")
    st.write("- Time-series anomaly detection")
    st.write("- Human-in-the-loop governance")


# -----------------------------
# Case Selection
# -----------------------------

st.subheader("Interactive Demo Setup")

col_case, col_expected, col_category = st.columns([2, 1, 1])

with col_case:
    selected_case = st.selectbox("Choose a demo case", list(DEMO_CASES.keys()))

case = DEMO_CASES[selected_case]

with col_expected:
    st.info(f"Expected: {case['expected']}")

with col_category:
    st.info(f"Category: {case['category']}")

# --- NEW: System Analytics Dashboard ---
st.divider()
st.subheader("System Analytics: Service Volume Monitor")
st.write(f"Analyzing historical claims trend for: **{case['service']}**")

trend_df = build_time_series_data(selected_case)
anomaly_status, z_score, anomaly_explanation = detect_time_series_anomaly(trend_df)

col_a, col_b, col_c = st.columns(3)

with col_a:
    st.metric("Trend Status", anomaly_status)
with col_b:
    st.metric("Anomaly Z-Score", z_score)
with col_c:
    st.metric("Latest Month Volume", int(trend_df["Claim Volume"].iloc[-1]))

# --- NEW: Upgraded Analytics Charts ---
col_chart1, col_chart2 = st.columns([2, 1])

with col_chart1:
    fig_line = px.line(
        trend_df,
        x="Month",
        y="Claim Volume",
        markers=True,
        title="Volume Trend (Trailing 12 Months)"
    )
    fig_line.update_traces(line_color="#1c7fb6", line_width=3, marker=dict(size=8))
    st.plotly_chart(fig_line, use_container_width=True)

with col_chart2:
    # Mock data for the donut chart representing historical macro trends
    donut_data = pd.DataFrame({
        "Status": ["Approved", "Denied", "Needs Info"],
        "Volume": [65, 20, 15]
    })
    
    fig_donut = px.pie(
        donut_data,
        names="Status",
        values="Volume",
        hole=0.5,
        title="Historical Outcomes",
        color="Status",
        color_discrete_map={
            "Approved": "#28a745",
            "Denied": "#dc3545",
            "Needs Info": "#ffc107"
        }
    )
    fig_donut.update_traces(textposition='inside', textinfo='percent+label')
    fig_donut.update_layout(showlegend=False)
    st.plotly_chart(fig_donut, use_container_width=True)

st.write(anomaly_explanation)


# --- UPGRADED: Side-by-Side Documentation Workstation ---
st.divider()
st.subheader("📝 Case Documentation Workspace")
st.write("Review or adjust the provider text and active payer policy guidelines prior to executing the agent core pipeline.")

# Position the service target clearly above the working panels
requested_service = st.text_input(
    "🎯 Target Healthcare Service / Procedure Code",
    value=case["service"]
)

st.write("") # Clean vertical spacing element

col_note, col_policy = st.columns(2)

with col_note:
    with st.container(border=True):
        st.markdown("### 🏥 Clinical Chart Note")
        st.caption("Extracted EHR data / Provider documentation text")
        clinical_note = st.text_area(
            "Clinical Note Input Panel",
            value=case["clinical_note"],
            height=320,
            label_visibility="collapsed"
        )

with col_policy:
    with st.container(border=True):
        st.markdown("### 📜 Active Payer Policy")
        st.caption("Medical necessity guidelines / Coverage criteria ruleset")
        payer_policy = st.text_area(
            "Payer Policy Input Panel",
            value=case["policy"],
            height=320,
            label_visibility="collapsed"
        )

st.write("") # Clean vertical spacing element

# Full-width action button accentuates the pipeline trigger point
run_review = st.button("🚀 Run Agentic Claims Review Pipeline", type="primary", use_container_width=True)

# -----------------------------
# Run Review
# -----------------------------

if run_review:
    with st.status("Running agentic claims review...", expanded=True) as status:
        st.write("Step 1: Policy Retrieval Agent is retrieving payer policy evidence.")
        policy_evidence = policy_retrieval_agent(payer_policy)

        st.write("Step 2: Clinical Evidence Agent is extracting patient facts.")
        clinical_evidence = clinical_evidence_agent(clinical_note, requested_service)

        st.write("Step 3: Decision Agent is comparing clinical evidence against policy.")
        decision_output = decision_agent(requested_service, policy_evidence, clinical_evidence)

        st.write("Step 4: Governance Agent is checking safety, auditability, and human review need.")
        governance_output = governance_agent(decision_output)

        status.update(label="Agentic claims review complete.", state="complete")

    decision = extract_decision(decision_output)
    risk_score = extract_risk_score(decision_output)
    human_review = extract_human_review(governance_output)

    decision_badge = get_decision_badge(decision)
    risk_label = get_risk_label(risk_score)

    st.header("Final Review Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Recommendation", decision_badge)

    with col2:
        if risk_score is not None:
            st.metric("Denial Risk Score", f"{risk_score}/100", risk_label)
            st.progress(min(risk_score, 100) / 100)
        else:
            st.metric("Denial Risk Score", "Not Available")

    with col3:
        st.metric("Human Review Needed", human_review)

    with col4:
        st.metric("Review Type", case["category"])

    st.divider()

    tab1, tab2, tab3 = st.tabs(
        ["Executive Summary", "Evidence Review", "Agent Trace"]
    )

    with tab1:
        st.markdown("### 📊 Executive Summary")
        
        # Dynamic color-coded summary based on the decision
        if "Approved" in decision:
            st.success(f"**PayRight AI** reviewed the request for **{requested_service}** and recommends **{decision_badge}** with a risk score of **{risk_score}/100**.")
        elif "Denial" in decision:
            st.error(f"**PayRight AI** reviewed the request for **{requested_service}** and recommends **{decision_badge}** with a risk score of **{risk_score}/100**.")
        else:
            st.warning(f"**PayRight AI** reviewed the request for **{requested_service}** and recommends **{decision_badge}** with a risk score of **{risk_score}/100**.")
        
        # Clean up the markdown asterisks bleeding through from the LLM output
        clean_human_review = human_review.replace('*', '').strip()
        st.info(f"🧑‍⚕️ **Human Review Status:** {clean_human_review}")

        st.markdown("### 💡 Business Value")
        st.write(
            "This workflow demonstrates how agentic AI can support healthcare payment integrity by "
            "identifying matched policy criteria, missing documentation, denial risk, governance concerns, "
            "and unusual claim-volume trends before payment decisions are finalized."
        )

    with tab2:
        st.markdown("### ⚖️ Evidence Review")
        
        left, right = st.columns(2)

        with left:
            with st.container(border=True):
                st.markdown("#### 📜 Policy Evidence")
                st.write(policy_evidence)

        with right:
            with st.container(border=True):
                st.markdown("#### 🏥 Clinical Evidence")
                st.write(clinical_evidence)

        st.markdown("### 🧠 Decision Output")
        with st.container(border=True):
            st.write(decision_output)

    with tab3:
        st.markdown("### 🕵️‍♂️ Agent Trace Log")
        
        # Formats the trace list like a dark-mode system terminal log
        st.code("""
[1] Policy Retrieval Agent : Retrieved the payer policy for the requested service.
[2] Clinical Evidence Agent: Extracted patient facts, symptoms, prior treatment, and missing information.
[3] Decision Agent         : Compared policy criteria against clinical evidence and assigned a recommendation.
[4] Governance Agent       : Reviewed hallucination risk, evidence quality, privacy concerns, and human review need.
[5] Anomaly Monitor        : Simulated monthly claim-volume trend analysis to flag unusual spikes.
        """, language="shell")

        st.markdown("### 🛡️ Governance Output")
        with st.container(border=True):
            st.write(governance_output)