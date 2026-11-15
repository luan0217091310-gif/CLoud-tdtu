#!/bin/sh
set -eu

case "${1:-}" in
  ""|--core) ;;
  *) printf 'Usage: init-storage.sh [--core]\n' >&2; exit 2 ;;
esac

mc alias set -- lab http://object-storage-server:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"
mc mb --ignore-existing lab/demo lab/profile-pics lab/documents
mc anonymous set-json /avatar-policy.json lab/profile-pics
mc cp /web/index.html lab/demo/index.html
mc stat lab/demo/index.html

missing=0
if [ -f /samples/bao-cao.pdf ]; then
  mc cp /samples/bao-cao.pdf lab/documents/bao-cao.pdf
  mc stat lab/documents/bao-cao.pdf
else
  printf 'Thiếu sample-files/bao-cao.pdf. Xuất PDF từ báo cáo Word.\n' >&2
  missing=1
fi
if [ -f /samples/avatar.jpg ]; then
  mc cp /samples/avatar.jpg lab/profile-pics/avatar.jpg
  mc stat lab/profile-pics/avatar.jpg
  printf 'URL ảnh demo: http://localhost:9000/profile-pics/avatar.jpg\n'
else
  printf 'Thiếu sample-files/avatar.jpg. Chép ảnh JPG thật để kiểm tra URL public.\n' >&2
  missing=1
fi

if [ "$missing" -ne 0 ] && [ "${1:-}" != --core ]; then
  exit 1
fi
