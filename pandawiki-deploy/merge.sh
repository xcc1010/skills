#!/bin/sh
# 在放着所有 .part-* 分卷的目录里执行,合并还原三个大包
set -e
for base in pandawiki-offline.tar.gz xinference-image.tar xinference-cache.tar.gz; do
  if ls "$base".part-* >/dev/null 2>&1; then
    echo ">> 合并 $base ..."
    cat "$base".part-* > "$base"
    echo "   完成: $(ls -lh "$base" | awk '{print $5}')"
  fi
done
echo ">> 全部合并完成。可选校验(见 大包-下载与合并.md 的 sha256)。"
