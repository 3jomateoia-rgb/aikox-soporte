#!/usr/bin/env python3
"""Aplica la marca AIKOX al codigo de RustDesk.

Se ejecuta en GitHub Actions justo despues de descargar el codigo (y se puede
ejecutar en local para comprobarlo):

    python aikox/aplicar_marca.py           # aplica los cambios
    python aikox/aplicar_marca.py --check   # solo comprueba que todo se encuentra

Todos los datos salen de aikox/marca.json. Cada cambio busca un texto exacto:
si una version nueva de RustDesk lo cambia, el script se para con un error
claro en lugar de compilar un programa a medio personalizar.
"""
import json
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MARCA = json.loads((RAIZ / "aikox" / "marca.json").read_text(encoding="utf-8"))
SOLO_COMPROBAR = "--check" in sys.argv

INTERNO = MARCA["nombre_interno"]
VISIBLE = MARCA["nombre_visible"]
errores = []
hechos = 0


def dart_str(s):
    return s.replace("\\", "\\\\").replace("'", "\\'")


def rust_str(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def cambiar(ruta, viejo, nuevo, veces=1):
    """Sustituye un texto exacto. veces=0: todas las apariciones (al menos una)."""
    global hechos
    f = RAIZ / ruta
    if not f.is_file():
        errores.append(f"{ruta}: no existe")
        return
    txt = f.read_text(encoding="utf-8")
    if nuevo and nuevo in txt:
        return  # ya aplicado
    n = txt.count(viejo)
    if n == 0 or (veces and n != veces):
        errores.append(f"{ruta}: se esperaba {veces or '>=1'} vez/veces y hay {n}: {viejo[:70]!r}")
        return
    if not SOLO_COMPROBAR:
        f.write_text(txt.replace(viejo, nuevo), encoding="utf-8", newline="")
    hechos += 1


def escribir(ruta, contenido):
    global hechos
    if not SOLO_COMPROBAR:
        f = RAIZ / ruta
        f.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(contenido, bytes):
            f.write_bytes(contenido)
        else:
            f.write_text(contenido, encoding="utf-8", newline="")
    hechos += 1


def copiar(origen, destino):
    global hechos
    o = RAIZ / "aikox" / "iconos" / origen
    if not o.is_file():
        errores.append(f"falta el icono aikox/iconos/{origen}")
        return
    if not SOLO_COMPROBAR:
        d = RAIZ / destino
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(o, d)
    hechos += 1


# ---------------------------------------------------------------- 1. Nombre, servidor y clave
CFG = "libs/hbb_common/src/config.rs"
cambiar(CFG, 'RwLock::new("RustDesk".to_owned());', f'RwLock::new("{INTERNO}".to_owned());')
cambiar(CFG, 'pub const RENDEZVOUS_SERVERS: &[&str] = &["rs-ny.rustdesk.com"];',
        f'pub const RENDEZVOUS_SERVERS: &[&str] = &["{MARCA["servidor_id"]}"];')
cambiar(CFG, 'pub const RS_PUB_KEY: &str = "OeVuKk5nlHiXp+APNn0Y3pC1Iwpwn44JGqrQCsWqmBw=";',
        f'pub const RS_PUB_KEY: &str = "{MARCA["clave"]}";')
cambiar(CFG, 'pub const LINK_DOCS_HOME: &str = "https://rustdesk.com/docs/en/";',
        f'pub const LINK_DOCS_HOME: &str = "{MARCA["web"]}";')

# ---------------------------------------------------------------- 2. Configuracion incrustada
# Mismo formato que el custom.txt del generador oficial, pero dentro del
# programa y sin firma (lo compilamos nosotros).
cliente = {
    "app-name": INTERNO,
    "override-settings": {
        # Servidor fijo: el cliente no puede cambiarlo.
        "custom-rendezvous-server": MARCA["servidor_id"],
        "relay-server": MARCA["servidor_relay"],
        "key": MARCA["clave"],
        # Sin avisos ni descargas de rustdesk.com.
        "enable-check-update": "N",
        "allow-auto-update": "N",
        # Ajustes que el cliente no debe tocar.
        "hide-server-settings": "Y",
        "hide-proxy-settings": "Y",
        "hide-websocket-settings": "Y",
        "hide-powered-by-me": "Y",
    },
    "default-settings": {
        "theme": "light",
    },
}
escribir("aikox/cliente.json", json.dumps(cliente, ensure_ascii=False, indent=2) + "\n")

COMMON = "src/common.rs"
# a) read_custom_client se parte en dos: verificar la firma / aplicar los datos.
cambiar(COMMON,
        '''        log::error!("Failed to parse custom client config");
        return;
    };

    if let Some(app_name) = data.remove("app-name") {''',
        '''        log::error!("Failed to parse custom client config");
        return;
    };
    apply_custom_client_data(data);
}

// AIKOX: aplica una configuracion de cliente ya verificada o incrustada.
pub fn apply_custom_client_data(mut data: std::collections::HashMap<String, serde_json::Value>) {
    if let Some(app_name) = data.remove("app-name") {''')
# b) la configuracion de AIKOX se aplica siempre, antes que cualquier custom.txt.
cambiar(COMMON,
        '''pub fn load_custom_client() {
''',
        '''pub fn load_custom_client() {
    // AIKOX: configuracion incrustada al compilar (aikox/cliente.json).
    if let Ok(data) = serde_json::from_str::<std::collections::HashMap<String, serde_json::Value>>(
        include_str!("../aikox/cliente.json"),
    ) {
        apply_custom_client_data(data);
    }
''')

# ---------------------------------------------------------------- 3. Textos: "RustDesk" -> "AIKOX Soporte"
cambiar("src/lang.rs",
        '''                let app_name = crate::get_app_name();
                if !app_name.contains("RustDesk") {''',
        f'''                let app_name = "{rust_str(VISIBLE)}".to_owned(); // AIKOX: nombre visible
                if !app_name.contains("RustDesk") {{''')
cambiar("src/auth_2fa.rs", 'const ISSUER: &str = "RustDesk";', f'const ISSUER: &str = "{rust_str(VISIBLE)}";')

# ---------------------------------------------------------------- 4. Interfaz (Flutter)
COM = "flutter/lib/common.dart"
cambiar(COM, '''String getWindowName({WindowType? overrideType}) {
  final name = bind.mainGetAppNameSync();''',
        f'''String getWindowName({{WindowType? overrideType}}) {{
  const name = '{dart_str(VISIBLE)}'; // AIKOX''')
cambiar(COM, '''    _appName = bind.mainGetAppNameSync();''', f'''    _appName = '{dart_str(VISIBLE)}'; // AIKOX''')
# Colores corporativos.
A = MARCA["color_acento"].upper()
cambiar(COM, "static const Color accent = Color(0xFF0071FF);", f"static const Color accent = Color(0xFF{A});")
cambiar(COM, "static const Color accent50 = Color(0x770071FF);", f"static const Color accent50 = Color(0x77{A});")
cambiar(COM, "static const Color accent80 = Color(0xAA0071FF);", f"static const Color accent80 = Color(0xAA{A});")
cambiar(COM, "static const Color idColor = Color(0xFF00B6F0);", f"static const Color idColor = Color(0xFF{A});")
cambiar(COM, "static const Color button = Color(0xFF2C8CFF);", f"static const Color button = Color(0xFF{A});")
cambiar(COM, "launchUrl(Uri.parse('https://rustdesk.com'));", f"launchUrl(Uri.parse('{MARCA['web']}'));")

SET = "flutter/lib/desktop/pages/desktop_setting_page.dart"
cambiar(SET, "launchUrlString('https://rustdesk.com/privacy.html');", f"launchUrlString('{MARCA['privacidad']}');")
cambiar(SET, "launchUrlString('https://rustdesk.com');", f"launchUrlString('{MARCA['web']}');")
cambiar(SET, "decoration: const BoxDecoration(color: Color(0xFF2c8cff)),",
        f"decoration: const BoxDecoration(color: Color(0xFF{MARCA['color_marino'].upper()})),")
# Licencia AGPL: se mantiene el copyright de RustDesk y se anade el enlace al codigo.
cambiar(SET, "'Copyright © ${DateTime.now().toString().substring(0, 4)} Purslane Tech Pte. Ltd.\\n$license',",
        "'" + dart_str(f"{VISIBLE} · {MARCA['empresa']}") + "\\n"
        "Basado en RustDesk · Copyright © ${DateTime.now().toString().substring(0, 4)} Purslane Tech Pte. Ltd.\\n"
        "Código fuente (AGPL-3.0): " + dart_str(MARCA["codigo_fuente"]) + "\\n$license',")
cambiar("flutter/lib/desktop/pages/install_page.dart", "'https://rustdesk.com/privacy.html'", f"'{MARCA['privacidad']}'", veces=0)
cambiar("flutter/lib/desktop/pages/desktop_home_page.dart", "Uri.parse('https://rustdesk.com/download')",
        f"Uri.parse('{MARCA['web']}')")

# ---------------------------------------------------------------- 5. Ejecutable de Windows (VERSIONINFO)
RC = "flutter/windows/runner/Runner.rc"
cambiar(RC, 'VALUE "FileDescription", "RustDesk Remote Desktop" "\\0"', f'VALUE "FileDescription", "{MARCA["descripcion"]}" "\\0"')
cambiar(RC, 'VALUE "InternalName", "rustdesk" "\\0"', f'VALUE "InternalName", "{INTERNO}" "\\0"')
cambiar(RC, 'VALUE "OriginalFilename", "rustdesk.exe" "\\0"', f'VALUE "OriginalFilename", "{INTERNO}.exe" "\\0"')
cambiar(RC, 'VALUE "ProductName", "RustDesk" "\\0"', f'VALUE "ProductName", "{VISIBLE}" "\\0"')

# ---------------------------------------------------------------- 6. Iconos y logos
copiar("icon.ico", "flutter/windows/runner/resources/app_icon.ico")
copiar("icon.ico", "res/icon.ico")
copiar("icon.png", "res/icon.png")
copiar("32x32.png", "res/32x32.png")
copiar("64x64.png", "res/64x64.png")
copiar("128x128.png", "res/128x128.png")
copiar("128x128@2x.png", "res/128x128@2x.png")
copiar("icon.svg", "res/icon.svg")
copiar("icon.svg", "res/scalable.svg")
copiar("icon.svg", "flutter/assets/icon.svg")
copiar("icon.png", "flutter/assets/icon.png")
copiar("logo.png", "flutter/assets/logo.png")
copiar("logo_light.png", "flutter/assets/logo_light.png")
copiar("logo_dark.png", "flutter/assets/logo_dark.png")
copiar("WixUIBannerBmp.bmp", "res/msi/Package/Resources/WixUIBannerBmp.bmp")
copiar("WixUIDialogBmp.bmp", "res/msi/Package/Resources/WixUIDialogBmp.bmp")

# ---------------------------------------------------------------- Resultado
if errores:
    print("ERROR al aplicar la marca AIKOX:")
    for e in errores:
        print("  -", e)
    sys.exit(1)
print(f"Marca AIKOX {'comprobada' if SOLO_COMPROBAR else 'aplicada'}: {hechos} cambios.")
