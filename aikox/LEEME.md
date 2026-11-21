# AIKOX Soporte

Programa de asistencia remota de **AIKOX Informática y Publicidad**, basado en
[RustDesk](https://github.com/rustdesk/rustdesk) 1.5.3 (licencia AGPL-3.0).
Este repositorio es el código fuente completo de la versión con la marca AIKOX.

## Qué cambia respecto a RustDesk
- Nombre «AIKOX Soporte» (nombre interno `AIKOXSoporte`, sin espacios porque
  se usa para el servicio de Windows y para el enlace `aikoxsoporte://`).
- Iconos, logo, colores corporativos e imágenes del instalador.
- Servidor de ID/relay y clave de AIKOX ya configurados y bloqueados.
- Sin comprobación de actualizaciones de rustdesk.com.

Todos los datos están en `aikox/marca.json`. El script `aikox/aplicar_marca.py`
los aplica al código justo antes de compilar.

## Compilar
Pestaña **Actions** › **AIKOX Soporte - Windows** › **Run workflow**.
Tarda alrededor de una hora. El resultado aparece en **Releases**.

## Rehacer iconos
Los iconos de `aikox/iconos/` se generan a partir del logo vectorial
(`aikox/iconos/icon.svg`).
