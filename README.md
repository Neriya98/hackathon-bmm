# 🔐 DealSure - Bitcoin Smart Contracts Platform

DealSure (formerly SecureDeal) is a professional web platform built with Flask/Python and Rust for creating, managing, and executing secure Bitcoin contracts via PSBT (Partially Signed Bitcoin Transactions).

## 🎯 Features

- ✅ **Secure authentication** with JWT and email validation
- ✅ **Bitcoin contract creation** via PSBT and optimized Rust scripts  
- ✅ **Collaborative invitations** by email with secure links
- ✅ **Multi-party signatures** with cryptographic validation
- ✅ **Automatic fund release** after conditions are met
- ✅ **Modern interface** with Tailwind CSS and Velocity.js animations
- ✅ **Complete REST API** documented with Swagger/OpenAPI

## 🛠️ Technical Stack

### Backend
- **Flask 3.0** - Modern Python web framework
- **SQLAlchemy 2.0** - ORM with async support
- **PyO3/Maturin** - High-performance Python-Rust binding
- **PostgreSQL** - Robust database
- **Redis** - Cache and sessions
- **Celery** - Asynchronous tasks
- **JWT** - Stateless authentication

### Rust Core
- **BDK (Bitcoin Dev Kit)** - Native Bitcoin tools
- **Miniscript** - Optimized Bitcoin scripts
- **PyO3** - Native Python bindings
- **Tokio** - Async runtime

### Frontend
- **Tailwind CSS 3.3** - Framework CSS utilitaire
- **Velocity.js 2.0** - Animations web fluides
- **HTMX** - Interactions dynamiques
- **Alpine.js** - Réactivité légère

### DevOps
- **Docker & Compose** - Containerisation
- **GitHub Actions** - CI/CD automatisé
- **pytest** - Tests automatisés
- **Black/isort** - Formatage code

## 📦 Installation Rapide

### Prérequis
```bash
# Versions requises
Python 3.11+
Rust 1.75+
PostgreSQL 15+
Redis 7+
Node.js 18+
```

### 1. Cloner et setup environnement
```bash
git clone <your-repo>
cd hackathon-bmm
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows
```

### 2. Installer dépendances Python
```bash
pip install -r requirements.txt
```

### 3. Compiler le module Rust
```bash
cd rust_core
maturin develop --release
cd ..
```

### 4. Setup base de données
```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/securedeal"
flask db upgrade
```

### 5. Compiler assets frontend
```bash
npm install
npm run build
```

### 6. Lancer l'application
```bash
flask run --debug
```

🌐 **Application disponible sur:** `http://localhost:5000`

## 🏗️ Architecture du Projet

```
hackathon-bmm/
├── 📁 app/                     # Application Flask principale
│   ├── 📁 api/                # Endpoints API REST
│   ├── 📁 models/             # Modèles SQLAlchemy
│   ├── 📁 services/           # Logique métier
│   ├── 📁 templates/          # Templates Jinja2
│   ├── 📁 static/             # Assets statiques
│   └── 📄 __init__.py         # Factory Flask
├── 📁 blockchain_services/    # Service Rust pour les opérations blockchain
│   ├── 📄 Cargo.toml         # Config Rust
│   └── 📁 src/               # Code Rust
├── 📁 tests/                  # Tests automatisés
├── 📁 instance/               # Données d'instance (BD SQLite)
├── 📁 notes/                  # Documentation du projet
├── 📄 requirements.txt        # Dépendances Python
├── 📄 package.json           # Dépendances Node.js
├── 📄 docker-compose.yml     # Services Docker
├── 📄 .env.example           # Variables d'environnement
└── 📄 config.py              # Configuration Flask
```

## 🏗️ Project Structure

```
app/                  # Main application package
├── api/              # API endpoints and logic
├── models/           # Database models
├── routes/           # Web routes (auth, contracts, invitations, main)
├── services/         # Service layer with business logic
├── static/           # Static assets (CSS, JS, images)
│   ├── css/          # CSS files (Tailwind)
│   ├── js/           # JavaScript files
│   │   └── contract_templates/ # Contract JSON templates
└── templates/        # HTML templates
    ├── auth/         # Authentication templates
    ├── contract_templates/ # Contract HTML templates
    ├── contracts/    # Contract management templates
    └── partials/     # Reusable template parts

blockchain_services/  # Rust backend for blockchain operations
├── src/              # Rust source code
    ├── main.rs       # HTTP API server
    └── handlers.rs   # Bitcoin functionality

tests/                # Application tests
```

## 🔄 Workflow Utilisateur

### 1. **Inscription/Connexion**
- Création compte avec email/mot de passe
- Validation email automatique
- JWT tokens sécurisés

### 2. **Création de Contrat**
- Choix type contrat (MultiSig, TimeLock, Escrow)
- Configuration participants et montants
- Génération PSBT via Rust

### 3. **Invitation Signataires**
- Envoi emails avec liens sécurisés
- Interface dédiée signature
- Suivi statut en temps réel

### 4. **Signature Collaborative**
- Validation cryptographique
- Signatures partielles PSBT
- Finalisation automatique

### 5. **Déblocage Fonds**
- Conditions smart contract validées
- Transaction Bitcoin diffusée
- Notification participants

## 🔧 API Endpoints

