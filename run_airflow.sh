#!/usr/bin/env bash
# Levanta el stack de Airflow para la demo con Docker Compose.
#
# El primer run construye la imagen (~1-2 min). Los siguientes arrancan en ~15s.
# Para apagar todo: docker compose down

set -euo pipefail
cd "$(dirname "$0")"

echo "▶  Construyendo imagen e iniciando servicios..."
docker compose up -d --build

echo "▶  Esperando a que el webserver esté listo..."
for i in $(seq 1 40); do
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:8080/health 2>/dev/null || echo "000")
  if [ "$code" = "200" ]; then
    echo ""
    echo "✅  ¡Airflow está listo!"
    echo ""
    echo "   UI  →  http://localhost:8080"
    echo "   Usuario: admin  |  Contraseña: admin"
    echo ""
    echo "   Para apagar:      docker compose down"
    echo "   Para ver logs:    docker compose logs -f"
    exit 0
  fi
  printf "."
  sleep 5
done

echo ""
echo "⚠️  El webserver no respondió después de ~200s. Verificar logs:"
echo "   docker compose logs airflow-webserver"
exit 1
