"""
Demo script to test FileManager with the provided CSV data.
"""
import sys
import os
sys.path.append('src')

from services.file_manager import FileManager
import json

def main():
    """Test FileManager functionality with real CSV data."""
    print("Testing FileManager with provided CSV data...")
    
    # Initialize FileManager
    fm = FileManager(base_directory="./test_projects")
    project_name = "ev_analysis_demo"
    
    print(f"\n1. Testing CSV file validation with provided data...")
    csv_file = "3ae033f50fa345051652.csv"
    
    if os.path.exists(csv_file):
        validation_result = fm.validate_dataset_file(csv_file)
        print(f"Validation result: {json.dumps(validation_result, indent=2)}")
        
        print(f"\n2. Copying CSV file to project directory...")
        copy_result = fm.copy_local_file(csv_file, project_name, "ev_dataset.csv")
        print(f"Copy result: {json.dumps(copy_result, indent=2)}")
        
        if copy_result['success']:
            print(f"\n3. Creating Jupyter notebook...")
            project_data = {
                'description': 'Electric Vehicle Analysis - AICTE Internship Project',
                'requirements': [
                    'Analyze EV adoption trends by state and county',
                    'Compare Battery Electric Vehicles (BEVs) vs Plug-In Hybrid Electric Vehicles (PHEVs)',
                    'Identify top performing counties for EV adoption',
                    'Create visualizations showing EV percentage over time',
                    'Develop insights for policy recommendations'
                ]
            }
            
            notebook_result = fm.create_notebook_from_template("", project_name, project_data)
            print(f"Notebook creation result: {json.dumps(notebook_result, indent=2)}")
            
            print(f"\n4. Preparing upload bundle...")
            bundle_result = fm.prepare_upload_bundle(project_name)
            print(f"Bundle preparation result: {json.dumps(bundle_result, indent=2)}")
            
            print(f"\n5. Getting project files list...")
            files_result = fm.get_project_files(project_name)
            print(f"Project files: {json.dumps(files_result, indent=2)}")
            
            print(f"\n✅ FileManager testing completed successfully!")
            print(f"Project created at: {fm.base_directory / project_name}")
            
    else:
        print(f"❌ CSV file '{csv_file}' not found in current directory")

if __name__ == "__main__":
    main()