/*
 * Rôle : définit la balise <forma3d-viewer> qui affiche un modèle activé dans une iframe isolée.
 * Exécution : le site intégrateur charge ce fichier une fois, puis ajoute la balise avec model, height et auto-rotate.
 */
// Fonction exécutée immédiatement : ses variables ne polluent pas la page du site client.
(() => {
  // Adresse de ce script (fournie par le navigateur pendant son exécution).
  const scriptUrl = document.currentScript?.src;
  // Origine du serveur Forma3D (celle du script), sinon celle de la page.
  const widgetOrigin = scriptUrl ? new URL(scriptUrl, document.baseURI).origin : window.location.origin;
  // Expression régulière d'un UUID public.
  const publicIdPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

  // Web Component : une classe qui hérite de HTMLElement devient une vraie balise HTML (<forma3d-viewer>).
  // Équivalent d'un composant Angular exporté avec Angular Elements, utilisable sur n'importe quel site.
  class Forma3DViewer extends HTMLElement {
    // Appelée par le navigateur quand la balise est ajoutée à la page : construit l'iframe.
    connectedCallback() {
      // Shadow DOM : zone isolée ; les styles du site client ne déforment pas le widget, et inversement.
      // Crée la zone isolée (ou réutilise celle qui existe).
      const root = this.shadowRoot || this.attachShadow({ mode: "open" });
      // Vide la zone (si la balise est ajoutée deux fois).
      root.replaceChildren();
      // Crée une balise <style>.
      const style = document.createElement("style");
      // Styles internes du widget : iframe pleine largeur, message d'erreur lisible.
      style.textContent = ":host{display:block;width:100%;min-width:0}iframe{display:block;width:100%;border:0;border-radius:8px;background:#0E1218}p{margin:0;padding:16px;border:1px solid #F87171;border-radius:8px;color:#F1F5F9;background:#161C26;font:16px/1.5 system-ui,sans-serif}";
      // Ajoute les styles à la zone isolée.
      root.append(style);

      // Lit l'attribut model (UUID public).
      const publicId = (this.getAttribute("model") || "").trim();
      // UUID absent ou mal formé...
      if (!publicIdPattern.test(publicId)) {
        // ...crée un paragraphe...
        const message = document.createElement("p");
        // ...annoncé comme alerte aux lecteurs d'écran...
        message.setAttribute("role", "alert");
        // ...avec un message clair...
        message.textContent = "Le modèle Forma3D demandé n’est pas disponible.";
        // ...l'ajoute...
        root.append(message);
        // ...et s'arrête.
        return;
      }

      // Lit la hauteur demandée (480 par défaut).
      const requestedHeight = (this.getAttribute("height") || "480").trim();
      // Accepte seulement un nombre de 2 à 4 chiffres (avec « px » facultatif), sinon 480.
      const parsedHeight = /^\d{2,4}(?:px)?$/i.test(requestedHeight) ? Number.parseInt(requestedHeight, 10) : 480;
      // Limite la hauteur entre 240 et 1200 pixels.
      const height = Math.min(1200, Math.max(240, parsedHeight));
      // Adresse de la page /embed sur le serveur Forma3D.
      const source = new URL(`/embed/${encodeURIComponent(publicId)}`, widgetOrigin);
      // Ajoute ?auto-rotate=1 si l'attribut auto-rotate est présent.
      if (this.hasAttribute("auto-rotate")) source.searchParams.set("auto-rotate", "1");

      // L'iframe affiche /embed/{public_id} servi par Forma3D ; aucune clé API n'est utilisée.
      // Crée l'iframe.
      const iframe = document.createElement("iframe");
      // Adresse affichée.
      iframe.src = source.toString();
      // Titre lu par les lecteurs d'écran.
      iframe.title = this.getAttribute("title") || "Aperçu 3D du produit";
      // Hauteur choisie.
      iframe.style.height = `${height}px`;
      // Chargement différé (seulement quand l'iframe approche de l'écran).
      iframe.loading = "lazy";
      // Adresse d'origine transmise de façon limitée.
      iframe.referrerPolicy = "strict-origin-when-cross-origin";
      // Autorise le plein écran et la réalité augmentée.
      iframe.allow = "fullscreen; xr-spatial-tracking";
      // Ajoute l'iframe à la zone isolée.
      root.append(iframe);
    }
  }

  // customElements.define enregistre la nouvelle balise, une seule fois même si le script est chargé deux fois.
  // Si la balise n'est pas encore enregistrée...
  if (!customElements.get("forma3d-viewer")) {
    // ...on l'enregistre avec sa classe.
    customElements.define("forma3d-viewer", Forma3DViewer);
  }
})();
