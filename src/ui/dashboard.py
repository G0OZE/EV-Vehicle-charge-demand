"""Streamlit dashboard for monitoring workflow progress."""
from __future__ import annotations

import streamlit as st

from ..services.progress_store import FileProgressStore
from ..services.workflow_core import WorkflowCore
from ..models.interfaces import StepStatus


def render_summary(summary: dict) -> None:
    """Render workflow completion summary using Streamlit."""
    st.subheader("Project Progress")

    if not summary or summary.get("total_steps", 0) == 0:
        st.info("No workflow progress available.")
        return

    st.text(f"Project: {summary.get('project_name')}")
    st.text(
        f"Completed: {summary.get('completed_steps')} / {summary.get('total_steps')}"
    )
    st.progress(summary.get("progress_percentage", 0) / 100)

    # Optional Plotly visualization
    try:
        import plotly.express as px

        fig = px.bar(
            x=["Completed", "Remaining"],
            y=[
                summary.get("completed_steps", 0),
                summary.get("total_steps", 0) - summary.get("completed_steps", 0),
            ],
            labels={"x": "Status", "y": "Steps"},
            title="Workflow Progress",
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        pass


def main() -> None:
    """Entry point for Streamlit dashboard."""
    st.title("Workflow Dashboard")

    progress_store = FileProgressStore()
    workflow = WorkflowCore(progress_store)
    workflow.load_existing_workflow()

    summary = progress_store.get_completion_summary()
    if summary.get("error"):
        st.error(summary["error"])
        return

    render_summary(summary)

    st.subheader("Actions")
    step_id = st.number_input(
        "Step ID",
        min_value=1,
        step=1,
        value=summary.get("current_step", 1) or 1,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Execute Step"):
            result = workflow.execute_step(int(step_id))
            if result.status == StepStatus.COMPLETED:
                st.success(f"Step {int(step_id)} completed")
            else:
                st.error(result.error_message or "Step failed")
            st.experimental_rerun()

    with col2:
        if st.button("Rollback Step"):
            workflow.rollback_step(int(step_id))
            if progress_store.rollback_step(int(step_id)):
                st.success(f"Rolled back step {int(step_id)}")
            else:
                st.error(f"Failed to rollback step {int(step_id)}")
            st.experimental_rerun()

    with col3:
        if st.button("Restore Backup"):
            if progress_store.restore_from_backup():
                st.success("Restored from latest backup")
            else:
                st.error("Restore failed")
            st.experimental_rerun()


if __name__ == "__main__":
    main()
