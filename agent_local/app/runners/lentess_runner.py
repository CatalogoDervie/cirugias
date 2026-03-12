from __future__ import annotations

import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Tuple

from ..logging_utils import append_log
from ..models import LentessPayload

LOGIN_URL = "https://efectores.pami.org.ar/pami_efectores/login.php?xgap_historial=clear"
FORM_URL = "https://efectores.pami.org.ar/pami_efectores/insu_prestador_cirugia_cargar.php?xgap_historial=reset"
CIRUGIA_CARACTER = "PROGRAMADO"


def _only_digits(s: str) -> str:
    return re.sub(r"\D+", "", s or "")


def _split_beneficio_parentesco(afiliado_full: str) -> Tuple[str, str]:
    d = _only_digits(afiliado_full)
    if len(d) >= 3:
        return d[:-2], d[-2:]
    return d, ""


def _normalize_ojo(ojo: str) -> str:
    o = (ojo or "").strip().upper()
    return o.replace("O.D.", "OD").replace("O.I.", "OI")


def _fecha_probable_hoy_mas_10() -> str:
    f = datetime.today() + timedelta(days=10)
    if f.weekday() == 6:
        f += timedelta(days=1)
    return f.strftime("%d/%m/%Y")


def _set_date_direct(page, selector: str, ddmmyyyy: str) -> None:
    page.locator(selector).first.fill(ddmmyyyy)
    page.locator(selector).first.press("Tab")


def _looks_like_login(page) -> bool:
    url = (page.url or "").lower()
    if "login.php" in url:
        return True
    return page.locator("input[type='password']").count() > 0


def _do_login_if_needed(page, user: str, pw: str, log_path: Path) -> bool:
    if not _looks_like_login(page):
        return False

    append_log(log_path, "LENTESS: paso login")
    page.goto(LOGIN_URL, wait_until="domcontentloaded")

    user_sel = None
    for sel in [
        "input[name*='user' i]",
        "input[id*='user' i]",
        "input[name*='usuario' i]",
        "input[id*='usuario' i]",
        "input[type='text']",
    ]:
        loc = page.locator(sel)
        if loc.count() > 0:
            user_sel = loc.first
            break
    if user_sel is None:
        raise RuntimeError("No se encontró input de usuario en login Lentess.")

    pass_sel = page.locator("input[type='password']").first
    user_sel.fill(user)
    pass_sel.fill(pw)

    btn = None
    for sel in ["button[type='submit']", "input[type='submit']", "button:has-text('Ingresar')", "button:has-text('Entrar')"]:
        loc = page.locator(sel)
        if loc.count() > 0:
            btn = loc.first
            break
    if btn:
        btn.click()
    else:
        pass_sel.press("Enter")

    page.wait_for_timeout(1200)
    return True


def _completar_campos_fijos(page, log_path: Path) -> None:
    append_log(log_path, "LENTESS: completar campos fijos")
    if page.locator("#f_probable_cirugia").count() > 0:
        _set_date_direct(page, "#f_probable_cirugia", _fecha_probable_hoy_mas_10())
    if page.locator("#c_caracter").count() > 0:
        page.locator("#c_caracter").select_option(label=CIRUGIA_CARACTER)


def _abrir_iframe_seleccionable(page):
    frame = page.frame_locator("iframe#iframe-seleccionable")
    frame.locator("body").wait_for(timeout=9000)
    return frame


def _seleccionar_beneficiario(page, afiliado: str, log_path: Path) -> None:
    append_log(log_path, f"LENTESS: seleccionar beneficiario {afiliado}")
    beneficio, parentesco = _split_beneficio_parentesco(afiliado)
    page.locator("a[onclick*='mostrar_seleccionable_beneficiario']").first.click()
    frame = _abrir_iframe_seleccionable(page)
    frame.locator("#bus_n_beneficio").fill(beneficio)
    if parentesco and frame.locator("#bus_grado_parentesco").count() > 0:
        frame.locator("#bus_grado_parentesco").fill(parentesco)
    frame.locator("#b_buscar").click()
    frame.locator("#BodyListado tr").first.wait_for(timeout=9000)
    frame.locator("#BodyListado tr a").first.click()
    page.wait_for_timeout(250)


