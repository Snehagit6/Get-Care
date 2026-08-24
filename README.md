# Get-Care

**Objective**: An application that aids in predictive analysis of medical conditions primarily Diabetes with the help of AI agents and
reunites Doctors and Patients towards achieving the health goals.

**Technique**: An agentic, role-aware clinical decision-support and patient education platform for Type II diabetes, combining longitudinal patient analysis, deterministic clinical tools, guideline-grounded RAG, and LLM-based reasoning.


**Architecture Overview**

**PLAN 1**
Patient Data
   |
   +-- Lab Reports
   +-- CGM Data
   +-- Medications
   +-- Diet Logs
   +-- Activity Data
   +-- Medical History
   |
Data Processing Agent
   |
Knowledge Retrieval Agent (RAG)
   |
Clinical Reasoning Agent
   |
Risk Prediction Models
   |
Doctor Dashboard <----> Patient Assistant

**PLAN 2**
PDF/DOCX/Image
      ↓
Deterministic Parser
      ↓
Canonical JSON
      ↓
Validation + Confidence
      ↓
Agent Orchestration
      ↓
Patient History + Trend Analysis
      ↓
ADA/WHO/IDF RAG
      ↓
Grok LLM Reasoning
      ↓
Doctor-side Decision Support

**Patient-Side Scenarios**
1. Diabetes Risk Assessment

User uploads:

HbA1c
Fasting glucose
Weight
Family history
Blood pressure

Agent predicts:

Prediabetes risk
Type 2 diabetes risk
Complication risk

Output:

"Based on current parameters, estimated progression risk to Type 2 Diabetes within 5 years is X%."

2. Personalized Diet Agent

Patient asks:

Can I eat mango today?

Agent checks:

Current glucose
Recent meals
HbA1c
Physician instructions

Provides personalized guidance.

3. Glucose Trend Forecasting

Using:

CGM devices
Historical glucose values

Predict:

Next 2 hours
Next meal spike
Overnight hypoglycemia risk
4. Medication Adherence Agent

Tracks:

Missed doses
Timing variations

Alerts patient.

5. Early Warning Agent

Detect:

Hyperglycemia patterns
Hypoglycemia patterns

Generate actionable alerts.

Doctor-Side Scenarios
1. Clinical Summary Agent

Doctor uploads patient records.

Agent creates:

HbA1c increased from 7.1 to 8.3

Medication:
Metformin 500mg BID

Observations:
- Weight gain 4kg
- Poor compliance
- Post-prandial spikes

This can save significant consultation time.

2. Treatment Recommendation Assistant

Doctor asks:

Why is HbA1c worsening?

Agent retrieves evidence from:

Guidelines
Research papers
Similar patient cohorts

and explains possible causes.

3. Diabetic Complication Prediction

Predict risk of:

Retinopathy
Neuropathy
Nephropathy
Cardiovascular disease

using patient history.

4. Doctor Copilot

Doctor asks:

Show latest evidence on SGLT2 inhibitors in CKD patients.

RAG retrieves relevant literature.

5. Population Analytics

Hospital administrators can analyze:

HbA1c distribution
Readmission rates
Medication effectiveness

across patient groups.

**Agentic Orchestration**

               Agent Orchestrator
                         │
               Role/Intent Router
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
     Doctor Workflow               Patient Workflow
          │                             │
          └──────────────┬──────────────┘
                         ▼
                 Shared Clinical Tools
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
 Patient Timeline        Trend Engine       Guideline RAG
       └─────────────────┼─────────────────┘
                         ▼
                  GPT-OSS Reasoning
                         │
                 Response Guardrails
                         │
                  Doctor / Patient



**Guideline RAG**
American Diabetes Association
International Diabetes Federation
World Health Organization


**Technology Stack**
Python, Custom agent framework or LangGraph, Tool-calling architecture, Vector DB, FAISS, LLM: openai/gpt-oss-20b
