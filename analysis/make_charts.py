"""Render charts straight from the warehouse as committed SVG.

Why SVG written by hand rather than matplotlib: no extra dependency to install
(and nothing to compile on a new Python), the output is text so git can diff
it, and GitHub renders SVG inline in the README. The charts on the repo's
front page are therefore produced by this script from the marts - not drawn in
a tool and pasted in, where they would quietly go stale.

    python analysis/make_charts.py
"""
from __future__ import annotations

import html
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "retail.duckdb"
OUT = ROOT / "charts"

# A restrained palette that stays legible on both GitHub themes.
ENCRE = "#1f2933"
GRIS = "#8b98a5"
GRILLE = "#e4e7eb"
ACCENT = "#2f6f9f"
ACCENT_PALE = "#9fc3dc"
CHAUD = "#b4541f"


def entete(largeur: int, hauteur: int, titre: str, sous_titre: str = "") -> list[str]:
    """Open an SVG and write its title block.

    font-family is a stack rather than a single face: these render on other
    people's machines, and a missing font silently changes every layout
    calculation below.
    """
    s = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{largeur}" '
        f'height="{hauteur}" viewBox="0 0 {largeur} {hauteur}" '
        f'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">',
        f'<rect width="{largeur}" height="{hauteur}" fill="white"/>',
        f'<text x="24" y="34" font-size="17" font-weight="600" fill="{ENCRE}">'
        f'{html.escape(titre)}</text>',
    ]
    if sous_titre:
        s.append(
            f'<text x="24" y="54" font-size="12" fill="{GRIS}">'
            f'{html.escape(sous_titre)}</text>'
        )
    return s


def ecrire(nom: str, morceaux: list[str]) -> None:
    morceaux.append("</svg>")
    chemin = OUT / nom
    chemin.write_text("\n".join(morceaux), encoding="utf-8")
    print(f"  {chemin.relative_to(ROOT)}")


def revenu_mensuel(con) -> None:
    lignes = con.execute("""
        select d.annee_mois, cast(round(sum(f.montant)) as double) as ca
        from main_marts.fct_ligne_commande f
        join main_marts.dim_date d on d.date_id = f.date_id
        group by d.annee_mois
        order by d.annee_mois
    """).fetchall()

    L, H = 900, 320
    gx, gy, gl, gh = 70, 80, L - 110, H - 150
    maxi = max(c for _, c in lignes)
    pas = gl / (len(lignes) - 1)

    s = entete(L, H, "Chiffre d'affaires mensuel",
               "Lignes attribuables. Le pic de novembre est reel : "
               "ce detaillant vend des cadeaux en gros avant Noel.")

    # Gridlines with labels, four of them - enough to read a value off, few
    # enough not to crowd the series.
    for i in range(5):
        y = gy + gh - (gh * i / 4)
        v = maxi * i / 4
        s.append(f'<line x1="{gx}" y1="{y:.1f}" x2="{gx + gl}" y2="{y:.1f}" '
                 f'stroke="{GRILLE}" stroke-width="1"/>')
        s.append(f'<text x="{gx - 10}" y="{y + 4:.1f}" font-size="10" fill="{GRIS}" '
                 f'text-anchor="end">{v / 1000:.0f}k</text>')

    pts = [f"{gx + i * pas:.1f},{gy + gh - (c / maxi) * gh:.1f}"
           for i, (_, c) in enumerate(lignes)]
    s.append(f'<polyline points="{" ".join(pts)}" fill="none" '
             f'stroke="{ACCENT}" stroke-width="2.5" stroke-linejoin="round"/>')

    for i, (mois, c) in enumerate(lignes):
        x = gx + i * pas
        y = gy + gh - (c / maxi) * gh
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{ACCENT}"/>')
        if i % 3 == 0 or i == len(lignes) - 1:
            s.append(f'<text x="{x:.1f}" y="{gy + gh + 18}" font-size="9.5" '
                     f'fill="{GRIS}" text-anchor="middle">{mois}</text>')

    s.append(f'<text x="24" y="{H - 14}" font-size="10" fill="{GRIS}">'
             f'Source : main_marts.fct_ligne_commande | genere par analysis/make_charts.py</text>')
    ecrire("revenu_mensuel.svg", s)


