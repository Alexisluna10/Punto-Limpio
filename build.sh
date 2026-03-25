#!/usr/bin/env bash
# Exit on error
set -o errexit

# Instalar librerías
pip install -r requirements.txt

# Recopilar archivos estáticos (CSS, JS, Imágenes)
python manage.py collectstatic --no-input

# Aplicar las migraciones a la base de datos
python manage.py migrate

# --- LA MAGIA: Sembrar la base de datos automáticamente ---
python init_db.py