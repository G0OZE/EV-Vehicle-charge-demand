"""
Tests for FileManager service using real CSV data.
"""
import pytest
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import patch, Mock
from src.services.file_manager import FileManager


class TestFileManager:
    """Test cases for FileManager functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.file_manager = FileManager(base_directory=self.temp_dir)
        self.test_project_name = "test_ev_analysis"
        
        # Create test CSV data (sample from the provided CSV)
        self.test_csv_content = """Date,County,State,Vehicle Primary Use,Battery Electric Vehicles (BEVs),Plug-In Hybrid Electric Vehicles (PHEVs),Electric Vehicle (EV) Total,Non-Electric Vehicle Total,Total Vehicles,Percent Electric Vehicles
September 30 2022,Riverside,CA,Passenger,7,0,7,460,467,1.50
December 31 2022,Prince William,VA,Passenger,1,2,3,188,191,1.57
January 31 2020,Dakota,MN,Passenger,0,1,1,32,33,3.03
June 30 2022,Ferry,WA,Truck,0,0,0,"3,575","3,575",0.00
July 31 2021,Douglas,CO,Passenger,0,1,1,83,84,1.19"""
        
        # Create test CSV file
        self.test_csv_path = Path(self.temp_dir) / "test_data.csv"
        with open(self.test_csv_path, 'w', encoding='utf-8') as f:
            f.write(self.test_csv_content)
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_validate_csv_file_success(self):
        """Test successful CSV file validation."""
        result = self.file_manager.validate_dataset_file(str(self.test_csv_path))
        
        assert result['valid'] is True
        assert result['format'] == 'csv'
        assert len(result['columns']) == 10
        assert 'Date' in result['columns']
        assert 'County' in result['columns']
        assert 'State' in result['columns']
        assert 'Battery Electric Vehicles (BEVs)' in result['columns']
        assert result['column_count'] == 10
        assert result['row_count'] > 0
        assert result['delimiter'] == ','
    
    def test_validate_csv_file_with_real_data_structure(self):
        """Test CSV validation with the actual data structure from provided file."""
        result = self.file_manager.validate_dataset_file(str(self.test_csv_path))
        
        # Verify expected columns from the EV dataset
        expected_columns = [
            'Date', 'County', 'State', 'Vehicle Primary Use',
            'Battery Electric Vehicles (BEVs)', 'Plug-In Hybrid Electric Vehicles (PHEVs)',
            'Electric Vehicle (EV) Total', 'Non-Electric Vehicle Total',
            'Total Vehicles', 'Percent Electric Vehicles'
        ]
        
        assert result['valid'] is True
        assert result['columns'] == expected_columns
        assert result['column_count'] == len(expected_columns)
    
    def test_validate_nonexistent_file(self):
        """Test validation of non-existent file."""
        result = self.file_manager.validate_dataset_file("nonexistent.csv")
        
        assert result['valid'] is False
        assert 'does not exist' in result['error']
    
    def test_validate_unsupported_format(self):
        """Test validation of unsupported file format."""
        # Create a file with unsupported extension
        unsupported_file = Path(self.temp_dir) / "test.xyz"
        unsupported_file.write_text("test content")
        
        result = self.file_manager.validate_dataset_file(str(unsupported_file))
        
        assert result['valid'] is False
        assert 'Unsupported file format' in result['error']
    
    def test_copy_local_file_success(self):
        """Test successful local file copy."""
        result = self.file_manager.copy_local_file(
            str(self.test_csv_path), 
            self.test_project_name,
            "ev_data.csv"
        )
        
        assert result['success'] is True
        assert result['filename'] == "ev_data.csv"
        assert Path(result['dest_path']).exists()
        assert result['validation']['valid'] is True
    
    def test_copy_nonexistent_file(self):
        """Test copying non-existent file."""
        result = self.file_manager.copy_local_file(
            "nonexistent.csv",
            self.test_project_name
        )
        
        assert result['success'] is False
        assert 'does not exist' in result['error']
    
    @patch('requests.get')
    def test_download_dataset_success(self, mock_get):
        """Test successful dataset download."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.iter_content.return_value = [self.test_csv_content.encode('utf-8')]
        mock_get.return_value = mock_response
        
        result = self.file_manager.download_dataset(
            "https://example.com/dataset.csv",
            self.test_project_name
        )
        
        assert result['success'] is True
        assert result['filename'] == "dataset.csv"
        assert Path(result['file_path']).exists()
        assert result['validation']['valid'] is True
    
    @patch('requests.get')
    def test_download_dataset_network_error(self, mock_get):
        """Test dataset download with network error."""
        mock_get.side_effect = Exception("Network error")
        
        result = self.file_manager.download_dataset(
            "https://example.com/dataset.csv",
            self.test_project_name
        )
        
        assert result['success'] is False
        assert 'Failed to download dataset' in result['error']
    
    def test_download_dataset_invalid_url(self):
        """Test dataset download with invalid URL."""
        result = self.file_manager.download_dataset(
            "invalid-url",
            self.test_project_name
        )
        
        assert result['success'] is False
        assert 'Invalid dataset URL' in result['error']
    
    def test_create_notebook_from_template(self):
        """Test notebook creation from template."""
        project_data = {
            'description': 'Electric Vehicle Analysis Project',
            'requirements': [
                'Analyze EV adoption trends by state',
                'Compare BEV vs PHEV distribution',
                'Identify top counties for EV adoption'
            ]
        }
        
        result = self.file_manager.create_notebook_from_template(
            "",  # Template path not used in current implementation
            self.test_project_name,
            project_data
        )
        
        assert result['success'] is True
        assert result['filename'] == f"{self.test_project_name}.ipynb"
        
        # Verify notebook file was created
        notebook_path = Path(result['notebook_path'])
        assert notebook_path.exists()
        
        # Verify notebook content
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook_content = json.load(f)
        
        assert notebook_content['nbformat'] == 4
        assert len(notebook_content['cells']) > 0
        
        # Check that project data was included
        first_cell = notebook_content['cells'][0]
        assert first_cell['cell_type'] == 'markdown'
        assert self.test_project_name in ''.join(first_cell['source'])
        assert project_data['description'] in ''.join(first_cell['source'])
    
    def test_prepare_upload_bundle(self):
        """Test preparation of upload bundle."""
        # First create some files in the project directory
        self.file_manager.copy_local_file(
            str(self.test_csv_path),
            self.test_project_name,
            "dataset.csv"
        )
        
        project_data = {
            'description': 'Test project',
            'requirements': ['Test requirement']
        }
        self.file_manager.create_notebook_from_template(
            "",
            self.test_project_name,
            project_data
        )
        
        # Test bundle preparation
        result = self.file_manager.prepare_upload_bundle(self.test_project_name)
        
        assert result['success'] is True
        assert result['total_files'] >= 2  # At least notebook and dataset
        assert any(f['type'] == 'notebook' for f in result['files'])
        assert any(f['type'] == 'dataset' for f in result['files'])
        assert result['total_size'] > 0
    
    def test_prepare_upload_bundle_nonexistent_project(self):
        """Test upload bundle preparation for non-existent project."""
        result = self.file_manager.prepare_upload_bundle("nonexistent_project")
        
        assert result['success'] is False
        assert 'does not exist' in result['error']
    
    def test_get_project_files(self):
        """Test getting project files list."""
        # Create some files
        self.file_manager.copy_local_file(
            str(self.test_csv_path),
            self.test_project_name,
            "data.csv"
        )
        
        result = self.file_manager.get_project_files(self.test_project_name)
        
        assert result['success'] is True
        assert result['total_files'] >= 1
        assert any(f['filename'] == 'data.csv' for f in result['files'])
        assert result['total_size'] > 0
    
    def test_get_project_files_nonexistent_project(self):
        """Test getting files for non-existent project."""
        result = self.file_manager.get_project_files("nonexistent_project")
        
        assert result['success'] is False
        assert 'does not exist' in result['error']
    
    def test_validate_json_file(self):
        """Test JSON file validation."""
        # Create test JSON file
        test_json_data = {
            "project": "test",
            "data": [{"id": 1, "value": "test"}]
        }
        json_path = Path(self.temp_dir) / "test.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(test_json_data, f)
        
        result = self.file_manager.validate_dataset_file(str(json_path))
        
        assert result['valid'] is True
        assert result['format'] == 'json'
        assert result['data_type'] == 'dict'
        assert 'project' in result['sample_keys']
    
    def test_validate_malformed_csv(self):
        """Test validation of malformed CSV file."""
        # Create malformed CSV
        malformed_csv = Path(self.temp_dir) / "malformed.csv"
        with open(malformed_csv, 'w', encoding='utf-8') as f:
            f.write("col1,col2\n")
            f.write("val1\n")  # Missing column
            f.write("val1,val2,val3\n")  # Extra column
        
        result = self.file_manager.validate_dataset_file(str(malformed_csv))
        
        assert result['valid'] is True  # Still valid CSV, just inconsistent
        assert len(result['inconsistent_rows']) > 0
    
    def test_cleanup_temp_files(self):
        """Test temporary files cleanup."""
        # Create some temp files
        temp_file = self.file_manager.temp_directory / "temp_test.txt"
        temp_file.write_text("test content")
        
        assert temp_file.exists()
        
        result = self.file_manager.cleanup_temp_files()
        
        assert result is True
        assert not temp_file.exists()
        assert self.file_manager.temp_directory.exists()  # Directory should still exist
    
    def test_file_manager_initialization(self):
        """Test FileManager initialization."""
        # Test with custom directory
        custom_dir = Path(self.temp_dir) / "custom"
        fm = FileManager(base_directory=str(custom_dir))
        
        assert fm.base_directory == custom_dir
        assert custom_dir.exists()
        assert fm.temp_directory.exists()
    
    def test_csv_with_quoted_values(self):
        """Test CSV validation with quoted values (like in the real dataset)."""
        # Create CSV with quoted values like in the real dataset
        csv_with_quotes = """Date,County,State,Total Vehicles,Percent
June 30 2022,Ferry,WA,"3,575",0.00
July 31 2021,Douglas,CO,"1,234",1.19"""
        
        quoted_csv_path = Path(self.temp_dir) / "quoted.csv"
        with open(quoted_csv_path, 'w', encoding='utf-8') as f:
            f.write(csv_with_quotes)
        
        result = self.file_manager.validate_dataset_file(str(quoted_csv_path))
        
        assert result['valid'] is True
        assert result['format'] == 'csv'
        assert result['column_count'] == 5
        assert len(result['inconsistent_rows']) == 0  # Should handle quoted values correctly


if __name__ == "__main__":
    pytest.main([__file__])