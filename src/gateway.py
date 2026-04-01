import argparse
import hashlib
import os
import sys # Pour arrêter le script proprement

import pandas as pd
from dotenv import load_dotenv

load_dotenv()
SALT = os.getenv("SECRET_SALT", "")

# --- CONFIGURATION DE GOUVERNANCE ---
# On définit strictement ce qui a le droit d'entrer dans le pipeline
EXPECTED_COLUMNS = [
    'order_id',
    'customer_name',
    'email',
    'ip_address',
    'total_spent',
    'purchase_date'
]


def anonymize_email(email):
    if pd.isna(email):
        return email
    normalized = str(email).strip().lower()
    if SALT:
        normalized = f"{normalized}|{SALT}"
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def resolve_input_path(input_file):
    if os.path.isabs(input_file) and os.path.exists(input_file):
        return input_file

    # If user passes a relative path, try as-is first
    rel_path = os.path.abspath(input_file)
    if os.path.exists(rel_path):
        return rel_path

    script_dir = os.path.dirname(os.path.abspath(__file__))

    candidates = [
        os.path.join(script_dir, input_file),
        os.path.join(script_dir, 'data', input_file),
    ]

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    return input_file


def protect_data(input_file, output_file):
    input_path = resolve_input_path(input_file)
    print(f"🚀 Ingestion du fichier : {input_file} -> {input_path}")

    if not os.path.exists(input_path):
        print(f"❌ Fichier introuvable : {input_path}")
        print("Veuillez vérifier le chemin et réessayer.")
        sys.exit(1)

    df = pd.read_csv(input_path)

    # 🛑 ÉTAPE DE SÉCURITÉ CRITIQUE : Vérification du Schéma (Whitelist)
    current_columns = set(df.columns)
    expected_set = set(EXPECTED_COLUMNS)

    # On cherche les colonnes présentes dans le fichier mais non autorisées
    unknown_columns = current_columns - expected_set

    if unknown_columns:
        print(f"⚠️  ALERTE SÉCURITÉ : Colonnes non autorisées détectées : {unknown_columns}")
        print("❌ Pipeline stoppé pour éviter une fuite de données (Data Leakage).")
        sys.exit(1)

    print("✅ Schéma validé. Aucune colonne suspecte détectée.")

    df['email_hash'] = df['email'].apply(anonymize_email)
    df['customer_name'] = df['customer_name'].apply(lambda x: x[0] + "***" if pd.notna(x) and len(str(x)) > 0 else x)

    df_clean = df.drop(columns=['email', 'ip_address'])
    df_clean.to_csv(output_file, index=False)
    print(f"🔒 Données sécurisées enregistrées dans : {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Privacy-first data gateway')
    parser.add_argument('--input', '-i', default='data/raw_customers.csv', help='Chemin du fichier d’entrée CSV')
    parser.add_argument('--output', '-o', default='clean_data_export.csv', help='Chemin du fichier de sortie CSV')
    args = parser.parse_args()

    protect_data(args.input, args.output)