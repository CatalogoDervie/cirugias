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

WAIT_FORM_STABLE_MS = 2000
WAIT_PRE_CAL_MS     = 1500

# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------

def _only_digits(s: str) -> str:
    return re.sub(r"\D+", "", s or "")

def _split_beneficio_parentesco(afiliado_full: str) -> Tuple[str, str]:
    d = _only_digits(str(afiliado_full))
    return (d[:-2], d[-2:]) if len(d) >= 3 else (d, "")

def _normalize_ojo(ojo: str) -> str:
    o = (ojo or "").strip().upper()
    return o.replace("O.D.", "OD").replace("O.I.", "OI")

def _normalize_lio(v) -> str:
    if v is None:
        return ""
    if isinstance(v, (int, float)):
        return f"{v:g}".replace(".", ",")
    s = str(v).strip()
    if "." in s and "," not in s:
        s = s.replace(".", ",")
    return s

def _fecha_probable_hoy_mas_10() -> str:
    f = datetime.today() + timedelta(days=10)
    if f.weekday() == 6:
        f += timedelta(days=1)
    return f.strftime("%d/%m/%Y")

def _profile_dir(log_path: Path) -> Path:
    return log_path.parent.parent / "chrome_profiles" / "lentess"

def _launch_args() -> list:
    return [
        "--window-size=1280,900",
        "--start-maximized",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-notifications",
        "--disable-infobars",
    ]

def _set_window_state(page, state: str) -> None:
    try:
        client = page.context.new_cdp_session(page)
        win_info = client.send("Browser.getWindowForTarget")
        client.send("Browser.setWindowBounds", {
            "windowId": win_info["windowId"],
            "bounds": {"windowState": state}
        })
    except Exception:
        pass

# ------------------------------------------------------------------
# LOGIN Y SESIÓN
# ------------------------------------------------------------------

def _looks_like_login(page) -> bool:
    url = (page.url or "").lower()
    return "login.php" in url or page.locator("input[type='password']").count() > 0

def _do_login(page, user: str, pw: str, log_path: Path) -> None:
    append_log(log_path, "LENTESS: completando login automático")
    page.goto(LOGIN_URL, wait_until="domcontentloaded")

    user_sel = None
    for sel in [
        "input[name*='user' i]", "input[id*='user' i]",
        "input[name*='usuario' i]", "input[id*='usuario' i]",
        "input[type='text']",
    ]:
        loc = page.locator(sel)
        if loc.count() > 0:
            user_sel = loc.first
            break
    if user_sel is None:
        raise RuntimeError("No se encontró campo usuario en login Lentess.")

    pass_sel = page.locator("input[type='password']").first
    user_sel.fill(user)
    pass_sel.fill(pw)

    for sel in ["button[type='submit']", "input[type='submit']",
                "button:has-text('Ingresar')", "button:has-text('Entrar')"]:
        loc = page.locator(sel)
        if loc.count() > 0:
            loc.first.click()
            break
    else:
        pass_sel.press("Enter")

    for _ in range(75):
        if not _looks_like_login(page):
            append_log(log_path, "LENTESS: login completado")
            return
        page.wait_for_timeout(200)

def _ensure_session(page, user: str, pw: str, log_path: Path) -> None:
    page.goto(FORM_URL, wait_until="domcontentloaded")

    if _looks_like_login(page):
        _do_login(page, user, pw, log_path)
        page.goto(FORM_URL, wait_until="domcontentloaded")

    if _looks_like_login(page):
        append_log(log_path, "LENTESS: Captcha o OTP detectado — Restaurando ventana para resolución manual (máx 3 min)")
        _set_window_state(page, "maximized")
        page.bring_to_front()
        for _ in range(180):
            if not _looks_like_login(page):
                append_log(log_path, "LENTESS: Captcha/OTP resuelto")
                break
            page.wait_for_timeout(1000)
        else:
            raise RuntimeError("Captcha/OTP no resuelto a tiempo.")
        _set_window_state(page, "minimized")
        page.goto(FORM_URL, wait_until="domcontentloaded")

    page.wait_for_timeout(WAIT_FORM_STABLE_MS)
    append_log(log_path, "LENTESS: sesión activa confirmada")

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
# CAMPOS FIJOS DEL FORMULARIO
# ------------------------------------------------------------------

_MONTHS_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}

def _parse_ddmmyyyy(s: str):
    try:
        return datetime.strptime(s.strip(), "%d/%m/%Y").date()
    except Exception:
        return None

