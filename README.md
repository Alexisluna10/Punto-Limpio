*[Read this in English](README_en.md)*

# Punto Limpio - Sistema de Gestión para Lavanderías 

Este repositorio contiene el código fuente de **Punto Limpio**, una plataforma web desarrollada como una solución de software a medida para gestionar las operaciones de una empresa de lavandería real. 

El sistema fue diseñado y construido de manera colaborativa por un equipo de desarrollo de 3 personas, enfocándose en la escalabilidad, la seguridad de los datos y la automatización de procesos internos.

## Demo en Vivo
Puedes probar la plataforma y ver la arquitectura en funcionamiento en el siguiente enlace de despliegue en producción:
**[Ver Demo de Punto Limpio en Render](https://punto-limpio.onrender.com)**

*(Nota: La base de datos de demostración se reinicia periódicamente. Se incluyen credenciales de prueba dentro de la plataforma o puedes registrar una cuenta nueva).*

## 🛠️ Stack Tecnológico
La arquitectura del proyecto está construida con las siguientes tecnologías:
* **Backend:** Python / Django
* **Base de Datos:** PostgreSQL (Alojada en Supabase con Transaction Pooling)
* **Despliegue y CI/CD:** Render (Web Service) con scripts de automatización e idempotencia (`build.sh`).
* **Manejo de Correos:** Integración con API de Brevo.

---
*Desarrollado con buenas prácticas de ingeniería de software y control de versiones.*