(() => {
  class GoGuideBookingWidget extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: "open" });
      this.apiBase = this.getAttribute("data-api-base") || `${window.location.origin}/api`;
      this.businessUnit = this.getAttribute("data-bu-id") || "";
      this.lang = this.getAttribute("data-lang") || "ru";
      this._services = [];
    }

    connectedCallback() {
      this.renderSkeleton();
      this.fetchServices();
    }

    renderSkeleton() {
      const style = `
        :host { all: initial; font-family: 'Inter', system-ui, -apple-system, sans-serif; display:block; }
        .card { background:#0f172a; color:#e2e8f0; border:1px solid #1e293b; border-radius:12px; padding:16px; box-shadow:0 10px 40px rgba(0,0,0,0.25); max-width:640px; }
        h3 { margin:0 0 12px; font-size:18px; }
        label { display:block; font-size:13px; color:#94a3b8; margin-bottom:4px; }
        input, select, textarea { width:100%; padding:10px; border-radius:10px; border:1px solid #1e293b; background:#0b1324; color:#e2e8f0; font-size:14px; box-sizing:border-box; }
        input:focus, select:focus, textarea:focus { outline:2px solid #64ffda44; border-color:#64ffda; }
        .row { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
        .btn { display:inline-flex; align-items:center; justify-content:center; gap:6px; padding:10px 14px; border-radius:10px; background:#64ffda; color:#0b1324; font-weight:700; cursor:pointer; border:none; transition:transform .1s ease, box-shadow .1s ease; }
        .btn:hover { transform:translateY(-1px); box-shadow:0 8px 24px rgba(100,255,218,0.35); }
        .btn:disabled { opacity:0.6; cursor:not-allowed; }
        .muted { color:#94a3b8; font-size:13px; }
        .error { margin-top:8px; color:#fecdd3; background:#7f1d1d55; border:1px solid #ef444433; padding:8px 10px; border-radius:10px; font-size:13px; }
        .success { margin-top:8px; color:#bbf7d0; background:#064e3b55; border:1px solid #22c55e33; padding:8px 10px; border-radius:10px; font-size:13px; }
        .preview-link { color:#64ffda; cursor:pointer; font-size:13px; }
        dialog { border:none; border-radius:12px; padding:0; background:transparent; }
        .overlay { width:80vw; max-width:900px; min-height:300px; border-radius:12px; overflow:hidden; border:1px solid #1e293b; background:#0b1324; box-shadow:0 20px 60px rgba(0,0,0,0.45); }
        .overlay-header { display:flex; justify-content:space-between; align-items:center; padding:12px 16px; border-bottom:1px solid #1e293b; }
        .overlay-body { padding:16px; background:#0f172a; color:#e2e8f0; min-height:240px; }
        .close { background:none; border:none; color:#e2e8f0; cursor:pointer; font-size:18px; }
      `;
      this.shadowRoot.innerHTML = `
        <style>${style}</style>
        <div class="card">
          <h3>Онлайн-бронирование</h3>
          <form id="form">
            <div>
              <label>Услуга / номер</label>
              <select name="service" required id="service"></select>
              <div class="muted" id="serviceHint"></div>
            </div>
            <div class="row" style="margin-top:12px;">
              <div>
                <label>Дата и время начала</label>
                <input type="datetime-local" name="start_at" required />
              </div>
              <div>
                <label>Дата и время окончания</label>
                <input type="datetime-local" name="end_at" required />
              </div>
            </div>
            <div class="row" style="margin-top:12px;">
              <div>
                <label>Имя</label>
                <input type="text" name="client_name" required placeholder="Иван" />
              </div>
              <div>
                <label>Телефон</label>
                <input type="tel" name="client_phone" required placeholder="+7..." />
              </div>
            </div>
            <div style="margin-top:12px;">
              <label>Email</label>
              <input type="email" name="client_email" placeholder="you@example.com" />
            </div>
            <div id="widgetLink" style="margin-top:10px; display:none;">
              <span class="preview-link" id="openPreview">Смотреть 360°</span>
            </div>
            <div style="margin-top:16px; display:flex; gap:10px; align-items:center;">
              <button type="submit" class="btn" id="submitBtn">Забронировать</button>
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
        this.previewContent.innerHTML = "";
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
      this.previewContent.innerHTML = widget;
      this._executeScripts(this.previewContent);
      this.previewModal.classList.add("show");
    }

    closePreview() {
      if (!this.previewModal) return;
      this.previewModal.classList.remove("show");
    }

    _executeScripts(container) {
      const scripts = container.querySelectorAll("script");
      scripts.forEach((old) => {
        const s = document.createElement("script");
        if (old.src) {
          s.src = old.src;
        } else {
          s.textContent = old.textContent || "";
        }
        // копируем атрибуты
        [...old.attributes].forEach((attr) => s.setAttribute(attr.name, attr.value));
        old.replaceWith(s);
      });
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
        end_at: formData.get("end_at"),
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
        this.showSuccess("Бронирование создано. Мы свяжемся для подтверждения.");
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

