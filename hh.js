/**
 * IrriOlive — Patch JavaScript
 * Remplace saveProfile() et deleteProfile() pour persister en MySQL via l'API PHP.
 *
 * ► COMMENT L'UTILISER :
 *   1. Placez api_profils.php sur votre serveur (même dossier que le HTML ou ajustez API_BASE).
 *   2. Exécutez irriOlive_database.sql dans phpMyAdmin / MySQL Workbench.
 *   3. Collez ce bloc <script> APRÈS le <script> existant du fichier HTML (juste avant </body>).
 */

/* ── URL de l'API (adapter si nécessaire) ── */
const API_BASE = 'api_profils.php';

/* ═══════════════════════════════════════
   CHARGEMENT INITIAL des profils au démarrage
═══════════════════════════════════════ */
async function loadProfilesFromDB() {
  try {
    const res  = await fetch(API_BASE);
    const json = await res.json();
    if (json.success) {
      // Convertir le format DB → format JS attendu par le code existant
      profiles = json.data.map(row => ({
        id:         String(row.id),
        region:     row.region,
        lat:        row.latitude  ? parseFloat(row.latitude)  : null,
        lon:        row.longitude ? parseFloat(row.longitude) : null,
        climate:    row.zone_climatique    || null,
        soil:       row.type_sol           || null,
        trees:      Array.isArray(row.varietes) ? row.varietes : [],
        count:      row.nb_oliviers        || 100,
        superficie: row.superficie_ha      ? parseFloat(row.superficie_ha) : null,
        water:      row.source_eau         || null,
        irrigation: row.methode_irrigation || null,
      }));
      renderGrid();
    }
  } catch (err) {
    console.error('Impossible de charger les profils :', err);
  }
}

/* ═══════════════════════════════════════
   SURCHARGE : saveProfile()
   Remplace la version JS-only
═══════════════════════════════════════ */
async function saveProfile() {
  const data = readForm();

  const payload = {
    region:     data.region,
    lat:        data.lat,
    lon:        data.lon,
    climate:    data.climate,
    soil:       data.soil,
    trees:      data.trees,
    count:      data.count,
    superficie: data.superficie,
    water:      data.water,
    irrigation: data.irrigation,
  };

  try {
    let res, json;

    if (editingId) {
      /* ── Mise à jour (PUT) ── */
      res  = await fetch(`${API_BASE}?id=${editingId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      json = await res.json();

      if (json.success) {
        const idx = profiles.findIndex(x => x.id === editingId);
        if (idx !== -1) profiles[idx] = { ...profiles[idx], ...data };
      } else {
        alert('Erreur mise à jour : ' + json.message);
        return;
      }

    } else {
      /* ── Création (POST) ── */
      if (profiles.length >= MAX_PROFILES) { closeModal(); return; }

      res  = await fetch(API_BASE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      json = await res.json();

      if (json.success) {
        const newProfile = { id: String(json.id), ...data };
        profiles.push(newProfile);
        editingId = String(json.id); // pour openProfilePage ci-dessous
      } else {
        alert('Erreur création : ' + json.message);
        return;
      }
    }

    const savedId = editingId;
    renderGrid();
    closeModal();

    /* Si les coordonnées GPS sont manquantes, géocodage puis mise à jour DB */
    const saved = profiles.find(p => p.id === savedId);
    if (!saved.lat && saved.region) {
      geocodeCity(saved.region).then(async coords => {
        if (coords) {
          saved.lat = coords.lat;
          saved.lon = coords.lon;
          /* Mise à jour silencieuse des coordonnées en DB */
          await fetch(`${API_BASE}?id=${savedId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ...saved }),
          });
        }
      });
    }

    setTimeout(() => {
      document.getElementById('profileSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
    setTimeout(() => openProfilePage(savedId), 700);
    setTimeout(() => { resetForm(); goToStep(1); }, 500);

  } catch (err) {
    console.error('Erreur réseau :', err);
    alert('Erreur réseau. Vérifiez que le serveur PHP est démarré.');
  }
}

/* ═══════════════════════════════════════
   SURCHARGE : deleteProfile()
═══════════════════════════════════════ */
async function deleteProfile(id) {
  const card = document.getElementById('card-' + id);
  if (card) {
    card.style.transition = 'opacity 0.3s, transform 0.3s';
    card.style.opacity    = '0';
    card.style.transform  = 'scale(0.9)';
  }

  try {
    const res  = await fetch(`${API_BASE}?id=${id}`, { method: 'DELETE' });
    const json = await res.json();
    if (!json.success) console.warn('Suppression DB :', json.message);
  } catch (err) {
    console.error('Erreur suppression :', err);
  }

  setTimeout(() => {
    profiles = profiles.filter(p => p.id !== id);
    renderGrid();
  }, 300);
}

/* ═══════════════════════════════════════
   LANCEMENT : charger les profils au démarrage
═══════════════════════════════════════ */
loadProfilesFromDB();