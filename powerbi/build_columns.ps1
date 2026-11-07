<#
    GENERATED FILE - do not edit by hand.
    Produced by analysis/generate_model_script.py from the DuckDB marts.

    Declares every column on the Power BI tables, marks the date table, and
    wires the relationships. Tables and measures are created by
    powerbi/build_model.ps1; run that first.

    Requires Power BI Desktop open on the .pbip and `pbi connect` done.
#>

$ErrorActionPreference = "Stop"
$echecs = @()

function Invoke-Pbi {
    param([string]$Etape, [scriptblock]$Commande)
    try {
        $sortie = & $Commande 2>&1
        if ($LASTEXITCODE -ne 0) { throw ($sortie | Out-String) }
    } catch {
        $script:echecs += [pscustomobject]@{ Etape = $Etape; Erreur = ($_ | Out-String).Trim() }
    }
}


Write-Host "dim_date (10 columns)"
Invoke-Pbi "dim_date.date_id" { pbi column create 'date_id' -t 'dim_date' --data-type int64 --source-column 'date_id' --is-key }
Invoke-Pbi "dim_date.date_complete" { pbi column create 'date_complete' -t 'dim_date' --data-type datetime --source-column 'date_complete' }
Invoke-Pbi "dim_date.annee" { pbi column create 'annee' -t 'dim_date' --data-type int64 --source-column 'annee' --format-string '#,##0' }
Invoke-Pbi "dim_date.mois" { pbi column create 'mois' -t 'dim_date' --data-type int64 --source-column 'mois' --format-string '#,##0' }
Invoke-Pbi "dim_date.trimestre" { pbi column create 'trimestre' -t 'dim_date' --data-type int64 --source-column 'trimestre' --format-string '#,##0' }
Invoke-Pbi "dim_date.annee_mois" { pbi column create 'annee_mois' -t 'dim_date' --data-type string --source-column 'annee_mois' }
Invoke-Pbi "dim_date.debut_mois" { pbi column create 'debut_mois' -t 'dim_date' --data-type datetime --source-column 'debut_mois' }
Invoke-Pbi "dim_date.jour_semaine_num" { pbi column create 'jour_semaine_num' -t 'dim_date' --data-type int64 --source-column 'jour_semaine_num' --format-string '#,##0' }
Invoke-Pbi "dim_date.jour_semaine" { pbi column create 'jour_semaine' -t 'dim_date' --data-type string --source-column 'jour_semaine' }
Invoke-Pbi "dim_date.est_weekend" { pbi column create 'est_weekend' -t 'dim_date' --data-type boolean --source-column 'est_weekend' }

Write-Host "dim_client (15 columns)"
Invoke-Pbi "dim_client.client_id" { pbi column create 'client_id' -t 'dim_client' --data-type int64 --source-column 'client_id' --is-key }
Invoke-Pbi "dim_client.pays" { pbi column create 'pays' -t 'dim_client' --data-type string --source-column 'pays' }
Invoke-Pbi "dim_client.date_premiere_commande" { pbi column create 'date_premiere_commande' -t 'dim_client' --data-type datetime --source-column 'date_premiere_commande' }
Invoke-Pbi "dim_client.date_derniere_commande" { pbi column create 'date_derniere_commande' -t 'dim_client' --data-type datetime --source-column 'date_derniere_commande' }
Invoke-Pbi "dim_client.cohorte_mois" { pbi column create 'cohorte_mois' -t 'dim_client' --data-type datetime --source-column 'cohorte_mois' }
Invoke-Pbi "dim_client.duree_vie_jours" { pbi column create 'duree_vie_jours' -t 'dim_client' --data-type int64 --source-column 'duree_vie_jours' --format-string '#,##0' }
Invoke-Pbi "dim_client.nb_commandes" { pbi column create 'nb_commandes' -t 'dim_client' --data-type int64 --source-column 'nb_commandes' --format-string '#,##0' }
Invoke-Pbi "dim_client.nb_lignes" { pbi column create 'nb_lignes' -t 'dim_client' --data-type int64 --source-column 'nb_lignes' --format-string '#,##0' }
Invoke-Pbi "dim_client.quantite_totale" { pbi column create 'quantite_totale' -t 'dim_client' --data-type int64 --source-column 'quantite_totale' --format-string '#,##0' }
Invoke-Pbi "dim_client.valeur_vie" { pbi column create 'valeur_vie' -t 'dim_client' --data-type decimal --source-column 'valeur_vie' --format-string '#,##0.00' }
Invoke-Pbi "dim_client.panier_moyen" { pbi column create 'panier_moyen' -t 'dim_client' --data-type double --source-column 'panier_moyen' }
Invoke-Pbi "dim_client.nb_retours" { pbi column create 'nb_retours' -t 'dim_client' --data-type int64 --source-column 'nb_retours' --format-string '#,##0' }
Invoke-Pbi "dim_client.montant_retourne" { pbi column create 'montant_retourne' -t 'dim_client' --data-type decimal --source-column 'montant_retourne' --format-string '#,##0.00' }
Invoke-Pbi "dim_client.taux_retour" { pbi column create 'taux_retour' -t 'dim_client' --data-type double --source-column 'taux_retour' }
Invoke-Pbi "dim_client.est_recurrent" { pbi column create 'est_recurrent' -t 'dim_client' --data-type boolean --source-column 'est_recurrent' }

