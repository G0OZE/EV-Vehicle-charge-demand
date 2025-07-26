"""
Comprehensive demo showing EV charge demand analysis workflow.
"""
import sys
import os
sys.path.append('src')

from services.file_manager import FileManager
from datetime import datetime, timedelta
import json

def analyze_ev_dataset(file_path: str):
    """Analyze the EV dataset and provide insights."""
    import pandas as pd
    
    try:
        # Load the dataset
        df = pd.read_csv(file_path)
        
        # Clean column names (remove BOM if present)
        df.columns = df.columns.str.replace('\ufeff', '')
        
        print(f"📊 Dataset Analysis:")
        print(f"   • Total records: {len(df):,}")
        print(f"   • Date range: {df['Date'].min()} to {df['Date'].max()}")
        print(f"   • States covered: {df['State'].nunique()}")
        print(f"   • Counties covered: {df['County'].nunique()}")
        
        # Top states by EV adoption
        state_ev_totals = df.groupby('State')['Electric Vehicle (EV) Total'].sum().sort_values(ascending=False)
        print(f"\n🏆 Top 5 States by Total EVs:")
        for i, (state, total) in enumerate(state_ev_totals.head().items(), 1):
            print(f"   {i}. {state}: {total} EVs")
        
        # BEV vs PHEV analysis
        total_bevs = df['Battery Electric Vehicles (BEVs)'].sum()
        total_phevs = df['Plug-In Hybrid Electric Vehicles (PHEVs)'].sum()
        print(f"\n🔋 BEV vs PHEV Distribution:")
        print(f"   • Battery Electric Vehicles (BEVs): {total_bevs:,} ({total_bevs/(total_bevs+total_phevs)*100:.1f}%)")
        print(f"   • Plug-In Hybrid Electric Vehicles (PHEVs): {total_phevs:,} ({total_phevs/(total_bevs+total_phevs)*100:.1f}%)")
        
        # Vehicle use analysis
        use_distribution = df.groupby('Vehicle Primary Use')['Electric Vehicle (EV) Total'].sum()
        print(f"\n🚗 Vehicle Use Distribution:")
        for use_type, total in use_distribution.items():
            print(f"   • {use_type}: {total:,} EVs")
        
        # High adoption counties
        county_adoption = df.groupby(['County', 'State'])['Percent Electric Vehicles'].max().sort_values(ascending=False)
        print(f"\n🌟 Top 5 Counties by EV Percentage:")
        for i, ((county, state), percentage) in enumerate(county_adoption.head().items(), 1):
            print(f"   {i}. {county}, {state}: {percentage}%")
        
        return {
            'total_records': len(df),
            'states_count': df['State'].nunique(),
            'counties_count': df['County'].nunique(),
            'total_evs': df['Electric Vehicle (EV) Total'].sum(),
            'total_bevs': total_bevs,
            'total_phevs': total_phevs,
            'top_state': state_ev_totals.index[0],
            'analysis_complete': True
        }
        
    except Exception as e:
        print(f"❌ Error analyzing dataset: {e}")
        return {'analysis_complete': False, 'error': str(e)}