def segments_rfm(con) -> None:
    lignes = con.execute("""
        select r.segment,
               count(*)                       as clients,
               cast(round(sum(c.valeur_vie)) as double) as valeur
        from main_marts.fct_rfm r
        join main_marts.dim_client c on c.client_id = r.client_id
        group by r.segment
        order by valeur desc
    """).fetchall()

    L, H = 900, 330
    gx, gy = 190, 80
    gl = L - gx - 130
    bh, ecart = 26, 12
    maxi = max(v for _, _, v in lignes)

    s = entete(L, H, "Valeur vie par segment RFM",
               "Scores par quintile sur recence, frequence et montant. "
               "Recence mesuree contre la derniere date du jeu, pas aujourd'hui.")

    for i, (seg, n, val) in enumerate(lignes):
        y = gy + i * (bh + ecart)
        w = (val / maxi) * gl
        couleur = ACCENT if seg == "Champions" else (CHAUD if seg in ("Perdus", "A risque") else ACCENT_PALE)
        s.append(f'<text x="{gx - 12}" y="{y + bh / 2 + 4:.0f}" font-size="12" '
                 f'fill="{ENCRE}" text-anchor="end">{html.escape(seg)}</text>')
        s.append(f'<rect x="{gx}" y="{y}" width="{w:.1f}" height="{bh}" '
                 f'fill="{couleur}" rx="3"/>')
        s.append(f'<text x="{gx + w + 10:.1f}" y="{y + bh / 2 + 4:.0f}" font-size="11" '
                 f'fill="{GRIS}">{val / 1e6:.2f}M GBP  ({n} clients)</text>')

    s.append(f'<text x="24" y="{H - 14}" font-size="10" fill="{GRIS}">'
             f'Source : main_marts.fct_rfm + main_marts.dim_client</text>')
    ecrire("segments_rfm.svg", s)


def retention_cohortes(con) -> None:
    """Cohort retention as a heatmap.

    Only cohorts with at least 30 customers are drawn. A cohort of four people
    produces retention values of 0%, 25%, 50% or 75% and nothing in between,
    which reads as dramatic movement on a heatmap and means nothing.
    """
    lignes = con.execute("""
        with grandes as (
            select cohorte_mois
            from main_marts.fct_retention_cohorte
            where mois_depuis_acquisition = 0 and clients_cohorte >= 30
        )
        select r.cohorte_mois, r.mois_depuis_acquisition, r.taux_retention, r.clients_cohorte
        from main_marts.fct_retention_cohorte r
        join grandes g on g.cohorte_mois = r.cohorte_mois
        where r.mois_depuis_acquisition <= 12
        order by r.cohorte_mois, r.mois_depuis_acquisition
    """).fetchall()

    cohortes = sorted({c for c, _, _, _ in lignes})
    valeurs = {(c, m): t for c, m, t, _ in lignes}
    tailles = {c: n for c, m, _, n in lignes if m == 0}

    cell, gx, gy = 52, 150, 100
    L = gx + cell * 13 + 40
    H = gy + cell * len(cohortes) + 60

    s = entete(L, H, "Retention par cohorte d'acquisition",
               "Cohortes de 30 clients et plus. Les cohortes recentes sont "
               "tronquees par la fin du jeu de donnees, ce n'est pas une chute.")

    for m in range(13):
        s.append(f'<text x="{gx + m * cell + cell / 2}" y="{gy - 10}" font-size="10" '
                 f'fill="{GRIS}" text-anchor="middle">M{m}</text>')

    for i, c in enumerate(cohortes):
        y = gy + i * cell
        s.append(f'<text x="{gx - 12}" y="{y + cell / 2 + 4}" font-size="11" '
                 f'fill="{ENCRE}" text-anchor="end">{c} ({tailles.get(c, 0)})</text>')
        for m in range(13):
            t = valeurs.get((c, m))
            x = gx + m * cell
            if t is None:
                s.append(f'<rect x="{x}" y="{y}" width="{cell - 3}" height="{cell - 3}" '
                         f'fill="#f7f8f9" rx="2"/>')
                continue
            op = 0.10 + 0.90 * min(t, 1.0)
            s.append(f'<rect x="{x}" y="{y}" width="{cell - 3}" height="{cell - 3}" '
                     f'fill="{ACCENT}" fill-opacity="{op:.2f}" rx="2"/>')
            s.append(f'<text x="{x + (cell - 3) / 2}" y="{y + cell / 2 + 4}" font-size="10" '
                     f'fill="{"white" if op > 0.55 else ENCRE}" text-anchor="middle">'
                     f'{t * 100:.0f}</text>')

    s.append(f'<text x="24" y="{H - 14}" font-size="10" fill="{GRIS}">'
             f'Source : main_marts.fct_retention_cohorte | valeurs en % de la cohorte</text>')
    ecrire("retention_cohortes.svg", s)


