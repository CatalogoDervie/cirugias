"""
recetas_runner.py  — Automatización PAMI Receta Electrónica
Abre Chrome visible (maximizado), hace login automático o espera
login/captcha/OTP manual si es necesario, carga 3 recetas de 2 meds cada una.
"""
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, Dict

from ..logging_utils import append_log
from ..models import RecetasPayload

PAMI_URL = "https://recetaelectronica.pami.org.ar/controllers/recetaController.php"
QTY = "1"


# ─────────────────────────────────────────────────────────────────
# PERFIL Y ARGS DE CHROME
# ─────────────────────────────────────────────────────────────────

def _profile_dir(log_path: Path) -> Path:
    """Perfil persistente — guarda la sesión entre ejecuciones."""
    return log_path.parent.parent / "chrome_profiles" / "recetas"


def _launch_args() -> list:
    """Chrome visible al frente. Maximizado para que el operador vea si hay captcha."""
    return [
        "--start-maximized",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-notifications",
        "--disable-infobars",
        "--disable-blink-features=AutomationControlled",
    ]


# ─────────────────────────────────────────────────────────────────
# HELPERS DE DETECCIÓN
# ─────────────────────────────────────────────────────────────────

def _on_login_page(page) -> bool:
    """True si la página actual parece ser un formulario de login."""
    try:
        return page.locator("input[type='password']").count() > 0
    except Exception:
        return False


def _form_ready(page) -> bool:
    """True si el formulario de carga de recetas está listo (#t_benef visible)."""
    try:
        loc = page.locator("#t_benef")
        return loc.count() > 0 and loc.first.is_visible(timeout=500)
    except Exception:
        return False


def _afiliado_no_encontrado(page) -> bool:
    try:
        return page.get_by_text("Afiliado no encontrado", exact=False).is_visible(timeout=800)
    except Exception:
        return False


def _save_screenshot(page, log_path: Path, tag: str) -> None:
    try:
        dst = log_path.with_name(f"{log_path.stem}_{tag}.png")
        page.screenshot(path=str(dst), full_page=True)
        append_log(log_path, f"RECETAS: screenshot → {dst.name}")
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────
# LOGIN AUTOMÁTICO
# ─────────────────────────────────────────────────────────────────

def _fill_field_robust(page, selector: str, value: str) -> bool:
    """
    Intenta rellenar un campo de texto de 3 formas distintas:
    1. fill() nativo de Playwright
    2. click + type carácter a carácter
    3. Asignación JS con disparo de eventos input/change/blur
    Devuelve True si tuvo éxito.
    """
    try:
        loc = page.locator(selector).first
        if loc.count() == 0:
            return False
        # Intento 1: fill estándar
        try:
            loc.click()
            loc.fill(value)
            if loc.input_value() == value:
                return True
        except Exception:
            pass
        # Intento 2: type carácter a carácter
        try:
            loc.click()
            loc.press("Control+A")
            loc.type(value, delay=40)
            if loc.input_value() == value:
                return True
        except Exception:
            pass
        # Intento 3: asignación JS
        try:
            page.evaluate(
                """([sel, val]) => {
                    const el = document.querySelector(sel);
                    if (!el) return;
                    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value').set;
                    nativeInputValueSetter.call(el, val);
                    el.dispatchEvent(new Event('input',  {bubbles:true}));
                    el.dispatchEvent(new Event('change', {bubbles:true}));
                    el.dispatchEvent(new Event('blur',   {bubbles:true}));
                }""",
                [selector, value]
            )
            return True
        except Exception:
            pass
        return False
    except Exception:
        return False