def main():
    """Demonstrate complete EV workflow with FileManager."""
    print("🚗 EV Charge Demand Analysis Workflow Demo")
    print("=" * 50)
    
    # Initialize FileManager
    fm = FileManager(base_directory="./test_projects")
    
    project_name = "ev_charge_demand_analysis"
    csv_file = "3ae033f50fa345051652.csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file '{csv_file}' not found!")
        return
    
    print(f"\n🔄 Step 1: Initialize Project")
    print(f"   ✅ Project initialized: {project_name}")
    
    print(f"\n📁 Step 2: Validate and Process Dataset")
    validation_result = fm.validate_dataset_file(csv_file)
    
    if validation_result['valid']:
        print(f"   ✅ Dataset validation passed:")
        print(f"      • Format: {validation_result['format'].upper()}")
        print(f"      • Columns: {validation_result['column_count']}")
        print(f"      • Rows analyzed: {validation_result['row_count']}")
        print(f"      • File size: {validation_result['file_size']:,} bytes")
        
        # Clean up column names for display
        clean_columns = [col.replace('\ufeff', '') for col in validation_result['columns']]
        print(f"      • Key columns: {', '.join(clean_columns[:3])}...")
    else:
        print(f"   ❌ Dataset validation failed: {validation_result['error']}")
        return
    
    print(f"\n📋 Step 3: Copy Dataset to Project")
    copy_result = fm.copy_local_file(csv_file, project_name, "ev_dataset.csv")
    
    if copy_result['success']:
        print(f"   ✅ Dataset copied successfully:")
        print(f"      • Destination: {copy_result['dest_path']}")
        print(f"      • Size: {copy_result['file_size']:,} bytes")
    else:
        print(f"   ❌ Failed to copy dataset: {copy_result['error']}")
        return
    
    print(f"\n📓 Step 4: Generate Jupyter Notebook")
    project_data = {
        'description': 'Electric Vehicle Charge Demand Analysis Project',
        'requirements': [
            'Load and explore the EV dataset with proper data cleaning',
            'Analyze EV adoption trends by state, county, and time period',
            'Compare Battery Electric Vehicles (BEVs) vs Plug-In Hybrid Electric Vehicles (PHEVs)',
            'Identify top-performing counties and states for EV adoption',
            'Create comprehensive visualizations (bar charts, time series, heatmaps)',
            'Develop insights and recommendations for policy makers',
            'Calculate growth rates and adoption patterns',
            'Analyze vehicle use patterns (Passenger vs Truck)',
            'Create a summary dashboard with key metrics',
            'Document findings and methodology clearly'
        ]
    }
    
    notebook_result = fm.create_notebook_from_template("", project_name, project_data)
    
    if notebook_result['success']:
        print(f"   ✅ Jupyter notebook created:")
        print(f"      • File: {notebook_result['filename']}")
        print(f"      • Path: {notebook_result['notebook_path']}")
    else:
        print(f"   ❌ Failed to create notebook: {notebook_result['error']}")
        return
    
    print(f"\n📊 Step 5: Analyze Dataset Content")
    analysis_result = analyze_ev_dataset(copy_result['dest_path'])
    
    if analysis_result.get('analysis_complete'):
        print(f"   ✅ Dataset analysis completed successfully")
    
    print(f"\n📦 Step 6: Prepare Upload Bundle")
    bundle_result = fm.prepare_upload_bundle(project_name)
    
    if bundle_result['success']:
        print(f"   ✅ Upload bundle prepared:")
        print(f"      • Total files: {bundle_result['total_files']}")
        print(f"      • Total size: {bundle_result['total_size']:,} bytes")
        print(f"      • Files included:")
        for file_info in bundle_result['files']:
            print(f"        - {file_info['filename']} ({file_info['type']}, {file_info['size']:,} bytes)")
    else:
        print(f"   ❌ Failed to prepare bundle: {bundle_result['error']}")
        return
    
    print(f"\n📋 Step 7: Project Summary")
    files_result = fm.get_project_files(project_name)
    
    if files_result['success']:
        print(f"   ✅ Project files summary:")
        print(f"      • Project directory: {files_result['project_directory']}")
        print(f"      • Total files: {files_result['total_files']}")
        print(f"      • Combined size: {files_result['total_size']:,} bytes")
        
        print(f"\n📁 Project Structure:")
        for file_info in files_result['files']:
            print(f"      • {file_info['filename']} ({file_info['size']:,} bytes)")
    
    print(f"\n🎉 Workflow Demo Completed Successfully!")
    print(f"   📂 Project location: {fm.base_directory / project_name}")
    print(f"   📊 Ready for GitHub upload and LMS submission")
    print(f"   🔗 Next steps: Upload to GitHub repository and submit to LMS")

if __name__ == "__main__":
    # Install pandas if not available
    try:
        import pandas as pd
    except ImportError:
        print("Installing pandas for dataset analysis...")
        os.system("pip install pandas")
        import pandas as pd
    
    main()