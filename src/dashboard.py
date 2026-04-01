import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os

def generate_secure_report(data_file):
    print(f"📊 Génération du rapport à partir de : {data_file}")
    
    # Vérification de sécurité : Le fichier existe-t-il ?
    if not os.path.exists(data_file):
        print(f"❌ ERREUR : Le fichier sécurisé {data_file} est introuvable.")
        print("Veuillez d'abord exécuter gateway.py pour générer les données anonymisées.")
        sys.exit(1)

    # Chargement des données NETTOYÉES
    df = pd.read_csv(data_file)

    # Vérification de sécurité (Double Check) : Y a-t-il des données en clair par erreur ?
    if 'email' in df.columns or 'ip_address' in df.columns:
         print("🛑 ALERTE CRITIQUE : Des données non cryptées (PII) ont été détectées dans le fichier source.")
         print("Génération du rapport annulée par sécurité.")
         sys.exit(1)

    # --- ANALYSE BUSINESS ---
    # On groupe les ventes par date pour voir le chiffre d'affaires quotidien
    daily_revenue = df.groupby('purchase_date')['total_spent'].sum().reset_index()

    # --- VISUALISATION (Style Professionnel) ---
    # Configuration du style graphique
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(10, 6))

    # Création du graphique en barres
    ax = sns.barplot(
        x='purchase_date', 
        y='total_spent', 
        data=daily_revenue, 
        palette="viridis"
    )

    # Ajout des titres et labels professionnels
    plt.title("Chiffre d'Affaires Quotidien (Données Anonymisées)", fontsize=16, pad=20)
    plt.xlabel('Date de Transaction', fontsize=12)
    plt.ylabel('Revenus Générés ($)', fontsize=12)

    # Ajout des montants exacts au-dessus des barres
    for p in ax.patches:
        ax.annotate(f"${p.get_height():.2f}", 
                    (p.get_x() + p.get_width() / 2., p.get_height()), 
                    ha='center', va='center', 
                    xytext=(0, 9), 
                    textcoords='offset points')

    # Ajustement de la mise en page
    plt.tight_layout()

    # Sauvegarde du graphique en image
    output_image = 'secure_revenue_report.png'
    plt.savefig(output_image, dpi=300)
    print(f"✅ Rapport généré avec succès : {output_image}")
    
    # Optionnel : Afficher le graphique à l'écran
    # plt.show()

if __name__ == "__main__":
    generate_secure_report('clean_data_export.csv')