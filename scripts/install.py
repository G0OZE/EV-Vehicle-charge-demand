#!/usr/bin/env python3
"""
Installation script for AICTE Project Workflow Automation Tool.
Handles dependency installation, configuration setup, and environment validation.
"""
import os
import sys
import subprocess
import json
import shutil
import platform
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class InstallationError(Exception):
    """Custom exception for installation errors."""
    pass


class WorkflowInstaller:
    """Handles installation and setup of the AICTE workflow tool."""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.python_version = sys.version_info
        self.project_root = Path(__file__).parent.parent
        self.config_dir = self.project_root / "config"
        self.logs_dir = self.project_root / "logs"
        self.projects_dir = self.project_root / "projects"
        
        # Installation requirements
        self.min_python_version = (3, 8)
        self.required_packages = [
            "requests>=2.25.0",
            "click>=8.0.0",
            "colorama>=0.4.4",
            "python-dotenv>=0.19.0",
            "cryptography>=3.4.0",
            "psutil>=5.8.0"
        ]
        self.dev_packages = [
            "pytest>=6.2.0",
            "pytest-cov>=2.12.0",
            "black>=21.0.0",
            "flake8>=3.9.0",
            "mypy>=0.910"
        ]
    
    def run_installation(self, dev_mode: bool = False, force: bool = False) -> bool:
        """Run complete installation process."""
        try:
            print("🚀 Starting AICTE Project Workflow Tool Installation")
            print("=" * 60)
            
            # Pre-installation checks
            self._check_system_requirements()
            self._check_python_version()
            
            # Create directories
            self._create_directories()
            
            # Install dependencies
            self._install_dependencies(dev_mode)
            
            # Setup configuration
            self._setup_configuration(force)
            
            # Setup logging
            self._setup_logging()
            
            # Validate installation
            self._validate_installation()
            
            # Create shortcuts/scripts
            self._create_launch_scripts()
            
            print("\n✅ Installation completed successfully!")
            print("\n📋 Next steps:")
            print("1. Edit config.json with your GitHub credentials")
            print("2. Run: python -m src.cli.workflow_cli --help")
            print("3. Start your first project: python -m src.cli.workflow_cli start")
            
            return True
            
        except InstallationError as e:
            print(f"\n❌ Installation failed: {e}")
            return False
        except Exception as e:
            print(f"\n💥 Unexpected error during installation: {e}")
            return False
    
    def _check_system_requirements(self) -> None:
        """Check system requirements."""
        print("🔍 Checking system requirements...")
        
        # Check operating system
        supported_systems = ['windows', 'linux', 'darwin']
        if self.system not in supported_systems:
            raise InstallationError(f"Unsupported operating system: {platform.system()}")
        
        # Check available disk space (minimum 100MB)
        free_space = shutil.disk_usage(self.project_root).free
        min_space = 100 * 1024 * 1024  # 100MB
        if free_space < min_space:
            raise InstallationError(f"Insufficient disk space. Need at least 100MB, have {free_space // (1024*1024)}MB")
        
        # Check if git is available
        try:
            subprocess.run(['git', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  Warning: Git not found. Some features may not work properly.")
        
        print("✅ System requirements check passed")
    
    def _check_python_version(self) -> None:
        """Check Python version compatibility."""
        print(f"🐍 Checking Python version (current: {self.python_version.major}.{self.python_version.minor})...")
        
        if self.python_version < self.min_python_version:
            raise InstallationError(
                f"Python {self.min_python_version[0]}.{self.min_python_version[1]}+ required, "
                f"but {self.python_version.major}.{self.python_version.minor} found"
            )
        
        print("✅ Python version check passed")
    
    def _create_directories(self) -> None:
        """Create necessary directories."""
        print("📁 Creating directories...")
        
        directories = [
            self.logs_dir,
            self.projects_dir,
            self.project_root / "temp",
            self.project_root / "backups"
        ]
        
        for directory in directories:
            directory.mkdir(exist_ok=True)
            print(f"   Created: {directory}")
        
        print("✅ Directories created")
    
    def _install_dependencies(self, dev_mode: bool) -> None:
        """Install Python dependencies."""
        print("📦 Installing dependencies...")
        
        packages = self.required_packages.copy()
        if dev_mode:
            packages.extend(self.dev_packages)
            print("   Installing development dependencies...")
        
        # Upgrade pip first
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                         check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Warning: Could not upgrade pip: {e}")
        
        # Install packages
        for package in packages:
            try:
                print(f"   Installing {package}...")
                subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                             check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                raise InstallationError(f"Failed to install {package}: {e}")
        
        print("✅ Dependencies installed")
    
    def _setup_configuration(self, force: bool) -> None:
        """Setup configuration files."""
        print("⚙️  Setting up configuration...")
        
        config_file = self.project_root / "config.json"
        
        # Don't overwrite existing config unless forced
        if config_file.exists() and not force:
            print("   Configuration file already exists, skipping...")
            return
        
        # Copy appropriate template
        if os.getenv('ENVIRONMENT') == 'production':
            template_file = self.config_dir / "config.production.json"
        else:
            template_file = self.config_dir / "config.development.json"
        
        if template_file.exists():
            shutil.copy2(template_file, config_file)
            print(f"   Copied configuration from {template_file.name}")
        else:
            # Create basic config if template doesn't exist
            basic_config = {
                "github": {"token": "", "username": ""},
                "workflow": {"project_directory": "./projects"},
                "logging": {"level": "INFO", "file": "logs/workflow.log"}
            }
            with open(config_file, 'w') as f:
                json.dump(basic_config, f, indent=2)
            print("   Created basic configuration file")
        
        # Create .env template
        env_file = self.project_root / ".env.template"
        env_content = """# AICTE Project Workflow Environment Variables
# Copy this file to .env and fill in your values

# GitHub Configuration
GITHUB_TOKEN=your_github_token_here
GITHUB_USERNAME=your_github_username

# Optional: Override default settings
# LOG_LEVEL=INFO
# DEFAULT_PROJECT_DIR=./projects
# PROGRESS_FILE=workflow_progress.json
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print("✅ Configuration setup completed")
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        print("📝 Setting up logging...")
        
        # Create log files with proper permissions
        log_files = [
            self.logs_dir / "workflow.log",
            self.logs_dir / "error.log",
            self.logs_dir / "debug.log"
        ]
        
        for log_file in log_files:
            log_file.touch(exist_ok=True)
            if self.system != 'windows':
                # Set appropriate permissions on Unix systems
                os.chmod(log_file, 0o644)
        
        print("✅ Logging setup completed")
    
    def _validate_installation(self) -> None:
        """Validate that installation was successful."""
        print("🔍 Validating installation...")
        
        # Check that main modules can be imported
        try:
            sys.path.insert(0, str(self.project_root))
            
            from src.cli.workflow_cli import WorkflowCLI
            from src.services.workflow_core import WorkflowCore
            from src.services.github_service import GitHubService
            from src.utils.config import ConfigManager
            
            print("   ✅ Core modules import successfully")
            
            # Test configuration loading
            config = ConfigManager(str(self.project_root / "config.json"))
            print("   ✅ Configuration loads successfully")
            
            # Test CLI initialization
            cli = WorkflowCLI()
            print("   ✅ CLI initializes successfully")
            
        except ImportError as e:
            raise InstallationError(f"Module import failed: {e}")
        except Exception as e:
            raise InstallationError(f"Validation failed: {e}")
        
        print("✅ Installation validation passed")
    
    def _create_launch_scripts(self) -> None:
        """Create convenient launch scripts."""
        print("🚀 Creating launch scripts...")
        
        # Create platform-specific launch scripts
        if self.system == 'windows':
            self._create_windows_scripts()
        else:
            self._create_unix_scripts()
        
        print("✅ Launch scripts created")
    
    def _create_windows_scripts(self) -> None:
        """Create Windows batch scripts."""
        # Main launcher
        launcher_content = f"""@echo off
cd /d "{self.project_root}"
python -m src.cli.workflow_cli %*
"""
        with open(self.project_root / "workflow.bat", 'w') as f:
            f.write(launcher_content)
        
        # Quick start script
        quickstart_content = f"""@echo off
cd /d "{self.project_root}"
echo Starting AICTE Project Workflow Tool...
python -m src.cli.workflow_cli start
pause
"""
        with open(self.project_root / "quickstart.bat", 'w') as f:
            f.write(quickstart_content)
    
    def _create_unix_scripts(self) -> None:
        """Create Unix shell scripts."""
        # Main launcher
        launcher_content = f"""#!/bin/bash
cd "{self.project_root}"
python3 -m src.cli.workflow_cli "$@"
"""
        launcher_file = self.project_root / "workflow.sh"
        with open(launcher_file, 'w') as f:
            f.write(launcher_content)
        os.chmod(launcher_file, 0o755)
        
        # Quick start script
        quickstart_content = f"""#!/bin/bash
cd "{self.project_root}"
echo "Starting AICTE Project Workflow Tool..."
python3 -m src.cli.workflow_cli start
"""
        quickstart_file = self.project_root / "quickstart.sh"
        with open(quickstart_file, 'w') as f:
            f.write(quickstart_content)
        os.chmod(quickstart_file, 0o755)
    
    def uninstall(self) -> bool:
        """Uninstall the workflow tool."""
        try:
            print("🗑️  Uninstalling AICTE Project Workflow Tool...")
            
            # Remove created directories (except projects)
            dirs_to_remove = [
                self.logs_dir,
                self.project_root / "temp",
                self.project_root / "backups"
            ]
            
            for directory in dirs_to_remove:
                if directory.exists():
                    shutil.rmtree(directory)
                    print(f"   Removed: {directory}")
            
            # Remove launch scripts
            scripts_to_remove = [
                "workflow.bat", "quickstart.bat",  # Windows
                "workflow.sh", "quickstart.sh"    # Unix
            ]
            
            for script in scripts_to_remove:
                script_path = self.project_root / script
                if script_path.exists():
                    script_path.unlink()
                    print(f"   Removed: {script}")
            
            # Ask about configuration and projects
            response = input("Remove configuration files? (y/N): ").lower()
            if response == 'y':
                config_file = self.project_root / "config.json"
                if config_file.exists():
                    config_file.unlink()
                    print("   Removed: config.json")
            
            response = input("Remove projects directory? (y/N): ").lower()
            if response == 'y' and self.projects_dir.exists():
                shutil.rmtree(self.projects_dir)
                print("   Removed: projects directory")
            
            print("✅ Uninstallation completed")
            return True
            
        except Exception as e:
            print(f"❌ Uninstallation failed: {e}")
            return False


def main():
    """Main installation function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AICTE Project Workflow Tool Installer")
    parser.add_argument('--dev', action='store_true', help='Install development dependencies')
    parser.add_argument('--force', action='store_true', help='Force overwrite existing configuration')
    parser.add_argument('--uninstall', action='store_true', help='Uninstall the tool')
    
    args = parser.parse_args()
    
    installer = WorkflowInstaller()
    
    if args.uninstall:
        success = installer.uninstall()
    else:
        success = installer.run_installation(dev_mode=args.dev, force=args.force)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()