/*
 * Rôle : définit la balise <forma3d-viewer> qui affiche un modèle activé dans une iframe isolée.
 * Exécution : le site intégrateur charge ce fichier une fois, puis ajoute la balise avec model, height et auto-rotate.
 */
(() => {
  const scriptUrl = document.currentScript?.src;
  const widgetOrigin = scriptUrl ? new URL(scriptUrl, document.baseURI).origin : window.location.origin;
  const publicIdPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

  class Forma3DViewer extends HTMLElement {
    connectedCallback() {
      const root = this.shadowRoot || this.attachShadow({ mode: "open" });
      root.replaceChildren();
      const style = document.createElement("style");
      style.textContent = ":host{display:block;width:100%;min-width:0}iframe{display:block;width:100%;border:0;border-radius:8px;background:#0E1218}p{margin:0;padding:16px;border:1px solid #F87171;border-radius:8px;color:#F1F5F9;background:#161C26;font:16px/1.5 system-ui,sans-serif}";
      root.append(style);

      const publicId = (this.getAttribute("model") || "").trim();
      if (!publicIdPattern.test(publicId)) {
        const message = document.createElement("p");
        message.setAttribute("role", "alert");
        message.textContent = "Le modèle Forma3D demandé n’est pas disponible.";
        root.append(message);
        return;
      }

      const requestedHeight = (this.getAttribute("height") || "480").trim();
      const parsedHeight = /^\d{2,4}(?:px)?$/i.test(requestedHeight) ? Number.parseInt(requestedHeight, 10) : 480;
      const height = Math.min(1200, Math.max(240, parsedHeight));
      const source = new URL(`/embed/${encodeURIComponent(publicId)}`, widgetOrigin);
      if (this.hasAttribute("auto-rotate")) source.searchParams.set("auto-rotate", "1");

      const iframe = document.createElement("iframe");
      iframe.src = source.toString();
      iframe.title = this.getAttribute("title") || "Aperçu 3D du produit";
      iframe.style.height = `${height}px`;
      iframe.loading = "lazy";
      iframe.referrerPolicy = "strict-origin-when-cross-origin";
      iframe.allow = "fullscreen; xr-spatial-tracking";
      root.append(iframe);
    }
  }

  if (!customElements.get("forma3d-viewer")) {
    customElements.define("forma3d-viewer", Forma3DViewer);
  }
})();
