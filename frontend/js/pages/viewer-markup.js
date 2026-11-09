/*
 * Rôle : fournit le balisage commun du viewer utilisé par la page Créer.
 * Exécution : create.js l'insère avant que la vue viewer.js ne relie ses commandes.
 */
export const viewerMarkup = `
  <section class="panel viewer-panel" aria-labelledby="viewer-title">
    <div class="viewer-heading">
      <div>
        <p class="eyebrow viewer-eyebrow">Espace de travail</p>
        <h2 id="viewer-title">Aperçu du modèle</h2>
      </div>
      <div class="viewer-actions">
        <span class="origin-badge" id="origin-badge" hidden></span>
        <button class="button button-secondary local-open-button" id="open-local-glb" type="button">Aperçu d’un fichier GLB (sans enregistrer)</button>
        <input class="visually-hidden" id="local-glb-input" type="file" accept=".glb,model/gltf-binary" aria-label="Choisir un modèle sur cet appareil">
        <a class="button button-download" id="download-link" href="#" download hidden>Télécharger le modèle</a>
      </div>
    </div>
    <div class="viewer-comparison">
      <div class="viewer-stage" id="viewer-stage">
        <div class="stage-grid" aria-hidden="true"></div>
        <div class="empty-state" id="empty-state">
          <span class="empty-cube" aria-hidden="true">◇</span>
          <h3>Votre modèle apparaîtra ici</h3>
          <p>Ajoutez une photo pour créer un modèle ou ouvrez un exemple.</p>
        </div>
        <model-viewer id="model-viewer" alt="Modèle 3D du produit affiché dans le viewer" camera-controls touch-action="pan-y" interaction-prompt="none" environment-image="neutral" tone-mapping="neutral" shadow-intensity="0.72" shadow-softness="0.8" exposure="1.08" loading="eager" hidden>
          <button class="ar-button" id="ar-button" slot="ar-button" type="button" hidden>Voir chez moi en AR</button>
        </model-viewer>
        <figure class="source-photo-preview" id="source-photo-preview" hidden>
          <figcaption class="visually-hidden">Photo source</figcaption>
          <button class="source-photo-trigger" id="source-photo-open" type="button" aria-label="Agrandir la photo source" aria-haspopup="dialog" aria-controls="source-photo-dialog">
            <img id="source-photo-image" alt="Photo source du produit">
            <span aria-hidden="true">Agrandir</span>
          </button>
        </figure>
      </div>
    </div>
    <div class="viewer-toolbar-anchor">
      <div class="viewer-toolbar" id="camera-controls" role="group" aria-label="Commandes du viewer" hidden>
        <div class="camera-group" role="group" aria-label="Rotation">
          <button class="icon-button" id="rotate-left" type="button" aria-label="Tourner à gauche de 15 degrés">↶</button>
          <button class="icon-button" id="rotate-right" type="button" aria-label="Tourner à droite de 15 degrés">↷</button>
        </div>
        <span class="toolbar-divider" aria-hidden="true"></span>
        <div class="camera-group" role="group" aria-label="Déplacement">
          <button class="icon-button" id="pan-left" type="button" aria-label="Déplacer la vue à gauche">←</button>
          <button class="icon-button" id="pan-right" type="button" aria-label="Déplacer la vue à droite">→</button>
          <button class="icon-button" id="pan-up" type="button" aria-label="Déplacer la vue vers le haut">↑</button>
          <button class="icon-button" id="pan-down" type="button" aria-label="Déplacer la vue vers le bas">↓</button>
        </div>
        <span class="toolbar-divider" aria-hidden="true"></span>
        <div class="camera-group" role="group" aria-label="Zoom">
          <button class="icon-button" id="zoom-out" type="button" aria-label="Dézoomer">−</button>
          <button class="icon-button" id="zoom-in" type="button" aria-label="Zoomer">+</button>
        </div>
        <span class="toolbar-spacer" aria-hidden="true"></span>
        <button class="toolbar-text-button" id="auto-rotate" type="button" aria-pressed="false">Rotation auto</button>
        <button class="toolbar-text-button" id="fullscreen" type="button">Plein écran</button>
        <button class="toolbar-text-button" id="reset-camera" type="button">Réinitialiser</button>
      </div>
    </div>
    <p class="stage-hint" id="stage-hint" hidden>Glisser pour tourner <span aria-hidden="true">·</span> Maj + glisser pour déplacer <span aria-hidden="true">·</span> Molette pour zoomer</p>
    <p class="viewer-announcement" id="viewer-announcement" role="status" aria-live="polite"></p>
  </section>
  <dialog class="source-photo-dialog" id="source-photo-dialog" aria-labelledby="source-photo-dialog-title">
    <div class="source-photo-dialog-heading">
      <h2 id="source-photo-dialog-title">Photo source</h2>
      <form method="dialog"><button class="icon-button dialog-close" type="submit" aria-label="Fermer la photo agrandie">×</button></form>
    </div>
    <img id="source-photo-large" alt="Photo source agrandie du produit">
  </dialog>
`;
