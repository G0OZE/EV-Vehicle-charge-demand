#!/usr/bin/env python3
"""
Deployment script for AICTE Project Workflow Automation Tool.
Handles deployment to various environments including Docker, systemd, and cloud platforms.
"""
import os
import sys
import subprocess
import json
import shutil
import platform
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional


class DeploymentError(Exception):
    """Custom exception for deployment errors."""
    pass


class WorkflowDeployer:
    """Handles deployment of the AICTE workflow tool."""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.project_root = Path(__file__).parent.parent
        self.deployment_dir = self.project_root / "deployment"
        self.config_dir = self.project_root / "config"
        
    def deploy(self, environment: str, deployment_type: str, **kwargs) -> bool:
        """
        Deploy the workflow tool to specified environment.
        
        Args:
            environment: Target environment (development, staging, production)
            deployment_type: Type of deployment (local, docker, systemd, cloud)
            **kwargs: Additional deployment options
            
        Returns:
            True if deployment successful, False otherwise
        """
        try:
            print(f"🚀 Starting deployment to {environment} using {deployment_type}")
            print("=" * 60)
            
            # Validate deployment parameters
            self._validate_deployment_params(environment, deployment_type)
            
            # Pre-deployment checks
            self._pre_deployment_checks(environment)
            
            # Execute deployment based on type
            if deployment_type == "local":
                success = self._deploy_local(environment, **kwargs)
            elif deployment_type == "docker":
                success = self._deploy_docker(environment, **kwargs)
            elif deployment_type == "systemd":
                success = self._deploy_systemd(environment, **kwargs)
            elif deployment_type == "cloud":
                success = self._deploy_cloud(environment, **kwargs)
            else:
                raise DeploymentError(f"Unsupported deployment type: {deployment_type}")
            
            if success:
                self._post_deployment_tasks(environment, deployment_type)
                print("\n✅ Deployment completed successfully!")
                self._print_next_steps(environment, deployment_type)
            
            return success
            
        except DeploymentError as e:
            print(f"\n❌ Deployment failed: {e}")
            return False
        except Exception as e:
            print(f"\n💥 Unexpected error during deployment: {e}")
            return False
    
    def _validate_deployment_params(self, environment: str, deployment_type: str) -> None:
        """Validate deployment parameters."""
        valid_environments = ['development', 'staging', 'production']
        if environment not in valid_environments:
            raise DeploymentError(f"Invalid environment: {environment}. Must be one of {valid_environments}")
        
        valid_types = ['local', 'docker', 'systemd', 'cloud']
        if deployment_type not in valid_types:
            raise DeploymentError(f"Invalid deployment type: {deployment_type}. Must be one of {valid_types}")
    
    def _pre_deployment_checks(self, environment: str) -> None:
        """Perform pre-deployment checks."""
        print("🔍 Performing pre-deployment checks...")
        
        # Check if configuration exists
        config_file = self.project_root / "config.json"
        if not config_file.exists():
            # Try to use environment-specific config
            env_config = self.config_dir / f"config.{environment}.json"
            if env_config.exists():
                shutil.copy2(env_config, config_file)
                print(f"   Copied {env_config.name} to config.json")
            else:
                raise DeploymentError(f"No configuration file found for {environment}")
        
        # Validate configuration
        from src.utils.config_validator import validate_configuration
        if not validate_configuration(str(config_file)):
            raise DeploymentError("Configuration validation failed")
        
        # Check dependencies
        self._check_dependencies()
        
        print("✅ Pre-deployment checks passed")
    
    def _check_dependencies(self) -> None:
        """Check if all dependencies are available."""
        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 8):
            raise DeploymentError(f"Python 3.8+ required, found {python_version.major}.{python_version.minor}")
        
        # Check required packages
        required_packages = ['requests', 'click', 'colorama']
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                raise DeploymentError(f"Required package '{package}' not installed")
    
    def _deploy_local(self, environment: str, **kwargs) -> bool:
        """Deploy locally (development/testing)."""
        print("📦 Deploying locally...")
        
        # Create virtual environment if requested
        if kwargs.get('create_venv', False):
            venv_path = self.project_root / ".venv"
            if not venv_path.exists():
                subprocess.run([sys.executable, '-m', 'venv', str(venv_path)], check=True)
                print(f"   Created virtual environment: {venv_path}")
        
        # Install dependencies
        if kwargs.get('install_deps', True):
            pip_cmd = [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt']
            subprocess.run(pip_cmd, cwd=self.project_root, check=True)
            print("   Installed dependencies")
        
        # Create necessary directories
        self._create_directories()
        
        # Setup logging
        self._setup_logging(environment)
        
        # Create launch scripts
        self._create_launch_scripts()
        
        return True
    
    def _deploy_docker(self, environment: str, **kwargs) -> bool:
        """Deploy using Docker."""
        print("🐳 Deploying with Docker...")
        
        # Check if Docker is available
        try:
            subprocess.run(['docker', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise DeploymentError("Docker not found. Please install Docker first.")
        
        # Build Docker image
        image_name = kwargs.get('image_name', 'aicte-workflow-tool')
        tag = kwargs.get('tag', environment)
        
        build_cmd = [
            'docker', 'build',
            '-t', f"{image_name}:{tag}",
            '-f', str(self.deployment_dir / 'docker' / 'Dockerfile'),
            str(self.project_root)
        ]
        
        subprocess.run(build_cmd, check=True)
        print(f"   Built Docker image: {image_name}:{tag}")
        
        # Deploy with docker-compose if requested
        if kwargs.get('use_compose', True):
            compose_file = self.deployment_dir / 'docker' / 'docker-compose.yml'
            compose_cmd = ['docker-compose', '-f', str(compose_file), 'up', '-d']
            
            # Set environment variables
            env = os.environ.copy()
            env['ENVIRONMENT'] = environment
            
            subprocess.run(compose_cmd, env=env, check=True)
            print("   Started services with docker-compose")
        
        return True
    
    def _deploy_systemd(self, environment: str, **kwargs) -> bool:
        """Deploy as systemd service (Linux only)."""
        if self.system != 'linux':
            raise DeploymentError("Systemd deployment only supported on Linux")
        
        print("⚙️  Deploying as systemd service...")
        
        # Create systemd service file
        service_content = self._generate_systemd_service(environment, **kwargs)
        service_file = Path(f"/etc/systemd/system/aicte-workflow.service")
        
        # Write service file (requires sudo)
        try:
            with open(service_file, 'w') as f:
                f.write(service_content)
        except PermissionError:
            # Try with sudo
            temp_file = Path("/tmp/aicte-workflow.service")
            with open(temp_file, 'w') as f:
                f.write(service_content)
            
            subprocess.run(['sudo', 'mv', str(temp_file), str(service_file)], check=True)
        
        # Reload systemd and enable service
        subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
        subprocess.run(['sudo', 'systemctl', 'enable', 'aicte-workflow'], check=True)
        
        if kwargs.get('start_service', True):
            subprocess.run(['sudo', 'systemctl', 'start', 'aicte-workflow'], check=True)
            print("   Started systemd service")
        
        return True
    
    def _deploy_cloud(self, environment: str, **kwargs) -> bool:
        """Deploy to cloud platform."""
        cloud_provider = kwargs.get('provider', 'aws')
        
        print(f"☁️  Deploying to {cloud_provider}...")
        
        if cloud_provider == 'aws':
            return self._deploy_aws(environment, **kwargs)
        elif cloud_provider == 'gcp':
            return self._deploy_gcp(environment, **kwargs)
        elif cloud_provider == 'azure':
            return self._deploy_azure(environment, **kwargs)
        else:
            raise DeploymentError(f"Unsupported cloud provider: {cloud_provider}")
    
    def _deploy_aws(self, environment: str, **kwargs) -> bool:
        """Deploy to AWS."""
        # This would implement AWS-specific deployment
        # For now, just create deployment configuration
        
        aws_config = {
            "region": kwargs.get('region', 'us-east-1'),
            "instance_type": kwargs.get('instance_type', 't3.micro'),
            "environment": environment
        }
        
        aws_config_file = self.deployment_dir / f"aws-{environment}.json"
        with open(aws_config_file, 'w') as f:
            json.dump(aws_config, f, indent=2)
        
        print(f"   Created AWS deployment configuration: {aws_config_file}")
        print("   Note: AWS deployment requires additional setup with AWS CLI/CDK")
        
        return True
    
    def _deploy_gcp(self, environment: str, **kwargs) -> bool:
        """Deploy to Google Cloud Platform."""
        # Placeholder for GCP deployment
        print("   GCP deployment not yet implemented")
        return True
    
    def _deploy_azure(self, environment: str, **kwargs) -> bool:
        """Deploy to Microsoft Azure."""
        # Placeholder for Azure deployment
        print("   Azure deployment not yet implemented")
        return True
    
    def _create_directories(self) -> None:
        """Create necessary directories."""
        directories = ['logs', 'projects', 'temp', 'backups']
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(exist_ok=True)
    
    def _setup_logging(self, environment: str) -> None:
        """Setup logging configuration."""
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # Create log files
        log_files = ['workflow.log', 'error.log', 'debug.log']
        for log_file in log_files:
            (log_dir / log_file).touch(exist_ok=True)
    
    def _create_launch_scripts(self) -> None:
        """Create platform-specific launch scripts."""
        if self.system == 'windows':
            self._create_windows_scripts()
        else:
            self._create_unix_scripts()
    
    def _create_windows_scripts(self) -> None:
        """Create Windows batch scripts."""
        launcher_content = f"""@echo off
cd /d "{self.project_root}"
python -m src.cli.workflow_cli %*
"""
        with open(self.project_root / "workflow.bat", 'w') as f:
            f.write(launcher_content)
    
    def _create_unix_scripts(self) -> None:
        """Create Unix shell scripts."""
        launcher_content = f"""#!/bin/bash
cd "{self.project_root}"
python3 -m src.cli.workflow_cli "$@"
"""
        launcher_file = self.project_root / "workflow.sh"
        with open(launcher_file, 'w') as f:
            f.write(launcher_content)
        os.chmod(launcher_file, 0o755)
    
    def _generate_systemd_service(self, environment: str, **kwargs) -> str:
        """Generate systemd service file content."""
        user = kwargs.get('user', 'workflow')
        working_dir = kwargs.get('working_dir', str(self.project_root))
        
        return f"""[Unit]
Description=AICTE Project Workflow Automation Tool
After=network.target

[Service]
Type=simple
User={user}
WorkingDirectory={working_dir}
Environment=ENVIRONMENT={environment}
ExecStart={sys.executable} -m src.cli.workflow_cli daemon
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    def _post_deployment_tasks(self, environment: str, deployment_type: str) -> None:
        """Perform post-deployment tasks."""
        print("🔧 Performing post-deployment tasks...")
        
        # Run configuration validation
        from src.utils.config_validator import validate_configuration
        if validate_configuration():
            print("   Configuration validation passed")
        
        # Create backup of current configuration
        config_file = self.project_root / "config.json"
        if config_file.exists():
            backup_file = self.project_root / "backups" / f"config-{environment}-backup.json"
            backup_file.parent.mkdir(exist_ok=True)
            shutil.copy2(config_file, backup_file)
            print(f"   Created configuration backup: {backup_file}")
    
    def _print_next_steps(self, environment: str, deployment_type: str) -> None:
        """Print next steps for the user."""
        print("\n📋 Next steps:")
        
        if deployment_type == "local":
            print("1. Verify configuration in config.json")
            print("2. Test the installation: python -m src.cli.workflow_cli --help")
            print("3. Start your first project: python -m src.cli.workflow_cli start")
        
        elif deployment_type == "docker":
            print("1. Check container status: docker ps")
            print("2. View logs: docker logs aicte-workflow-tool")
            print("3. Access the tool: docker exec -it aicte-workflow-tool bash")
        
        elif deployment_type == "systemd":
            print("1. Check service status: sudo systemctl status aicte-workflow")
            print("2. View logs: sudo journalctl -u aicte-workflow -f")
            print("3. Restart service: sudo systemctl restart aicte-workflow")
        
        elif deployment_type == "cloud":
            print("1. Verify cloud resources are created")
            print("2. Configure monitoring and alerting")
            print("3. Test connectivity and functionality")
    
    def rollback(self, environment: str, deployment_type: str) -> bool:
        """Rollback deployment."""
        try:
            print(f"🔄 Rolling back {deployment_type} deployment for {environment}...")
            
            if deployment_type == "docker":
                compose_file = self.deployment_dir / 'docker' / 'docker-compose.yml'
                subprocess.run(['docker-compose', '-f', str(compose_file), 'down'], check=True)
                print("   Stopped Docker services")
            
            elif deployment_type == "systemd":
                subprocess.run(['sudo', 'systemctl', 'stop', 'aicte-workflow'], check=True)
                subprocess.run(['sudo', 'systemctl', 'disable', 'aicte-workflow'], check=True)
                print("   Stopped and disabled systemd service")
            
            # Restore configuration backup if available
            backup_file = self.project_root / "backups" / f"config-{environment}-backup.json"
            if backup_file.exists():
                config_file = self.project_root / "config.json"
                shutil.copy2(backup_file, config_file)
                print("   Restored configuration backup")
            
            print("✅ Rollback completed")
            return True
            
        except Exception as e:
            print(f"❌ Rollback failed: {e}")
            return False


def main():
    """Main deployment function."""
    parser = argparse.ArgumentParser(description="AICTE Project Workflow Tool Deployer")
    parser.add_argument('environment', choices=['development', 'staging', 'production'],
                       help='Target environment')
    parser.add_argument('deployment_type', choices=['local', 'docker', 'systemd', 'cloud'],
                       help='Deployment type')
    parser.add_argument('--rollback', action='store_true', help='Rollback deployment')
    parser.add_argument('--image-name', default='aicte-workflow-tool', help='Docker image name')
    parser.add_argument('--tag', help='Docker image tag (defaults to environment)')
    parser.add_argument('--provider', choices=['aws', 'gcp', 'azure'], default='aws',
                       help='Cloud provider for cloud deployment')
    parser.add_argument('--region', default='us-east-1', help='Cloud region')
    parser.add_argument('--create-venv', action='store_true', help='Create virtual environment')
    parser.add_argument('--no-install-deps', action='store_true', help='Skip dependency installation')
    parser.add_argument('--user', default='workflow', help='User for systemd service')
    
    args = parser.parse_args()
    
    deployer = WorkflowDeployer()
    
    kwargs = {
        'image_name': args.image_name,
        'tag': args.tag or args.environment,
        'provider': args.provider,
        'region': args.region,
        'create_venv': args.create_venv,
        'install_deps': not args.no_install_deps,
        'user': args.user
    }
    
    if args.rollback:
        success = deployer.rollback(args.environment, args.deployment_type)
    else:
        success = deployer.deploy(args.environment, args.deployment_type, **kwargs)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()