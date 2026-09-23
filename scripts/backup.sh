#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
backup_dir="$project_dir/backups"
timestamp=$(date -u +%Y%m%dT%H%M%SZ)
archive="$backup_dir/petsus-$timestamp.tar.gz"
work_dir="$backup_dir/.working-$timestamp"

mkdir -p "$work_dir"

docker compose -f "$project_dir/compose.yaml" exec -T app python -c \
  "import sqlite3; source=sqlite3.connect('/app/data/usuarios.db'); target=sqlite3.connect('/app/data/usuarios-backup.db'); source.backup(target); target.close(); source.close()"

docker compose -f "$project_dir/compose.yaml" cp app:/app/data/usuarios-backup.db "$work_dir/usuarios.db"
docker compose -f "$project_dir/compose.yaml" exec -T app rm -f /app/data/usuarios-backup.db

if docker compose -f "$project_dir/compose.yaml" exec -T app test -f /app/data/usuarios.secret; then
  docker compose -f "$project_dir/compose.yaml" cp app:/app/data/usuarios.secret "$work_dir/usuarios.secret"
  tar -czf "$archive" -C "$work_dir" usuarios.db usuarios.secret
else
  tar -czf "$archive" -C "$work_dir" usuarios.db
  echo "Aviso: usuarios.secret não existe; preserve PETSUS_CPF_PEPPER do .env separadamente."
fi

rm -f "$work_dir/usuarios.db" "$work_dir/usuarios.secret"
rmdir "$work_dir"

echo "Backup criado em: $archive"
