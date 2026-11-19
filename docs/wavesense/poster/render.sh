#!/bin/zsh
# WaveSense A1 포스터 빌드 + 렌더.
#   ./render.sh                → 벡터 버전 HTML/PDF + 미리보기
#   ./render.sh final          → 벡터 버전 제출용 JPEG(7016x9933, 300dpi)까지
#   ./render.sh photo [final]  → 실사 장면 버전 (WaveSense_포스터_A1_실사.*)
set -euo pipefail
HERE="${0:A:h}"
PROJ="${HERE:h}"
SSD=/Volumes/ProjectsSSD
WORK="$SSD/Work/공설/poster-a1"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

NAME="WaveSense_포스터_A1"; VARIANT=""; FINAL=""
for a in "$@"; do
  case "$a" in
    photo) VARIANT="photo"; NAME="WaveSense_포스터_A1_실사" ;;
    final) FINAL=1 ;;
  esac
done

diskutil info "$SSD" 2>/dev/null | grep -q "70A149BB-89E8-40EB-9137-5B9C4A36917C" || { echo "ProjectsSSD가 연결되지 않았습니다." >&2; exit 1; }
mkdir -p "$WORK"

python3 "$HERE/build_poster.py" $VARIANT
rm -f "$PROJ/$NAME.pdf"
"$CHROME" --headless=new --disable-gpu --no-pdf-header-footer --hide-scrollbars \
  --user-data-dir="$WORK/chrome-profile" \
  --print-to-pdf="$PROJ/$NAME.pdf" "file://$PROJ/$NAME.html" 2>/dev/null || true
# 큰 배경 이미지가 들어가면 Chrome이 PDF를 다 쓰기 전에 돌아오는 경우가 있어 완성될 때까지 기다린다.
for i in {1..60}; do pdfinfo "$PROJ/$NAME.pdf" >/dev/null 2>&1 && break; sleep 1; done
pdfinfo "$PROJ/$NAME.pdf" | grep -E "Pages|Page size"
pdftoppm -r 46 -png -singlefile "$PROJ/$NAME.pdf" "$WORK/preview${VARIANT:+_$VARIANT}" 2>/dev/null
echo "preview: $WORK/preview${VARIANT:+_$VARIANT}.png"

if [[ -n "$FINAL" ]]; then
  pdftoppm -r 300 -png -singlefile "$PROJ/$NAME.pdf" "$WORK/final300" 2>/dev/null
  magick "$WORK/final300.png" -resize '7016x9933!' -background white -alpha remove -units PixelsPerInch -density 300 -quality 94 "$PROJ/$NAME.jpg"
  rm -f "$WORK/final300.png"
  magick identify -format "%wx%h %x x %y %U depth=%z %[colorspace] channels=%[channels]\n" "$PROJ/$NAME.jpg"
fi
