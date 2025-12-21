(() => {
  class GoGuideBookingWidget extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: "open" });
      this.apiBase = this.getAttribute("data-api-base") || `${window.location.origin}/api`;
      this.businessUnit = this.getAttribute("data-bu-id") || "";
      this.lang = this.getAttribute("data-lang") || "ru";
      this.theme = {
        primary: this.getAttribute("data-primary") || "#0f172a",
        panel: this.getAttribute("data-panel") || "#0b1324",
        accent: this.getAttribute("data-accent") || "#64ffda",
        text: this.getAttribute("data-text") || "#e2e8f0",
        muted: this.getAttribute("data-muted") || "#94a3b8",
        border: this.getAttribute("data-border") || "#1e293b",
        errorBg: this.getAttribute("data-error") || "#7f1d1d55",
        errorText: this.getAttribute("data-error-text") || "#fecdd3",
        successBg: this.getAttribute("data-success") || "#064e3b55",
        successText: this.getAttribute("data-success-text") || "#bbf7d0",
        shadow: this.getAttribute("data-shadow") || "0 10px 40px rgba(0,0,0,0.25)",
        radius: this.getAttribute("data-radius") || "12px",
        fontFamily: this.getAttribute("data-font-family") || "'Inter', system-ui, -apple-system, sans-serif",
        previewHeight: this.getAttribute("data-preview-height") || "70vh",
      };
      this.labels = {
        title: this.getAttribute("data-label-title") || "Онлайн-бронирование",
        service: this.getAttribute("data-label-service") || "Выберите услугу",
        start: this.getAttribute("data-label-start") || "Желаемая дата и время начала",
        end: this.getAttribute("data-label-end") || "Окончание (если нужно)",
        name: this.getAttribute("data-label-name") || "Имя",
        phone: this.getAttribute("data-label-phone") || "Телефон",
        email: this.getAttribute("data-label-email") || "Email",
        submit: this.getAttribute("data-label-submit") || "Забронировать",
        preview: this.getAttribute("data-label-preview") || "Смотреть 360°",
        success: this.getAttribute("data-success-text") || "Бронирование создано. Мы свяжемся для подтверждения.",
      };
      this.options = {
        hideEmail: this.getAttribute("data-hide-email") === "true",
        emailOptional: this.getAttribute("data-email-optional") === "true",
        phonePlaceholder: this.getAttribute("data-phone-placeholder") || "+7...",
        autoOpenPreview: this.getAttribute("data-auto-open-preview") === "true",
        previewAutoClose: parseInt(this.getAttribute("data-preview-autoclose") || "0", 10),
        previewHeight: this.theme.previewHeight,
        scrollIntoView: this.getAttribute("data-scroll-into-view") === "true",
        cardWidth: this.getAttribute("data-width") || "100%",
        hideEnd: this.getAttribute("data-hide-end") === "true",
      };
      this._services = [];
    }

    connectedCallback() {
      this.renderSkeleton();
      this.fetchServices();
    }

    renderSkeleton() {
      const t = this.theme;
      const style = `
        :host { all: initial; font-family: ${t.fontFamily}; display:block; }
        .card { background:${t.primary}; color:${t.text}; border:1px solid ${t.border}; border-radius:${t.radius}; padding:16px; box-shadow:${t.shadow}; max-width:640px; width:${this.options.cardWidth}; }
        h3 { margin:0 0 12px; font-size:18px; }
        label { display:block; font-size:13px; color:${t.muted}; margin-bottom:4px; }
        input, select, textarea { width:100%; padding:10px; border-radius:${t.radius}; border:1px solid ${t.border}; background:${t.panel}; color:${t.text}; font-size:14px; box-sizing:border-box; }
        input:focus, select:focus, textarea:focus { outline:2px solid ${t.accent}44; border-color:${t.accent}; }
        .row { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
        .row.single { grid-template-columns:1fr; }
        .btn { display:inline-flex; align-items:center; justify-content:center; gap:6px; padding:10px 14px; border-radius:${t.radius}; background:${t.accent}; color:${t.panel}; font-weight:700; cursor:pointer; border:none; transition:transform .1s ease, box-shadow .1s ease; }
        .btn:hover { transform:translateY(-1px); box-shadow:0 8px 24px ${t.accent}55; }
        .btn:disabled { opacity:0.6; cursor:not-allowed; }
        .muted { color:${t.muted}; font-size:13px; }
        .error { margin-top:8px; color:${t.errorText}; background:${t.errorBg}; border:1px solid #ef444433; padding:8px 10px; border-radius:${t.radius}; font-size:13px; }
        .success { margin-top:8px; color:${t.successText}; background:${t.successBg}; border:1px solid #22c55e33; padding:8px 10px; border-radius:${t.radius}; font-size:13px; }
        .preview-link { color:${t.accent}; cursor:pointer; font-size:13px; }
        dialog { border:none; border-radius:${t.radius}; padding:0; background:transparent; }
        .overlay { width:80vw; max-width:900px; min-height:300px; border-radius:${t.radius}; overflow:hidden; border:1px solid ${t.border}; background:${t.panel}; box-shadow:0 20px 60px rgba(0,0,0,0.45); }
        .overlay-header { display:flex; justify-content:space-between; align-items:center; padding:12px 16px; border-bottom:1px solid ${t.border}; }
        .overlay-body { padding:16px; background:${t.primary}; color:${t.text}; min-height:240px; }
        .close { background:none; border:none; color:${t.text}; cursor:pointer; font-size:18px; }
      `;
      this.shadowRoot.innerHTML = `
        <style>${style}</style>
        <div class="card">
          <h3>${this.labels.title}</h3>
          <form id="form">
            <div>
              <label>${this.labels.service}</label>
              <select name="service" required id="service"></select>
              <div class="muted" id="serviceHint"></div>
            </div>
            <div class="row ${this.options.hideEnd ? "single" : ""}" style="margin-top:12px;">
              <div>
                <label>${this.labels.start}</label>
                <input type="datetime-local" name="start_at" required />
              </div>
              ${
                this.options.hideEnd
                  ? ""
                  : `<div>
                <label>${this.labels.end}</label>
                <input type="datetime-local" name="end_at" required />
              </div>`
              }
            </div>
            <div class="row" style="margin-top:12px;">
              <div>
                <label>${this.labels.name}</label>
                <input type="text" name="client_name" required placeholder="${this.getAttribute("data-name-placeholder") || "Иван"}" />
              </div>
              <div>
                <label>${this.labels.phone}</label>
                <input type="tel" name="client_phone" required placeholder="${this.options.phonePlaceholder}" />
              </div>
            </div>
            <div style="margin-top:12px; ${this.options.hideEmail ? "display:none;" : ""}">
              <label>${this.labels.email}</label>
              <input type="email" name="client_email" ${this.options.emailOptional ? "" : "required"} placeholder="${this.getAttribute("data-email-placeholder") || "you@example.com"}" />
            </div>
            <div id="widgetLink" style="margin-top:10px; display:none;">
              <span class="preview-link" id="openPreview">${this.labels.preview}</span>
            </div>
            <div style="margin-top:16px; display:flex; gap:10px; align-items:center;">
              <button type="submit" class="btn" id="submitBtn">${this.labels.submit}</button>
              <span class="muted" id="statusText"></span>
            </div>
            <div id="message"></div>
          </form>
        </div>
        <dialog id="previewModal">
          <div class="overlay">
            <div class="overlay-header">
              <span>360°</span>
              <button class="close" id="closePreview">×</button>
            </div>
            <div class="overlay-body">
              <div id="previewContent"></div>
            </div>
          </div>
        </dialog>
      `;
      this.form = this.shadowRoot.querySelector("#form");
      this.serviceSelect = this.shadowRoot.querySelector("#service");
      this.statusText = this.shadowRoot.querySelector("#statusText");
      this.messageBox = this.shadowRoot.querySelector("#message");
      this.widgetLink = this.shadowRoot.querySelector("#widgetLink");
      this.previewModal = null;
      this.previewContent = null;
      this.shadowRoot.querySelector("#openPreview").addEventListener("click", () => this.openPreview());
      this.form.addEventListener("submit", (e) => this.handleSubmit(e));
    }

    async fetchServices() {
      try {
        const url = new URL(`${this.apiBase}/services/`);
        if (this.businessUnit) url.searchParams.set("business_unit", this.businessUnit);
        const res = await fetch(url.toString());
        if (!res.ok) throw new Error("Не удалось загрузить услуги");
        this._services = await res.json();
        this.populateServices();
      } catch (e) {
        this.showError(e.message || "Ошибка загрузки услуг");
      }
    }

    populateServices() {
      this.serviceSelect.innerHTML = "";
      this._services.forEach((s) => {
        const opt = document.createElement("option");
        opt.value = s.id;
        opt.textContent = `${s.title} — ${s.price || 0} ₽`;
        opt.dataset.widget = s.tour_widget || "";
        this.serviceSelect.appendChild(opt);
      });
      this.serviceSelect.addEventListener("change", () => this.handleServiceChange());
      this.handleServiceChange();
    }

    handleServiceChange() {
      const sel = this.serviceSelect.selectedOptions[0];
      const widget = sel ? sel.dataset.widget : "";
      if (widget && widget.trim()) {
        this.widgetLink.style.display = "block";
        if (this.previewContent) this.previewContent.innerHTML = "";
        if (this.options.autoOpenPreview) this.openPreview();
      } else {
        this.widgetLink.style.display = "none";
      }
    }

    openPreview() {
      const sel = this.serviceSelect.selectedOptions[0];
      if (!sel) return;
      const widget = sel.dataset.widget || "";
      if (!widget.trim()) return;
      this._ensurePreviewHost();
      if (!this.previewModal || !this.previewContent) {
        this.showError("Не удалось открыть 360-превью");
        return;
      }
      this.clearMessage();
      this._renderIframe(widget);
      this.previewModal.classList.add("show");
    }

    closePreview() {
      if (!this.previewModal) return;
      this.previewModal.classList.remove("show");
      this.clearMessage();
    }

    _ensurePreviewHost() {
      if (this.previewModal && this.previewContent) return;
      let host = document.getElementById("booking-widget-preview-host");
      if (!host) {
        host = document.createElement("div");
        host.id = "booking-widget-preview-host";
        host.innerHTML = `
          <style>
            #booking-widget-preview-host { position: fixed; inset: 0; display: none; align-items: center; justify-content: center; z-index: 99999; }
            #booking-widget-preview-host.show { display: flex; background: rgba(0,0,0,0.65); backdrop-filter: blur(2px); }
            #booking-widget-preview-modal { width: 80vw; max-width: 900px; min-height: 300px; background:#0b1324; color:#e2e8f0; border:1px solid #1e293b; border-radius:12px; box-shadow:0 20px 60px rgba(0,0,0,0.45); display:flex; flex-direction:column; overflow:hidden; }
            #booking-widget-preview-modal header { display:flex; align-items:center; justify-content:space-between; padding:12px 16px; border-bottom:1px solid #1e293b; font-weight:600; }
            #booking-widget-preview-modal .body { padding:16px; min-height:240px; }
            #booking-widget-preview-close { background:none; border:none; color:#e2e8f0; font-size:18px; cursor:pointer; }
          </style>
          <div id="booking-widget-preview-modal">
            <header>
              <span>360°</span>
              <button id="booking-widget-preview-close" aria-label="Закрыть">×</button>
            </header>
            <div class="body"><div id="booking-widget-preview-content"></div></div>
          </div>
        `;
        document.body.appendChild(host);
        host.querySelector("#booking-widget-preview-close").addEventListener("click", () => this.closePreview());
      }
      this.previewModal = host;
      this.previewContent = host.querySelector("#booking-widget-preview-content");
      if (!this.previewContent) {
        const body = host.querySelector(".body") || host;
        const fallback = document.createElement("div");
        fallback.id = "booking-widget-preview-content";
        body.appendChild(fallback);
        this.previewContent = fallback;
      }
    }

    _renderIframe(html) {
      if (!this.previewContent) return;
      this.previewContent.innerHTML = "";
      const iframe = document.createElement("iframe");
      iframe.setAttribute("sandbox", "allow-same-origin allow-scripts allow-popups allow-forms");
      iframe.setAttribute("referrerpolicy", "no-referrer");
      iframe.style.width = "100%";
      iframe.style.height = this.options.previewHeight || "70vh";
      iframe.style.border = "0";
      iframe.style.background = this.theme.panel;
      iframe.srcdoc = `
        <!doctype html>
        <html>
          <head>
            <meta charset="utf-8" />
            <style>
              html, body { margin:0; padding:0; background:${this.theme.panel}; color:${this.theme.text}; }
            </style>
          </head>
          <body>
            ${html}
          </body>
        </html>`;
      this.previewContent.appendChild(iframe);
    }

    async handleSubmit(e) {
      e.preventDefault();
      this.clearMessage();
      const formData = new FormData(this.form);
      const payload = {
        business_unit: this.businessUnit || undefined,
        service: formData.get("service"),
        client_name: formData.get("client_name"),
        client_phone: formData.get("client_phone"),
        client_email: formData.get("client_email") || "",
        start_at: formData.get("start_at"),
        end_at: formData.get("end_at") || (this.options.hideEnd ? formData.get("start_at") : null),
      };
      this.setLoading(true);
      try {
        const res = await fetch(`${this.apiBase}/appointments/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!res.ok) {
          const msg = typeof data === "object" ? Object.values(data).flat().join("; ") : "Ошибка бронирования";
          throw new Error(msg);
        }
        const payStatus = (data && data.payment_status) || "pending";
        const successText =
          payStatus === "paid"
            ? "Бронирование и оплата приняты."
            : `Бронирование создано. Статус оплаты: ${payStatus === "pending" ? "ожидает" : payStatus}.`;
        this.showSuccess(successText);
        this.form.reset();
        this.handleServiceChange();
      } catch (err) {
        this.showError(err.message || "Не удалось создать бронь");
      } finally {
        this.setLoading(false);
      }
    }

    setLoading(state) {
      const btn = this.shadowRoot.querySelector("#submitBtn");
      btn.disabled = state;
      this.statusText.textContent = state ? "Отправляем..." : "";
    }

    clearMessage() {
      this.messageBox.innerHTML = "";
    }

    showError(text) {
      if (!text) return;
      if (typeof text === "string" && (text.includes("innerHTML") || text.toLowerCase().includes("превью"))) {
        // не показываем сервисные предупреждения для превью 360, тихо логируем
        console.warn("[booking-widget] preview notice:", text);
        return;
      }
      this.messageBox.innerHTML = `<div class="error">${text}</div>`;
    }

    showSuccess(text) {
      this.messageBox.innerHTML = `<div class="success">${text}</div>`;
    }
  }

  if (!customElements.get("booking-widget")) {
    customElements.define("booking-widget", GoGuideBookingWidget);
  }
})();

