#!/usr/bin/env bash
# Descarga los originales de la carpeta pública de Drive "la rete videos" sin recodificar.
# Uso: bash scripts/descargar_drive.sh   (desde la raíz del repo)
set -u
cd "$(dirname "$0")/.."
tail -n +2 analisis/drive_manifest.tsv | while IFS=$'\t' read -r dest name id size; do
  mkdir -p "$dest"
  out="$dest/$name"
  for try in 1 2 3; do
    have=$(stat -c %s "$out" 2>/dev/null || echo 0)
    [ "$have" = "$size" ] && break
    curl -s -L -C - --retry 3 -o "$out" \
      "https://drive.usercontent.google.com/download?id=$id&export=download&confirm=t"
  done
  have=$(stat -c %s "$out" 2>/dev/null || echo 0)
  if [ "$have" = "$size" ]; then echo "OK   $out"; else echo "FAIL $out ($have/$size)"; fi
done
