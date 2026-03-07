from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, Dict

from ..logging_utils import append_log
from ..models import RecetasPayload

PAMI_URL = "https://recetaelectronica.pami.org.ar/controllers/recetaController.php"
QTY_1 = "1"
QTY_2 = "1"

# Segundos máximos esperando resolución manual del captcha
CAPTCHA_TIMEOUT_S = 300


def _profile_dir(log_path: Path) -> Path:
    return log_path.parent.parent / "chrome_profiles" / "recetas"


def _launch_args() -> list:
    """Chrome real, arranca MINIMIZADO en la barra de tareas.
    El operador puede maximizarlo / cerrarlo en cualquier momento.
    PAMI no detecta bot porque es Chrome real con perfil persistente."""
    return [
        "--start-minimized",                            # <-- minimizado, no oculto
        "--window-size=1280,900",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-notifications",
        "--disable-infobars",
        "--disable-blink-features=AutomationControlled",  # oculta señales de automatización
    ]


# ------------------------------------------------------------------
# CAPTCHA
# ------------------------------------------------------------------

def _has_captcha(page) -> bool:
    try:
        for sel in [
            "iframe[src*='recaptcha']",
            "iframe[src*='hcaptcha']",
            "iframe[title*='captcha' i]",
            "div.g-recaptcha",
            "div[data-sitekey]",
            "#captcha",
            "div[class*='captcha' i]",
        ]:
            if page.locator(sel).count() > 0:
                return True
        return False
    except Exception:
        return False


def _wait_for_captcha(page, log_path: Path, ctx: str = "RECETAS") -> None:
    """Si hay captcha, registra en log y espera resolución del operador.
    Chrome está minimizado pero accesible — el operador lo maximiza,
    resuelve el captcha, y el script continúa automáticamente."""
    if not _has_captcha(page):
        return
    append_log(log_path, f"{ctx}: ⚠️  CAPTCHA detectado en la página")
    append_log(log_path, f"{ctx}: → Chrome está minimizado en la barra de tareas")
    append_log(log_path, f"{ctx}: → Maximizalo, resolvé el captcha, y el proceso continúa solo")
    append_log(log_path, f"{ctx}: → Esperando hasta {CAPTCHA_TIMEOUT_S}s...")
    for elapsed in range(CAPTCHA_TIMEOUT_S):
        if not _has_captcha(page):
            append_log(log_path, f"{ctx}: ✓ Captcha resuelto ({elapsed}s)")
            page.wait_for_timeout(800)
            return
        page.wait_for_timeout(1000)
    raise RuntimeError(f"Captcha no resuelto en {CAPTCHA_TIMEOUT_S}s — job cancelado.")


# ------------------------------------------------------------------
# SESSION / LOGIN
# ------------------------------------------------------------------

def _afiliado_no_encontrado(page) -> bool:
    try:
        return page.get_by_text("Afiliado no encontrado", exact=False).is_visible(timeout=800)
    except Exception:
        return False


def _on_login_page(page) -> bool:
    try:
        return page.locator("input[type='password']").count() > 0
    except Exception:
        return False


def _do_login(page, user: str, password: str, log_path: Path) -> None:
    append_log(log_path, "RECETAS: completando login automático")

    _wait_for_captcha(page, log_path)   # captcha antes de rellenar

    pass_field = page.locator("input[type='password']").first
    user_field = None
    for sel in [
        "input[name*=usuario i]", "input[id*=usuario i]",
        "input[name*=user i]",    "input[id*=user i]",
        "input[type='email']",    "input[type='text']",
    ]:
        loc = page.locator(sel)
        if loc.count() > 0 and loc.first.is_visible():
            user_field = loc.first
            break
    if user_field:
        user_field.fill(user)
    pass_field.fill(password)

    btn = page.get_by_role("button", name=re.compile(r"Ingresar|Entrar|Acceder|Iniciar", re.I))
    if btn.count() > 0 and btn.first.is_visible():
        btn.first.click()
    else:
        for sel in ["input[type='submit']", "button[type='submit']"]:
            loc = page.locator(sel)
            if loc.count() > 0:
                loc.first.click()
                break
        else:
            pass_field.press("Enter")

    page.wait_for_timeout(1200)
    _wait_for_captcha(page, log_path)   # captcha post-click

    for _ in range(100):
        if not _on_login_page(page):
            append_log(log_path, "RECETAS: login completado ✓")
            return
        page.wait_for_timeout(200)

    append_log(log_path, "RECETAS: advertencia — campo password sigue visible tras login")


