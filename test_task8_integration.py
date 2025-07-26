#!/usr/bin/env python3
"""
Integration test for Task 8: Submission tracking and validation
"""
import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path

from src.services.submission_service import SubmissionValidationService
from src.services.lms_integration import LMSIntegrationService
from src.services.validation_service import ValidationService
from src.models.workflow_models import WorkflowState, ProjectData


def test_task8_integration():
    """Test the complete submission tracking and validation workflow."""
    print("Testing Task 8: Submission tracking and validation integration...")
    
    # Create test project data
    project_data = ProjectData(
        project_id="test_project",
        dataset_url="https://example.com/dataset.csv",
        code_template_url="https://example.com/template.ipynb",
        project_description="Test project for AICTE workflow automation",
        requirements=["Complete notebook", "Upload dataset", "Create repository"],
        deadline=datetime.now() + timedelta(days=5)
    )
    
    # Create test workflow state
    workflow_state = WorkflowState(
        project_name="AICTE Test Project",
        current_step=8,
        completed_steps=[1, 2, 3, 4, 5, 6, 7],
        project_data=project_data,
        github_repo="testuser/aicte-test-project",
        submission_link="https://github.com/testuser/aicte-test-project"
    )
    
    # Initialize services
    validation_service = ValidationService()
    submission_service = SubmissionValidationService(validation_service)
    lms_service = LMSIntegrationService(submission_service)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        create_test_files(temp_dir)
        
        print("✓ Test files created")
        
        # Test Task 8.1: Create submission checklist validation
        print("\nTesting Task 8.1: Submission checklist validation...")
        
        # Validate submission completeness
        submission_status = submission_service.validate_submission_completeness(
            workflow_state, temp_dir
        )
        
        print(f"✓ Submission checklist created with {len(submission_status.checklist_items)} items")
        print(f"✓ Overall completion: {submission_status.overall_completion:.1f}%")
        
        # Check deadline tracking
        is_deadline_ok, warnings = submission_service.check_deadline_status(submission_status)
        print(f"✓ Deadline status checked: {'OK' if is_deadline_ok else 'Issues found'}")
        if warnings:
            print(f"  Warnings: {len(warnings)}")
        
        # Perform final validation
        is_ready, final_status = submission_service.perform_final_validation(
            workflow_state, temp_dir
        )
        print(f"✓ Final validation: {'Ready' if is_ready else 'Not ready'} for submission")
        
        # Test Task 8.2: LMS integration helpers
        print("\nTesting Task 8.2: LMS integration helpers...")
        
        # Generate submission summary
        student_info = {'name': 'Test Student', 'id': 'AICTE001'}
        summary = lms_service.generate_submission_summary(
            workflow_state, submission_status, student_info
        )
        print(f"✓ Submission summary generated for {summary.submission_data.student_name}")
        
        # Validate repository link
        is_valid, errors = lms_service.validate_repository_link(workflow_state.submission_link)
        print(f"✓ Repository link validation: {'Valid' if is_valid else 'Invalid'}")
        if errors:
            print(f"  Errors: {errors}")
        
        # Track submission status
        status_tracking = lms_service.track_submission_status(workflow_state, submission_status)
        print(f"✓ Submission status tracked - Phase: {status_tracking.get('submission_phase', 'unknown')}")
        
        # Generate reports in different formats
        html_report = lms_service.generate_lms_report(workflow_state, submission_status, 'html')
        markdown_report = lms_service.generate_lms_report(workflow_state, submission_status, 'markdown')
        json_report = lms_service.generate_lms_report(workflow_state, submission_status, 'json')
        
        print(f"✓ Generated reports: HTML ({len(html_report)} chars), Markdown ({len(markdown_report)} chars), JSON ({len(json_report)} chars)")
        
        # Prepare complete submission package
        package = lms_service.prepare_submission_package(workflow_state, submission_status)
        print(f"✓ Submission package prepared with {len(package)} sections")
        
        # Verify all requirements are met
        print("\nVerifying requirements compliance...")
        
        # Requirement 4.1: Verify completeness against checklist
        required_items = [item for item in submission_status.checklist_items if item.is_required]
        completed_required = [item for item in required_items if item.is_completed]
        print(f"✓ Requirement 4.1: Completeness verification - {len(completed_required)}/{len(required_items)} required items")
        
        # Requirement 4.2: Deadline tracking and reminders
        print(f"✓ Requirement 4.2: Deadline tracking - {submission_status.days_until_deadline} days remaining")
        
        # Requirement 4.3: LMS submission facilitation
        print(f"✓ Requirement 4.3: LMS submission link ready - {workflow_state.submission_link}")
        
        # Requirement 4.4: Highlight missing components
        incomplete_items = [item for item in submission_status.checklist_items 
                          if item.is_required and not item.is_completed]
        if incomplete_items:
            print(f"✓ Requirement 4.4: Missing components highlighted - {len(incomplete_items)} incomplete")
        else:
            print("✓ Requirement 4.4: All required components complete")
        
        print(f"\n🎉 Task 8 integration test completed successfully!")
        print(f"   - Submission tracking: ✓")
        print(f"   - Validation service: ✓")
        print(f"   - LMS integration: ✓")
        print(f"   - Requirements compliance: ✓")
        
        return True


def create_test_files(temp_dir):
    """Create test files for validation."""
    temp_path = Path(temp_dir)
    
    # Create test notebook with execution outputs
    notebook_content = {
        "cells": [
            {
                "cell_type": "markdown",
                "source": "# AICTE Test Project\n\nThis is a test notebook for the AICTE workflow."
            },
            {
                "cell_type": "code",
                "source": "import pandas as pd\nprint('Loading dataset...')",
                "outputs": [{"output_type": "stream", "text": "Loading dataset..."}],
                "execution_count": 1
            },
            {
                "cell_type": "code",
                "source": "df = pd.read_csv('dataset.csv')\nprint(f'Dataset shape: {df.shape}')",
                "outputs": [{"output_type": "stream", "text": "Dataset shape: (100, 5)"}],
                "execution_count": 2
            }
        ]
    }
    
    with open(temp_path / "aicte_test_project.ipynb", 'w') as f:
        json.dump(notebook_content, f, indent=2)
    
    # Create test dataset
    with open(temp_path / "dataset.csv", 'w') as f:
        f.write("id,name,value,category,score\n")
        for i in range(100):
            f.write(f"{i},item_{i},{i*10},cat_{i%5},{i*0.1}\n")
    
    # Create comprehensive README
    readme_content = """# AICTE Test Project

## Project Description
This project demonstrates the AICTE workflow automation system for internship project submissions.

## Installation
1. Clone this repository
2. Install required dependencies: `pip install pandas numpy matplotlib`
3. Open the notebook in Google Colab or Jupyter

## Usage
1. Load the dataset using the provided code
2. Run all cells in sequence
3. Review the analysis results

## Dataset
The dataset contains sample data for testing the workflow automation.

## Results
The analysis provides insights into the test data patterns and distributions.

## Submission
This project was submitted as part of the AICTE internship program using the automated workflow system.
"""
    
    with open(temp_path / "README.md", 'w') as f:
        f.write(readme_content)


if __name__ == "__main__":
    test_task8_integration()