def _get_calendar_title(cal):
    for sel in ["td.title", "td.head"]:
        loc = cal.locator(sel)
        if loc.count() > 0:
            t = loc.first.inner_text().strip()
            if re.search(r"\b20\d{2}\b", t):
                return t
    return cal.inner_text()

def _parse_month_year(title_text: str):
    t = (title_text or "").strip().lower().replace("\n", " ")
    parts = [p.strip() for p in t.split(",")]
    if len(parts) >= 2:
        mes  = parts[0]
        anio = "".join(ch for ch in parts[1] if ch.isdigit())
        if mes in _MONTHS_ES and anio.isdigit():
            return _MONTHS_ES[mes], int(anio)
    return None, None

def _btn_exact(cal, text_exact: str):
    rx = re.compile(rf"^\s*{re.escape(text_exact)}\s*$")
    for scope in [cal.locator("td.button"), cal.locator("td")]:
        loc = scope.filter(has_text=rx)
        if loc.count() > 0:
            return loc.first
    return None

def _set_fecha_probable(page, fecha_str: str, log_path: Path) -> None:
    append_log(log_path, f"LENTESS: fecha probable = {fecha_str}")
    target = _parse_ddmmyyyy(fecha_str)
    if not target:
        raise RuntimeError(f"Fecha inválida: {fecha_str}")

    inp_direct = page.locator("#f_probable_cirugia, input[name='f_probable_cirugia']").first
    if inp_direct.count() > 0:
        try:
            inp_direct.fill(fecha_str)
            inp_direct.press("Tab")
            page.wait_for_timeout(300)
            val = (_parse_ddmmyyyy(inp_direct.input_value() or "") )
            if val == target:
                return
        except Exception:
            pass

    page.wait_for_timeout(WAIT_PRE_CAL_MS)
    btn = page.locator("#b_f_probable_cirugia").first
    btn.scroll_into_view_if_needed()
    btn.click()

    cal = page.locator("div.calendar").first
    cal.wait_for(state="visible", timeout=8000)

    for _ in range(36):
        title = _get_calendar_title(cal)
        m, y  = _parse_month_year(title)
        if not (m and y):
            raise RuntimeError(f"No pude leer mes/año del calendario. title={title!r}")
        shown = y * 12 + m
        tgt   = target.year * 12 + target.month
        if shown == tgt:
            break
        nb = _btn_exact(cal, ">") or _btn_exact(cal, "›")
        pb = _btn_exact(cal, "<") or _btn_exact(cal, "‹")
        if shown < tgt:
            (nb or (_ for _ in ()).throw(RuntimeError("No encontré botón siguiente del calendario."))).click()
        else:
            (pb or (_ for _ in ()).throw(RuntimeError("No encontré botón anterior del calendario."))).click()
        page.wait_for_timeout(200)

    day  = str(target.day)
    cell = cal.locator("td.day:not(.othermonth):not(.wn)").filter(
        has_text=re.compile(rf"^\s*{re.escape(day)}\s*$")
    )
    if cell.count() == 0:
        cell = cal.locator("td.day").filter(has_text=re.compile(rf"^\s*{re.escape(day)}\s*$"))
    if cell.count() == 0:
        raise RuntimeError(f"No encontré el día {day} en el calendario.")
    cell.first.click()

    inp = page.locator("#f_probable_cirugia, input[name='f_probable_cirugia']").first
    inp.wait_for(timeout=5000)
    for _ in range(15):
        if _parse_ddmmyyyy(inp.input_value() or "") == target:
            return
        page.wait_for_timeout(150)
    raise RuntimeError(f"Fecha no quedó seteada. Esperaba {fecha_str}, quedó {inp.input_value()!r}")

def _safe_select_by_contains(select_locator, text_contains: str) -> bool:
    if not text_contains:
        return False
    try:
        options = select_locator.locator("option")
        n = options.count()
        for i in range(n):
            t = options.nth(i).inner_text().strip()
            if text_contains.lower() in t.lower():
                val = options.nth(i).get_attribute("value")
                if val is not None:
                    select_locator.select_option(value=val)
                    return True
        return False
    except Exception:
        return False

