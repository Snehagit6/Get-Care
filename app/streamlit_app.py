from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.agents.orchestrator import AgentOrchestrator
from backend.clinical_tools.clinical_toolkit import ClinicalToolkit
from backend.clinical_tools.guideline_rag import GuidelineRAG
from backend.llm.groq_client import GroqLLM
from backend.parsers.report_parser import parse_report

PARSED_REPORTS_DIR = PROJECT_ROOT / "parsed_reports"
RAG_DIR = PROJECT_ROOT / "data" / "rag"


st.set_page_config(
    page_title="Get-Care Clinical Copilot",
    page_icon="+",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --ink: #17231f;
        --muted: #66756f;
        --paper: #f5f7f2;
        --mint: #d9eee1;
        --teal: #176b68;
        --coral: #d96e54;
        --line: #d8e2db;
    }
    .stApp { background: var(--paper); color: var(--ink); }
    [data-testid="stSidebar"] { background: #e7f0e8; border-right: 1px solid var(--line); }
    h1, h2, h3 { color: var(--ink); letter-spacing: 0; }
    .hero { padding: 1.2rem 0 0.5rem; }
    .eyebrow { color: var(--coral); font-size: .75rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; }
    .hero h1 { font-size: clamp(2rem, 4vw, 3.6rem); line-height: 1; margin: .35rem 0; }
    .hero p { color: var(--muted); max-width: 720px; font-size: 1.05rem; }
    .metric-card { background: white; border: 1px solid var(--line); border-radius: 8px; padding: 1rem; min-height: 108px; }
    .metric-label { color: var(--muted); font-size: .78rem; text-transform: uppercase; letter-spacing: .08em; }
    .metric-value { color: var(--teal); font-size: 1.65rem; font-weight: 700; margin-top: .35rem; }
    .copilot { background: #173f3c; color: white; border-radius: 8px; padding: 1.25rem; }
    .copilot h3 { color: #d9eee1; margin-top: 0; }
    .source-note { color: var(--muted); font-size: .82rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


def existing_report_paths() -> list[Path]:
    return sorted(PARSED_REPORTS_DIR.glob("*.json"))


def parse_uploads(uploaded_files: list[Any]) -> list[dict[str, Any]]:
    reports = []
    for uploaded_file in uploaded_files:
        suffix = Path(uploaded_file.name).suffix.lower()
        with tempfile.NamedTemporaryFile(
            suffix=suffix,
            delete=False,
        ) as temporary_file:
            temporary_file.write(uploaded_file.getvalue())
            temporary_path = Path(temporary_file.name)

        try:
            reports.append(parse_report(str(temporary_path)))
        finally:
            temporary_path.unlink(missing_ok=True)
    return reports


def get_toolkit(report_sources: list[Any]) -> ClinicalToolkit:
    return ClinicalToolkit(
        report_paths=report_sources,
        rag=GuidelineRAG(
            knowledge_dir=str(RAG_DIR),
            index_dir=str(RAG_DIR / "index"),
        ),
    )


def metric_card(label: str, value: str) -> None:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div></div>',
        unsafe_allow_html=True,
    )


def render_timeline(timeline: dict[str, Any]) -> None:
    patient = timeline.get("patient", {})
    columns = st.columns(4)
    values = [
        ("Patient", patient.get("name") or "Unknown"),
        ("Reports", str(timeline.get("report_count", 0))),
        ("From", timeline.get("date_range", {}).get("start") or "Unknown"),
        ("To", timeline.get("date_range", {}).get("end") or "Unknown"),
    ]
    for column, (label, value) in zip(columns, values):
        with column:
            metric_card(label, value)

    st.subheader("Lab history")
    lab_history = timeline.get("lab_history", {})
    if not lab_history:
        st.info("No laboratory results were found in the selected reports.")
        return

    for metric, observations in lab_history.items():
        with st.expander(metric.replace("_", " ").title(), expanded=True):
            st.dataframe(observations, use_container_width=True, hide_index=True)


def render_trends(trends: dict[str, Any]) -> None:
    analysis = trends.get("analysis", {})
    if not analysis:
        st.info("No trend data is available.")
        return

    for metric, result in analysis.items():
        with st.expander(metric.replace("_", " ").title(), expanded=True):
            if result.get("status") != "analyzed":
                st.caption(f"Status: {result.get('status', 'unknown')}")
                continue
            columns = st.columns(4)
            for column, label, value in zip(
                columns,
                ["Direction", "First", "Latest", "Change"],
                [
                    result.get("direction", "unknown"),
                    result.get("first", {}).get("value", ""),
                    result.get("latest", {}).get("value", ""),
                    f"{result.get('percentage_change')}%",
                ],
            ):
                with column:
                    metric_card(label, str(value))
            st.dataframe(result.get("history", []), use_container_width=True, hide_index=True)


def render_guidelines(toolkit: ClinicalToolkit) -> None:
    query = st.text_input(
        "Search clinical guidance",
        placeholder="Ask about HbA1c targets, screening, or diabetes care",
    )
    if st.button("Retrieve guidance", type="primary", disabled=not query):
        try:
            results = toolkit.retrieve_guidelines(query=query, top_k=5)
            if not results:
                st.info("No matching guidance was found.")
                return
            for result in results:
                st.markdown(
                    f"**{result.get('source', 'Source')}** · "
                    f"{result.get('document', 'Document')} · "
                    f"page {result.get('page', '?')}"
                )
                st.write(result.get("text", ""))
                st.caption(f"Similarity: {result.get('similarity', 'n/a')}")
        except FileNotFoundError:
            st.warning("Build the guideline index before retrieving guidance.")
            if st.button("Build guideline index"):
                toolkit.guideline_rag.build_index()
                st.success("Guideline index built. Search again.")
        except ValueError as error:
            st.warning(str(error))


def render_copilot(role: str, toolkit: ClinicalToolkit) -> None:
    st.markdown(
        f'<div class="copilot"><h3>{role} copilot</h3>'
        "Ask a question grounded in the selected patient record, trends, and guidelines.</div>",
        unsafe_allow_html=True,
    )
    question = st.text_area(
        "Question",
        placeholder=(
            "Doctor: What changed in the patient's HbA1c?"
            if role == "Doctor"
            else "What do my recent results mean?"
        ),
        label_visibility="collapsed",
    )
    if st.button("Ask copilot", type="primary", disabled=not question):
        if not os.getenv("GROQ_API_KEY"):
            st.error("Set GROQ_API_KEY to use copilot recommendations.")
            return
        try:
            result = AgentOrchestrator(
                toolkit=toolkit,
                llm=GroqLLM(),
            ).run(question=question, role=role.lower())
            st.markdown(result["answer"])
        except Exception as error:
            st.error(f"Copilot request failed: {error}")


def main() -> None:
    st.markdown(
        '<div class="hero"><div class="eyebrow">Get-Care · Clinical workspace</div>'
        '<h1>Clinical copilot</h1>'
        '<p>Review longitudinal records, inspect trends, retrieve guideline evidence, and ask a role-aware copilot.</p></div>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Workspace")
        role = st.radio("Workflow", ["Doctor", "Patient"], horizontal=True)
        st.divider()
        st.subheader("Patient records")
        uploaded_files = st.file_uploader(
            "Upload records",
            type=["pdf", "docx", "jpg", "jpeg", "png"],
            accept_multiple_files=True,
        )
        available_paths = existing_report_paths()
        selected_names = st.multiselect(
            "Use saved canonical reports",
            options=[path.name for path in available_paths],
            default=[path.name for path in available_paths],
        )

    uploaded_reports = parse_uploads(uploaded_files or [])
    selected_paths = [
        path for path in available_paths if path.name in selected_names
    ]
    report_sources: list[Any] = [*selected_paths, *uploaded_reports]

    if not report_sources:
        st.info("Select a saved report or upload a patient record to begin.")
        return

    try:
        toolkit = get_toolkit(report_sources)
        timeline = toolkit.get_patient_timeline()
    except Exception as error:
        st.error(f"Could not build the patient workspace: {error}")
        return

    patient = timeline.get("patient", {})
    summary_columns = st.columns(4)
    summary_values = [
        ("Patient", patient.get("name") or "Unknown"),
        ("Reports", str(timeline.get("report_count", 0))),
        ("From", timeline.get("date_range", {}).get("start") or "Unknown"),
        ("To", timeline.get("date_range", {}).get("end") or "Unknown"),
    ]
    for column, (label, value) in zip(summary_columns, summary_values):
        with column:
            metric_card(label, value)
    st.divider()

    timeline_tab, trends_tab, guideline_tab, copilot_tab = st.tabs(
        ["Patient timeline", "Trend engine", "Guideline RAG", f"{role} copilot"]
    )

    with timeline_tab:
        render_timeline(timeline)

    with trends_tab:
        render_trends(toolkit.calculate_trends())

    with guideline_tab:
        render_guidelines(toolkit)

    with copilot_tab:
        render_copilot(role, toolkit)


if __name__ == "__main__":
    main()
