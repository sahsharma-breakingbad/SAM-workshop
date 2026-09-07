#!/usr/bin/env bash
# build.sh — Cross-compile travel-planner for all SAM STR target platforms.
#
# Usage:
#   ./build.sh                  # build all platforms
#   ./build.sh linux-amd64      # build one platform
#   ./build.sh --package        # build all + create .zip files for SAM upload
#
# Output layout:
#   dist/
#     darwin-arm64/    travel-planner        manifest.yaml
#     linux-amd64/     travel-planner        manifest.yaml
#     linux-arm64/     travel-planner        manifest.yaml
#     windows-amd64/   travel-planner.exe    manifest.yaml
#   dist/packages/     (only with --package)
#     Travel-planner-darwin-arm64.zip
#     Travel-planner-linux-amd64.zip
#     Travel-planner-linux-arm64.zip
#     Travel-planner-windows-amd64.zip

set -euo pipefail

NAME="travel-planner"
DIST="dist"
PACKAGE=false

# Parse args
TARGETS=()
for arg in "$@"; do
  case "$arg" in
    --package) PACKAGE=true ;;
    *)         TARGETS+=("$arg") ;;
  esac
done

# Default: all platforms
if [ ${#TARGETS[@]} -eq 0 ]; then
  TARGETS=(darwin-arm64 linux-amd64 linux-arm64 windows-amd64)
fi

build_platform() {
  local PLATFORM="$1"
  local GOOS GOARCH EXE_NAME

  case "$PLATFORM" in
    darwin-arm64)  GOOS=darwin;  GOARCH=arm64; EXE_NAME="${NAME}" ;;
    linux-amd64)   GOOS=linux;   GOARCH=amd64; EXE_NAME="${NAME}" ;;
    linux-arm64)   GOOS=linux;   GOARCH=arm64; EXE_NAME="${NAME}" ;;
    windows-amd64) GOOS=windows; GOARCH=amd64; EXE_NAME="${NAME}.exe" ;;
    *)
      echo "ERROR: unknown platform '${PLATFORM}'. Valid: darwin-arm64, linux-amd64, linux-arm64, windows-amd64"
      return 1
      ;;
  esac

  local OUT_DIR="${DIST}/${PLATFORM}"
  mkdir -p "$OUT_DIR"

  echo "==> Building ${PLATFORM} ..."
  CGO_ENABLED=0 GOOS="$GOOS" GOARCH="$GOARCH" \
    go build -trimpath -ldflags="-s -w" -o "${OUT_DIR}/${EXE_NAME}" .

  # Write the manifest with the correct executable name for this platform
  cat > "${OUT_DIR}/manifest.yaml" <<MANIFEST
version: 1
tools:
  compile_itinerary:
    runtime: go
    executable: ./${EXE_NAME}
    timeout_seconds: 30
  calculate_budget:
    runtime: go
    executable: ./${EXE_NAME}
    timeout_seconds: 15
MANIFEST

  echo "    binary  : ${OUT_DIR}/${EXE_NAME}  ($(du -sh "${OUT_DIR}/${EXE_NAME}" | cut -f1))"
  echo "    manifest: ${OUT_DIR}/manifest.yaml"
}

package_platform() {
  local PLATFORM="$1"
  local OUT_DIR="${DIST}/${PLATFORM}"
  local PKG_DIR="${DIST}/packages"
  local ZIP_NAME="Travel-planner-${PLATFORM}.zip"

  mkdir -p "$PKG_DIR"
  (cd "$OUT_DIR" && zip -q "../packages/${ZIP_NAME}" *)
  echo "    package : ${PKG_DIR}/${ZIP_NAME}  ($(du -sh "${PKG_DIR}/${ZIP_NAME}" | cut -f1))"
}

for PLATFORM in "${TARGETS[@]}"; do
  build_platform "$PLATFORM"
  if [ "$PACKAGE" = "true" ]; then
    package_platform "$PLATFORM"
  fi
done

echo ""
echo "Done. Built: ${TARGETS[*]}"
if [ "$PACKAGE" = "true" ]; then
  echo "Packages in ${DIST}/packages/ — upload the correct .zip to SAM Desktop for each platform."
fi
