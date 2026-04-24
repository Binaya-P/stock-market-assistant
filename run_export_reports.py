from analysis.data_loader import load_data_bundle
import os

def export_raw_reports(bundle, output_path="data/exports/"):
    os.makedirs(output_path, exist_ok=True)

    bundle["snapshot_index"].to_csv(f"{output_path}/snapshot_index.csv", index=False)
    bundle["raw_dataset_report"].to_csv(f"{output_path}/raw_dataset_report.csv", index=False)
    bundle["duplicate_contract_report"].to_csv(f"{output_path}/duplicate_contract_report.csv", index=False)

if __name__ == "__main__":
    bundle = load_data_bundle("data/")
    export_raw_reports(bundle)
    print("✅ Reports exported to data/exports/")