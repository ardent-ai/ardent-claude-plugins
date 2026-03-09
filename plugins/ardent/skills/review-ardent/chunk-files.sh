#!/usr/bin/env bash
set -euo pipefail

# chunk-files.sh — Build agent file manifest and pre-save diffs for code review
# Usage: bash chunk-files.sh "git diff main...HEAD"
#
# Output: Pre-chunked file lists per agent category, with pre-saved diff files.
# Each CHUNK header shows its diff file path: [/tmp/review-<section>-<N>.diff]
# Caps: 20 files AND 1500 changed lines per chunk.
# Trailing chunks under 50 lines are merged into the previous chunk.
# Domain agents are skipped if their total lines < 20.

DIFF_CMD="${1:?Usage: $0 'git diff main...HEAD'}"

# Clean up any prior run
rm -f /tmp/_rc.tsv /tmp/_rc_* /tmp/review-*.diff

# Phase 1: Classify files and sort by change size (largest first)
eval "$DIFF_CMD" --numstat | awk '{
  if ($1 == "-" || $1 ~ /Binary/) next
  total = $1 + $2; f = $3
  t = (f ~ /\.test\./ || f ~ /__tests__/) ? 1 : 0
  b = (!t && f ~ /\/backend\//) ? 1 : 0
  fr = (!t && (f ~ /\.tsx$/ || f ~ /\.css$/ || f ~ /\/frontend\// || f ~ /\/renderer\//)) ? 1 : 0
  sc = (!t && (f ~ /\/oauth\// || f ~ /\/auth\// || f ~ /\/mcp\// || f ~ /\/ipc\//)) ? 1 : 0
  ty = (!t && (f ~ /^packages\/schema\// || f ~ /^packages\/skill-manifest\// || f ~ /^packages\/sdk\//)) ? 1 : 0
  pf = (!t && (f ~ /^packages\/db\// || f ~ /^packages\/llm-core\// || f ~ /^packages\/mcp-remote\// || f ~ /^packages\/search\//)) ? 1 : 0
  printf "%d\t%d\t%d\t%d\t%d\t%d\t%d\t%s\n", total, t, b, fr, sc, ty, pf, f
}' | sort -t$'\t' -k1,1rn > /tmp/_rc.tsv

# Greedy bin-pack. Also saves file lists to /tmp/_rc_<section>_<N> for diff generation.
_bp() {
  local section=$1
  awk -F'\t' -v sec="$section" '{
    t=$1+0; f=$2; p=0
    for(i=1;i<=n;i++) if(nf[i]<20 && nl[i]+t<=1500){nf[i]++;nl[i]+=t;fl[i]=fl[i]"\n"f" ("t")";fp[i]=fp[i]" "f;p=1;break}
    if(!p){n++;nf[n]=1;nl[n]=t;fl[n]=f" ("t")";fp[n]=f}
  } END {
    if(n>1 && nl[n]<50){nf[n-1]+=nf[n];nl[n-1]+=nl[n];fl[n-1]=fl[n-1]"\n"fl[n];fp[n-1]=fp[n-1]" "fp[n];n--}
    for(i=1;i<=n;i++){
      df="/tmp/review-"sec"-"i".diff"
      printf "CHUNK %d/%d (%d files, %d lines) [%s]\n%s\n\n",i,n,nf[i],nl[i],df,fl[i]
      fn="/tmp/_rc_"sec"_"i
      print fp[i] > fn
      close(fn)
    }
  }'
}

_cat() {
  local label=$1 section; section=$(echo "$label" | tr '[:upper:]' '[:lower:]'); shift
  local data; data=$(awk -F'\t' "$@" /tmp/_rc.tsv)
  echo "=== $label ==="
  if [ -z "$data" ]; then echo "(skip)"; echo; return; fi
  echo "$data" | _bp "$section"
}

_dom() {
  local label=$1 col=$2 section; section=$(echo "$label" | tr '[:upper:]' '[:lower:]')
  local data; data=$(awk -F'\t' -v c="$col" '$2==0 && $c==1{print $1"\t"$8}' /tmp/_rc.tsv)
  echo "=== $label ==="
  if [ -z "$data" ]; then echo "(skip)"; echo; return; fi
  local tl; tl=$(echo "$data" | awk -F'\t' '{s+=$1}END{print s+0}')
  if [ "$tl" -lt 20 ]; then echo "($tl lines, skip)"; echo; return; fi
  echo "$data" | _bp "$section"
}

_cat "CROSS" '$2==0{print $1"\t"$8}'
_cat "TEST" '$2==1{print $1"\t"$8}'
_dom "ARCHITECTURE" 3
_dom "FRONTEND" 4
_dom "SECURITY" 5
_dom "TYPESCRIPT" 6
_dom "PERFORMANCE" 7

# Phase 2: Pre-save per-chunk diffs in parallel
for list_file in /tmp/_rc_*; do
  [ -f "$list_file" ] || continue
  chunk_id=$(basename "$list_file" | sed 's/^_rc_//; s/_/-/')
  files=$(cat "$list_file")
  eval "$DIFF_CMD" -- $files > "/tmp/review-${chunk_id}.diff" &
done
wait

rm -f /tmp/_rc.tsv /tmp/_rc_*
