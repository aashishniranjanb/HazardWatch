import os
import glob
import json
import csv
import pandas as pd
import numpy as np

def run_dataset_audit():
    csv_files = glob.glob('*.csv')
    audit_data = {}
    inventory_rows = []

    for filepath in sorted(csv_files):
        filename = os.path.basename(filepath)
        size_bytes = os.path.getsize(filepath)

        df = None
        malformed_count = 0

        # Specialized handling for headerless or malformed files
        if filename in ['Air Quality dataset for ADL classification.csv', 'gsalc.csv']:
            try:
                df = pd.read_csv(filepath, header=None, low_memory=False)
            except Exception as e:
                df = None
        elif filename == 'log_temp.csv':
            try:
                df = pd.read_csv(filepath, header=None, names=['Date', 'Time', 'Temp', 'Humidity'])
            except Exception:
                df = None
        elif filename == 'mq2_data.csv':
            # Handle tokenizing error at line 15996 gracefully
            valid_rows = []
            header = None
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f)
                header = next(reader)
                for line_idx, row in enumerate(reader):
                    if len(row) == len(header):
                        valid_rows.append(row)
                    else:
                        malformed_count += 1
            df = pd.DataFrame(valid_rows, columns=header)
            # Cast numeric columns
            for col in ['ADC', 'Voltage', 'Rs', 'R0', 'Ratio', 'PPM']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            try:
                df = pd.read_csv(filepath, low_memory=False)
            except Exception as e:
                df = None

        if df is None:
            audit_data[filename] = {'status': 'UNREADABLE'}
            continue

        row_count, col_count = df.shape
        columns = [str(c) for c in df.columns.tolist()]
        missing_count = int(df.isna().sum().sum())
        missing_per_col = {str(k): int(v) for k, v in df.isna().sum().items() if v > 0}
        duplicate_rows = int(df.duplicated().sum())

        # Check for sensor channels
        col_str = ' '.join(columns).lower()
        has_mq2 = 'mq2' in col_str or 'mq-2' in col_str or (filename == 'mq2_data.csv')
        has_mq135 = 'mq135' in col_str or 'mq-135' in col_str
        has_mq7 = 'mq7' in col_str or 'mq-7' in col_str
        has_dht = 'temp' in col_str or 'hum' in col_str or 'temparature' in col_str

        # Label checking
        labels_found = []
        label_col = None
        for candidate in ['Gas', 'label', 'Label', 'Class', 'Alcohol Presence', 'class', 6]:
            if candidate in df.columns:
                label_col = str(candidate)
                val_counts = df[candidate].value_counts().to_dict()
                labels_found = {str(k): int(v) for k, v in val_counts.items()}
                break

        # Determine hardware compatibility
        compat_category = "INCOMPATIBLE"
        if has_mq2 and has_mq135:
            compat_category = "MQ2_MQ135_DUAL"
        elif has_mq2:
            compat_category = "MQ2_ONLY"
        elif has_mq135:
            compat_category = "MQ135_ONLY"
        elif has_dht:
            compat_category = "ENVIRONMENTAL_ONLY"

        audit_data[filename] = {
            'filename': filename,
            'size_bytes': size_bytes,
            'total_rows': row_count,
            'total_cols': col_count,
            'columns': columns if col_count <= 25 else columns[:10] + [f'... and {col_count - 10} more'],
            'missing_values': missing_count,
            'missing_details': missing_per_col,
            'duplicate_rows': duplicate_rows,
            'malformed_rows': malformed_count,
            'has_mq2': has_mq2,
            'has_mq135': has_mq135,
            'has_mq7': has_mq7,
            'has_dht': has_dht,
            'label_column': label_col,
            'label_distribution': labels_found,
            'compatibility_profile': compat_category,
        }

        inventory_rows.append({
            'filename': filename,
            'size_kb': round(size_bytes / 1024, 2),
            'rows': row_count,
            'cols': col_count,
            'has_mq2': 'YES' if has_mq2 else 'NO',
            'has_mq135': 'YES' if has_mq135 else 'NO',
            'has_mq7': 'YES' if has_mq7 else 'NO',
            'has_dht': 'YES' if has_dht else 'NO',
            'label_col': label_col or 'NONE',
            'label_count': len(labels_found) if labels_found else 0,
            'profile': compat_category,
        })

    # Save JSON audit
    with open('ml/config/dataset_audit.json', 'w') as f:
        json.dump(audit_data, f, indent=2)

    # Save CSV inventory
    df_inv = pd.DataFrame(inventory_rows)
    df_inv.to_csv('ml/config/dataset_inventory.csv', index=False)
    print(f'Audit complete. Processed {len(inventory_rows)} datasets.')
    return audit_data, df_inv

if __name__ == '__main__':
    run_dataset_audit()