### Authentification
```http
POST /api/auth/register     # Inscription
POST /api/auth/login        # Connexion
POST /api/auth/logout       # Déconnexion
GET  /api/auth/verify/:token # Validation email
```

### Contrats
```http
POST /api/contracts              # Créer contrat
GET  /api/contracts              # Lister contrats
GET  /api/contracts/:id          # Détails contrat
POST /api/contracts/:id/invite   # Inviter signataire
POST /api/contracts/:id/sign     # Signer contrat
POST /api/contracts/:id/finalize # Finaliser transaction
```

### PSBT (via Rust)
```http
POST /api/psbt/create       # Créer PSBT
POST /api/psbt/sign         # Signer PSBT
POST /api/psbt/combine      # Combiner PSBTs
POST /api/psbt/finalize     # Finaliser PSBT
```

## 🎨 Design System

### Palette de Couleurs
- **Primary:** `#1e40af` (Bleu confiance)
- **Secondary:** `#6b7280` (Gris neutre)
- **Accent:** `#f59e0b` (Orange action)
- **Success:** `#10b981` (Vert validation)
- **Error:** `#ef4444` (Rouge erreur)
- **Bitcoin:** `#f7931a` (Orange Bitcoin)

### Composants UI
- Boutons avec états hover/focus
- Cards avec shadows subtiles
- Modals avec animations Velocity
- Loaders animés pour transactions
- Alerts contextuelles

## 🧪 Tests et Qualité

### Tests Unitaires
```bash
pytest tests/unit/           # Tests modèles/services
pytest tests/integration/    # Tests API
pytest tests/rust/          # Tests module Rust
```

### Couverture Code
```bash
pytest --cov=app tests/
```

### Linting & Formatage
```bash
black app/ tests/           # Formatage Python
isort app/ tests/          # Tri imports
flake8 app/ tests/         # Linting
mypy app/                  # Type checking
```

## 🚀 Déploiement

### Render Cloud Deployment

See the [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) file for detailed instructions on deploying to Render.

In short:
1. Connect your repository to Render
2. Render will detect the `render.yaml` file and automatically set up all required services
3. Review settings and deploy

### Docker Production Deployment
```bash
# Build production image
docker build --target production -t securedeal:latest .

# Run with docker-compose (production profile)
docker-compose --profile production up -d

# Or deploy to cloud platforms
# AWS ECS, Google Cloud Run, Azure Container Instances, etc.
```

### Manual Production Deployment

```bash
# 1. Set production environment
export FLASK_ENV=production
export DATABASE_URL="postgresql://user:password@localhost/securedeal"
export REDIS_URL="redis://localhost:6379/0"

# 2. Install dependencies
pip install -r requirements.txt
npm install && npm run build

# 3. Build Rust extension
cd rust_core && maturin build --release
pip install target/wheels/*.whl

# 4. Initialize database
flask db upgrade

# 5. Run with Gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 "app:create_app()"
```

### Environment Variables (Production)

```bash
# Security
SECRET_KEY=your-super-secure-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

# Database
DATABASE_URL=postgresql://user:password@host:5432/securedeal

# Bitcoin
BITCOIN_NETWORK=mainnet  # or testnet
BITCOIN_RPC_URL=https://your-bitcoin-node:8332/
BITCOIN_RPC_USER=your-rpc-user
BITCOIN_RPC_PASSWORD=your-rpc-password

# Email
MAIL_SERVER=smtp.sendgrid.net
MAIL_USERNAME=apikey
MAIL_PASSWORD=your-sendgrid-api-key

# Redis/Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# Security Headers
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
WTF_CSRF_ENABLED=True
```

### SSL/TLS Configuration

For production, ensure SSL/TLS is properly configured:

```nginx
# nginx.conf example
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Monitoring & Logging

- **Health Check**: `GET /health`
- **Metrics**: Integrate with Prometheus/Grafana
- **Logs**: Structured JSON logging with rotation
- **Alerts**: Set up alerts for failed transactions, security events

### Backup Strategy

1. **Database**: Regular PostgreSQL backups
2. **User Data**: Encrypted backup of sensitive information
3. **Configuration**: Version-controlled environment configs
4. **Bitcoin Data**: Backup of generated keys and PSBTs

### Security Checklist

- [ ] Use HTTPS everywhere
- [ ] Enable CSRF protection
- [ ] Set secure session cookies
- [ ] Configure rate limiting
- [ ] Enable audit logging
- [ ] Regular security updates
- [ ] Monitor failed login attempts
- [ ] Implement 2FA (future feature)

## 🔧 Development Commands

```bash
# Development server with auto-reload
npm run dev

# Build assets for production
npm run build

# Run tests
flask test

# Database operations
flask init-db
flask create-admin
flask seed-data

# Rust operations
npm run install:rust
flask build-rust
flask install-rust

# Code quality
flask format  # Format with black
flask lint    # Lint with flake8

# Docker operations
npm run docker:build
npm run docker:run
npm run docker:stop
npm run docker:logs
```

## 📄 Licence

MIT License - voir fichier `LICENSE`

## 🆘 Support

- 📧 Email: support@securedeal.com
- 💬 Discord: [SecureDeal Community](https://discord.gg/securedeal)
- 📖 Wiki: [Documentation complète](https://docs.securedeal.com)

---

**Made with ❤️ and ⚡ by the SecureDeal Team**
