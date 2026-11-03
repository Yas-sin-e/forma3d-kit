/*
 * Rôle : affiche un GLB dans model-viewer et gère ses commandes et son origine.
 * Exécution : main.js lui transmet un modèle DONE, un modèle de galerie ou un fichier local.
 */
export function setupViewer({ onReady = () => {}, onError = () => {} } = {}) {
  const viewer = document.querySelector("#model-viewer");
  const emptyState = document.querySelector("#empty-state");
  const stageHint = document.querySelector("#stage-hint");
  const cameraControls = document.querySelector("#camera-controls");
  const downloadLink = document.querySelector("#download-link");
  const originBadge = document.querySelector("#origin-badge");
  const sourcePhotoFigure = document.querySelector("#source-photo-preview");
  const sourcePhotoImage = document.querySelector("#source-photo-image");
  const sourcePhotoOpen = document.querySelector("#source-photo-open");
  const sourcePhotoDialog = document.querySelector("#source-photo-dialog");
  const sourcePhotoLarge = document.querySelector("#source-photo-large");
  const announcement = document.querySelector("#viewer-announcement");
  const openLocalButton = document.querySelector("#open-local-glb");
  const localInput = document.querySelector("#local-glb-input");
  const autoRotateButton = document.querySelector("#auto-rotate");
  const arButton = document.querySelector("#ar-button");
  let localObjectUrl = null;
  let sourcePhotoObjectUrl = null;
  let activeModel = null;
  const categoryLabels = { chair: "Chaise", stool: "Tabouret", "side-table": "Table d’appoint" };

  function releaseLocalObjectUrl() {
    if (localObjectUrl !== null) {
      URL.revokeObjectURL(localObjectUrl);
      localObjectUrl = null;
    }
  }

  function releaseSourcePhotoObjectUrl() {
    if (sourcePhotoObjectUrl !== null) {
      URL.revokeObjectURL(sourcePhotoObjectUrl);
      sourcePhotoObjectUrl = null;
    }
    sourcePhotoLarge.removeAttribute("src");
  }

  function announce(message) {
    announcement.textContent = message;
  }

  function updateArAvailability() {
    if (!activeModel) return;
    viewer.setAttribute("ar", "");
    const canActivate = viewer.canActivateAR === true;
    arButton.hidden = !canActivate;
    if (!canActivate) viewer.removeAttribute("ar");
  }

  function clear() {
    viewer.removeAttribute("ar");
    viewer.removeAttribute("auto-rotate");
    viewer.removeAttribute("src");
    if (sourcePhotoDialog.open) sourcePhotoDialog.close();
    releaseLocalObjectUrl();
    releaseSourcePhotoObjectUrl();
    sourcePhotoImage.removeAttribute("src");
    sourcePhotoFigure.hidden = true;
    activeModel = null;
    viewer.hidden = true;
    emptyState.hidden = false;
    stageHint.hidden = true;
    cameraControls.hidden = true;
    downloadLink.hidden = true;
    originBadge.hidden = true;
    arButton.hidden = true;
    autoRotateButton.setAttribute("aria-pressed", "false");
    announce("");
  }

  function showModel({ url, filename, source, category = null, downloadUrl = null, sourcePhoto = null }) {
    clear();
    if (source === "local") {
      localObjectUrl = URL.createObjectURL(url);
      viewer.src = localObjectUrl;
      originBadge.textContent = "Importé manuellement";
      announce("Fichier local, non généré par l’application. Il est chargé dans ce navigateur sans être envoyé au serveur.");
    } else {
      viewer.src = url;
      const origin = source === "gallery"
        ? "Généré par l’application · modèle d’essai"
        : "Généré par l’application";
      originBadge.textContent = categoryLabels[category]
        ? origin + " · " + categoryLabels[category]
        : origin;
      announce(filename ? "Chargement du modèle : " + filename + "." : "Chargement du GLB fourni par le serveur.");
    }

    if (sourcePhoto) {
      if (sourcePhoto instanceof File) {
        sourcePhotoObjectUrl = URL.createObjectURL(sourcePhoto);
        sourcePhotoImage.src = sourcePhotoObjectUrl;
      } else {
        sourcePhotoImage.src = sourcePhoto;
      }
      sourcePhotoImage.alt = filename
        ? "Photo source du modèle " + filename
        : "Photo source du produit envoyé";
      sourcePhotoFigure.hidden = false;
    }

    activeModel = { source, filename };
    viewer.alt = filename
      ? "Modèle 3D " + filename + " affiché dans le viewer"
      : "Modèle 3D du produit affiché dans le viewer";
    viewer.hidden = false;
    emptyState.hidden = true;
    stageHint.hidden = false;
    cameraControls.hidden = false;
    originBadge.hidden = false;
    downloadLink.hidden = !downloadUrl;
    if (downloadUrl) {
      downloadLink.href = downloadUrl;
      downloadLink.download = filename ? filename.replace(/\.glb$/i, "") + ".glb" : "forma3d-modele.glb";
    } else {
      downloadLink.removeAttribute("href");
    }
  }

  function whenModelIsLoaded(action) {
    if (!activeModel || viewer.modelIsVisible !== true) return;
    action();
  }

  function rotateCamera(direction) {
    whenModelIsLoaded(() => {
      const orbit = viewer.getCameraOrbit();
      orbit.theta += direction * (Math.PI / 12);
      viewer.cameraOrbit = orbit.toString();
    });
  }

  function panCamera(axis, direction) {
    whenModelIsLoaded(() => {
      const target = viewer.getCameraTarget();
      const dimensions = viewer.getDimensions();
      const step = Math.max(dimensions.x, dimensions.y, dimensions.z, 0.1) * 0.05;
      target[axis] += direction * step;
      viewer.cameraTarget = target.toString();
    });
  }

  document.querySelector("#rotate-left").addEventListener("click", () => rotateCamera(-1));
  document.querySelector("#rotate-right").addEventListener("click", () => rotateCamera(1));
  document.querySelector("#pan-left").addEventListener("click", () => panCamera("x", -1));
  document.querySelector("#pan-right").addEventListener("click", () => panCamera("x", 1));
  document.querySelector("#pan-up").addEventListener("click", () => panCamera("y", 1));
  document.querySelector("#pan-down").addEventListener("click", () => panCamera("y", -1));
  document.querySelector("#zoom-in").addEventListener("click", () => whenModelIsLoaded(() => viewer.zoom(1)));
  document.querySelector("#zoom-out").addEventListener("click", () => whenModelIsLoaded(() => viewer.zoom(-1)));

  document.querySelector("#reset-camera").addEventListener("click", () => whenModelIsLoaded(() => {
    viewer.cameraTarget = "auto auto auto";
    viewer.cameraOrbit = "0deg 75deg 105%";
    viewer.updateFraming();
    announce("Vue du modèle réinitialisée.");
  }));

  autoRotateButton.addEventListener("click", () => whenModelIsLoaded(() => {
    const enabled = viewer.hasAttribute("auto-rotate");
    if (enabled) viewer.removeAttribute("auto-rotate");
    else viewer.setAttribute("auto-rotate", "");
    autoRotateButton.setAttribute("aria-pressed", enabled ? "false" : "true");
    announce(enabled ? "Rotation automatique arrêtée." : "Rotation automatique activée.");
  }));

  document.querySelector("#fullscreen").addEventListener("click", async () => {
    if (!activeModel) return;
    try {
      await viewer.requestFullscreen();
      announce("Viewer affiché en plein écran. Appuyez sur Échap pour revenir.");
    } catch {
      announce("Le navigateur n’a pas autorisé le plein écran.");
    }
  });

  sourcePhotoOpen.addEventListener("click", () => {
    if (!sourcePhotoImage.src) return;
    sourcePhotoLarge.src = sourcePhotoImage.currentSrc || sourcePhotoImage.src;
    sourcePhotoLarge.alt = sourcePhotoImage.alt.replace("source", "source agrandie");
    sourcePhotoDialog.showModal();
  });

  openLocalButton.addEventListener("click", () => localInput.click());
  localInput.addEventListener("change", () => {
    const file = localInput.files[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".glb") || file.size === 0) {
      localInput.value = "";
      announce("Le fichier local doit être un GLB non vide.");
      return;
    }
    showModel({ url: file, filename: file.name, source: "local" });
  });

  viewer.addEventListener("load", () => {
    if (!activeModel) return;
    viewer.cameraOrbit = "0deg 75deg 105%";
    viewer.updateFraming();
    updateArAvailability();
    announce("Modèle chargé. Utilisez les commandes de caméra ou les gestes dans le viewer.");
    onReady(activeModel);
  });

  viewer.addEventListener("error", () => {
    const isLocal = activeModel?.source === "local";
    const message = isLocal
      ? "Le fichier local ne peut pas être lu comme modèle GLB."
      : "Le fichier existe, mais le navigateur n’a pas pu afficher le modèle. Le téléchargement reste disponible.";
    announce(message);
    onError(message);
  });

  window.addEventListener("pagehide", () => {
    releaseLocalObjectUrl();
    releaseSourcePhotoObjectUrl();
  });

  return { clear, showModel, announce };
}
