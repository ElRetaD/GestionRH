"""Script temporaire pour convertir les salaires DZD -> MAD dans la base de données."""
from app.database.connection import db

# Taux de conversion approximatif: 1 DZD ≈ 0.073 MAD
# Les salaires actuels sont en dinars algériens (ex: 85000 DZD ≈ 6200 MAD)
# Les salaires marocains typiques :
#   - SMIG : ~3000 MAD
#   - Employé moyen : 5000-8000 MAD
#   - Cadre : 10000-20000 MAD

FACTOR = 0.073  # DZD -> MAD

# 1. Convertir salaires_employes
rows = db.fetchall("SELECT id, salaire_base, taux_horaire FROM salaires_employes")
print(f"Conversion de {len(rows)} salaire(s)...")
for r in rows:
    new_base = round(r["salaire_base"] * FACTOR, 2)
    new_taux = round(r["taux_horaire"] * FACTOR, 2)
    db.execute(
        "UPDATE salaires_employes SET salaire_base=?, taux_horaire=?, date_modification=datetime('now','localtime') WHERE id=?",
        (new_base, new_taux, r["id"])
    )
    print(f"  ID {r['id']}: {r['salaire_base']} DZD -> {new_base} MAD")

# 2. Convertir bulletins_paie
buls = db.fetchall("SELECT id, salaire_base, total_primes, total_heures_sup, total_deductions, salaire_brut, salaire_net FROM bulletins_paie")
print(f"Conversion de {len(buls)} bulletin(s)...")
for b in buls:
    updates = {
        "salaire_base": round(b["salaire_base"] * FACTOR, 2),
        "total_primes": round(b["total_primes"] * FACTOR, 2),
        "total_heures_sup": round(b["total_heures_sup"] * FACTOR, 2),
        "total_deductions": round(b["total_deductions"] * FACTOR, 2),
        "salaire_brut": round(b["salaire_brut"] * FACTOR, 2),
        "salaire_net": round(b["salaire_net"] * FACTOR, 2),
    }
    db.execute(
        """UPDATE bulletins_paie SET salaire_base=?, total_primes=?, total_heures_sup=?,
           total_deductions=?, salaire_brut=?, salaire_net=? WHERE id=?""",
        (*updates.values(), b["id"])
    )
    print(f"  Bulletin {b['id']}: Net {b['salaire_net']} DZD -> {updates['salaire_net']} MAD")

# 3. Convertir elements_paie (primes, deductions, etc.)
elems = db.fetchall("SELECT id, montant, taux FROM elements_paie")
print(f"Conversion de {len(elems)} élément(s) de paie...")
for e in elems:
    new_montant = round(e["montant"] * FACTOR, 2)
    new_taux = round(e["taux"] * FACTOR, 2)
    db.execute(
        "UPDATE elements_paie SET montant=?, taux=? WHERE id=?",
        (new_montant, new_taux, e["id"])
    )

print("\n✅ Conversion DZD -> MAD terminée !")

# Vérification
rows2 = db.fetchall("SELECT s.salaire_base, e.nom, e.prenom FROM salaires_employes s JOIN employes e ON e.id = s.employe_id")
for r in rows2:
    print(f"  {r['nom']} {r['prenom']}: {r['salaire_base']} MAD")
