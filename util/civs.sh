
#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  civ_lora_pull.sh [-h] <civitai_url> <lora_file>

Writes (same basename as lora file):
  <base>.png  (first gallery item -> PNG)
  <base>.txt  (triggers, base model, example prompt/params, author, stats, hashes)

Deps: curl jq ffmpeg
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then usage; exit 0; fi
if [[ $# -ne 2 ]]; then usage; exit 1; fi

url="$1"
lora="$2"
[[ -f "$lora" ]] || { echo "lora file not found: $lora" >&2; exit 1; }

for cmd in curl jq ffmpeg; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "missing: $cmd" >&2; exit 1; }
done

base="${lora%.*}"
png="${base}.png"
meta="${base}.txt"

tmp_mv="$(mktemp)"
tmp_model="$(mktemp)"
tmp_img="$(mktemp)"
tmp_dl="$(mktemp)"
trap 'rm -f "$tmp_mv" "$tmp_model" "$tmp_img" "$tmp_dl"' EXIT

# jq helpers: never explode if field type changes
JQ_DEF='
def S:
  if .==null then ""
  elif type=="string" then .
  elif type=="number" or type=="boolean" then tostring
  elif type=="array" then map(S) | join(", ")
  elif type=="object" then tojson
  else tostring end;

def SARR:
  if .==null then ""
  elif type=="array" then map(tostring) | join(", ")
  elif type=="string" then .
  else tostring end;

def J:
  if .==null then "{}"
  elif type=="object" or type=="array" then tojson
  else tojson end;
'

mv_id=""
model_id=""

# accept either ...?modelVersionId=123 or /models/456
if [[ "$url" =~ modelVersionId=([0-9]+) ]]; then
  mv_id="${BASH_REMATCH[1]}"
elif [[ "$url" =~ /models/([0-9]+) ]]; then
  model_id="${BASH_REMATCH[1]}"
  mv_id="$(curl -fsSL "https://civitai.com/api/v1/models/${model_id}" | jq -r '.modelVersions[0].id // empty')"
else
  echo "could not parse civitai url: $url" >&2
  exit 1
fi

[[ -n "$mv_id" ]] || { echo "could not resolve modelVersionId from: $url" >&2; exit 1; }

curl -fsSL "https://civitai.com/api/v1/model-versions/${mv_id}" -o "$tmp_mv"
model_id="$(jq -r '.modelId // empty' "$tmp_mv")"
[[ -n "$model_id" ]] || { echo "no modelId in model-version payload (mv_id=$mv_id)" >&2; exit 1; }

curl -fsSL "https://civitai.com/api/v1/models/${model_id}" -o "$tmp_model"

# pull 1 example image with meta (often includes prompt + settings)
curl -fsSL "https://civitai.com/api/v1/images?modelVersionId=${mv_id}&limit=1" -o "$tmp_img" || true

# thumbnail (prefer mv images[0], else images endpoint url)
thumb_url="$(jq -r '.images[0].url // empty' "$tmp_mv")"
if [[ -z "$thumb_url" ]]; then
  thumb_url="$(jq -r '.items[0].url // empty' "$tmp_img")"
fi
[[ -n "$thumb_url" ]] || { echo "no thumbnail url found" >&2; exit 1; }

curl -fsSL "$thumb_url" -o "$tmp_dl"
ffmpeg -hide_banner -loglevel error -y -i "$tmp_dl" -frames:v 1 "$png"

# core "use it" fields
trained_words="$(jq -r "$JQ_DEF (.trainedWords|SARR)" "$tmp_mv")"
base_model="$(jq -r "$JQ_DEF (.baseModel|S)" "$tmp_mv")"

# example params
ex_prompt="$(jq -r "$JQ_DEF (.items[0].meta.prompt|S)" "$tmp_img" 2>/dev/null || true)"
ex_neg="$(jq -r "$JQ_DEF (.items[0].meta.negativePrompt|S)" "$tmp_img" 2>/dev/null || true)"
ex_sampler="$(jq -r "$JQ_DEF (.items[0].meta.sampler|S)" "$tmp_img" 2>/dev/null || true)"
ex_steps="$(jq -r "$JQ_DEF (.items[0].meta.steps|S)" "$tmp_img" 2>/dev/null || true)"
ex_cfg="$(jq -r "$JQ_DEF (.items[0].meta.cfgScale|S)" "$tmp_img" 2>/dev/null || true)"
ex_seed="$(jq -r "$JQ_DEF (.items[0].meta.seed|S)" "$tmp_img" 2>/dev/null || true)"
ex_size="$(jq -r "$JQ_DEF (.items[0].meta.Size|S)" "$tmp_img" 2>/dev/null || true)"
ex_meta_json="$(jq -r "$JQ_DEF (.items[0].meta|J)" "$tmp_img" 2>/dev/null || echo "{}")"

# extract <lora:NAME:WEIGHT> tags from example prompt (if present)
example_lora_tags="$(
  printf '%s' "$ex_prompt" |
    grep -Eo '<lora:[^:>]+:[0-9]+(\.[0-9]+)?>' 2>/dev/null |
    paste -sd ' ' - || true
)"
recommended_weight=""
if [[ -n "$example_lora_tags" ]]; then
  # if exactly one tag, grab its weight
  if [[ "$(printf '%s\n' "$example_lora_tags" | wc -w | tr -d ' ')" == "1" ]]; then
    recommended_weight="$(printf '%s' "$example_lora_tags" | sed -E 's/.*:([0-9]+(\.[0-9]+)?)>.*/\1/')"
  fi
fi

