(() => {
  const cfg = document.getElementById("widget-configurator");
  if (!cfg) return;

  // сохраняем флаг из исходного embed (например, data-hide-end), чтобы не потерять при пересборке
  const staticFlags = {
    hideEnd: (() => {
      const embedVal = (document.getElementById("embedCode") || {}).value || "";
      if (/\bdata-hide-end="true"/.test(embedVal)) return true;
      const def = cfg.dataset.defaultHideEnd === "true";
      return def;
    })(),
  };
  const defaultSubmit = cfg.dataset.defaultSubmit || "Забронировать";
  const embedTextarea = document.getElementById("embedCode");
  const hiddenField = document.querySelector('input[name="widget_config"]');
  const presetTheme = cfg.querySelector("#presetTheme");

  const fields = {
    width: cfg.querySelector("#cfgWidth"),
    primary: cfg.querySelector("#cfgPrimary"),
    panel: cfg.querySelector("#cfgPanel"),
    accent: cfg.querySelector("#cfgAccent"),
    text: cfg.querySelector("#cfgText"),
    muted: cfg.querySelector("#cfgMuted"),
    border: cfg.querySelector("#cfgBorder"),
    radius: cfg.querySelector("#cfgRadius"),
    font: cfg.querySelector("#cfgFont"),
    previewHeight: cfg.querySelector("#cfgPreviewHeight"),
    submit: cfg.querySelector("#cfgSubmit"),
    hideEmail: cfg.querySelector("#cfgHideEmail"),
    autoOpen: cfg.querySelector("#cfgAutoOpen"),
  };

  // отображаем дефолт по бизнес-типу в placeholder
  fields.submit.placeholder = defaultSubmit;

  function getConfig() {
    try {
      return JSON.parse(hiddenField.value || "{}");
    } catch (e) {
      return {};
    }
  }

  function setConfig(obj) {
    hiddenField.value = JSON.stringify(obj || {});
  }

  function loadPreset(name) {
    if (!window.widgetPresets || !window.widgetPresets[name]) return;
    const p = window.widgetPresets[name];
    fields.primary.value = p.primary || "#0f172a";
    fields.panel.value = p.panel || "#0b1324";
    fields.accent.value = p.accent || "#64ffda";
    fields.text.value = p.text || "#e2e8f0";
    fields.muted.value = p.muted || "#94a3b8";
    fields.border.value = p.border || "#1e293b";
    fields.radius.value = p.radius || "12px";
    fields.font.value = p.fontFamily || "'Inter', system-ui, sans-serif";
    updateConfig();
  }

  function fillFormFromConfig() {
    const data = getConfig();
    if (data.width) fields.width.value = data.width;
    if (data.primary) fields.primary.value = data.primary;
    if (data.panel) fields.panel.value = data.panel;
    if (data.accent) fields.accent.value = data.accent;
    if (data.text) fields.text.value = data.text;
    if (data.muted) fields.muted.value = data.muted;
    if (data.border) fields.border.value = data.border;
    if (data.radius) fields.radius.value = data.radius;
    if (data.fontFamily) fields.font.value = data.fontFamily;
    if (data.previewHeight) fields.previewHeight.value = data.previewHeight;
    if (data.submit) fields.submit.value = data.submit;
    fields.hideEmail.checked = data.hideEmail === true;
    fields.autoOpen.checked = data.autoOpenPreview === true;
  }

  function updateConfig() {
    const data = getConfig();
    data.width = fields.width.value || data.width || "100%";
    data.primary = fields.primary.value || data.primary || "#0f172a";
    data.panel = fields.panel.value || data.panel || "#0b1324";
    data.accent = fields.accent.value || data.accent || "#64ffda";
    data.text = fields.text.value || data.text || "#e2e8f0";
    data.muted = fields.muted.value || data.muted || "#94a3b8";
    data.border = fields.border.value || data.border || "#1e293b";
    data.radius = fields.radius.value || data.radius || "12px";
    data.fontFamily = fields.font.value || data.fontFamily || "'Inter', system-ui, sans-serif";
    data.previewHeight = fields.previewHeight.value || data.previewHeight || "70vh";
    data.submit = fields.submit.value || data.submit || defaultSubmit;
    data.hideEmail = fields.hideEmail.checked;
    data.autoOpenPreview = fields.autoOpen.checked;
    setConfig(data);
    rebuildEmbed(data);
  }

  function rebuildEmbed(data) {
    if (!embedTextarea) return;
    const base = embedTextarea.value.split("\n")[0].includes("<script") ? embedTextarea.value : "";
    // используем текущий embed как основу, а затем заменяем/добавляем data-атрибуты
    const buMatch = embedTextarea.value.match(/data-bu-id="([^"]+)"/);
    const apiMatch = embedTextarea.value.match(/data-api-base="([^"]+)"/);
    const buId = buMatch ? buMatch[1] : "";
    const apiBase = apiMatch ? apiMatch[1] : "";
    const attrs = Object.entries({
      "data-bu-id": buId,
      "data-api-base": apiBase,
      "data-primary": data.primary,
      "data-panel": data.panel,
      "data-accent": data.accent,
      "data-text": data.text,
      "data-muted": data.muted,
      "data-border": data.border,
      "data-radius": data.radius,
      "data-font-family": data.fontFamily,
      "data-preview-height": data.previewHeight,
      "data-label-submit": data.submit,
      "data-hide-email": data.hideEmail ? "true" : "false",
      "data-auto-open-preview": data.autoOpenPreview ? "true" : "false",
      "data-width": data.width,
      "data-hide-end": staticFlags.hideEnd ? "true" : undefined,
    })
      .filter(([, v]) => v !== undefined && v !== null && v !== "")
      .map(([k, v]) => `${k}="${v}"`)
      .join(" ");
    const scriptLine = `<script src="${apiBase.replace(/\/api$/, "")}/static/widget/booking-widget.js" defer></script>`;
    const widgetLine = `<booking-widget ${attrs}></booking-widget>`;
    embedTextarea.value = `${scriptLine}\n${widgetLine}`;
  }

  cfg.querySelector("#cfgApply").addEventListener("click", updateConfig);
  presetTheme.addEventListener("change", (e) => {
    if (e.target.value) loadPreset(e.target.value);
  });

  // init
  fillFormFromConfig();
})();