def qualite_donnees(con) -> None:
    """What was excluded from revenue, and why.

    This is the chart a reviewer should look at first: it quantifies the gap
    between "rows in the file" and "rows that are a sale", which is the part
    of the work that does not show up in a revenue number.
    """
    lignes = con.execute("""
        select
            count(*)                                                  as total,
            count(*) filter (where est_annulation)                    as annulations,
            count(*) filter (where est_hors_produit and not est_annulation) as hors_produit,
            count(*) filter (where not est_annulation and not est_hors_produit
                             and (quantity <= 0 or unit_price <= 0))  as invalides,
            count(*) filter (where est_vente and not est_attribuable) as non_attribuees,
            count(*) filter (where est_vente and est_attribuable)     as ventes
        from main_staging.stg_retail__lines
    """).fetchone()

    total, annul, hors, inval, non_attr, ventes = lignes
    cats = [
        ("Ventes attribuables", ventes, ACCENT),
        ("Ventes sans client", non_attr, ACCENT_PALE),
        ("Annulations (retours)", annul, CHAUD),
        ("Hors produit (port, frais)", hors, "#d9a441"),
        ("Quantite ou prix invalide", inval, GRIS),
    ]

    L, H = 900, 300
    gx, gy, gl, bh = 24, 92, L - 48, 44
    s = entete(L, H, f"Composition des {total:,} lignes brutes".replace(",", " "),
               "Une ligne du fichier n'est pas une vente. L'ecart entre les deux, c'est le travail.")

    x = gx
    for nom, n, couleur in cats:
        w = (n / total) * gl
        s.append(f'<rect x="{x:.1f}" y="{gy}" width="{max(w - 2, 1):.1f}" height="{bh}" '
                 f'fill="{couleur}" rx="2"/>')
        if w > 70:
            s.append(f'<text x="{x + w / 2:.1f}" y="{gy + bh / 2 + 4}" font-size="11" '
                     f'fill="white" text-anchor="middle" font-weight="600">'
                     f'{n / total * 100:.1f}%</text>')
        x += w

    for i, (nom, n, couleur) in enumerate(cats):
        y = gy + bh + 36 + i * 22
        s.append(f'<rect x="{gx}" y="{y - 10}" width="12" height="12" fill="{couleur}" rx="2"/>')
        s.append(f'<text x="{gx + 20}" y="{y}" font-size="12" fill="{ENCRE}">'
                 f'{html.escape(nom)}</text>')
        s.append(f'<text x="{gx + 250}" y="{y}" font-size="12" fill="{GRIS}">'
                 f'{n:,}'.replace(",", " ") + '</text>')

    s.append(f'<text x="24" y="{H - 14}" font-size="10" fill="{GRIS}">'
             f'Source : main_staging.stg_retail__lines, qui ne supprime aucune ligne</text>')
    ecrire("qualite_donnees.svg", s)


if __name__ == "__main__":
    if not DB.exists():
        raise SystemExit(
            f"{DB.name} not found. Run `python ingest/load_raw.py` then "
            f"`dbt build` in dbt/ first."
        )
    OUT.mkdir(exist_ok=True)
    con = duckdb.connect(str(DB), read_only=True)
    print("rendering charts from the warehouse:")
    qualite_donnees(con)
    revenu_mensuel(con)
    segments_rfm(con)
    retention_cohortes(con)
    con.close()
    print("done")