# file + hashes (prefer primary file)
file_name="$(jq -r '(.files[]|select(.primary==true)|.name) // (.files[0].name // "")' "$tmp_mv")"
file_size_kb="$(jq -r '(.files[]|select(.primary==true)|.sizeKB) // (.files[0].sizeKB // "")' "$tmp_mv")"
file_download_url="$(jq -r '(.files[]|select(.primary==true)|.downloadUrl) // (.files[0].downloadUrl // .downloadUrl // "")' "$tmp_mv")"
hash_auto_v2="$(jq -r '(.files[]|select(.primary==true)|.hashes.AutoV2) // (.files[0].hashes.AutoV2 // "")' "$tmp_mv")"
hash_sha256="$(jq -r '(.files[]|select(.primary==true)|.hashes.SHA256) // (.files[0].hashes.SHA256 // "")' "$tmp_mv")"
hash_blake3="$(jq -r '(.files[]|select(.primary==true)|.hashes.BLAKE3) // (.files[0].hashes.BLAKE3 // "")' "$tmp_mv")"

# model/version fields
model_name="$(jq -r "$JQ_DEF (.name|S)" "$tmp_model")"
model_type="$(jq -r "$JQ_DEF (.type|S)" "$tmp_model")"
tags="$(jq -r "$JQ_DEF (.tags|S)" "$tmp_model")"

creator_user="$(jq -r "$JQ_DEF (.creator.username|S)" "$tmp_model")"
creator_image="$(jq -r "$JQ_DEF (.creator.image|S)" "$tmp_model")"
creator_models_api="https://civitai.com/api/v1/models?username=${creator_user}"

m_dl="$(jq -r '.stats.downloadCount // ""' "$tmp_model")"
m_fav="$(jq -r '.stats.favoriteCount // ""' "$tmp_model")"
m_up="$(jq -r '.stats.thumbsUpCount // ""' "$tmp_model")"
m_dn="$(jq -r '.stats.thumbsDownCount // ""' "$tmp_model")"
m_rate="$(jq -r '.stats.rating // ""' "$tmp_model")"
m_ratec="$(jq -r '.stats.ratingCount // ""' "$tmp_model")"
m_comm="$(jq -r '.stats.commentCount // ""' "$tmp_model")"

v_dl="$(jq -r '.stats.downloadCount // ""' "$tmp_mv")"
v_up="$(jq -r '.stats.thumbsUpCount // ""' "$tmp_mv")"
v_dn="$(jq -r '.stats.thumbsDownCount // ""' "$tmp_mv")"
v_rate="$(jq -r '.stats.rating // ""' "$tmp_mv")"
v_ratec="$(jq -r '.stats.ratingCount // ""' "$tmp_mv")"

allow_no_credit="$(jq -r '.allowNoCredit // ""' "$tmp_model")"
allow_deriv="$(jq -r '.allowDerivatives // ""' "$tmp_model")"
allow_diff_lic="$(jq -r '.allowDifferentLicense // ""' "$tmp_model")"
allow_comm_use="$(jq -r "$JQ_DEF (.allowCommercialUse|S)" "$tmp_model")"

created_at="$(jq -r "$JQ_DEF (.createdAt|S)" "$tmp_mv")"
published_at="$(jq -r "$JQ_DEF (.publishedAt|S)" "$tmp_mv")"

ver_desc="$(jq -r "$JQ_DEF (.description|S)" "$tmp_mv")"
model_desc="$(jq -r "$JQ_DEF (.description|S)" "$tmp_model")"

model_page="https://civitai.com/models/${model_id}"
ver_page="https://civitai.com/models/${model_id}?modelVersionId=${mv_id}"

cat >"$meta" <<EOF
trigger:""                      # optional: your preferred single trigger
trainedWords:"$trained_words"   # civitai triggers
baseModel:"$base_model"

recommendedWeight:"$recommended_weight"     # best-effort: from example prompt <lora:...:X>
exampleLoraTags:"$example_lora_tags"

examplePrompt:"$ex_prompt"
exampleNegativePrompt:"$ex_neg"
exampleSampler:"$ex_sampler"
exampleSteps:"$ex_steps"
exampleCfgScale:"$ex_cfg"
exampleSeed:"$ex_seed"
exampleSize:"$ex_size"
exampleMetaJson:$ex_meta_json

CivUrl:"$url"
modelPage:"$model_page"
modelVersionPage:"$ver_page"

modelName:"$model_name"
modelType:"$model_type"
tags:"$tags"

creatorUsername:"$creator_user"
creatorImage:"$creator_image"
creatorModelsApi:"$creator_models_api"

modelId:"$model_id"
modelVersionId:"$mv_id"

modelDownloadCount:"$m_dl"
modelFavoriteCount:"$m_fav"
modelThumbsUp:"$m_up"
modelThumbsDown:"$m_dn"
modelRating:"$m_rate"
modelRatingCount:"$m_ratec"
modelCommentCount:"$m_comm"

versionDownloadCount:"$v_dl"
versionThumbsUp:"$v_up"
versionThumbsDown:"$v_dn"
versionRating:"$v_rate"
versionRatingCount:"$v_ratec"

allowNoCredit:"$allow_no_credit"
allowDerivatives:"$allow_deriv"
allowDifferentLicense:"$allow_diff_lic"
allowCommercialUse:"$allow_comm_use"

fileName:"$file_name"
fileSizeKB:"$file_size_kb"
downloadUrl:"$file_download_url"
hashAutoV2:"$hash_auto_v2"
hashSHA256:"$hash_sha256"
hashBLAKE3:"$hash_blake3"

thumbnailUrl:"$thumb_url"
createdAt:"$created_at"
publishedAt:"$published_at"

--- modelDescription ---
$model_desc
--- versionDescription ---
$ver_desc
EOF

echo "wrote: $png"
echo "wrote: $meta"

