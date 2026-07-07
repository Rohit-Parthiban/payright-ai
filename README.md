# PayRight AI

## Overview

**PayRight AI** is a policy-aware agentic AI prototype for healthcare payment integrity and claims review.

The application reviews a healthcare service request by comparing a mock clinical note against payer policy criteria. It generates a claim recommendation, denial risk score, missing documentation summary, governance review, and time-series anomaly detection for claim-volume trends.

This project demonstrates how agentic AI can support healthcare payer operations by making claims review more evidence-based, auditable, and human-supervised.

---

## What PayRight AI Does

PayRight AI takes three inputs:

1. **Clinical Note**  
   A mock provider/patient documentation note.

2. **Payer Policy**  
   Medical necessity or coverage criteria.

3. **Requested Service**  
   Example: Lumbar spine MRI, physical therapy, CT scan, sleep study.

The system then produces:

- Claim recommendation
- Denial risk score
- Human review flag
- Extracted clinical evidence
- Matched/missing documentation
- Governance review
- Time-series anomaly monitoring for claim-volume spikes

---

## Core Workflow

PayRight AI uses a multi-agent workflow:

```text
Clinical Note + Payer Policy + Requested Service
        ↓
Policy Retrieval Agent
        ↓
Clinical Evidence Agent
        ↓
Decision Agent
        ↓
Governance Agent
        ↓
Time-Series Anomaly Monitor
```

### 1. Policy Retrieval Agent

Retrieves the payer policy criteria for the selected healthcare service.

### 2. Clinical Evidence Agent

Extracts relevant patient facts, symptoms, prior treatment, and missing documentation from the clinical note.

### 3. Decision Agent

Compares clinical evidence against payer policy and classifies the claim as:

- **Approved**
- **Needs More Documentation**
- **Denial Risk**

It also assigns a denial risk score from `0–100`.

### 4. Governance Agent

Reviews the output for:

- Hallucination risk
- Evidence quality
- PHI/privacy concern
- Human review need
- Auditability concern

### 5. Time-Series Anomaly Monitor

Simulates monthly claim-volume trends and flags unusual spikes using a simple z-score based anomaly detection method.

This helps identify unusual utilization patterns, billing behavior changes, or areas needing targeted payment-integrity review.

---

## Demo Test Cases

The app includes multiple healthcare claim scenarios:

- Approved - Lumbar Spine MRI
- Needs Documentation - Lumbar Spine MRI
- Denial Risk - Lumbar Spine MRI
- Approved - Physical Therapy
- Denial Risk - CT Head Scan
- Needs Documentation - Cardiac Stress Test
- Approved - Sleep Study
- Denial Risk - Vitamin D Lab Test

These cases demonstrate different claim review outcomes across imaging, rehabilitation, cardiology, sleep medicine, and laboratory services.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend/UI | Streamlit |
| Programming Language | Python |
| LLM Reasoning | Google Gemini 2.5 Flash |
| Environment Variables | python-dotenv |
| Data Processing | pandas |
| Visualization | Streamlit charts |
| Architecture Pattern | Agentic AI workflow |
| Anomaly Detection | Z-score based time-series monitoring |

---

## Installation

### 1. Clone or open the project folder

```bash
cd ~/Desktop/payright-ai
```

### 2. Create and activate virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

If needed:

```bash
python -m pip install streamlit google-generativeai python-dotenv pandas
```

---

## Environment Setup

Create a `.env` file in the project root:

```bash
GOOGLE_API_KEY=your_gemini_api_key_here
```

Do not commit `.env` to GitHub.

Your `.gitignore` should include:

```gitignore
.env
venv/
__pycache__/
.DS_Store
```

---

## Run the Application

From the project folder:

```bash
cd ~/Desktop/payright-ai
source venv/bin/activate
python -m streamlit run app.py
```

Open the local URL shown in the terminal:

```text
http://localhost:8501
```

---

## How to Use

1. Select a demo case from the dropdown.
2. Review or edit the clinical note.
3. Review or edit the payer policy.
4. Confirm the requested service.
5. Click **Run Agentic Claims Review**.
6. Review the generated outputs:
   - Final Review Summary
   - Evidence Review
   - Agent Trace
   - Anomaly Monitor
   - Test Case Library

---

## Output Explanation

### Final Review Summary

Shows the main result:

- Recommendation
- Denial risk score
- Human review status
- Review category

### Evidence Review

Shows how the system compared:

- Payer policy evidence
- Clinical note evidence
- Decision output

### Agent Trace

Explains each agent step in the workflow.

### Anomaly Monitor

Displays monthly claim-volume trend data and flags unusual spikes.

### Test Case Library

Lists available scenarios and expected outcomes.

---

## Why This Matters

Healthcare payment review is often policy-heavy, documentation-heavy, and manually intensive. PayRight AI demonstrates how agentic AI can assist payment-integrity teams by:

- Reviewing clinical documentation against payer policy
- Identifying missing evidence before payment decisions
- Producing explainable recommendations
- Supporting human-in-the-loop review
- Flagging unusual claim-volume trends
- Improving auditability and operational efficiency

---

## Important Note

PayRight AI is a prototype built for demonstration purposes only.

It does not make real medical, legal, or payment decisions. It uses mock clinical notes and mock payer policies. In a production healthcare environment, this type of system would require stronger data governance, privacy controls, model validation, human oversight, and compliance review.

---

## Future Enhancements

Possible next steps:

- Add real retrieval using ChromaDB or FAISS
- Add structured policy parsing
- Add evidence checklist with matched/missing criteria
- Add exportable claim review summary
- Add batch claims review
- Add claims-level dashboard
- Add role-based access control
- Add model evaluation and hallucination scoring
- Integrate with claims and policy databases
- Add stronger anomaly detection models

---

## Project Summary

PayRight AI demonstrates a practical agentic AI workflow for healthcare payment integrity. It combines policy-grounded reasoning, clinical evidence extraction, decision classification, governance review, and time-series anomaly detection into a simple interactive claims review console.