def _do_login(page, user: str, password: str, log_path: Path) -> None:
    """
    Intenta login automático. Si la URL no es la de login, navega ahí primero.
    Usa _fill_field_robust para mayor compatibilidad con el formulario de PAMI.
    """
    append_log(log_path, "RECETAS: intentando login automático")

    # Asegurarse de estar en la página de PAMI
    if not _on_login_page(page):
        page.goto(PAMI_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(1000)

    if not _on_login_page(page):
        append_log(log_path, "RECETAS: no hay campo password visible — no se puede hacer login automático")
        return

    # Buscar campo usuario con múltiples selectores
    user_sel = None
    for sel in [
        "input[name*='usuario' i]",
        "input[id*='usuario' i]",
        "input[name*='user' i]",
        "input[id*='user' i]",
        "input[type='email']",
        "input[type='text']:visible",
    ]:
        try:
            loc = page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                user_sel = sel
                break
        except Exception:
            continue

    if user_sel:
        ok = _fill_field_robust(page, user_sel, user)
        if not ok:
            append_log(log_path, f"RECETAS: advertencia — no pude rellenar usuario con selector {user_sel}")
    else:
        append_log(log_path, "RECETAS: advertencia — no encontré campo usuario")

    ok = _fill_field_robust(page, "input[type='password']", password)
    if not ok:
        append_log(log_path, "RECETAS: advertencia — no pude rellenar contraseña")

    # Hacer click en el botón de login
    btn = page.get_by_role("button", name=re.compile(r"Ingresar|Entrar|Acceder|Iniciar", re.I))
    if btn.count() > 0 and btn.first.is_visible():
        btn.first.click()
    else:
        clicked = False
        for sel in ["input[type='submit']", "button[type='submit']"]:
            loc = page.locator(sel)
            if loc.count() > 0:
                loc.first.click()
                clicked = True
                break
        if not clicked:
            page.locator("input[type='password']").first.press("Enter")

    # Esperar hasta 20s que desaparezca el campo password (= login exitoso)
    for _ in range(100):
        if not _on_login_page(page):
            append_log(log_path, "RECETAS: login automático completado ✓")
            return
        page.wait_for_timeout(200)

    append_log(log_path, "RECETAS: login automático no completó — puede necesitar captcha/OTP manual")


def _wait_for_access(page, log_path: Path, timeout_s: int = 180) -> None:
    """
    Espera hasta timeout_s segundos a que el formulario de recetas sea accesible.
    Si hay login/captcha/OTP pendiente, el operador puede resolverlo en Chrome.
    Hace logs cada 15s para que el operador sepa qué espera.
    """
    if _form_ready(page):
        return

    _save_screenshot(page, log_path, "esperando_acceso")
    append_log(log_path, f"RECETAS: esperando acceso al sistema (máx {timeout_s}s)")
    if _on_login_page(page):
        append_log(log_path, "RECETAS: → hay un formulario de login/captcha/OTP visible en Chrome")
        append_log(log_path, "RECETAS: → si el login automático no funcionó, completalo manualmente")

    t0 = time.time()
    last_log = t0
    while time.time() - t0 < timeout_s:
        if _form_ready(page):
            append_log(log_path, f"RECETAS: ✓ acceso confirmado ({int(time.time()-t0)}s)")
            return
        now = time.time()
        if now - last_log >= 15:
            remaining = int(timeout_s - (now - t0))
            append_log(log_path, f"RECETAS: esperando ({remaining}s restantes)...")
            last_log = now
        page.wait_for_timeout(1000)

    _save_screenshot(page, log_path, "timeout_acceso")
    raise RuntimeError(
        f"No se pudo acceder al sistema en {timeout_s}s. "
        "Revisá el log y el screenshot para ver qué bloqueó el acceso."
    )


def _ensure_session(page, user: str, password: str, log_path: Path) -> None:
    """
    Garantiza sesión activa en PAMI Recetas.
    1. Navega a PAMI_URL
    2. Si ya está listo → reutiliza sesión
    3. Si hay login → intenta automático
    4. Si sigue bloqueado → espera resolución manual
    """
    page.goto(PAMI_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(800)

    if _form_ready(page):
        append_log(log_path, "RECETAS: sesión reutilizada ✓")
        return

    if _on_login_page(page):
        _do_login(page, user, password, log_path)
        page.wait_for_timeout(1000)

    _wait_for_access(page, log_path, timeout_s=180)
    append_log(log_path, "RECETAS: sesión activa ✓")


# ─────────────────────────────────────────────────────────────────
# DIALOG HANDLER
# ─────────────────────────────────────────────────────────────────

def _attach_dialog_handler(page) -> None:
    def _on(d):
        try:
            d.accept()
        except Exception:
            pass
    page.on("dialog", _on)


# ─────────────────────────────────────────────────────────────────
# BUSCADOR DE MEDICAMENTOS
# ─────────────────────────────────────────────────────────────────

def _get_meds_context(page, timeout_s: float = 25.0):
    """Devuelve la página o el iframe que contiene #accion y #t_busqueda."""
    from playwright.sync_api import TimeoutError as PWTimeout
    # Intento en página principal
    try:
        page.wait_for_selector("#accion",     state="visible", timeout=2500)
        page.wait_for_selector("#t_busqueda", state="visible", timeout=2500)
        return page
    except PWTimeout:
        pass
    # Buscar en iframes
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        for fr in page.frames:
            if fr == page.main_frame:
                continue
            try:
                if fr.locator("#accion").count() > 0 and fr.locator("#t_busqueda").count() > 0:
                    fr.wait_for_selector("#accion",     state="visible", timeout=1500)
                    fr.wait_for_selector("#t_busqueda", state="visible", timeout=1500)
                    return fr
            except Exception:
                pass
        time.sleep(0.2)
    raise RuntimeError("No apareció el buscador de medicamentos (ni en página ni en iframes).")


def _abrir_buscador_y_elegir(page, idx: int, nombre: str, log_path: Path) -> None:
    append_log(log_path, f"RECETAS: buscando med idx={idx} '{nombre}'")

    # Click en el botón de nombre comercial
    for sel in [f"#btnNombreComercial_{idx} > span", f"#btnNombreComercial_{idx}"]:
        loc = page.locator(sel)
        if loc.count() > 0:
            loc.first.click(force=True)
            break

    ctx = _get_meds_context(page)
    ctx.locator("#accion").select_option(label="Nombre Comercial")

    # Rellenar el campo de búsqueda robustamente
    if not _fill_field_robust(ctx if ctx != page else page, "#t_busqueda", nombre):
        ctx.locator("#t_busqueda").fill(nombre)

    # Hacer click en Buscar
    if ctx.locator("input[value='Buscar']").count() > 0:
        ctx.locator("input[value='Buscar']").first.click()
    else:
        ctx.get_by_role("button", name=re.compile(r"BUSCAR|Buscar", re.I)).first.click()

    # Esperar resultados
    xpath = "//*[@id='t_busqueda']/ancestor::*[self::div or self::form][1]//following::table[1]//tbody//tr[td]/td[3]"
    nom_cells = ctx.locator(f"xpath={xpath}")
    nom_cells.first.wait_for(state="visible", timeout=15000)

    # Elegir: exacto > contiene > primero
    exact    = nom_cells.filter(has_text=re.compile(rf"^\s*{re.escape(nombre)}\s*$", re.I))
    contains = nom_cells.filter(has_text=re.compile(re.escape(nombre), re.I))
    cell = (
        exact.first    if exact.count()    > 0 else
        contains.first if contains.count() > 0 else
        nom_cells.first
    )
    cell.click(force=True)
    page.wait_for_timeout(250)


# ─────────────────────────────────────────────────────────────────
# CONFIRMACIONES POST-GUARDADO
# ─────────────────────────────────────────────────────────────────

def _handle_save_confirmations(page) -> None:
    """Acepta cualquier modal de confirmación que aparezca al guardar."""
    for _ in range(8):
        try:
            yes = page.locator("button:has-text('Sí'), button:has-text('Si'), button.ui-confirm-button")
            if yes.count() > 0 and yes.first.is_visible():
                yes.first.click()
                time.sleep(0.2)
            ok_btn = page.locator("button:has-text('Aceptar'), button:has-text('OK')")
            if ok_btn.count() > 0 and ok_btn.first.is_visible():
                ok_btn.first.click()
                time.sleep(0.2)
        except Exception:
            pass
        time.sleep(0.15)


# ─────────────────────────────────────────────────────────────────
# CARGA DE 1 RECETA (2 medicamentos)
# ─────────────────────────────────────────────────────────────────

def _cargar_una_receta(page, benef: str, diag: str,
                        med_a: str, med_b: str,
                        user: str, password: str,
                        log_path: Path) -> None:
    append_log(log_path, f"RECETAS: cargando receta '{med_a}' + '{med_b}'")

    # Navegar al formulario
    page.goto(PAMI_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(600)

    # Re-login si la sesión venció
    if _on_login_page(page) or not _form_ready(page):
        append_log(log_path, "RECETAS: sesión expiró entre recetas — recuperando")
        if _on_login_page(page):
            _do_login(page, user, password, log_path)
            page.wait_for_timeout(800)
        _wait_for_access(page, log_path, timeout_s=120)

    # Rellenar afiliado
    page.locator("#t_benef").fill(benef)
    page.click("body")
    page.wait_for_timeout(700)

    if _afiliado_no_encontrado(page):
        raise RuntimeError(f"Afiliado no encontrado: {benef}")

    # Diagnóstico 1
    page.locator("#t_diag_cod_1").fill(diag)
    page.click("body")
    page.wait_for_timeout(200)

    # Med 1
    _abrir_buscador_y_elegir(page, 1, med_a, log_path)
    page.locator("#t_cantidad_1").fill(QTY)

    # Agregar 2do medicamento
    otro = page.locator("#otroMedicamento > span")
    if otro.count() > 0:
        otro.click()
    else:
        page.locator("#otroMedicamento").click()

    # Diagnóstico 2
    page.locator("#t_diag_cod_2").fill(diag)
    page.click("body")
    page.wait_for_timeout(200)

    # Med 2
    _abrir_buscador_y_elegir(page, 2, med_b, log_path)
    page.locator("#t_cantidad_2").fill(QTY)

    # Guardar
    page.locator("#btnGuardar").click()
    page.wait_for_timeout(700)
    _handle_save_confirmations(page)
    append_log(log_path, f"RECETAS: ✓ receta guardada")


# ─────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────

def run_recetas(payload: RecetasPayload, log_path: Path) -> Dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Playwright no está instalado en el conector local.") from exc

    append_log(log_path, "RECETAS: iniciando")
    append_log(log_path, f"RECETAS: paciente={payload.paciente or '(sin nombre)'}  afiliado={payload.afiliado}")

    if (payload.obraSocial or "").strip().upper() not in {"PAMI", ""}:
        raise RuntimeError("Obra social no es PAMI — el flujo de recetas no aplica.")

    profile = _profile_dir(log_path)
    profile.mkdir(parents=True, exist_ok=True)
    append_log(log_path, f"RECETAS: perfil Chrome → {profile}")
    append_log(log_path, "RECETAS: abriendo Chrome (visible, maximizado)...")

    ok_count = 0
    n = len(payload.medicamentos)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(profile),
            channel="chrome",
            headless=False,
            args=_launch_args(),
        )
        page = context.new_page()
        _attach_dialog_handler(page)

        try:
            page.bring_to_front()
        except Exception:
            pass

        _ensure_session(page, payload.credenciales.user, payload.credenciales.password, log_path)

        for idx, pair in enumerate(payload.medicamentos, start=1):
            med_a, med_b = pair[0], pair[1]
            append_log(log_path, f"RECETAS: receta {idx}/{n}")
            _cargar_una_receta(
                page,
                benef=payload.afiliado,
                diag=payload.diagnostico,
                med_a=med_a,
                med_b=med_b,
                user=payload.credenciales.user,
                password=payload.credenciales.password,
                log_path=log_path,
            )
            ok_count += 1
            page.wait_for_timeout(400)

        context.close()

    if ok_count != n:
        raise RuntimeError(f"Recetas incompletas: {ok_count}/{n} guardadas")

    append_log(log_path, f"RECETAS: ✓ {ok_count}/{n} recetas guardadas")
    return {
        "result": {
            "benef":      payload.afiliado,
            "nombre":     payload.paciente,
            "status":     "OK",
            "recetas_ok": ok_count,
        }
    }
