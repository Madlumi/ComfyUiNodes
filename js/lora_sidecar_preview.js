
import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";
import { ComfyWidgets } from "/scripts/widgets.js";

function pickField(meta, key) {
  const re = new RegExp(`${key}\\s*:\\s*"(.*?)"`, "i");
  const m = meta.match(re);
  return m ? m[1] : "";
}

async function initNode(node) {
  if (node.__mn_inited) return;
  node.__mn_inited = true;

  if (node.comfyClass !== "MExtendedLoraLoader") return;

  const loraW = node.widgets?.find(w => w.name === "lora_name");
  if (!loraW) return;

  // multiline textarea widget (ComfyUI widget, not the plain LiteGraph text)
  let metaW = node.widgets?.find(w => w.name === "meta");
  if (!metaW) {
    metaW = ComfyWidgets["STRING"](node, "meta", ["STRING", { multiline: true }], app).widget;
  }
  metaW.options = metaW.options || {};
  metaW.options.multiline = true;

  // IMPORTANT: give it a fixed height so we can draw under it
  metaW.options.height = 220;
  if (metaW.inputEl) metaW.inputEl.style.height = `${metaW.options.height}px`;

  // keep reference for drawing
  node.__mn_metaW = metaW;

  // image state
  node.__mn_thumb_img = new Image();
  node.__mn_thumb_ready = false;
  node.__mn_thumb_img.onload = () => {
    node.__mn_thumb_ready = true;
    node.setDirtyCanvas(true, true);
  };

  node.__mn_margin = 10;
  node.__mn_thumb_min_h = 360; // bigger

  async function refresh(value) {
    try {
      const r = await api.fetchApi(`/mnodes/lora_sidecar?name=${encodeURIComponent(value)}`);
      const j = await r.json();

      const raw = j.meta || "";
      const trigger = pickField(raw, "trigger");
      const trained = pickField(raw, "trainedWords");
      const baseModel = pickField(raw, "baseModel");
      const weight = pickField(raw, "recommendedWeight");

      const header =
        `trigger:"${trigger}"\n` +
        `trainedWords:"${trained}"\n` +
        `baseModel:"${baseModel}"\n` +
        `recommendedWeight:"${weight}"\n\n`;

      metaW.value = header + raw;

      node.__mn_thumb_ready = false;
      node.__mn_thumb_img.src = j.thumb_b64 ? `data:image/png;base64,${j.thumb_b64}` : "";

    } catch (e) {
      metaW.value = "(sidecar fetch failed)";
      node.__mn_thumb_ready = false;
      node.__mn_thumb_img.src = "";
    }

    // ensure node is tall enough for textarea + thumb
    const m = node.__mn_margin;
    const metaBottom = (metaW.y || 0) + (metaW.options.height || 0) + 14;
    node.size[1] = Math.max(node.size[1], metaBottom + node.__mn_thumb_min_h + m);

    node.setDirtyCanvas(true, true);
  }

  // hook dropdown change
  const origCb = loraW.callback;
  loraW.callback = async (value) => {
    if (origCb) origCb.call(loraW, value);
    await refresh(value);
  };

  // draw thumb BELOW the meta textarea, aspect-fit
  const origDraw = node.onDrawForeground;
  node.onDrawForeground = function (ctx) {
    if (origDraw) origDraw.call(this, ctx);

    const img = this.__mn_thumb_img;
    if (!this.__mn_thumb_ready || !img?.naturalWidth || !img?.naturalHeight) return;

    const metaW2 = this.__mn_metaW;
    const m = this.__mn_margin;

    const topY = (metaW2?.y || 0) + (metaW2?.options?.height || 0) + 14;
    const boxX = m;
    const boxY = topY;
    const boxW = Math.max(64, this.size[0] - m * 2);
    const boxH = Math.max(this.__mn_thumb_min_h, this.size[1] - boxY - m);

    const iw = img.naturalWidth, ih = img.naturalHeight;
    const scale = Math.min(boxW / iw, boxH / ih);
    const dw = Math.floor(iw * scale);
    const dh = Math.floor(ih * scale);
    const dx = boxX + Math.floor((boxW - dw) / 2);
    const dy = boxY + Math.floor((boxH - dh) / 2);

    ctx.drawImage(img, dx, dy, dw, dh);
  };

  await refresh(loraW.value);
}

app.registerExtension({
  name: "mnodes.lora_sidecar_preview",
  async nodeCreated(node) { await initNode(node); },
  async loadedGraphNode(node) { await initNode(node); },
});

