# AppCafeProyect ☕️ - Reseñas de Cafeterías

Este es un proyecto web en Django para dejar reseñas de cafeterías en Buenos Aires. La app permite a usuarios registrados dejar puntuaciones, comentarios y ver reseñas de otras personas.

---

## 📦 Tecnologías

- Python 3.13
- Django
- Django REST Framework
- django-allauth (autenticación)

---

## 🛠️ Instalación

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd AppCafeProyect

Crear entorno virtual
python -m venv env

Activar entorno (Windows)
source env/Scripts/activate  # Git Bash
# o
.\env\Scripts\activate       # PowerShell o cmd

Instalar dependencias
pip install django djangorestframework django-allauth

Crear proyecto y app Django
django-admin startproject cafe_reviews .
python manage.py startapp core

Estructura del Proyecto
AppCafeProyect/
├── cafe_reviews/       # Proyecto principal
│   ├── settings.py     # Configuraciones
│   ├── urls.py         # Rutas generales
├── core/               # App principal: usuarios, reseñas, cafeterías
├── env/                # Entorno virtual
├── manage.py
└── README.md
