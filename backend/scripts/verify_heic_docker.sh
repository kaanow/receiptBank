#!/bin/sh
# Verify HEIC decode inside the built Docker image (run from repo root).
# Usage: ./backend/scripts/verify_heic_docker.sh [path/to/receipt.heic]
set -e
HEIC="${1:-test_receipts/Ferry.HEIC}"
if [ ! -f "$HEIC" ]; then
  echo "No HEIC file at $HEIC"
  exit 1
fi
echo "Building image..."
docker build -t receiptbank:heic-test .
echo "Testing HEIC decode in container..."
docker run --rm -v "$(pwd)/$(dirname "$HEIC"):/data:ro" receiptbank:heic-test \
  python -c "
from app.ocr import _image_to_text, HAS_HEIF
path = '/data/$(basename "$HEIC")'
b = open(path, 'rb').read()
print('HAS_HEIF:', HAS_HEIF)
text = _image_to_text(b, 'image/heic')
print('Decode OK, len(text):', len(text))
print('First 200 chars:', repr(text[:200]))
"
echo "HEIC verify done."