Write-Host "dim_produit (9 columns)"
Invoke-Pbi "dim_produit.produit_id" { pbi column create 'produit_id' -t 'dim_produit' --data-type string --source-column 'produit_id' --is-key }
Invoke-Pbi "dim_produit.libelle" { pbi column create 'libelle' -t 'dim_produit' --data-type string --source-column 'libelle' }
Invoke-Pbi "dim_produit.nb_libelles_distincts" { pbi column create 'nb_libelles_distincts' -t 'dim_produit' --data-type int64 --source-column 'nb_libelles_distincts' --format-string '#,##0' }
Invoke-Pbi "dim_produit.nb_lignes_vendues" { pbi column create 'nb_lignes_vendues' -t 'dim_produit' --data-type int64 --source-column 'nb_lignes_vendues' --format-string '#,##0' }
Invoke-Pbi "dim_produit.quantite_totale" { pbi column create 'quantite_totale' -t 'dim_produit' --data-type int64 --source-column 'quantite_totale' --format-string '#,##0' }
Invoke-Pbi "dim_produit.chiffre_affaires" { pbi column create 'chiffre_affaires' -t 'dim_produit' --data-type decimal --source-column 'chiffre_affaires' --format-string '#,##0.00' }
Invoke-Pbi "dim_produit.prix_unitaire_moyen" { pbi column create 'prix_unitaire_moyen' -t 'dim_produit' --data-type double --source-column 'prix_unitaire_moyen' }
Invoke-Pbi "dim_produit.premiere_vente" { pbi column create 'premiere_vente' -t 'dim_produit' --data-type datetime --source-column 'premiere_vente' }
Invoke-Pbi "dim_produit.derniere_vente" { pbi column create 'derniere_vente' -t 'dim_produit' --data-type datetime --source-column 'derniere_vente' }

Write-Host "fct_commande (10 columns)"
Invoke-Pbi "fct_commande.commande_id" { pbi column create 'commande_id' -t 'fct_commande' --data-type string --source-column 'commande_id' --is-key }
Invoke-Pbi "fct_commande.date_id" { pbi column create 'date_id' -t 'fct_commande' --data-type int64 --source-column 'date_id' }
Invoke-Pbi "fct_commande.client_id" { pbi column create 'client_id' -t 'fct_commande' --data-type int64 --source-column 'client_id' }
Invoke-Pbi "fct_commande.est_non_attribuee" { pbi column create 'est_non_attribuee' -t 'fct_commande' --data-type boolean --source-column 'est_non_attribuee' }
Invoke-Pbi "fct_commande.invoice_at" { pbi column create 'invoice_at' -t 'fct_commande' --data-type datetime --source-column 'invoice_at' }
Invoke-Pbi "fct_commande.invoice_date" { pbi column create 'invoice_date' -t 'fct_commande' --data-type datetime --source-column 'invoice_date' }
Invoke-Pbi "fct_commande.pays" { pbi column create 'pays' -t 'fct_commande' --data-type string --source-column 'pays' }
Invoke-Pbi "fct_commande.nb_lignes" { pbi column create 'nb_lignes' -t 'fct_commande' --data-type int64 --source-column 'nb_lignes' --format-string '#,##0' }
Invoke-Pbi "fct_commande.quantite" { pbi column create 'quantite' -t 'fct_commande' --data-type int64 --source-column 'quantite' --format-string '#,##0' }
Invoke-Pbi "fct_commande.montant" { pbi column create 'montant' -t 'fct_commande' --data-type decimal --source-column 'montant' --format-string '#,##0.00' }

