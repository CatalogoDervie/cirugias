# AGENTS.md

## Objetivo del proyecto
Este repositorio contiene una plataforma web de gestión de cirugías usada por personal no técnico.
La UX debe ser simple, clara y vendible.
La prioridad es NO romper funcionalidades existentes.

## Estado actual
La parte funcional hasta el envío de WhatsApp está correcta.
Las alertas actuales están correctas y NO deben modificarse salvo que sea estrictamente necesario para compatibilidad.
La página principal y los flujos actuales deben seguir funcionando.

## Objetivo nuevo
Agregar 2 automatizaciones:
1. Pami recetas
2. Lentess

Estas automatizaciones NO deben descargarse como scripts manuales para el usuario final.
Deben verse como funciones que se ejecutan desde la página.

## Restricción técnica
La web puede seguir siendo estática en frontend, pero debe integrarse con un agente local instalable en Windows.
Ese agente debe ejecutarse en segundo plano y exponer endpoints locales para que la web lo invoque.
La experiencia del usuario debe parecer “desde la página y la nube”.

## UX esperada
- El usuario no debe editar código.
- El usuario no debe abrir consola.
- El usuario no debe ejecutar scripts manuales.
- Todo debe activarse desde botones dentro de la página.
- Debe haber estados visuales claros: conector activo, ejecutando, completado, error.

## Reglas
- No romper filtros.
- No romper tabla principal.
- No romper WhatsApp.
- No romper alertas.
- No eliminar funciones existentes sin reemplazo compatible.
- Mantener estilo visual consistente.
- Priorizar cambios mínimos y seguros.

## Entregables esperados
- Modificaciones del frontend en index.html
- Agente local Python/Windows
- README de instalación
- Empaquetado simple para cliente final
- Instrucciones de prueba
