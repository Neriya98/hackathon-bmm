#!/usr/bin/env python3
"""
SecureDeal Application Entry Point
Professional Bitcoin Contract Management Platform
"""

import os
import sys
from flask.cli import FlaskGroup
from app import create_app, db
from app.models.user import User
from app.models.contract import Contract
from app.models.invitation import Invitation
from app.models.signature import Signature

# Create Flask application
app = create_app()
cli = FlaskGroup(app)

@cli.command("init-db")
def init_db():
    """Initialize the database."""
    db.create_all()
    print("Database initialized!")

@cli.command("create-admin")
def create_admin():
    """Create an admin user."""
    email = input("Admin email: ")
    password = input("Admin password: ")
    
    if User.query.filter_by(email=email).first():
        print("User already exists!")
        return
    
    admin = User(email=email, is_admin=True)
    admin.set_password(password)
    admin.email_verified = True
    
    db.session.add(admin)
    db.session.commit()
    
    print(f"Admin user {email} created successfully!")

@cli.command("reset-db")
def reset_db():
    """Reset the database (WARNING: This will delete all data!)."""
    confirm = input("Are you sure you want to reset the database? Type 'yes' to confirm: ")
    if confirm.lower() == 'yes':
        db.drop_all()
        db.create_all()
        print("Database reset successfully!")
    else:
        print("Database reset cancelled.")

@cli.command("seed-data")
def seed_data():
    """Seed the database with sample data."""
    # Create sample users
    users = []
    for i in range(3):
        user = User(email=f'user{i+1}@example.com')
        user.set_password('password123')
        user.email_verified = True
        users.append(user)
        db.session.add(user)
    
    db.session.commit()
    print(f"Created {len(users)} sample users")
    
    # Create sample contracts
    from app.models.contract import ContractType
    contracts = []
    for i, user in enumerate(users):
        contract = Contract(
            title=f'Sample Contract {i+1}',
            contract_type=ContractType.MULTISIG,
            amount_sats=1000000 * (i+1),  # 0.01, 0.02, 0.03 BTC
            creator_id=user.id,
            description=f'This is a sample multi-signature contract #{i+1}',
            required_signatures=2
        )
        contracts.append(contract)
        db.session.add(contract)
    
    db.session.commit()
    print(f"Created {len(contracts)} sample contracts")

@cli.command("build-rust")
def build_rust():
    """Build the Rust extension."""
    import subprocess
    import os
    
    rust_dir = os.path.join(os.path.dirname(__file__), 'rust_core')
    
    try:
        # Build with maturin
        result = subprocess.run(['maturin', 'build', '--release'], 
                              cwd=rust_dir, 
                              capture_output=True, 
                              text=True)
        
        if result.returncode == 0:
            print("Rust extension built successfully!")
            print(result.stdout)
        else:
            print("Failed to build Rust extension:")
            print(result.stderr)
            sys.exit(1)
            
    except FileNotFoundError:
        print("Error: maturin not found. Please install it with: pip install maturin")
        sys.exit(1)

@cli.command("install-rust")
def install_rust():
    """Install the Rust extension."""
    import subprocess
    import os
    import glob
    
    rust_dir = os.path.join(os.path.dirname(__file__), 'rust_core')
    wheels_dir = os.path.join(rust_dir, 'target', 'wheels')
    
    # Find the wheel file
    wheel_files = glob.glob(os.path.join(wheels_dir, '*.whl'))
    
    if not wheel_files:
        print("No wheel files found. Please run 'flask build-rust' first.")
        sys.exit(1)
    
    # Install the latest wheel
    latest_wheel = max(wheel_files, key=os.path.getctime)
    
    try:
        result = subprocess.run(['pip', 'install', '--force-reinstall', latest_wheel], 
                              capture_output=True, 
                              text=True)
        
        if result.returncode == 0:
            print(f"Rust extension installed successfully: {latest_wheel}")
        else:
            print("Failed to install Rust extension:")
            print(result.stderr)
            sys.exit(1)
            
    except FileNotFoundError:
        print("Error: pip not found.")
        sys.exit(1)

@cli.command("test")
def run_tests():
    """Run the test suite."""
    import subprocess
    
    try:
        result = subprocess.run(['pytest', '-v', 'tests/'], 
                              capture_output=True, 
                              text=True)
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
            
        sys.exit(result.returncode)
        
    except FileNotFoundError:
        print("Error: pytest not found. Please install it with: pip install pytest")
        sys.exit(1)

@cli.command("format")
def format_code():
    """Format the code with black."""
    import subprocess
    
    try:
        result = subprocess.run(['black', '.'], 
                              capture_output=True, 
                              text=True)
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
            
    except FileNotFoundError:
        print("Error: black not found. Please install it with: pip install black")

@cli.command("lint")
def lint_code():
    """Lint the code with flake8."""
    import subprocess
    
    try:
        result = subprocess.run(['flake8', '.'], 
                              capture_output=True, 
                              text=True)
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
            
        if result.returncode == 0:
            print("No linting errors found!")
        else:
            sys.exit(result.returncode)
            
    except FileNotFoundError:
        print("Error: flake8 not found. Please install it with: pip install flake8")

if __name__ == '__main__':
    cli()
