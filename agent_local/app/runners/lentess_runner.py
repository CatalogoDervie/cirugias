"""
lentess_runner.py  — Automatización PAMI Efectores (Cirugías / Lentess)
Abre Chrome visible, hace login, carga solicitudes de insumos de lentes
para cada paciente de la lista. Optimizado: esperas sobre selectores reales,
sin sleep() fijos innecesarios.
"""
from __future__ import annotations

import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Tuple

from ..logging_utils import append_log
from ..models import LentessPayload

LOGIN_URL = "https://efectores.pami.org.ar/pami_efectores/login.php?xgap_historial=clear"
FORM_URL  = "https://efectores.pami.org.ar/pami_efectores/insu_prestador_cirugia_cargar.php?xgap_historial=reset"

CIRUGIA_CARACTER    = "PROGRAMADO"
BATE_CONTIENE       = "Joaquin Esteves - Urquiza"
PERSONAL_AUTORIZADO = "MAGRINI LUISINA, MORANO JEREMIAS"
MEDICO_CONTACTO     = "01159146509"
MEDICO_NOMBRE       = "JOAQUIN ESTEVES"


# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────

def _only_digits(s: str) -> str:
    return re.sub(r"\D+", "", s or "")


def _split_beneficio_parentesco(afiliado_full: str) -> Tuple[str, str]:
    d = _only_digits(str(afiliado_full))
    return (d[:-2], d[-2:]) if len(d) >= 3 else (d, "")


def _normalize_ojo(ojo: str) -> str:
    return (ojo or "").strip().upper().replace("O.D.", "OD").replace("O.I.", "OI")


def _normalize_lio(v) -> str:
    if v is None:
        return ""
    s = f"{v:g}" if isinstance(v, (int, float)) else str(v).strip()
    return s.replace(".", ",") if "." in s and "," not in s else s


def _fecha_probable_hoy_mas_10() -> str:
    f = datetime.today() + timedelta(days=10)
    if f.weekday() == 6:
        f += timedelta(days=1)
    return f.strftime("%d/%m/%Y")


def _profile_dir(log_path: Path) -> Path:
    return log_path.parent.parent / "chrome_profiles" / "lentess"


def _launch_args() -> list:
    """Chrome visible y maximizado. Si hay captcha/OTP el operador lo ve directo."""
    return [
        "--start-maximized",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-notifications",
        "--disable-infobars",
        "--disable-blink-features=AutomationControlled",
    ]


def _save_screenshot(page, log_path: Path, tag: str) -> None:
    try:
        dst = log_path.with_name(f"{log_path.stem}_{tag}.png")
        page.screenshot(path=str(dst), full_page=True)
        append_log(log_path, f"LENTESS: screenshot → {dst.name}")
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────
# DETECCIÓN DE ESTADO
# ─────────────────────────────────────────────────────────────────

def _on_login_page(page) -> bool:
    try:
        url = (page.url or "").lower()
        return "login.php" in url or page.locator("input[type='password']").count() > 0
    except Exception:
        return False


def _form_ready(page) -> bool:
    """True si el formulario de carga ya cargó completamente."""
    for sel in ["#c_caracter", "#f_probable_cirugia",
                "a[onclick*='mostrar_seleccionable_beneficiario']"]:
        try:
            if page.locator(sel).count() > 0:
                return True
        except Exception:
            pass
    return False


# ─────────────────────────────────────────────────────────────────
# FILL ROBUSTO
# ─────────────────────────────────────────────────────────────────

def _fill_robust(loc_or_page, selector_or_loc, value: str) -> bool:
    """Rellena un campo con 3 estrategias de fallback."""
    try:
        # Si pasamos un locator directamente
        if hasattr(selector_or_loc, 'fill'):
            loc = selector_or_loc
        else:
            loc = loc_or_page.locator(selector_or_loc).first
            if loc.count() == 0:
                return False
        # 1. fill estándar
        try:
            loc.click()
            loc.fill(value)
            if loc.input_value() == value:
                return True
        except Exception:
            pass
        # 2. type carácter a carácter
        try:
            loc.click()
            loc.press("Control+A")
            loc.type(value, delay=35)
            if loc.input_value() == value:
                return True
        except Exception:
            pass
        # 3. JS nativo
        try:
            page = loc_or_page if hasattr(loc_or_page, 'evaluate') else None
            if page:
                page.evaluate(
                    """([sel, val]) => {
                        const el = document.querySelector(sel);
                        if (!el) return;
                        const s = Object.getOwnPropertyDescriptor(
                            window.HTMLInputElement.prototype,'value').set;
                        s.call(el,val);
                        el.dispatchEvent(new Event('input',{bubbles:true}));
                        el.dispatchEvent(new Event('change',{bubbles:true}));
                        el.dispatchEvent(new Event('blur',{bubbles:true}));
                    }""",
                    [str(selector_or_loc) if isinstance(selector_or_loc, str) else "", value]
                )
            return True
        except Exception:
            pass
        return False
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────────────────────────

