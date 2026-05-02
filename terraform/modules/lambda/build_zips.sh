#!/usr/bin/env bash
set -euo pipefail

SOURCE_ROOT="$1"
MODULE_PATH="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="${MODULE_PATH}/build"
TMP_ROOT="${MODULE_PATH}/.tmp_zip_build"

rm -rf "${BUILD_DIR}" "${TMP_ROOT}"
mkdir -p "${BUILD_DIR}" "${TMP_ROOT}"

build_zip() {
  local lambda_name="$1"
  local stage_dir="${TMP_ROOT}/${lambda_name}"

  rm -rf "${stage_dir}"
  mkdir -p "${stage_dir}"

  python3 -m pip install --target "${stage_dir}" --quiet pydantic redis

  mkdir -p "${stage_dir}/${lambda_name}" "${stage_dir}/shared"
  cp -R "${SOURCE_ROOT}/src/${lambda_name}/." "${stage_dir}/${lambda_name}/"
  cp -R "${SOURCE_ROOT}/src/shared/." "${stage_dir}/shared/"

  mkdir -p "${stage_dir}/src"
  cp -R "${SOURCE_ROOT}/src/shared" "${stage_dir}/src/shared"

  if [ -f "${SOURCE_ROOT}/src/__init__.py" ]; then
    cp "${SOURCE_ROOT}/src/__init__.py" "${stage_dir}/__init__.py"
    cp "${SOURCE_ROOT}/src/__init__.py" "${stage_dir}/src/__init__.py"
  fi

  (cd "${stage_dir}" && zip -r9 "${BUILD_DIR}/${lambda_name}.zip" .)
}

build_zip producer
build_zip consumer

rm -rf "${TMP_ROOT}"