Write-Host "fct_ligne_commande (13 columns)"
Invoke-Pbi "fct_ligne_commande.ligne_id" { pbi column create 'ligne_id' -t 'fct_ligne_commande' --data-type string --source-column 'ligne_id' --is-key }
Invoke-Pbi "fct_ligne_commande.commande_id" { pbi column create 'commande_id' -t 'fct_ligne_commande' --data-type string --source-column 'commande_id' }
Invoke-Pbi "fct_ligne_commande.numero_occurrence" { pbi column create 'numero_occurrence' -t 'fct_ligne_commande' --data-type int64 --source-column 'numero_occurrence' --format-string '#,##0' }
Invoke-Pbi "fct_ligne_commande.date_id" { pbi column create 'date_id' -t 'fct_ligne_commande' --data-type int64 --source-column 'date_id' }
Invoke-Pbi "fct_ligne_commande.client_id" { pbi column create 'client_id' -t 'fct_ligne_commande' --data-type int64 --source-column 'client_id' }
Invoke-Pbi "fct_ligne_commande.produit_id" { pbi column create 'produit_id' -t 'fct_ligne_commande' --data-type string --source-column 'produit_id' }
Invoke-Pbi "fct_ligne_commande.invoice_at" { pbi column create 'invoice_at' -t 'fct_ligne_commande' --data-type datetime --source-column 'invoice_at' }
Invoke-Pbi "fct_ligne_commande.invoice_date" { pbi column create 'invoice_date' -t 'fct_ligne_commande' --data-type datetime --source-column 'invoice_date' }
Invoke-Pbi "fct_ligne_commande.quantite" { pbi column create 'quantite' -t 'fct_ligne_commande' --data-type int64 --source-column 'quantite' --format-string '#,##0' }
Invoke-Pbi "fct_ligne_commande.prix_unitaire" { pbi column create 'prix_unitaire' -t 'fct_ligne_commande' --data-type decimal --source-column 'prix_unitaire' --format-string '#,##0.00' }
Invoke-Pbi "fct_ligne_commande.montant" { pbi column create 'montant' -t 'fct_ligne_commande' --data-type decimal --source-column 'montant' --format-string '#,##0.00' }
Invoke-Pbi "fct_ligne_commande.pays" { pbi column create 'pays' -t 'fct_ligne_commande' --data-type string --source-column 'pays' }
Invoke-Pbi "fct_ligne_commande.source_sheet" { pbi column create 'source_sheet' -t 'fct_ligne_commande' --data-type string --source-column 'source_sheet' }

Write-Host "fct_rfm (9 columns)"
Invoke-Pbi "fct_rfm.client_id" { pbi column create 'client_id' -t 'fct_rfm' --data-type int64 --source-column 'client_id' --is-key }
Invoke-Pbi "fct_rfm.recence_jours" { pbi column create 'recence_jours' -t 'fct_rfm' --data-type int64 --source-column 'recence_jours' --format-string '#,##0' }
Invoke-Pbi "fct_rfm.frequence" { pbi column create 'frequence' -t 'fct_rfm' --data-type int64 --source-column 'frequence' --format-string '#,##0' }
Invoke-Pbi "fct_rfm.montant" { pbi column create 'montant' -t 'fct_rfm' --data-type decimal --source-column 'montant' --format-string '#,##0.00' }
Invoke-Pbi "fct_rfm.score_recence" { pbi column create 'score_recence' -t 'fct_rfm' --data-type int64 --source-column 'score_recence' --format-string '#,##0' }
Invoke-Pbi "fct_rfm.score_frequence" { pbi column create 'score_frequence' -t 'fct_rfm' --data-type int64 --source-column 'score_frequence' --format-string '#,##0' }
Invoke-Pbi "fct_rfm.score_montant" { pbi column create 'score_montant' -t 'fct_rfm' --data-type int64 --source-column 'score_montant' --format-string '#,##0' }
Invoke-Pbi "fct_rfm.score_rfm" { pbi column create 'score_rfm' -t 'fct_rfm' --data-type int64 --source-column 'score_rfm' --format-string '#,##0' }
Invoke-Pbi "fct_rfm.segment" { pbi column create 'segment' -t 'fct_rfm' --data-type string --source-column 'segment' }

