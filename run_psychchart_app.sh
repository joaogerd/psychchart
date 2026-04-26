#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

# =============================================================================
# psychChart - local launcher
# =============================================================================
#
# Objetivo
# --------
# Subir o ambiente local do psychChart Web a partir da raiz do repositório.
#
# Este script:
#   - valida dependências locais
#   - instala o pacote Python em modo editável com extras da API
#   - instala dependências do frontend quando necessário
#   - sobe a API FastAPI com Uvicorn
#   - sobe o frontend React/Vite
#   - aguarda a API responder
#   - oferece comandos auxiliares para logs, status, restart e down
#
# Uso
# ---
#   bash run_psychchart_app.sh
#   bash run_psychchart_app.sh up
#   bash run_psychchart_app.sh down
#   bash run_psychchart_app.sh restart
#   bash run_psychchart_app.sh logs
#   bash run_psychchart_app.sh status
#
# Observação
# ----------
# O arquivo pode ser executado com "bash run_psychchart_app.sh" logo após o clone,
# desde que Python, pip, Node.js e npm estejam disponíveis no ambiente local.
# =============================================================================

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
LOG_DIR="$ROOT_DIR/.psychchart/logs"
PID_DIR="$ROOT_DIR/.psychchart/pids"
API_PID_FILE="$PID_DIR/api.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"
API_LOG="$LOG_DIR/api.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"
API_HOST="127.0.0.1"
API_PORT="8001"
FRONTEND_HOST="127.0.0.1"
FRONTEND_PORT="5173"
API_HEALTH_URL="http://${API_HOST}:${API_PORT}/health"
API_DOCS_URL="http://${API_HOST}:${API_PORT}/docs"
FRONTEND_URL="http://${FRONTEND_HOST}:${FRONTEND_PORT}"
WAIT_TIMEOUT=120
SUBCOMMAND="up"
INSTALL_DEPS=1

log_info()  { printf '[INFO] %s\n' "$*"; }
log_ok()    { printf '[ OK ] %s\n' "$*"; }
log_warn()  { printf '[WARN] %s\n' "$*"; }
log_error() { printf '[ERRO] %s\n' "$*" >&2; }

usage() {
  cat <<EOF
psychChart local launcher

Uso:
  bash run_psychchart_app.sh [subcomando] [opções]

Subcomandos:
  up       Sobe API FastAPI + frontend React/Vite (padrão)
  down     Encerra API e frontend iniciados pelo launcher
  restart  Reinicia o ambiente
  logs     Mostra logs da API e do frontend
  status   Mostra estado atual dos processos

Opções:
  --api-port PORTA       Porta da API FastAPI (default: 8001)
  --frontend-port PORTA  Porta do frontend Vite (default: 5173)
  --timeout SEG          Tempo máximo de espera pela API (default: 120)
  --no-install           Não instala/atualiza dependências
  -h, --help             Exibe esta ajuda

Exemplos:
  bash run_psychchart_app.sh
  bash run_psychchart_app.sh up --api-port 8001 --frontend-port 5173
  bash run_psychchart_app.sh restart
  bash run_psychchart_app.sh logs
  bash run_psychchart_app.sh down
EOF
}

require_cmd() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || {
    log_error "Dependência obrigatória não encontrada: $cmd"
    exit 1
  }
}

check_repo_root() {
  [[ -f "$ROOT_DIR/pyproject.toml" ]] || {
    log_error "pyproject.toml não encontrado. Execute este script na raiz do repositório psychChart."
    exit 1
  }

  [[ -d "$FRONTEND_DIR" ]] || {
    log_error "Diretório frontend/ não encontrado. Atualize o repositório com git pull."
    exit 1
  }
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      up|down|restart|logs|status)
        SUBCOMMAND="$1"
        shift
        ;;
      --api-port)
        API_PORT="$2"
        API_HEALTH_URL="http://${API_HOST}:${API_PORT}/health"
        API_DOCS_URL="http://${API_HOST}:${API_PORT}/docs"
        shift 2
        ;;
      --frontend-port)
        FRONTEND_PORT="$2"
        FRONTEND_URL="http://${FRONTEND_HOST}:${FRONTEND_PORT}"
        shift 2
        ;;
      --timeout)
        WAIT_TIMEOUT="$2"
        shift 2
        ;;
      --no-install)
        INSTALL_DEPS=0
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        log_error "Argumento inválido: $1"
        usage
        exit 1
        ;;
    esac
  done
}

ensure_dirs() {
  mkdir -p "$LOG_DIR" "$PID_DIR"
}

is_pid_running() {
  local pid_file="$1"
  [[ -f "$pid_file" ]] || return 1
  local pid
  pid="$(cat "$pid_file")"
  [[ -n "$pid" ]] || return 1
  kill -0 "$pid" >/dev/null 2>&1
}

port_in_use() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -ltn "sport = :${port}" | grep -q ":${port}"
  elif command -v lsof >/dev/null 2>&1; then
    lsof -i ":${port}" >/dev/null 2>&1
  else
    return 1
  fi
}

install_python_deps() {
  if (( INSTALL_DEPS == 0 )); then
    log_info "Instalação de dependências Python ignorada (--no-install)."
    return
  fi

  log_info "Instalando psychChart em modo editável com extras da API..."
  python -m pip install -e "$ROOT_DIR[api]" >/dev/null
  log_ok "Dependências Python prontas."
}