def _completar_campos_fijos(page, log_path: Path) -> None:
    append_log(log_path, "LENTESS: completando campos fijos")
    _set_fecha_probable(page, _fecha_probable_hoy_mas_10(), log_path)
    page.locator("#c_caracter").select_option(label=CIRUGIA_CARACTER)
    bate = page.locator("#c_bate")
    if bate.count() > 0:
        if not _safe_select_by_contains(bate, BATE_CONTIENE):
            raise RuntimeError(f"No encontré Bate que contenga: {BATE_CONTIENE!r}")

    for d in ["lun", "mar", "mie", "jue", "vie"]:
        chk = page.locator(f"#chk_{d}")
        if chk.count() > 0:
            chk.check()
        desde = page.locator(f"#sel_desde_{d}")
        hasta  = page.locator(f"#sel_hasta_{d}")
        if desde.count() > 0:
            desde.select_option(label="08:00")
        if hasta.count() > 0:
            hasta.select_option(label="14:00")

    if page.locator("#d_personal_autorizado").count() > 0:
        page.locator("#d_personal_autorizado").fill(PERSONAL_AUTORIZADO)
    if page.locator("#d_medico_contacto").count() > 0:
        page.locator("#d_medico_contacto").fill(MEDICO_CONTACTO)
    if page.locator("#d_medico_nombre").count() > 0:
        page.locator("#d_medico_nombre").fill(MEDICO_NOMBRE)

# ------------------------------------------------------------------
# SELECTABLES (iframe)
# ------------------------------------------------------------------

def _abrir_iframe_seleccionable(page):
    frame = page.frame_locator("iframe#iframe-seleccionable")
    frame.locator("body").wait_for(timeout=9000)
    return frame

def _cerrar_seleccionable(page) -> None:
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
        page.wait_for_timeout(150)
        page.mouse.click(10, 10)
        page.wait_for_timeout(150)
        iframe.wait_for(state="hidden", timeout=1500)
    except Exception:
        pass

def _seleccionar_beneficiario(page, afiliado: str, log_path: Path) -> None:
    append_log(log_path, f"LENTESS: seleccionando beneficiario {afiliado}")
    beneficio, parentesco = _split_beneficio_parentesco(afiliado)
    page.locator("a[onclick*='mostrar_seleccionable_beneficiario']").first.click()
    frame = _abrir_iframe_seleccionable(page)
    frame.locator("#bus_n_beneficio").fill(beneficio)
    if parentesco:
        for sel in ["#bus_grado_parentesco", "#bus_parentesco", "#bus_grado_parent",
                    "input[name*='parent' i]", "input[id*='parent' i]"]:
            loc = frame.locator(sel)
            if loc.count() > 0:
                loc.first.fill(parentesco)
                break
    frame.locator("#b_buscar").click()
    frame.locator("#BodyListado tr").first.wait_for(timeout=9000)

    rows = frame.locator("#BodyListado tr")
    n = rows.count()
    chosen = None
    if parentesco and n > 0:
        for i in range(n):
            tds = rows.nth(i).locator("td")
            if tds.count() >= 2:
                gp = _only_digits(tds.nth(1).inner_text() or "").zfill(2)
                if gp == parentesco:
                    chosen = rows.nth(i)
                    break
    if chosen is None and n > 0:
        chosen = rows.nth(0)
    if chosen is None:
        raise RuntimeError("No hay filas al buscar el beneficiario.")

    chosen.locator("a").first.click()
    _cerrar_seleccionable(page)
    page.wait_for_timeout(250)

def _seleccionar_diagnostico(page, log_path: Path) -> None:
    append_log(log_path, "LENTESS: seleccionando diagnóstico")
    page.locator("a[onclick*='mostrar_seleccionable_diagnostico']").first.click()
    frame = _abrir_iframe_seleccionable(page)
    frame.locator("#bus_d_cie10").fill("CATARATA senil")
    frame.locator("#b_buscar").click()
    frame.locator("a:has-text('CATARATA SENIL')").first.wait_for(timeout=9000)
    frame.locator("a:has-text('CATARATA SENIL')").first.click()
    _cerrar_seleccionable(page)
    page.wait_for_timeout(250)

