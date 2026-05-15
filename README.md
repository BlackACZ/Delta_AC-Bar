# Delta_AC-Bar

Minimalista HUD "Katana Delta Bar" para Assetto Corsa (AC Python App).

## Instalación
1. Copia la carpeta `apps/python/Delta_AC-Bar` dentro de tu instalación de Assetto Corsa.
2. Activa la app en **Options → General → UI Modules**.
3. Inicia una sesión y activa la app desde el menú lateral.

## Notas
- Se adapta automáticamente a la resolución (60% del ancho de pantalla, 10px de alto).
- Usa `graphics.normalized_car_position` (via `acsys.CS.NormalizedCarPosition`) para el progreso real.
- Registra límites de sectores dinámicamente cuando detecta cambios de sector.
