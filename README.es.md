# mcp-mexico

Servidor MCP que da a los agentes de IA datos públicos oficiales de México: tipo de cambio y tasas de Banxico, inflación de INEGI, valores de la UMA y tablas de ISR.

[![CI](https://github.com/DiegoTepichin/mcp-mexico/actions/workflows/ci.yml/badge.svg)](https://github.com/DiegoTepichin/mcp-mexico/actions/workflows/ci.yml)
[![Licencia: MIT](https://img.shields.io/badge/Licencia-MIT-blue.svg)](LICENSE)

[Read in English](README.md)

<!-- GIF de demo antes de hacer público el repo. -->

## Por qué

Los asistentes de IA inventan las cifras económicas de México o usan datos viejos, así que terminas buscándolas a mano en Banxico, INEGI o el SAT para pegarlas en el chat. Con `mcp-mexico`, cualquier cliente [MCP](https://modelcontextprotocol.io) (Claude Desktop, Claude Code, Cursor) las consulta directamente. Cada resultado dice su fuente oficial y la fecha a la que corresponde.

## Herramientas

| Herramienta | Qué regresa | Fuente | Token |
|---|---|---|---|
| `get_fix_rate` | Tipo de cambio FIX USD/MXN, el más reciente o el de una fecha. En fines de semana y días festivos regresa el del día hábil anterior. | Banxico SIE | `BANXICO_TOKEN` |
| `get_fix_rate_range` | FIX diario entre dos fechas (máximo 366 días). | Banxico SIE | `BANXICO_TOKEN` |
| `get_interest_rate` | Tasa objetivo de Banxico, TIIE a 28 días, TIIE de Fondeo o CETES a 28 días; la más reciente o la de una fecha. | Banxico SIE | `BANXICO_TOKEN` |
| `get_interest_rate_range` | Una de esas tasas entre dos fechas (máximo 366 días). | Banxico SIE | `BANXICO_TOKEN` |
| `get_inflation` | INPC e inflación mensual, anual y acumulada en el año para un mes (por defecto, el último publicado). | INEGI | `INEGI_TOKEN` |
| `get_inflation_range` | Lo mismo para cada mes de un rango (máximo 240 meses). | INEGI | `INEGI_TOKEN` |
| `get_uma` | Valores diario, mensual y anual de la UMA, 2020–2026, con su vigencia. | INEGI | ninguno |
| `get_isr_table` | Tablas de ISR para personas físicas, 2020–2026: mensual (art. 96 LISR) y anual (art. 152 LISR). | Anexo 8 de la RMF (SAT / DOF) | ninguno |

`get_uma` y `get_isr_table` funcionan sin conexión y sin configurar nada. Sus datos vienen dentro del paquete; cada tabla cita el documento del que salió y la fecha en que se verificó.

## Consigue tus tokens

Los dos son gratuitos y se obtienen en un par de minutos.

1. **Banxico**: abre la [página de token de la API del SIE](https://www.banxico.org.mx/SieAPIRest/service/v1/token), resuelve el captcha y da clic en "Generar token". El token de 64 caracteres aparece en la misma página.
2. **INEGI**: escribe tu correo en el [formulario de token de INEGI](https://www.inegi.org.mx/app/desarrolladores/generatoken/Usuarios/token_Verify). El token llega por correo.

Puedes empezar con un solo token, o con ninguno: las herramientas a las que les falta su token regresan un mensaje que explica cómo conseguirlo.

## Instalación

Necesitas [uv](https://docs.astral.sh/uv/getting-started/installation/). El servidor corre con `uvx mcp-mexico`; no lo arrancas tú, lo arranca tu cliente MCP.

### Claude Code

```bash
claude mcp add mcp-mexico -e BANXICO_TOKEN=tu-token -e INEGI_TOKEN=tu-token -- uvx mcp-mexico
```

### Claude Desktop

Agrega esto a `claude_desktop_config.json` (Settings → Developer → Edit Config) y reinicia Claude Desktop:

```json
{
  "mcpServers": {
    "mcp-mexico": {
      "command": "uvx",
      "args": ["mcp-mexico"],
      "env": {
        "BANXICO_TOKEN": "tu-token",
        "INEGI_TOKEN": "tu-token"
      }
    }
  }
}
```

### Cursor

Agrega el mismo bloque `mcpServers` a `~/.cursor/mcp.json`.

## Pruébalo

Pregúntale a tu asistente:

- "¿Cuál es el tipo de cambio FIX de hoy?"
- "¿Cuál fue la inflación anual de México en diciembre de 2024?"
- "¿Cuánto son 30 UMAs en pesos este año?"
- "Con la tabla mensual de ISR 2026, ¿cuánto se retiene a un sueldo de 25,000 pesos?"

## Configuración

| Variable | Obligatoria | Descripción |
|---|---|---|
| `BANXICO_TOKEN` | Para las herramientas de Banxico | Token de la API del SIE de Banxico. |
| `INEGI_TOKEN` | Para las herramientas de INEGI | Token de la API de Indicadores de INEGI. |

Las respuestas se guardan solo en memoria: hasta 1 hora los valores más recientes, 24 horas los rangos pasados de Banxico y 6 horas la serie del INPC. No se escribe nada en disco.

## Desarrollo

```bash
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check . && uv run mypy .
uv run mcp-mexico      # arranca el servidor por stdio
```

Los tests nunca tocan la red: reproducen respuestas grabadas de las APIs reales. Consulta [CONTRIBUTING.md](CONTRIBUTING.md).

## Aviso

Este proyecto no está afiliado al Banco de México, al INEGI ni al SAT. Las cifras vienen de sus fuentes públicas, pero revisa la fuente citada antes de usarlas para decisiones fiscales o legales.

## Licencia

[MIT](LICENSE) © Diego Tepichin