install_frontend_deps() {
  if (( INSTALL_DEPS == 0 )); then
    log_info "Instalação de dependências frontend ignorada (--no-install)."
    return
  fi

  if [[ -d "$FRONTEND_DIR/node_modules" ]]; then
    log_ok "Dependências do frontend já instaladas."
    return
  fi

  log_info "Instalando dependências do frontend..."
  (cd "$FRONTEND_DIR" && npm install) >/dev/null
  log_ok "Dependências do frontend prontas."
}

start_api() {
  if is_pid_running "$API_PID_FILE"; then
    log_ok "API já está rodando (PID $(cat "$API_PID_FILE"))."
    return
  fi

  if port_in_use "$API_PORT"; then
    log_warn "A porta ${API_PORT} já está em uso. A API pode já estar rodando fora deste launcher."
  fi

  log_info "Subindo API FastAPI em http://${API_HOST}:${API_PORT} ..."
  (
    cd "$ROOT_DIR"
    python -m uvicorn psychchart.api.fastapi_app:app \
      --host "$API_HOST" \
      --port "$API_PORT" \
      --reload
  ) >"$API_LOG" 2>&1 &

  echo $! > "$API_PID_FILE"
  log_ok "API iniciada (PID $(cat "$API_PID_FILE"))."
}

start_frontend() {
  if is_pid_running "$FRONTEND_PID_FILE"; then
    log_ok "Frontend já está rodando (PID $(cat "$FRONTEND_PID_FILE"))."
    return
  fi

  if port_in_use "$FRONTEND_PORT"; then
    log_warn "A porta ${FRONTEND_PORT} já está em uso. O frontend pode já estar rodando fora deste launcher."
  fi

  log_info "Subindo frontend Vite em ${FRONTEND_URL} ..."
  (
    cd "$FRONTEND_DIR"
    VITE_PSYCHCHART_API_URL="http://${API_HOST}:${API_PORT}" \
      npm run dev -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT"
  ) >"$FRONTEND_LOG" 2>&1 &

  echo $! > "$FRONTEND_PID_FILE"
  log_ok "Frontend iniciado (PID $(cat "$FRONTEND_PID_FILE"))."
}

wait_for_api() {
  local start_ts now elapsed
  start_ts="$(date +%s)"

  log_info "Aguardando API responder em $API_HEALTH_URL ..."

  until curl -fsS "$API_HEALTH_URL" >/dev/null 2>&1; do
    sleep 2
    now="$(date +%s)"
    elapsed=$((now - start_ts))

    if (( elapsed >= WAIT_TIMEOUT )); then
      log_error "Timeout aguardando a API após ${WAIT_TIMEOUT}s."
      log_error "Consulte os logs com: bash run_psychchart_app.sh logs"
      exit 1
    fi
  done

  log_ok "API está respondendo."
}

stop_process() {
  local name="$1"
  local pid_file="$2"

  if ! [[ -f "$pid_file" ]]; then
    log_info "$name não possui PID registrado."
    return
  fi

  local pid
  pid="$(cat "$pid_file")"

  if [[ -z "$pid" ]]; then
    rm -f "$pid_file"
    return
  fi

  if kill -0 "$pid" >/dev/null 2>&1; then
    log_info "Encerrando $name (PID $pid)..."
    kill "$pid" >/dev/null 2>&1 || true
    sleep 1
    if kill -0 "$pid" >/dev/null 2>&1; then
      log_warn "$name ainda ativo. Forçando encerramento..."
      kill -9 "$pid" >/dev/null 2>&1 || true
    fi
    log_ok "$name encerrado."
  else
    log_info "$name não está em execução."
  fi

  rm -f "$pid_file"
}

show_endpoints() {
  cat <<EOF

psychChart está no ar.

URLs:
  Frontend : $FRONTEND_URL
  API      : http://${API_HOST}:${API_PORT}
  Docs     : $API_DOCS_URL
  Health   : $API_HEALTH_URL

Logs:
  API      : $API_LOG
  Frontend : $FRONTEND_LOG

Comandos úteis:
  bash run_psychchart_app.sh status
  bash run_psychchart_app.sh logs
  bash run_psychchart_app.sh down

EOF
}

do_up() {
  ensure_dirs
  install_python_deps
  install_frontend_deps
  start_api
  wait_for_api
  start_frontend
  show_endpoints
}

do_down() {
  ensure_dirs
  stop_process "Frontend" "$FRONTEND_PID_FILE"
  stop_process "API" "$API_PID_FILE"
}

do_restart() {
  do_down || true
  do_up
}

do_logs() {
  ensure_dirs
  log_info "Mostrando logs. Use Ctrl+C para sair."
  touch "$API_LOG" "$FRONTEND_LOG"
  tail -f "$API_LOG" "$FRONTEND_LOG"
}

do_status() {
  ensure_dirs
  if is_pid_running "$API_PID_FILE"; then
    log_ok "API rodando (PID $(cat "$API_PID_FILE")) em http://${API_HOST}:${API_PORT}"
  else
    log_warn "API não está rodando pelo launcher."
  fi

  if is_pid_running "$FRONTEND_PID_FILE"; then
    log_ok "Frontend rodando (PID $(cat "$FRONTEND_PID_FILE")) em $FRONTEND_URL"
  else
    log_warn "Frontend não está rodando pelo launcher."
  fi
}

main() {
  parse_args "$@"

  require_cmd python
  require_cmd curl
  require_cmd npm
  require_cmd node
  check_repo_root

  case "$SUBCOMMAND" in
    up)      do_up ;;
    down)    do_down ;;
    restart) do_restart ;;
    logs)    do_logs ;;
    status)  do_status ;;
    *)
      log_error "Subcomando inválido: $SUBCOMMAND"
      usage
      exit 1
      ;;
  esac
}

main "$@"