def _do_login(page, user: str, pw: str, log_path: Path) -> None:
    append_log(log_path, "LENTESS: completando login")

    # Ir a la página de login si no estamos ahí
    if "login.php" not in (page.url or "").lower():
        page.goto(LOGIN_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(800)

    # Buscar campo usuario
    user_sel = None
    for sel in [
        "input[name*='user' i]", "input[id*='user' i]",
        "input[name*='usuario' i]", "input[id*='usuario' i]",
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
        _fill_robust(page, user_sel, user)
    else:
        append_log(log_path, "LENTESS: advertencia — no encontré campo usuario")

    _fill_robust(page, "input[type='password']", pw)

    # Click en botón
    clicked = False
    for sel in ["button[type='submit']", "input[type='submit']",
                "button:has-text('Ingresar')", "button:has-text('Entrar')"]:
        loc = page.locator(sel)
        if loc.count() > 0:
            loc.first.click()
            clicked = True
            break
    if not clicked:
        page.locator("input[type='password']").first.press("Enter")

    # Esperar hasta 20s que desaparezca la pantalla de login
    for _ in range(100):
        if not _on_login_page(page):
            append_log(log_path, "LENTESS: login completado ✓")
            return
        page.wait_for_timeout(200)

    append_log(log_path, "LENTESS: login no completó — puede necesitar captcha/OTP manual")


def _wait_for_form(page, log_path: Path, timeout_s: int = 180) -> None:
    """Espera a que el formulario de carga esté accesible."""
    if _form_ready(page):
        return

    _save_screenshot(page, log_path, "esperando_form")
    append_log(log_path, f"LENTESS: esperando formulario (máx {timeout_s}s)")
    if _on_login_page(page):
        append_log(log_path, "LENTESS: → hay un formulario de login/captcha/OTP visible en Chrome")

    t0 = time.time()
    last_log = t0
    while time.time() - t0 < timeout_s:
        if _form_ready(page) and not _on_login_page(page):
            append_log(log_path, f"LENTESS: ✓ formulario listo ({int(time.time()-t0)}s)")
            return
        now = time.time()
        if now - last_log >= 15:
            append_log(log_path, f"LENTESS: esperando ({int(timeout_s-(now-t0))}s restantes)...")
            last_log = now
        page.wait_for_timeout(1000)

    _save_screenshot(page, log_path, "timeout_form")
    raise RuntimeError(f"Formulario no accesible en {timeout_s}s.")


def _ensure_session(page, user: str, pw: str, log_path: Path) -> None:
    page.goto(FORM_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(800)

    if _form_ready(page) and not _on_login_page(page):
        append_log(log_path, "LENTESS: sesión reutilizada ✓")
        return

    if _on_login_page(page):
        _do_login(page, user, pw, log_path)
        page.goto(FORM_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(800)

    _wait_for_form(page, log_path, timeout_s=180)
    append_log(log_path, "LENTESS: sesión activa ✓")


# ─────────────────────────────────────────────────────────────────
# DIALOG HANDLER
# ─────────────────────────────────────────────────────────────────

def _attach_dialog_handler(page) -> None:
    page.on("dialog", lambda d: d.accept() if True else None)


# ─────────────────────────────────────────────────────────────────
# FECHA PROBABLE (calendario PAMI)
# ─────────────────────────────────────────────────────────────────

_MONTHS_ES = {
    "enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,
    "julio":7,"agosto":8,"septiembre":9,"setiembre":9,"octubre":10,
    "noviembre":11,"diciembre":12,
}

def _parse_date(s: str):
    try:
        return datetime.strptime(s.strip(), "%d/%m/%Y").date()
    except Exception:
        return None

def _set_fecha_probable(page, fecha_str: str, log_path: Path) -> None:
    append_log(log_path, f"LENTESS: fecha probable = {fecha_str}")
    target = _parse_date(fecha_str)
    if not target:
        raise RuntimeError(f"Fecha inválida: {fecha_str}")

    # Intento 1: fill directo en el input
    inp = page.locator("#f_probable_cirugia, input[name='f_probable_cirugia']").first
    if inp.count() > 0:
        try:
            inp.fill(fecha_str)
            inp.press("Tab")
            page.wait_for_timeout(300)
            if _parse_date(inp.input_value() or "") == target:
                return
        except Exception:
            pass

    # Intento 2: calendario visual
    btn_cal = page.locator("#b_f_probable_cirugia").first
    btn_cal.scroll_into_view_if_needed()
    btn_cal.click()

    cal = page.locator("div.calendar").first
    cal.wait_for(state="visible", timeout=6000)

    def _get_cal_title():
        for sel in ["td.title", "td.head"]:
            loc = cal.locator(sel)
            if loc.count() > 0:
                t = loc.first.inner_text().strip()
                if re.search(r"\b20\d{2}\b", t):
                    return t
        return cal.inner_text()

    def _parse_my(title):
        t = title.strip().lower().replace("\n"," ")
        parts = [p.strip() for p in t.split(",")]
        if len(parts) >= 2:
            mes = parts[0]
            yr  = "".join(c for c in parts[1] if c.isdigit())
            if mes in _MONTHS_ES and yr.isdigit():
                return _MONTHS_ES[mes], int(yr)
        return None, None

    def _btn(text):
        rx = re.compile(rf"^\s*{re.escape(text)}\s*$")
        for scope in [cal.locator("td.button"), cal.locator("td")]:
            loc = scope.filter(has_text=rx)
            if loc.count() > 0:
                return loc.first
        return None

    for _ in range(36):
        m, y = _parse_my(_get_cal_title())
        if not (m and y):
            raise RuntimeError("No pude leer el mes/año del calendario PAMI")
        shown = y * 12 + m
        tgt   = target.year * 12 + target.month
        if shown == tgt:
            break
        if shown < tgt:
            b = _btn(">") or _btn("›")
            if b: b.click()
        else:
            b = _btn("<") or _btn("‹")
            if b: b.click()
        page.wait_for_timeout(180)

    day = str(target.day)
    cell = cal.locator("td.day:not(.othermonth):not(.wn)").filter(
        has_text=re.compile(rf"^\s*{re.escape(day)}\s*$")
    )
    if cell.count() == 0:
        cell = cal.locator("td.day").filter(has_text=re.compile(rf"^\s*{re.escape(day)}\s*$"))
    if cell.count() == 0:
        raise RuntimeError(f"No encontré el día {day} en el calendario")
    cell.first.click()

    # Verificar que se seteó
    inp2 = page.locator("#f_probable_cirugia, input[name='f_probable_cirugia']").first
    for _ in range(15):
        if _parse_date(inp2.input_value() or "") == target:
            return
        page.wait_for_timeout(120)
    raise RuntimeError(f"Fecha no quedó seteada: esperaba {fecha_str}, quedó {inp2.input_value()!r}")


def _safe_select_contains(select_loc, text: str) -> bool:
    try:
        opts = select_loc.locator("option")
        for i in range(opts.count()):
            t = opts.nth(i).inner_text().strip()
            if text.lower() in t.lower():
                val = opts.nth(i).get_attribute("value")
                if val is not None:
                    select_loc.select_option(value=val)
                    return True
        return False
    except Exception:
        return False


def _completar_campos_fijos(page, log_path: Path) -> None:
    """Rellena todos los campos fijos del formulario de carga de cirugía."""
    append_log(log_path, "LENTESS: completando campos fijos")

    _set_fecha_probable(page, _fecha_probable_hoy_mas_10(), log_path)

    # Caracter de la cirugía
    page.locator("#c_caracter").select_option(label=CIRUGIA_CARACTER)

    # BATE (seleccionar el que contiene el nombre)
    bate = page.locator("#c_bate")
    if bate.count() > 0 and not _safe_select_contains(bate, BATE_CONTIENE):
        raise RuntimeError(f"No encontré BATE que contenga: {BATE_CONTIENE!r}")

    # Horarios lun-vie 08:00-14:00
    for d in ["lun", "mar", "mie", "jue", "vie"]:
        chk = page.locator(f"#chk_{d}")
        if chk.count() > 0:
            chk.check()
        for fid, val in [(f"#sel_desde_{d}", "08:00"), (f"#sel_hasta_{d}", "14:00")]:
            loc = page.locator(fid)
            if loc.count() > 0:
                loc.select_option(label=val)

    # Datos del médico
    for fid, val in [
        ("#d_personal_autorizado", PERSONAL_AUTORIZADO),
        ("#d_medico_contacto",     MEDICO_CONTACTO),
        ("#d_medico_nombre",       MEDICO_NOMBRE),
    ]:
        loc = page.locator(fid)
        if loc.count() > 0:
            loc.fill(val)


# ─────────────────────────────────────────────────────────────────
# SELECTABLES (iframes modales)
# ─────────────────────────────────────────────────────────────────

def _open_iframe(page):
    frame = page.frame_locator("iframe#iframe-seleccionable")
    frame.locator("body").wait_for(timeout=9000)
    return frame


def _close_iframe(page) -> None:
    iframe = page.locator("iframe#iframe-seleccionable")
    if iframe.count() == 0:
        return
    try:
        iframe.wait_for(state="hidden", timeout=1500)
        return
    except Exception:
        pass
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(120)
        page.mouse.click(10, 10)
        iframe.wait_for(state="hidden", timeout=1500)
    except Exception:
        pass


def _sel_beneficiario(page, afiliado: str, log_path: Path) -> None:
    append_log(log_path, f"LENTESS: seleccionando beneficiario {afiliado}")
    beneficio, parentesco = _split_beneficio_parentesco(afiliado)

    page.locator("a[onclick*='mostrar_seleccionable_beneficiario']").first.click()
    frame = _open_iframe(page)
    frame.locator("#bus_n_beneficio").fill(beneficio)

    if parentesco:
        for sel in ["#bus_grado_parentesco","#bus_parentesco","#bus_grado_parent",
                    "input[name*='parent' i]","input[id*='parent' i]"]:
            loc = frame.locator(sel)
            if loc.count() > 0:
                loc.first.fill(parentesco)
                break

    frame.locator("#b_buscar").click()
    frame.locator("#BodyListado tr").first.wait_for(timeout=9000)

    rows = frame.locator("#BodyListado tr")
    chosen = None
    if parentesco:
        for i in range(rows.count()):
            tds = rows.nth(i).locator("td")
            if tds.count() >= 2:
                gp = _only_digits(tds.nth(1).inner_text() or "").zfill(2)
                if gp == parentesco:
                    chosen = rows.nth(i)
                    break
    if chosen is None and rows.count() > 0:
        chosen = rows.nth(0)
    if chosen is None:
        raise RuntimeError("No hay filas al buscar el beneficiario.")
    chosen.locator("a").first.click()
    _close_iframe(page)
    page.wait_for_timeout(200)


def _sel_diagnostico(page, log_path: Path) -> None:
    append_log(log_path, "LENTESS: seleccionando diagnóstico")
    page.locator("a[onclick*='mostrar_seleccionable_diagnostico']").first.click()
    frame = _open_iframe(page)
    frame.locator("#bus_d_cie10").fill("CATARATA senil")
    frame.locator("#b_buscar").click()
    frame.locator("a:has-text('CATARATA SENIL')").first.wait_for(timeout=9000)
    frame.locator("a:has-text('CATARATA SENIL')").first.click()
    _close_iframe(page)
    page.wait_for_timeout(200)


def _sel_insumo(page, ojo: str, lio: str, log_path: Path) -> None:
    append_log(log_path, f"LENTESS: seleccionando insumo ojo={ojo} lio={lio}")
    page.locator("a[onclick*='mostrar_seleccionable_insumo']").first.click()
    frame = _open_iframe(page)
    frame.locator("#bus_c_especialidad").select_option(label="OFTALMOLOGÍA")
    frame.locator("#b_buscar").click()
    frame.locator("#BodyListado a").first.wait_for(timeout=9000)

    # OD = índice 0, OI = índice 2
    idx = 0 if _normalize_ojo(ojo) == "OD" else 2
    frame.locator("#BodyListado a").nth(idx).click()
    _close_iframe(page)
    page.wait_for_timeout(200)

    # Cantidad
    qty = page.locator("#insumo_cantidad").first
    qty.click()
    qty.press("Control+A")
    qty.type("1", delay=50)
    qty.press("Tab")
    page.wait_for_timeout(200)

    # Observaciones
    obs = page.locator("#insumo_obs").first
    obs.fill(f"DIOPTRIA: {_normalize_lio(lio)}\nVISCOELASTICA PESADA")
    obs.press("Tab")
    page.wait_for_timeout(120)

    # Agregar insumo
    btn = page.locator("#btn_add_insumo").first
    btn.wait_for(state="visible", timeout=6000)
    btn.click()
    # Esperar confirmación de que se agregó
    page.locator("text=Listado de Insumos a Solicitar").first.wait_for(timeout=9000)


def _guardar_form(page, log_path: Path) -> None:
    append_log(log_path, "LENTESS: guardando solicitud")
    btn = page.locator("#b_guardar").first
    btn.wait_for(state="visible", timeout=9000)
    btn.scroll_into_view_if_needed()

    # Esperar que esté habilitado
    try:
        page.wait_for_function(
            "() => { const b = document.querySelector('#b_guardar'); return b && !b.disabled; }",
            timeout=5000,
        )
    except Exception:
        pass

    btn.click()

    # Esperar navegación al listado
    try:
        page.wait_for_url(re.compile(r"insu_prestador_cirugia_listado\.php"), timeout=15000)
    except Exception:
        try:
            page.wait_for_load_state("networkidle", timeout=12000)
        except Exception:
            pass

    page.wait_for_timeout(600)
    append_log(log_path, "LENTESS: ✓ solicitud guardada")


# ─────────────────────────────────────────────────────────────────
# PROCESAR UN PACIENTE
# ─────────────────────────────────────────────────────────────────

def _procesar_paciente(page, afiliado: str, ojo: str, lio: str,
                        user: str, pw: str, log_path: Path) -> None:
    # Re-login si la sesión venció
    if _on_login_page(page):
        append_log(log_path, "LENTESS: sesión vencida — relogueando")
        _do_login(page, user, pw, log_path)
        page.goto(FORM_URL, wait_until="domcontentloaded")
        _wait_for_form(page, log_path, timeout_s=120)

    _completar_campos_fijos(page, log_path)
    _sel_beneficiario(page, afiliado, log_path)
    _sel_diagnostico(page, log_path)
    _sel_insumo(page, ojo, lio, log_path)
    _guardar_form(page, log_path)


# ─────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────

def run_lentess(payload: LentessPayload, log_path: Path) -> Dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Playwright no está instalado en el conector local.") from exc

    n = len(payload.pacientes)
    append_log(log_path, "LENTESS: iniciando")
    append_log(log_path, f"LENTESS: {n} paciente(s) a procesar")

    profile = _profile_dir(log_path)
    profile.mkdir(parents=True, exist_ok=True)
    append_log(log_path, f"LENTESS: perfil Chrome → {profile}")
    append_log(log_path, "LENTESS: abriendo Chrome (visible, maximizado)...")

    ok, errors = 0, []

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(profile),
            channel="chrome",
            headless=False,
            no_viewport=True,
            args=_launch_args(),
        )
        page = context.new_page()
        _attach_dialog_handler(page)

        try:
            page.bring_to_front()
        except Exception:
            pass

        _ensure_session(page, payload.credenciales.user, payload.credenciales.password, log_path)

        for i, pac in enumerate(payload.pacientes, start=1):
            append_log(log_path, f"LENTESS: paciente {i}/{n} — afiliado={pac.afiliado}")
            try:
                _procesar_paciente(
                    page,
                    afiliado=pac.afiliado,
                    ojo=pac.ojo,
                    lio=pac.lio,
                    user=payload.credenciales.user,
                    pw=payload.credenciales.password,
                    log_path=log_path,
                )
                ok += 1
                append_log(log_path, f"LENTESS: ✓ {pac.afiliado}")
            except Exception as exc:
                errors.append({"afiliado": pac.afiliado, "error": str(exc)})
                append_log(log_path, f"LENTESS: ✗ ERROR {pac.afiliado}: {exc}")
                _save_screenshot(page, log_path, f"error_{i}")

            # Ir al formulario limpio para el próximo paciente
            if i < n:
                page.goto(FORM_URL, wait_until="domcontentloaded")
                # Esperar que el form cargue en lugar de sleep fijo
                try:
                    page.wait_for_selector("#c_caracter", state="visible", timeout=8000)
                except Exception:
                    page.wait_for_timeout(1500)

        context.close()

    if ok == 0:
        raise RuntimeError("No se completó ninguna solicitud Lentess.")

    if errors:
        err_list = "; ".join(f"{e['afiliado']}:{e['error']}" for e in errors)
        raise RuntimeError(f"Lentess parcial — OK={ok} ERRORES={len(errors)} — {err_list}")

    append_log(log_path, f"LENTESS: ✓ {ok}/{n} solicitudes guardadas")
    return {"summary": {"total": n, "ok": ok, "errors": 0}}
