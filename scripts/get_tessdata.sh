#!/bin/sh
# Download the German OCR model (~8.6 MB, Apache-2.0) into ./tessdata. Alternative: brew install tesseract-lang
set -e
cd "$(dirname "$0")/.."
mkdir -p tessdata
curl -fL -o tessdata/deu.traineddata https://github.com/tesseract-ocr/tessdata_best/raw/main/deu.traineddata
echo "ok: tessdata/deu.traineddata"
