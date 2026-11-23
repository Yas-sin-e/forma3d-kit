/*
 * Rôle : affiche un GLB dans model-viewer et gère ses commandes et son origine.
 * Exécution : create.js lui transmet un modèle DONE ou un fichier local choisi par la propriétaire.
 * Refonte : squelette pendant le chargement, rotation automatique douce à l'ouverture,
 * bascule Vue 3D / Photo source / Comparer quand une photo source est disponible.
 * Sous-étape A : matériau mat pour les GLB sans matériau, recadrage et rotation en pause en mode Comparer.
 */
// Importe le recadrage de caméra et la correction d'apparence.
import { refitCamera, watchProductAppearance } from "./model-appearance.js?v=20261117-r2";

// Branche le viewer 3D de la page Créer et ses boutons de caméra.
// <model-viewer> est un composant web de Google : une balise HTML qui affiche un fichier GLB avec rotation et zoom.
export function setupViewer({ onReady = () => {}, onError = () => {} } = {}) {
  // Le viewer 3D.
  const viewer = document.querySelector("#model-viewer");
  // Message affiché quand aucun modèle n'est chargé.
  const emptyState = document.querySelector("#empty-state");
  // Aide sur les gestes.
  const stageHint = document.querySelector("#stage-hint");
  // Boutons de caméra.
  const cameraControls = document.querySelector("#camera-controls");
  // Lien de téléchargement du GLB.
  const downloadLink = document.querySelector("#download-link");
  // Badge d'origine du modèle.
  const originBadge = document.querySelector("#origin-badge");
  // Vignette de la photo source.
  const sourcePhotoFigure = document.querySelector("#source-photo-preview");
  // Image de cette vignette.
  const sourcePhotoImage = document.querySelector("#source-photo-image");
  // Bouton qui agrandit la photo.
  const sourcePhotoOpen = document.querySelector("#source-photo-open");
  // Fenêtre de la photo agrandie.
  const sourcePhotoDialog = document.querySelector("#source-photo-dialog");
  // Image agrandie.
  const sourcePhotoLarge = document.querySelector("#source-photo-large");
  // Zone lue par les lecteurs d'écran.
  const announcement = document.querySelector("#viewer-announcement");
  // Bouton « Ouvrir un GLB local ».
  const openLocalButton = document.querySelector("#open-local-glb");
  // Champ de fichier caché pour ce GLB.
  const localInput = document.querySelector("#local-glb-input");
  // Bouton de rotation automatique.
  const autoRotateButton = document.querySelector("#auto-rotate");
  // Bouton de réalité augmentée.
  const arButton = document.querySelector("#ar-button");
  // Squelette animé pendant le chargement.
  const skeleton = document.querySelector("#viewer-skeleton");
  // Scène qui contient le viewer et la photo.
  const stage = document.querySelector("#viewer-stage");
  // Bascule Vue 3D / Photo / Comparer.
  const viewToggle = document.querySelector("#viewer-view-toggle");
  // Zone de la photo dans la scène.
  const stagePhoto = document.querySelector("#stage-photo");
  // Image de la photo dans la scène.
  const stagePhotoImage = document.querySelector("#stage-photo-image");
  // Adresse temporaire du GLB local.
  let localObjectUrl = null;
  // Adresse temporaire de la photo source.
  let sourcePhotoObjectUrl = null;
  // Modèle affiché (null = aucun).
  let activeModel = null;
  // Libellés des catégories historiques.
  const categoryLabels = { chair: "Chaise", stool: "Tabouret", "side-table": "Table d’appoint" };

  // Libère l'adresse temporaire d'un GLB local ouvert dans le navigateur.
  function releaseLocalObjectUrl() {
    // S'il y a une adresse...
    if (localObjectUrl !== null) {
      // ...on la libère...
      URL.revokeObjectURL(localObjectUrl);
      // ...et on l'oublie.
      localObjectUrl = null;
    }
  }

  // Libère l'adresse temporaire de la photo source affichée.
  function releaseSourcePhotoObjectUrl() {
    // S'il y a une adresse...
    if (sourcePhotoObjectUrl !== null) {
      // ...on la libère...
      URL.revokeObjectURL(sourcePhotoObjectUrl);
      // ...et on l'oublie.
      sourcePhotoObjectUrl = null;
    }
    // Retire l'image agrandie.
    sourcePhotoLarge.removeAttribute("src");
  }

  // Écrit un message dans une zone lue par les lecteurs d'écran (accessibilité).
  function announce(message) {
    // Écrit le message.
    announcement.textContent = message;
  }

  // Montre le bouton de réalité augmentée seulement si l'appareil le permet.
  function updateArAvailability() {
    // Pas de modèle : rien à faire.
    if (!activeModel) return;
    // Active la réalité augmentée pour tester l'appareil.
    viewer.setAttribute("ar", "");
    // Vrai si l'appareil sait lancer la réalité augmentée.
    const canActivate = viewer.canActivateAR === true;
    // Bouton visible seulement dans ce cas.
    arButton.hidden = !canActivate;
    // Sinon on retire l'attribut.
    if (!canActivate) viewer.removeAttribute("ar");
  }

  /* Modes d'affichage : « model » (3D seule), « photo » (photo seule) ou « compare » (côte à côte). */
  function setView(mode) {
    // Mode précédent.
    const previous = stage.dataset.view;
    // data-view : le CSS dispose la scène selon le mode.
    stage.dataset.view = mode;
    // Photo de la scène masquée en mode 3D seule.
    stagePhoto.hidden = mode === "model";
    // Vignette visible seulement en mode 3D et si une photo existe.
    sourcePhotoFigure.hidden = mode !== "model" || !sourcePhotoImage.getAttribute("src");
    // Pour chaque bouton de la bascule...
    viewToggle.querySelectorAll("button[data-view]").forEach((button) => {
      // ...marque celui du mode choisi.
      button.setAttribute("aria-pressed", button.dataset.view === mode ? "true" : "false");
    });
    // En comparaison, le modèle reste fixe face à la photo ; la rotation reprend avec le bouton dédié.
    // En mode Comparer, si la rotation tourne...
    if (mode === "compare" && viewer.hasAttribute("auto-rotate")) {
      // ...on l'arrête...
      viewer.removeAttribute("auto-rotate");
      // ...et on met à jour le bouton.
      autoRotateButton.setAttribute("aria-pressed", "false");
    }
    // Le mode a changé : on recadre la caméra.
    if (activeModel && previous !== mode) refitCamera(viewer);
  }

  // Remet le viewer à l'état vide : plus de modèle, de photo ni de boutons.
  function clear() {
    // Retire la réalité augmentée.
    viewer.removeAttribute("ar");
    // Arrête la rotation.
    viewer.removeAttribute("auto-rotate");
    // Retire le modèle.
    viewer.removeAttribute("src");
    // Ferme la photo agrandie si elle est ouverte.
    if (sourcePhotoDialog.open) sourcePhotoDialog.close();
    // Libère l'adresse du GLB local.
    releaseLocalObjectUrl();
    // Libère l'adresse de la photo.
    releaseSourcePhotoObjectUrl();
    // Retire la vignette.
    sourcePhotoImage.removeAttribute("src");
    // Retire la photo de la scène.
    stagePhotoImage.removeAttribute("src");
    // Masque la vignette.
    sourcePhotoFigure.hidden = true;
    // Masque la bascule.
    viewToggle.hidden = true;
    // Masque le squelette.
    skeleton.hidden = true;
    // Revient au mode 3D seule.
    setView("model");
    // Plus de modèle actif.
    activeModel = null;
    // Masque le viewer.
    viewer.hidden = true;
    // Montre l'état vide.
    emptyState.hidden = false;
    // Masque l'aide.
    stageHint.hidden = true;
    // Masque les boutons de caméra.
    cameraControls.hidden = true;
    // Masque le téléchargement.
    downloadLink.hidden = true;
    // Masque le badge.
    originBadge.hidden = true;
    // Masque la réalité augmentée.
    arButton.hidden = true;
    // Bouton de rotation non enfoncé.
    autoRotateButton.setAttribute("aria-pressed", "false");
    // Efface l'annonce.
    announce("");
  }

  // Affiche un modèle : adresse du serveur, ou fichier local (source « local », jamais envoyé au serveur).
  // Gère aussi la photo source, le badge d'origine et le lien de téléchargement.
  function showModel({ url, filename, source, category = null, downloadUrl = null, sourcePhoto = null }) {
    // Repart d'un viewer vide.
    clear();
    // Fichier local choisi par la propriétaire...
    if (source === "local") {
      // ...adresse temporaire locale...
      localObjectUrl = URL.createObjectURL(url);
      // ...affichée dans le viewer...
      viewer.src = localObjectUrl;
      // ...badge « Importé manuellement »...
      originBadge.textContent = "Importé manuellement";
      // ...annonce : rien n'est envoyé au serveur.
      announce("Fichier local, non généré par l’application. Il est chargé dans ce navigateur sans être envoyé au serveur.");
    // Sinon (modèle du serveur)...
    } else {
      // ...adresse du GLB...
      viewer.src = url;
      // ...texte d'origine...
      const origin = source === "gallery"
        ? "Généré par l’application · modèle d’essai"
        : "Généré par l’application";
      // ...badge avec la catégorie si elle est connue...
      originBadge.textContent = categoryLabels[category]
        ? origin + " · " + categoryLabels[category]
        : origin;
      // ...annonce du chargement.
      announce(filename ? "Chargement du modèle : " + filename + "." : "Chargement du modèle 3D.");
    }

    // Si une photo source est fournie...
    if (sourcePhoto) {
      // ...fichier local...
      if (sourcePhoto instanceof File) {
        // ...adresse temporaire...
        sourcePhotoObjectUrl = URL.createObjectURL(sourcePhoto);
        // ...affichée dans la vignette...
        sourcePhotoImage.src = sourcePhotoObjectUrl;
      // ...sinon adresse du serveur...
      } else {
        // ...affichée dans la vignette.
        sourcePhotoImage.src = sourcePhoto;
      }
      // Texte alternatif de la photo...
      sourcePhotoImage.alt = filename
        ? "Photo source du modèle " + filename
        : "Photo source du produit envoyé";
      // Même photo dans la scène...
      stagePhotoImage.src = sourcePhotoImage.src;
      // ...avec le même texte alternatif.
      stagePhotoImage.alt = sourcePhotoImage.alt;
      // Vignette visible.
      sourcePhotoFigure.hidden = false;
      // Bascule visible.
      viewToggle.hidden = false;
    }

    // Mémorise le modèle actif.
    activeModel = { source, filename };
    // Texte alternatif du viewer...
    viewer.alt = filename
      ? "Modèle 3D " + filename + " affiché dans le viewer"
      : "Modèle 3D du produit affiché dans le viewer";
    // Viewer visible.
    viewer.hidden = false;
    // État vide masqué.
    emptyState.hidden = true;
    // Squelette visible jusqu'au chargement.
    skeleton.hidden = false;
    // Rotation douce à l'ouverture pour mettre le modèle en valeur ; elle se met en pause pendant les gestes.
    // Démarre la rotation.
    viewer.setAttribute("auto-rotate", "");
    // Bouton de rotation enfoncé.
    autoRotateButton.setAttribute("aria-pressed", "true");
    // Aide visible.
    stageHint.hidden = false;
    // Boutons de caméra visibles.
    cameraControls.hidden = false;
    // Badge visible.
    originBadge.hidden = false;
    // Téléchargement visible seulement s'il existe.
    downloadLink.hidden = !downloadUrl;
    // Adresse de téléchargement fournie...
    if (downloadUrl) {
      // ...lien vers le GLB...
      downloadLink.href = downloadUrl;
      // ...nom proposé, toujours terminé par .glb.
      downloadLink.download = filename ? filename.replace(/\.glb$/i, "") + ".glb" : "forma3d-modele.glb";
    // Sinon...
    } else {
      // ...lien sans adresse.
      downloadLink.removeAttribute("href");
    }
  }

  // N'exécute l'action que si un modèle est réellement affiché.
  function whenModelIsLoaded(action) {
    // Pas de modèle ou pas encore visible : rien à faire.
    if (!activeModel || viewer.modelIsVisible !== true) return;
    // Sinon on exécute l'action.
    action();
  }

  // Tourne la caméra de 15° (π/12) à gauche ou à droite.
  function rotateCamera(direction) {
    // Seulement si le modèle est chargé...
    whenModelIsLoaded(() => {
      // ...position actuelle de la caméra...
      const orbit = viewer.getCameraOrbit();
      // ...ajoute ou retire 15°...
      orbit.theta += direction * (Math.PI / 12);
      // ...et l'applique.
      viewer.cameraOrbit = orbit.toString();
    });
  }

  // Déplace le point visé de 5 % de la plus grande dimension du modèle.
  function panCamera(axis, direction) {
    // Seulement si le modèle est chargé...
    whenModelIsLoaded(() => {
      // ...point visé actuel...
      const target = viewer.getCameraTarget();
      // ...dimensions du modèle...
      const dimensions = viewer.getDimensions();
      // ...pas : 5 % de la plus grande dimension (au moins 0,1)...
      const step = Math.max(dimensions.x, dimensions.y, dimensions.z, 0.1) * 0.05;
      // ...décale sur l'axe demandé...
      target[axis] += direction * step;
      // ...et l'applique.
      viewer.cameraTarget = target.toString();
    });
  }

  // Bouton : tourner à gauche.
  document.querySelector("#rotate-left").addEventListener("click", () => rotateCamera(-1));
  // Bouton : tourner à droite.
  document.querySelector("#rotate-right").addEventListener("click", () => rotateCamera(1));
  // Bouton : déplacer à gauche.
  document.querySelector("#pan-left").addEventListener("click", () => panCamera("x", -1));
  // Bouton : déplacer à droite.
  document.querySelector("#pan-right").addEventListener("click", () => panCamera("x", 1));
  // Bouton : monter.
  document.querySelector("#pan-up").addEventListener("click", () => panCamera("y", 1));
  // Bouton : descendre.
  document.querySelector("#pan-down").addEventListener("click", () => panCamera("y", -1));
  // Bouton : zoom avant.
  document.querySelector("#zoom-in").addEventListener("click", () => whenModelIsLoaded(() => viewer.zoom(1)));
  // Bouton : zoom arrière.
  document.querySelector("#zoom-out").addEventListener("click", () => whenModelIsLoaded(() => viewer.zoom(-1)));

  // Bouton : réinitialiser la vue...
  document.querySelector("#reset-camera").addEventListener("click", () => whenModelIsLoaded(() => {
    // ...point visé automatique...
    viewer.cameraTarget = "auto auto auto";
    // ...angle et distance de départ...
    viewer.cameraOrbit = "0deg 75deg 105%";
    // ...recadre...
    viewer.updateFraming();
    // ...et l'annonce.
    announce("Vue du modèle réinitialisée.");
  }));

  // Bouton : rotation automatique...
  autoRotateButton.addEventListener("click", () => whenModelIsLoaded(() => {
    // ...état actuel...
    const enabled = viewer.hasAttribute("auto-rotate");
    // ...l'arrête si elle tourne...
    if (enabled) viewer.removeAttribute("auto-rotate");
    // ...sinon la démarre...
    else viewer.setAttribute("auto-rotate", "");
    // ...met à jour le bouton...
    autoRotateButton.setAttribute("aria-pressed", enabled ? "false" : "true");
    // ...et l'annonce.
    announce(enabled ? "Rotation automatique arrêtée." : "Rotation automatique activée.");
  }));

  // Bouton : plein écran...
  document.querySelector("#fullscreen").addEventListener("click", async () => {
    // ...pas de modèle : rien à faire...
    if (!activeModel) return;
    // ...essaie...
    try {
      // ...de passer en plein écran...
      await viewer.requestFullscreen();
      // ...et l'annonce...
      announce("Viewer affiché en plein écran. Appuyez sur Échap pour revenir.");
    // ...refus du navigateur...
    } catch {
      // ...annoncé.
      announce("Le navigateur n’a pas autorisé le plein écran.");
    }
  });

  // Clic sur la vignette...
  sourcePhotoOpen.addEventListener("click", () => {
    // ...pas de photo : rien à faire...
    if (!sourcePhotoImage.src) return;
    // ...image agrandie...
    sourcePhotoLarge.src = sourcePhotoImage.currentSrc || sourcePhotoImage.src;
    // ...texte alternatif adapté...
    sourcePhotoLarge.alt = sourcePhotoImage.alt.replace("source", "source agrandie");
    // ...ouvre la fenêtre.
    sourcePhotoDialog.showModal();
  });

  // Clic sur « Ouvrir un GLB local » : ouvre le choix de fichier.
  openLocalButton.addEventListener("click", () => localInput.click());
  localInput.addEventListener("change", () => {
    // Fichier choisi...
    const file = localInput.files[0];
    // ...aucun : rien à faire...
    if (!file) return;
    // ...pas un .glb, ou vide...
    if (!file.name.toLowerCase().endsWith(".glb") || file.size === 0) {
      // ...on vide le champ...
      localInput.value = "";
      // ...on l'annonce...
      announce("Choisissez un fichier de modèle 3D valide.");
      // ...et on s'arrête.
      return;
    }
    // Affiche le fichier localement.
    showModel({ url: file, filename: file.name, source: "local" });
  });

  // Clic dans la bascule...
  viewToggle.addEventListener("click", (event) => {
    // ...bouton visé...
    const button = event.target.closest("button[data-view]");
    // ...change le mode.
    if (button) setView(button.dataset.view);
  });

  // Branche la correction d'apparence.
  watchProductAppearance(viewer);
  // Quand le modèle est chargé...
  viewer.addEventListener("load", () => {
    // ...plus de modèle actif : rien à faire...
    if (!activeModel) return;
    // ...masque le squelette...
    skeleton.hidden = true;
    // ...angle de départ...
    viewer.cameraOrbit = "0deg 75deg 105%";
    // ...recadre...
    viewer.updateFraming();
    // ...vérifie la réalité augmentée...
    updateArAvailability();
    // ...l'annonce...
    announce("Modèle chargé. Utilisez les commandes de caméra ou les gestes dans le viewer.");
    // ...et prévient la page.
    onReady(activeModel);
  });

  // En cas d'erreur d'affichage...
  viewer.addEventListener("error", () => {
    // ...masque le squelette...
    skeleton.hidden = true;
    // ...vrai si c'est un fichier local...
    const isLocal = activeModel?.source === "local";
    // ...message adapté...
    const message = isLocal
      ? "Ce fichier ne peut pas être affiché comme modèle 3D."
      : "Le fichier existe, mais le modèle n’a pas pu être affiché. Le téléchargement reste disponible.";
    // ...annoncé...
    announce(message);
    // ...et transmis à la page.
    onError(message);
  });

  // Quand on quitte la page...
  window.addEventListener("pagehide", () => {
    // ...libère l'adresse du GLB local...
    releaseLocalObjectUrl();
    // ...et celle de la photo.
    releaseSourcePhotoObjectUrl();
  });

  // Renvoie les fonctions utilisables par la page.
  return { clear, showModel, announce };
}