def _ensure_session(page, user: str, password: str, log_path: Path) -> None:
    page.goto(PAMI_URL, wait_until="domcontentloaded")
    _wait_for_captcha(page, log_path)

    if _on_login_page(page):
        _do_login(page, user, password, log_path)

    # OTP / 2FA
    if _on_login_page(page):
        append_log(log_path, "RECETAS: OTP/2FA detectado — esperando (máx 180s)")
        append_log(log_path, "RECETAS: → Chrome minimizado — maximizalo para ingresar el código")
        for elapsed in range(180):
            if not _on_login_page(page):
                append_log(log_path, f"RECETAS: OTP resuelto ({elapsed}s) ✓")
                break
            page.wait_for_timeout(1000)
        else:
            raise RuntimeError("OTP no resuelto en 180s.")

    page.wait_for_selector("#t_benef", timeout=20000)
    append_log(log_path, "RECETAS: sesión activa ✓")


# ------------------------------------------------------------------
# DIALOG HANDLER
# ------------------------------------------------------------------

def _attach_dialog_handler(page) -> None:
    def _on(d):
        try:
            d.accept()
        except Exception:
            pass
    page.on("dialog", _on)


# ------------------------------------------------------------------
# BUSCADOR DE MEDICAMENTOS
# ------------------------------------------------------------------

def _get_meds_context(page, timeout_s: float = 30.0):
    from playwright.sync_api import TimeoutError as PWTimeout
    try:
        page.wait_for_selector("#accion",     state="visible", timeout=2500)
        page.wait_for_selector("#t_busqueda", state="visible", timeout=2500)
        return page
    except PWTimeout:
        pass
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
    raise RuntimeError("No apareció el buscador de medicamentos.")


def _abrir_buscador_y_elegir(page, idx: int, nombre: str, log_path: Path) -> None:
    append_log(log_path, f"RECETAS: buscando med idx={idx} nombre={nombre!r}")
    span_sel = f"#btnNombreComercial_{idx} > span"
    base_sel = f"#btnNombreComercial_{idx}"
    if page.locator(span_sel).count() > 0:
        page.locator(span_sel).click(force=True)
    else:
        page.locator(base_sel).click(force=True)

    ctx = _get_meds_context(page)
    ctx.locator("#accion").select_option(label="Nombre Comercial")
    ctx.locator("#t_busqueda").fill(nombre)

    if ctx.locator("input[value='Buscar']").count() > 0:
        ctx.locator("input[value='Buscar']").first.click()
    else:
        ctx.get_by_role("button", name=re.compile(r"BUSCAR|Buscar", re.I)).first.click()

    xpath_base = "//*[@id='t_busqueda']/ancestor::*[self::div or self::form][1]//following::table[1]"
    nom_cells = ctx.locator(f"xpath={xpath_base}//tbody//tr[td]/td[3]")
    nom_cells.first.wait_for(state="visible", timeout=15000)

    exact    = nom_cells.filter(has_text=re.compile(rf"^\s*{re.escape(nombre)}\s*$", re.I))
    contains = nom_cells.filter(has_text=re.compile(re.escape(nombre), re.I))
    cell = (
        exact.first    if exact.count()    > 0 else
        contains.first if contains.count() > 0 else
        nom_cells.first
    )
    cell.click(force=True)
    page.wait_for_timeout(250)


# ------------------------------------------------------------------
# CONFIRMACIONES DE GUARDADO
# ------------------------------------------------------------------

def _handle_save_confirmations(page) -> None:
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


# ------------------------------------------------------------------
# CARGA DE 1 RECETA (2 medicamentos)
# ------------------------------------------------------------------

