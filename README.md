# BuskoGuard - Système de Gestion des Présences et Accès NFC 🏢

<div align="center">

[Français](#fr) | [English](#en) | [Español](#es) | [Português](#pt)

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2-green.svg)](https://www.djangoproject.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange.svg)](https://www.mysql.com/)
[![React](https://img.shields.io/badge/React-18.0-blue.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/license-MIT-purple.svg)](https://opensource.org/licenses/MIT)
</div>

<div align="center">
  <img src="busko_guard_logo.png" alt="BuskoGuard Banner" />
</div>

<a name="fr"></a>
# 🇫🇷 Documentation Française

## 📋 Table des Matières
- [Vue d'ensemble](#fr-overview)
- [Fonctionnalités](#fr-features)
- [Architecture](#fr-architecture)
- [Installation](#fr-installation)
- [Configuration](#fr-configuration)
- [Documentation API](#fr-api)
- [Contribution](#fr-contribution)

<a name="fr-overview"></a>
## 🌟 Vue d'ensemble

BuskoGuard est une solution complète de gestion des présences et de contrôle d'accès, conçue avec une architecture monolithique modulaire. Le système utilise la technologie NFC pour un contrôle d'accès sécurisé et offre une gestion complète des présences, des congés et des rapports.

<a name="fr-features"></a>
## ✨ Fonctionnalités Principales

- 🔐 Authentification et autorisation avancées
- 👥 Gestion complète des utilisateurs et départements
- ⏰ Suivi des présences en temps réel
- 🚪 Contrôle d'accès NFC sécurisé
- 📅 Gestion des congés et absences
- 📊 Rapports et statistiques détaillés
- 🔔 Système de notifications en temps réel
- 📱 Interface responsive moderne
- 🌐 API RESTful complète
- 🔄 Intégration Celery pour les tâches asynchrones

<a name="fr-architecture"></a>
## 🏗️ Architecture

### Structure du Projet
```plaintext
buskoguard/
├── 📁 attendance_system/        # Configuration projet
│   ├── 📄 settings.py          # Paramètres Django
│   ├── 📄 celery.py           # Configuration Celery
│   └── 📄 urls.py             # URLs principales
│
├── 📁 presence/                # Application principale
│   ├── 📁 api/
│   │   ├── 📄 views.py        # Vues API
│   │   ├── 📄 serializers.py  # Sérialiseurs
│   │   └── 📄 urls.py        # Routes API
│   ├── 📁 utils/
│   │   ├── 📄 nfc_utils.py    # Utilitaires NFC
│   │   └── 📄 attendanceutils.py # Utilitaires présence
│   ├── 📁 permissions/
│   │   └── 📄 custom_permissions.py # Permissions personnalisées
│   ├── 📄 models.py           # Modèles de données
│   ├── 📄 tasks.py           # Tâches Celery
│   └── 📄 signals.py         # Signaux Django
│
├── 📁 frontend/               # Interface utilisateur
│   ├── 📁 src/
│   │   ├── 📁 components/    # Composants React
│   │   ├── 📁 pages/        # Pages
│   │   └── 📁 services/     # Services API
│   └── 📄 package.json
│
├── 📄 requirements.txt        # Dépendances Python
└── 📄 manage.py              # Script Django
```

<a name="fr-installation"></a>
## 🚀 Installation

### Prérequis
- Python 3.13
- MySQL 8.0
- Node.js 16+
- Redis (pour Celery)
- Lecteur NFC compatible

### Installation Pas à Pas

1. **Cloner le Repository**
```bash
git clone https://github.com/josephsamijona/busko_guard2.git
cd busko_guard2
```

2. **Configurer l'Environnement Python**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

3. **Configurer MySQL**
```bash
mysql -u root -p
CREATE DATABASE buskoguard;
CREATE USER 'buskoguard_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON buskoguard.* TO 'buskoguard_user'@'localhost';
FLUSH PRIVILEGES;
```

4. **Configuration Environnement**
Créer un fichier `.env` à la racine du projet:
```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=mysql://buskoguard_user:your_password@localhost/buskoguard
REDIS_URL=redis://localhost:6379/0
```

5. **Migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Créer un Super Utilisateur**
```bash
python manage.py createsuperuser
```

7. **Lancer Celery**
```bash
celery -A attendance_system worker -l info
```

8. **Démarrer le Serveur**
```bash
python manage.py runserver
```

<a name="fr-api"></a>
## 📚 Documentation API

### Points d'Accès Principaux

#### Authentification
```http
POST /api/auth/token/           # Obtenir un token JWT
POST /api/auth/token/refresh/   # Rafraîchir le token
```

#### Gestion des Utilisateurs
```http
GET    /api/users/              # Liste des utilisateurs
POST   /api/users/              # Créer un utilisateur
GET    /api/users/{id}/         # Détails utilisateur
PUT    /api/users/{id}/         # Modifier utilisateur
DELETE /api/users/{id}/         # Supprimer utilisateur
```

#### Présences
```http
GET    /api/attendance-records/ # Liste des présences
POST   /api/attendance-records/ # Enregistrer présence
GET    /api/statistics/presence/ # Statistiques
```

[Suite dans la partie 2...]

<a name="en"></a>
# 🇬🇧 English Documentation

[Suite de la Documentation Française...]

<a name="fr-configuration"></a>
## ⚙️ Configuration

### Configuration NFC
```python
# presence/utils/nfc_utils.py
NFC_SETTINGS = {
    'READER_PORT': '/dev/ttyUSB0',
    'BAUDRATE': 115200,
    'TIMEOUT': 2
}
```

### Configuration Celery
```python
# attendance_system/celery.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

<a name="fr-contribution"></a>
## 🤝 Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit les changements (`git commit -m 'Ajout nouvelle fonctionnalite'`)
4. Push vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Créer une Pull Request

## 📦 Requirements.txt
```python
Django==4.2
djangorestframework==3.14.0
djangorestframework-simplejwt==5.3.1
mysqlclient==2.2.1
celery==5.3.6
redis==5.0.1
channels==4.0.0
python-dotenv==1.0.1
Pillow==10.2.0
django-cors-headers==4.3.1
drf-yasg==1.21.7
django-filter==23.5
```

<a name="es"></a>
# 🇪🇸 Documentación en Español

## 📋 Tabla de Contenidos
- [Descripción General](#es-overview)
- [Características](#es-features)
- [Arquitectura](#es-architecture)
- [Instalación](#es-installation)
- [Configuración](#es-configuration)
- [Documentación API](#es-api)
- [Contribución](#es-contribution)

<a name="es-overview"></a>
## 🌟 Descripción General

BuskoGuard es una solución integral de gestión de asistencia y control de acceso, diseñada con una arquitectura monolítica modular. El sistema utiliza tecnología NFC para un control de acceso seguro y ofrece gestión completa de asistencia, permisos e informes.

<a name="es-features"></a>
## ✨ Características Principales

- 🔐 Autenticación y autorización avanzadas
- 👥 Gestión completa de usuarios y departamentos
- ⏰ Seguimiento de asistencia en tiempo real
- 🚪 Control de acceso NFC seguro
- 📅 Gestión de permisos y ausencias
- 📊 Informes y estadísticas detalladas
- 🔔 Sistema de notificaciones en tiempo real
- 📱 Interfaz responsive moderna
- 🌐 API RESTful completa
- 🔄 Integración Celery para tareas asíncronas

[... Continúa con la misma structure que la version française ...]

<a name="pt"></a>
# 🇵🇹 Documentação em Português

## 📋 Índice
- [Visão Geral](#pt-overview)
- [Funcionalidades](#pt-features)
- [Arquitetura](#pt-architecture)
- [Instalação](#pt-installation)
- [Configuração](#pt-configuration)
- [Documentação API](#pt-api)
- [Contribuição](#pt-contribution)

<a name="pt-overview"></a>
## 🌟 Visão Geral

BuskoGuard é uma solução completa de gestão de presença e controle de acesso, projetada com uma arquitetura monolítica modular. O sistema utiliza tecnologia NFC para controle de acesso seguro e oferece gestão completa de presenças, licenças e relatórios.

<a name="pt-features"></a>
## ✨ Funcionalidades Principais

- 🔐 Autenticação e autorização avançadas
- 👥 Gestão completa de usuários e departamentos
- ⏰ Monitoramento de presença em tempo real
- 🚪 Controle de acesso NFC seguro
- 📅 Gestão de licenças e ausências
- 📊 Relatórios e estatísticas detalhadas
- 🔔 Sistema de notificações em tempo real
- 📱 Interface responsiva moderna
- 🌐 API RESTful completa
- 🔄 Integração Celery para tarefas assíncronas

[... Continue with the same structure as French version ...]

## 🌐 Support International

| Language | Support |
|----------|---------|
| Français | ✅ Principal |
| English | ✅ Full Support |
| Español | ✅ Full Support |
| Português | ✅ Full Support |

## 📧 Contact

Joseph Sami - [GitHub](https://github.com/josephsamijona)

Project Link: [https://github.com/josephsamijona/busko_guard2.git](https://github.com/josephsamijona/busko_guard2.git)

---
<div align="center">
  <sub>Built with ❤️ by Joseph Sami</sub>
</div>
