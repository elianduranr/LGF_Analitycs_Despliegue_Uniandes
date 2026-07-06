#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if command -v cygpath >/dev/null 2>&1; then
  ROOT_DIR_PY="$(cygpath -w "$ROOT_DIR")"
else
  ROOT_DIR_PY="$ROOT_DIR"
fi

export PYTHONPATH="${PYTHONPATH:-};$ROOT_DIR_PY\\src;$ROOT_DIR_PY"

DEFAULT_DATA_PATH="/c/Proyectos_gaitana/Proyecto_despliegue/bases de datos historicas/historic_sales_acum.csv"
DATA_PATH="${LGF_DATA_PATH:-$DEFAULT_DATA_PATH}"
HOST="${LGF_DASH_HOST:-127.0.0.1}"
PORT="${LGF_DASH_PORT:-8052}"

if [[ ! -f "$DATA_PATH" ]]; then
  echo "No encontre el acumulado en: $DATA_PATH"
  echo "Define LGF_DATA_PATH con la ruta a historic_sales_acum.csv y vuelve a correr."
  exit 1
fi

if command -v cygpath >/dev/null 2>&1; then
  DATA_PATH_PY="$(cygpath -w "$DATA_PATH")"
else
  DATA_PATH_PY="$DATA_PATH"
fi

python app/dash_ventas.py \
  --data-path "$DATA_PATH_PY" \
  --host "$HOST" \
  --port "$PORT"