def _seleccionar_diagnostico(page, log_path: Path) -> None:
    append_log(log_path, "LENTESS: seleccionar diagnóstico")
    page.locator("a[onclick*='mostrar_seleccionable_diagnostico']").first.click()
    frame = _abrir_iframe_seleccionable(page)
    frame.locator("#bus_d_cie10").fill("CATARATA senil")
    frame.locator("#b_buscar").click()
    frame.locator("a:has-text('CATARATA SENIL')").first.wait_for(timeout=9000)
    frame.locator("a:has-text('CATARATA SENIL')").first.click()
    page.wait_for_timeout(250)


def _seleccionar_insumo(page, ojo: str, lio: str, log_path: Path) -> None:
    append_log(log_path, f"LENTESS: seleccionar insumo ojo={ojo} lio={lio}")
    page.locator("a[onclick*='mostrar_seleccionable_insumo']").first.click()
    frame = _abrir_iframe_seleccionable(page)
    frame.locator("#bus_c_especialidad").select_option(label="OFTALMOLOGÍA")
    frame.locator("#b_buscar").click()
    frame.locator("#BodyListado a").first.wait_for(timeout=9000)

    idx = 0 if _normalize_ojo(ojo) == "OD" else 2
    frame.locator("#BodyListado a").nth(idx).click()
    page.wait_for_timeout(250)

    page.locator("#insumo_cantidad").first.fill("1")
    page.locator("#insumo_obs").first.fill(f"DIOPTRIA: {lio}\nVISCOELASTICA PESADA")
    page.locator("#btn_add_insumo").first.click()

    page.locator("text=Listado de Insumos a Solicitar").first.wait_for(timeout=9000)


def _guardar(page, log_path: Path) -> None:
    append_log(log_path, "LENTESS: guardar solicitud")
    btn = page.locator("#b_guardar").first
    btn.wait_for(state="visible", timeout=9000)
    btn.click()
    page.wait_for_timeout(1200)



def run_lentess(payload: LentessPayload, log_path: Path) -> Dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        raise RuntimeError("Playwright no está instalado en el conector local.") from exc

    append_log(log_path, "LENTESS: inicio de ejecución real")
    append_log(log_path, f"LENTESS: pacientes recibidos={len(payload.pacientes)}")

    ok = 0
    errors = []

    with sync_playwright() as p:
        append_log(log_path, "LENTESS: abriendo navegador Chrome (visible)")
        browser = p.chromium.launch(
            channel="chrome",
            headless=False,
            args=["--start-maximized", "--no-first-run", "--no-default-browser-check"],
        )
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        page.goto(FORM_URL, wait_until="domcontentloaded")
        _do_login_if_needed(page, payload.credenciales.user, payload.credenciales.password, log_path)
        page.goto(FORM_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(1200)

        for i, pac in enumerate(payload.pacientes, start=1):
            append_log(log_path, f"LENTESS: paciente {i}/{len(payload.pacientes)} afiliado={pac.afiliado}")
            try:
                _completar_campos_fijos(page, log_path)
                _seleccionar_beneficiario(page, pac.afiliado, log_path)
                _seleccionar_diagnostico(page, log_path)
                _seleccionar_insumo(page, pac.ojo, pac.lio, log_path)
                _guardar(page, log_path)
                ok += 1
                append_log(log_path, f"LENTESS: paciente {pac.afiliado} OK")
            except Exception as exc:
                errors.append({"afiliado": pac.afiliado, "error": str(exc)})
                append_log(log_path, f"LENTESS: ERROR paciente {pac.afiliado}: {exc}")

            if i < len(payload.pacientes):
                page.goto(FORM_URL, wait_until="domcontentloaded")
                _do_login_if_needed(page, payload.credenciales.user, payload.credenciales.password, log_path)
                page.goto(FORM_URL, wait_until="domcontentloaded")
                page.wait_for_timeout(800)

        # Cerrar contexto al finalizar
        context.close()
        browser.close()

    if ok == 0:
        raise RuntimeError("No se pudo completar ninguna solicitud Lentess.")

    if errors:
        raise RuntimeError(f"Lentess parcial: OK={ok}, ERROR={len(errors)}. Revisar log del job.")

    append_log(log_path, "LENTESS: ejecución real finalizada con éxito")
    return {"summary": {"total": len(payload.pacientes), "ok": ok, "error": 0}}