def _seleccionar_insumo(page, ojo: str, lio: str, log_path: Path) -> None:
    append_log(log_path, f"LENTESS: seleccionando insumo ojo={ojo} lio={lio}")
    page.locator("a[onclick*='mostrar_seleccionable_insumo']").first.click()
    frame = _abrir_iframe_seleccionable(page)
    frame.locator("#bus_c_especialidad").select_option(label="OFTALMOLOGÍA")
    frame.locator("#b_buscar").click()
    frame.locator("#BodyListado a").first.wait_for(timeout=9000)

    idx = 0 if _normalize_ojo(ojo) == "OD" else 2
    frame.locator("#BodyListado a").nth(idx).click()
    _cerrar_seleccionable(page)
    page.wait_for_timeout(250)

    qty = page.locator("#insumo_cantidad").first
    qty.click()
    qty.press("Control+A")
    qty.type("1", delay=60)
    qty.press("Tab")
    page.wait_for_timeout(250)

    obs = page.locator("#insumo_obs").first
    obs.fill(f"DIOPTRIA: {_normalize_lio(lio)}\nVISCOELASTICA PESADA")
    obs.press("Tab")
    page.wait_for_timeout(150)

    btn = page.locator("#btn_add_insumo").first
    btn.wait_for(state="visible", timeout=6000)
    btn.click()
    page.locator("text=Listado de Insumos a Solicitar").first.wait_for(timeout=9000)

def _guardar(page, log_path: Path) -> None:
    append_log(log_path, "LENTESS: guardando solicitud")
    btn = page.locator("#b_guardar").first
    btn.wait_for(state="visible", timeout=9000)
    btn.scroll_into_view_if_needed()
    try:
        page.wait_for_function(
            "() => { const b = document.querySelector('#b_guardar'); return b && !b.disabled; }",
            timeout=5000,
        )
    except Exception:
        pass
    btn.click()
    try:
        from playwright.sync_api import TimeoutError as PWTimeout
        page.wait_for_url(re.compile(r"insu_prestador_cirugia_listado\.php"), timeout=15000)
    except Exception:
        try:
            page.wait_for_load_state("networkidle", timeout=12000)
        except Exception:
            pass
    page.wait_for_timeout(800)
    append_log(log_path, "LENTESS: solicitud guardada OK")

# ------------------------------------------------------------------
# PROCESAR UN PACIENTE
# ------------------------------------------------------------------

def _procesar_paciente(page, afiliado: str, ojo: str, lio: str,
                        user: str, pw: str, log_path: Path) -> None:
    if _looks_like_login(page):
        append_log(log_path, "LENTESS: sesión vencida — relogueando")
        _do_login(page, user, pw, log_path)
        page.goto(FORM_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(WAIT_FORM_STABLE_MS)

    _completar_campos_fijos(page, log_path)
    _seleccionar_beneficiario(page, afiliado, log_path)
    _seleccionar_diagnostico(page, log_path)
    _seleccionar_insumo(page, ojo, lio, log_path)
    _guardar(page, log_path)

# ------------------------------------------------------------------
# ENTRY POINT
# ------------------------------------------------------------------

def run_lentess(payload: LentessPayload, log_path: Path) -> Dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        raise RuntimeError("Playwright no instalado en el conector local.") from exc

    append_log(log_path, "LENTESS: iniciando")
    append_log(log_path, f"LENTESS: {len(payload.pacientes)} paciente(s) a procesar")

    profile = _profile_dir(log_path)
    profile.mkdir(parents=True, exist_ok=True)
    
    ok = 0
    errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=False,
            args=_launch_args(), 
        )
        context = browser.new_context(no_viewport=True)
        page = context.new_page()
        _attach_dialog_handler(page)

        # Minimizar ventana al iniciar
        _set_window_state(page, "minimized")

        _ensure_session(page, payload.credenciales.user, payload.credenciales.password, log_path)

        for i, pac in enumerate(payload.pacientes, start=1):
            append_log(log_path, f"LENTESS: paciente {i}/{len(payload.pacientes)} afiliado={pac.afiliado}")
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
                append_log(log_path, f"LENTESS: ✓ afiliado {pac.afiliado} OK")
            except Exception as exc:
                errors.append({"afiliado": pac.afiliado, "error": str(exc)})
                append_log(log_path, f"LENTESS: ✗ ERROR afiliado {pac.afiliado}: {exc}")

            if i < len(payload.pacientes):
                page.goto(FORM_URL, wait_until="domcontentloaded")
                page.wait_for_timeout(WAIT_FORM_STABLE_MS)

        context.close()
        browser.close()

    if ok == 0:
        raise RuntimeError("No se completó ninguna solicitud Lentess.")

    if errors:
        err_list = "; ".join(f"{e['afiliado']}:{e['error']}" for e in errors)
        raise RuntimeError(f"Lentess parcial — OK={ok} ERROR={len(errors)} — {err_list}")

    append_log(log_path, f"LENTESS: ✓ {ok}/{len(payload.pacientes)} solicitudes guardadas")
    return {"summary": {"total": len(payload.pacientes), "ok": ok, "errors": 0}}