def _cargar_una_receta(page, benef: str, diag: str,
                        med_a: str, med_b: str,
                        user: str, password: str,
                        log_path: Path) -> None:
    append_log(log_path, f"RECETAS: cargando receta — meds=({med_a!r} + {med_b!r})")
    page.goto(PAMI_URL, wait_until="domcontentloaded")

    _wait_for_captcha(page, log_path)   # captcha entre recetas (raro pero posible)

    # Re-login si la sesión venció entre recetas
    if _on_login_page(page):
        append_log(log_path, "RECETAS: sesión vencida entre recetas — relogueando")
        _do_login(page, user, password, log_path)

    page.wait_for_selector("#t_benef", timeout=25000)
    page.locator("#t_benef").fill(benef)
    page.click("body")
    page.wait_for_timeout(700)

    if _afiliado_no_encontrado(page):
        raise RuntimeError(f"Afiliado no encontrado: {benef}")

    page.locator("#t_diag_cod_1").fill(diag)
    page.click("body")
    page.wait_for_timeout(150)

    _abrir_buscador_y_elegir(page, 1, med_a, log_path)
    page.locator("#t_cantidad_1").fill(QTY_1)

    if page.locator("#otroMedicamento > span").count() > 0:
        page.click("#otroMedicamento > span")
    else:
        page.click("#otroMedicamento")

    page.locator("#t_diag_cod_2").fill(diag)
    page.click("body")
    page.wait_for_timeout(150)

    _abrir_buscador_y_elegir(page, 2, med_b, log_path)
    page.locator("#t_cantidad_2").fill(QTY_2)

    page.click("#btnGuardar")
    page.wait_for_timeout(600)
    _handle_save_confirmations(page)
    append_log(log_path, f"RECETAS: ✓ receta ({med_a} + {med_b}) guardada")


# ------------------------------------------------------------------
# ENTRY POINT
# ------------------------------------------------------------------

def run_recetas(payload: RecetasPayload, log_path: Path) -> Dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        raise RuntimeError("Playwright no instalado en el conector local.") from exc

    append_log(log_path, "RECETAS: iniciando")
    append_log(log_path, f"RECETAS: paciente={payload.paciente or '(sin nombre)'}  afiliado={payload.afiliado}")

    if (payload.obraSocial or "").strip().upper() not in {"PAMI", ""}:
        raise RuntimeError("Obra social no es PAMI — flujo recetas no aplica.")

    profile = _profile_dir(log_path)
    profile.mkdir(parents=True, exist_ok=True)
    append_log(log_path, f"RECETAS: perfil Chrome → {profile}")
    append_log(log_path, "RECETAS: Chrome se abrirá MINIMIZADO en la barra de tareas")
    append_log(log_path, "RECETAS: podés maximizarlo, mirarlo o cerrarlo en cualquier momento")

    ok_count = 0

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(profile),
            channel="chrome",
            headless=False,
            args=_launch_args(),
        )
        page = context.new_page()
        _attach_dialog_handler(page)
        _ensure_session(page, payload.credenciales.user, payload.credenciales.password, log_path)

        for idx, pair in enumerate(payload.medicamentos, start=1):
            med_a, med_b = pair[0], pair[1]
            append_log(log_path, f"RECETAS: receta {idx}/{len(payload.medicamentos)}")
            _cargar_una_receta(
                page, payload.afiliado, payload.diagnostico,
                med_a, med_b,
                payload.credenciales.user, payload.credenciales.password,
                log_path,
            )
            ok_count += 1
            page.wait_for_timeout(500)

        context.close()

    if ok_count != len(payload.medicamentos):
        raise RuntimeError(f"Recetas incompletas: {ok_count}/{len(payload.medicamentos)} guardadas")

    append_log(log_path, f"RECETAS: ✓ {ok_count}/{len(payload.medicamentos)} recetas guardadas")
    return {
        "result": {
            "benef":      payload.afiliado,
            "nombre":     payload.paciente,
            "status":     "OK",
            "recetas_ok": ok_count,
        }
    }
