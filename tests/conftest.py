import os
import tempfile
import pytest
from app import create_app, db
from app.models.user import User
from app.models.contract import Contract, ContractType
from app.models.invitation import Invitation
from app.models.signature import Signature
from config import TestingConfig


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    
    # Set environment variables for testing
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    
    app = create_app('config.TestingConfig')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


@pytest.fixture
def auth(client):
    """Authentication helper."""
    class AuthActions:
        def __init__(self, client):
            self._client = client

        def register(self, email='test@example.com', password='testpass123'):
            return self._client.post(
                '/auth/register',
                data={'email': email, 'password': password, 'password2': password, 'accept_terms': True}
            )

        def login(self, email='test@example.com', password='testpass123'):
            return self._client.post(
                '/auth/login',
                data={'email': email, 'password': password}
            )

        def logout(self):
            return self._client.get('/auth/logout')

    return AuthActions(client)


@pytest.fixture
def user(app):
    """Create a test user."""
    with app.app_context():
        user = User(email='test@example.com')
        user.set_password('testpass123')
        user.email_verified = True
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def admin_user(app):
    """Create an admin test user."""
    with app.app_context():
        user = User(email='admin@example.com', is_admin=True)
        user.set_password('adminpass123')
        user.email_verified = True
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def contract(app, user):
    """Create a test contract."""
    with app.app_context():
        contract = Contract(
            title='Test Contract',
            contract_type=ContractType.MULTISIG,
            amount_sats=10000000,  # 0.1 BTC in satoshis
            creator_id=user.id,
            description='A test Bitcoin contract',
            required_signatures=2,
            psbt_base64='test_psbt_base64'
        )
        db.session.add(contract)
        db.session.commit()
        return contract


@pytest.fixture
def invitation(app, contract, user):
    """Create a test invitation."""
    with app.app_context():
        invitation = Invitation(
            recipient_email='invitee@example.com',
            contract_id=contract.id,
            sender_id=user.id,
            role='signer'
        )
        db.session.add(invitation)
        db.session.commit()
        return invitation
