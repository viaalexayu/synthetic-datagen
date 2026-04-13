import pandas as pd
import ollama_service as ollama

def read_dataset(filename):
    try:
        df = pd.read_csv(filename)

        print("Dataset loaded successfully!")
        print(f"Rows: {len(df)} | Columns: {len(df.columns)}")

        print("\nColumns:")
        print(df.columns.tolist())

        return df

    except Exception as e:
        print("Caught exception:", repr(e))

df = read_dataset("BGP Network dataset.csv")

rows = ollama.generate_rows(df, n=3)
print("\nGenerated Rows:")
for r in rows:
    print(r)
