/*
 * Rôle : fournit le balisage commun du viewer utilisé par la page Créer.
 * Exécution : create.js l'insère avant que la vue viewer.js ne relie ses commandes.
 * Refonte : scène soignée (dégradé, grille en perspective, halo), squelette de chargement,
 * bascule Vue 3D / Photo source / Comparer, éclairage plus flatteur et note discrète.
 */
import { emptyCubeIllustration } from "../views/illustrations.js?v=20261117-r2";

export const viewerMarkup = `
  <section class="panel viewer-panel" aria-labelledby="viewer-title">
    <div class="viewer-heading">
      <div>
        <p class="eyebrow viewer-eyebrow">Espace de travail</p>
        <h2 id="viewer-title">Aperçu du modèle</h2>
      </div>
      <div class="viewer-actions">
        <span class="origin-badge" id="origin-badge" hidden></span>
        <div class="view-toggle" id="viewer-view-toggle" role="group" aria-label="Mode d’affichage" hidden>
          <button type="button" data-view="model" aria-pressed="true">Vue 3D</button>
          <button type="button" data-view="photo" aria-pressed="false">Photo source</button>
          <button type="button" data-view="compare" aria-pressed="false">Comparer</button>
        </div>
        <button class="button button-ghost local-open-button" id="open-local-glb" type="button">Aperçu d’un fichier GLB (sans enregistrer)</button>
        <input class="visually-hidden" id="local-glb-input" type="file" accept=".glb,model/gltf-binary" aria-label="Choisir un modèle sur cet appareil">
        <a class="button button-primary" id="download-link" href="#" download hidden>Télécharger</a>
      </div>
    </div>
    <div class="viewer-comparison">
      <div class="viewer-stage" id="viewer-stage" data-view="model">
        <div class="stage-grid" aria-hidden="true"></div>
        <div class="empty-state" id="empty-state">
          ${emptyCubeIllustration()}
          <h3>Votre modèle apparaîtra ici</h3>
          <p>Déposez une photo à gauche, ou ouvrez un exemple pour découvrir le viewer.</p>
        </div>
        <div class="viewer-skeleton" id="viewer-skeleton" role="status" hidden>Chargement du modèle 3D…</div>
        <model-viewer id="model-viewer" alt="Modèle 3D du produit affiché dans le viewer" camera-controls touch-action="pan-y" interaction-prompt="none" environment-image="neutral" tone-mapping="neutral" shadow-intensity="1" shadow-softness="1" exposure="1.1" rotation-per-second="20deg" auto-rotate-delay="2500" loading="eager" hidden>
          <button class="ar-button" id="ar-button" slot="ar-button" type="button" hidden>Voir chez moi en AR</button>
        </model-viewer>
        <div class="stage-photo" id="stage-photo" hidden><img id="stage-photo-image" alt="Photo source du produit"></div>
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
    <p class="stage-footnote"><span class="note-mark" aria-hidden="true">i</span>Aperçu 3D généré automatiquement — idéal pour la visualisation produit. La géométrie est une estimation.</p>
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
