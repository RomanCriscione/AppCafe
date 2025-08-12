# Gota – Launch checklist (prod-ready)

## Configuración
- [ ] `.env` completo (SECRET_KEY, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, DATABASE_URL, DEFAULT_FROM_EMAIL).
- [ ] `DEBUG=False` en producción.
- [ ] `TIME_ZONE=America/Argentina/Buenos_Aires`.
- [ ] `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` con el dominio final (https://).

## Estáticos & Media
- [ ] `python manage.py collectstatic` en build.
- [ ] `whitenoise` activo y `STATIC_ROOT` configurado.

## Seguridad
- [ ] `SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO','https')`.
- [ ] Revisar cookies seguras/HSTS con `DEBUG=False`.

## SEO/Metadatos
- [ ] `<title>` y meta OG/Twitter por café.
- [ ] `sitemap.xml` y `robots.txt` servidos.

## Accesibilidad & UX
- [ ] `alt` correcto en imágenes.
- [ ] Labels asociados a inputs/checkboxes.

## Tests/CI
- [ ] GitHub Actions corriendo en `main`.
- [ ] Cobertura objetivo verificada.

## Datos & Admin
- [ ] Crear superuser en prod.
- [ ] SMTP validado si se envían correos.
