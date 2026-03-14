import pymysql

# ── Configuration connexion MySQL ─────────────────────────
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "1234"  # mets ton mot de passe si nécessaire

def create_database():
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD
    )

    cursor = connection.cursor()

    # ── Création base ─────────────────────────────────────
    cursor.execute("""
    CREATE DATABASE IF NOT EXISTS irriOlive
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
    """)

    cursor.execute("USE irriOlive;")

    # ── Création table ────────────────────────────────────
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profils_oliveraie (
      id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

      region VARCHAR(255) NOT NULL,
      latitude DECIMAL(10,7) DEFAULT NULL,
      longitude DECIMAL(10,7) DEFAULT NULL,

      zone_climatique ENUM(
        'semi-aride','aride','mediterraneen',
        'subhumide','montagnard','plaine'
      ) DEFAULT NULL,

      type_sol ENUM(
        'argileux','limoneux','sableux',
        'calcaire','argilo-limoneux','rocailleux'
      ) DEFAULT NULL,

      varietes JSON DEFAULT NULL,

      nb_oliviers INT UNSIGNED NOT NULL DEFAULT 100,
      superficie_ha DECIMAL(8,2) DEFAULT NULL,

      densite_arb_ha DECIMAL(8,2)
      AS (
        CASE
          WHEN superficie_ha > 0 THEN ROUND(nb_oliviers / superficie_ha, 2)
          ELSE NULL
        END
      ) STORED,

      source_eau ENUM(
        'puits','oued','reseau',
        'forage','citerne','mixte-eau'
      ) DEFAULT NULL,

      methode_irrigation ENUM(
        'goutte-a-goutte','micro-aspersion',
        'aspersion','gravitaire',
        'subsurface','bassins'
      ) DEFAULT NULL,

      cree_le DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      modifie_le DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

      INDEX idx_region (region(100)),
      INDEX idx_climate (zone_climatique),
      INDEX idx_cree_le (cree_le)
    ) ENGINE=InnoDB
    DEFAULT CHARSET=utf8mb4
    COLLATE=utf8mb4_unicode_ci;
    """)

    # ── Création vue ─────────────────────────────────────
    cursor.execute("""
    CREATE OR REPLACE VIEW v_profils AS
    SELECT
      id, region, latitude, longitude,
      zone_climatique,
      type_sol,
      varietes,
      nb_oliviers,
      superficie_ha,
      densite_arb_ha,
      source_eau,
      methode_irrigation,
      cree_le,
      modifie_le
    FROM profils_oliveraie;
    """)

    # ── Donnée test ──────────────────────────────────────
    cursor.execute("""
    INSERT INTO profils_oliveraie
    (region, latitude, longitude, zone_climatique, type_sol,
     varietes, nb_oliviers, superficie_ha, source_eau, methode_irrigation)
    VALUES
    ('El Kelaa des Sraghna, Maroc',
     32.0560, -7.4074,
     'semi-aride','argilo-limoneux',
     '["menara","haouziya"]',
     350, 12.50,
     'forage','goutte-a-goutte');
    """)

    connection.commit()
    cursor.close()
    connection.close()

    print("✅ Base de données créée avec succès !")

if __name__ == "__main__":
    create_database()