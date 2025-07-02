from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
import redis
import structlog

# Extensions globales
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
mail = Mail()
limiter = Limiter(key_func=get_remote_address)
csrf = CSRFProtect()

# Logger structuré
logger = structlog.get_logger()

def create_app(config_object='config.DevelopmentConfig'):
    """Factory pour créer l'application Flask"""
    
    app = Flask(__name__)
    app.config.from_object(config_object)
    
    # Configuration du logging structuré
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Initialiser les extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    csrf.init_app(app)
    
    # Configuration CORS sécurisée
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": app.config.get('ALLOWED_ORIGINS', ["http://localhost:3000"]),
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    mail.init_app(app)
    
    # Rate limiting avec Redis
    limiter.init_app(app)
    
    # Configuration JWT
    setup_jwt(app)
    
    # Context processor pour CSRF token
    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)
    
    # Context processor pour current_user
    @app.context_processor
    def inject_current_user():
        from flask import session
        # For now, return a simple anonymous user object
        # This should be replaced with proper JWT-based authentication
        class AnonymousUser:
            is_authenticated = False
            is_anonymous = True
        
        return dict(current_user=AnonymousUser())
    
    # Importer et enregistrer les modèles
    from app.models import user, contract, signature, invitation
    
    # Enregistrer les blueprints
    from app.api import auth, contracts, psbt
    from app.routes import main
    
    app.register_blueprint(auth.bp, url_prefix='/api/auth')
    app.register_blueprint(contracts.bp, url_prefix='/api/contracts')
    app.register_blueprint(psbt.bp, url_prefix='/api/psbt')
    app.register_blueprint(main.bp)
    
    # Handlers d'erreur
    setup_error_handlers(app)
    
    # Middleware de sécurité
    setup_security_headers(app)
    
    # Logging des requêtes
    if not app.testing:
        setup_request_logging(app)
    
    return app


def setup_jwt(app):
    """Configuration JWT avancée"""
    
    # Store des tokens révoqués en Redis
    redis_client = redis.from_url(app.config['REDIS_URL'])
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload['jti']
        token_in_redis = redis_client.get(jti)
        return token_in_redis is not None
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {'error': 'Token has expired', 'code': 'TOKEN_EXPIRED'}, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {'error': 'Invalid token', 'code': 'INVALID_TOKEN'}, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {'error': 'Authorization token is required', 'code': 'TOKEN_REQUIRED'}, 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return {'error': 'Token has been revoked', 'code': 'TOKEN_REVOKED'}, 401


def setup_error_handlers(app):
    """Configuration des handlers d'erreur"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return {'error': 'Bad request', 'code': 'BAD_REQUEST'}, 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return {'error': 'Unauthorized access', 'code': 'UNAUTHORIZED'}, 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return {'error': 'Forbidden access', 'code': 'FORBIDDEN'}, 403
    
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Resource not found', 'code': 'NOT_FOUND'}, 404
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return {
            'error': 'Rate limit exceeded', 
            'code': 'RATE_LIMIT_EXCEEDED',
            'retry_after': str(error.retry_after)
        }, 429
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        logger.error("Internal server error", exc_info=error)
        return {'error': 'Internal server error', 'code': 'INTERNAL_ERROR'}, 500


def setup_security_headers(app):
    """Configuration des headers de sécurité"""
    
    @app.after_request
    def after_request(response):
        from flask import request
        # Headers de sécurité
        for header, value in app.config.get('SECURITY_HEADERS', {}).items():
            response.headers[header] = value
        
        # CORS headers pour les requêtes préflight
        if request.method == 'OPTIONS':
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response


def setup_request_logging(app):
    """Configuration du logging des requêtes"""
    
    @app.before_request
    def log_request_info():
        from flask import request
        logger.info(
            "Request received",
            method=request.method,
            url=request.url,
            remote_addr=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
    
    @app.after_request
    def log_response_info(response):
        logger.info(
            "Response sent",
            status_code=response.status_code,
            content_length=response.content_length
        )
        return response


# Factory pour Celery
def create_celery(app):
    """Créer instance Celery configurée avec Flask"""
    from celery import Celery
    
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        """Tâche avec contexte Flask"""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery
