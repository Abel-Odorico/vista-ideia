#!/usr/bin/env bash
# Baixa a Montserrat (SIL Open Font License) usada nas legendas
set -e; cd "$(dirname "$0")/.."; mkdir -p assets/fonts
for w in Light Regular Medium SemiBold; do
  curl -sfL -o assets/fonts/Montserrat-$w.ttf "https://raw.githubusercontent.com/JulietaUla/Montserrat/master/fonts/ttf/Montserrat-$w.ttf"
done; echo "Fontes prontas em assets/fonts/"