Write-Host "fct_retention_cohorte (6 columns)"
Invoke-Pbi "fct_retention_cohorte.cohorte_mois" { pbi column create 'cohorte_mois' -t 'fct_retention_cohorte' --data-type datetime --source-column 'cohorte_mois' }
Invoke-Pbi "fct_retention_cohorte.mois_activite" { pbi column create 'mois_activite' -t 'fct_retention_cohorte' --data-type datetime --source-column 'mois_activite' }
Invoke-Pbi "fct_retention_cohorte.mois_depuis_acquisition" { pbi column create 'mois_depuis_acquisition' -t 'fct_retention_cohorte' --data-type int64 --source-column 'mois_depuis_acquisition' --format-string '#,##0' }
Invoke-Pbi "fct_retention_cohorte.clients_cohorte" { pbi column create 'clients_cohorte' -t 'fct_retention_cohorte' --data-type int64 --source-column 'clients_cohorte' --format-string '#,##0' }
Invoke-Pbi "fct_retention_cohorte.clients_actifs" { pbi column create 'clients_actifs' -t 'fct_retention_cohorte' --data-type int64 --source-column 'clients_actifs' --format-string '#,##0' }
Invoke-Pbi "fct_retention_cohorte.taux_retention" { pbi column create 'taux_retention' -t 'fct_retention_cohorte' --data-type double --source-column 'taux_retention' }

Write-Host "`nRefreshing"
Invoke-Pbi "refresh dim_date" { pbi table refresh dim_date }
Invoke-Pbi "refresh dim_client" { pbi table refresh dim_client }
Invoke-Pbi "refresh dim_produit" { pbi table refresh dim_produit }
Invoke-Pbi "refresh fct_commande" { pbi table refresh fct_commande }
Invoke-Pbi "refresh fct_ligne_commande" { pbi table refresh fct_ligne_commande }
Invoke-Pbi "refresh fct_rfm" { pbi table refresh fct_rfm }
Invoke-Pbi "refresh fct_retention_cohorte" { pbi table refresh fct_retention_cohorte }

Write-Host "`nDate table"
Invoke-Pbi "mark dim_date" { pbi table mark-date dim_date --date-column date_complete }

Write-Host "`nRelationships"
Invoke-Pbi "fct_ligne_commande.date_id -> dim_date.date_id" { pbi relationship create --from-table fct_ligne_commande --from-column date_id --to-table dim_date --to-column date_id }
Invoke-Pbi "fct_ligne_commande.client_id -> dim_client.client_id" { pbi relationship create --from-table fct_ligne_commande --from-column client_id --to-table dim_client --to-column client_id }
Invoke-Pbi "fct_ligne_commande.produit_id -> dim_produit.produit_id" { pbi relationship create --from-table fct_ligne_commande --from-column produit_id --to-table dim_produit --to-column produit_id }
Invoke-Pbi "fct_commande.date_id -> dim_date.date_id" { pbi relationship create --from-table fct_commande --from-column date_id --to-table dim_date --to-column date_id }
Invoke-Pbi "fct_commande.client_id -> dim_client.client_id" { pbi relationship create --from-table fct_commande --from-column client_id --to-table dim_client --to-column client_id }
Invoke-Pbi "fct_rfm.client_id -> dim_client.client_id" { pbi relationship create --from-table fct_rfm --from-column client_id --to-table dim_client --to-column client_id }

Write-Host "`n--------------------------------------------------"
if ($echecs.Count -eq 0) {
    Write-Host "All steps succeeded." -ForegroundColor Green
} else {
    Write-Host "$($echecs.Count) step(s) failed:" -ForegroundColor Yellow
    $echecs | Select-Object -First 12 | ForEach-Object {
        Write-Host "`n  * $($_.Etape)" -ForegroundColor Yellow
        Write-Host "    $(($_.Erreur -split "`n")[0..1] -join ' ')"
    }
}
