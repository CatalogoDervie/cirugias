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


def _afiliado_no_encontrado(page) -> bool:
    try:
        return page.get_by_text("Afiliado no encontrado", exact=False).is_visible(timeout=800)
    except Exception:
        return False


def _login_if_needed(page, user: str, password: str, log_path: Path) -> None:
    if page.locator("input[type='password']").count() == 0:
        return

    append_log(log_path, "RECETAS: paso login detectado")
    pass_field = page.locator("input[type='password']").first

    user_field = None
    for sel in [
        "input[name*=usuario i]",
        "input[id*=usuario i]",
        "input[name*=user i]",
        "input[id*=user i]",
        "input[name*=login i]",
        "input[id*=login i]",
        "input[type='email']",
        "input[type='text']",
    ]:
        loc = page.locator(sel)
        if loc.count() > 0 and loc.first.is_visible():
            user_field = loc.first
            break

    if user_field:
        user_field.fill(user)
    pass_field.fill(password)

    btn = page.get_by_role("button", name=re.compile("Ingresar|Entrar|Acceder|Iniciar", re.I))
    if btn.count() > 0 and btn.first.is_visible():
        btn.first.click()
    else:
        pass_field.press("Enter")

    page.wait_for_timeout(1500)


def _get_meds_context(page, timeout_s: float = 25.0):
    from playwright.sync_api import TimeoutError as PWTimeout

    try:
        page.wait_for_selector("#accion", state="visible", timeout=2500)
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
                    fr.wait_for_selector("#accion", state="visible", timeout=1500)
                    fr.wait_for_selector("#t_busqueda", state="visible", timeout=1500)
                    return fr
            except Exception:
                pass
        time.sleep(0.2)

    raise RuntimeError("No apareció el buscador de medicamentos.")


def _abrir_buscador_y_elegir(page, idx: int, nombre: str, log_path: Path) -> None:
    append_log(log_path, f"RECETAS: buscar medicamento idx={idx} nombre={nombre}")
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
        ctx.get_by_role("button", name=re.compile("BUSCAR|Buscar", re.I)).first.click()

    table_cell = ctx.locator(
        "xpath=//*[@id='t_busqueda']/ancestor::*[self::div or self::form][1]//following::table[1]//tbody//tr[td]/td[3]"
    ).first
    table_cell.wait_for(state="visible", timeout=12000)
    table_cell.click(force=True)
    page.wait_for_timeout(250)


def _handle_save_confirmations(page) -> None:
    for _ in range(6):
        try:
            yes_btn = page.locator("button:has-text('Sí'), button:has-text('Si'), button.ui-confirm-button")
            if yes_btn.count() > 0 and yes_btn.first.is_visible():
                yes_btn.first.click()
                time.sleep(0.2)

            ok_btn = page.locator("button:has-text('Aceptar'), button:has-text('OK')")
            if ok_btn.count() > 0 and ok_btn.first.is_visible():
                ok_btn.first.click()
                time.sleep(0.2)
        except Exception:
            pass
        time.sleep(0.15)


def _cargar_una_receta(page, benef: str, diag: str, med_a: str, med_b: str, log_path: Path) -> None:
    append_log(log_path, f"RECETAS: cargar receta para afiliado={benef} ({med_a} + {med_b})")
    page.goto(PAMI_URL, wait_until="domcontentloaded")

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



def run_recetas(payload: RecetasPayload, log_path: Path) -> Dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        raise RuntimeError("Playwright no está instalado en el conector local.") from exc

    append_log(log_path, "RECETAS: inicio de ejecución real")
    append_log(log_path, f"RECETAS: paciente={payload.paciente or '(sin nombre)'} afiliado={payload.afiliado}")

    if (payload.obraSocial or "").strip().upper() not in {"PAMI", ""}:
        raise RuntimeError("El paciente no pertenece a PAMI para flujo recetas.")

    meds = payload.medicamentos
    ok_count = 0

    with sync_playwright() as p:
        append_log(log_path, "RECETAS: abriendo navegador Chrome (visible)")
        context = p.chromium.launch_persistent_context(
            str((log_path.parent / "chrome_profile_recetas").resolve()),
            channel="chrome",
            headless=False,
        )
        page = context.new_page()
        page.goto(PAMI_URL, wait_until="domcontentloaded")

        _login_if_needed(page, payload.credenciales.user, payload.credenciales.password, log_path)
        # Si hay OTP, permitir intervención manual breve
        if page.locator("input[type='password']").count() > 0:
            append_log(log_path, "RECETAS: login aún visible; esperando intervención OTP (hasta 120s)")
            for _ in range(120):
                if page.locator("input[type='password']").count() == 0:
                    break
                page.wait_for_timeout(1000)

        if page.locator("input[type='password']").count() > 0:
            raise RuntimeError("No se pudo completar login/OTP para Recetas.")

        for idx, pair in enumerate(meds, start=1):
            append_log(log_path, f"RECETAS: receta {idx}/3 en ejecución")
            _cargar_una_receta(page, payload.afiliado, payload.diagnostico, pair[0], pair[1], log_path)
            ok_count += 1
            append_log(log_path, f"RECETAS: receta {idx}/3 guardada")
            page.wait_for_timeout(500)

        context.close()

    if ok_count != 3:
        raise RuntimeError(f"Recetas incompletas: {ok_count}/3 guardadas")

    append_log(log_path, "RECETAS: ejecución real finalizada con éxito")
    return {
        "result": {
            "benef": payload.afiliado,
            "nombre": payload.paciente,
            "status": "OK",
            "recetas_ok": ok_count,
        }
    }
