import pandas as pd
import ollama_service as ollama
from evaluator import evaluate

def read_dataset(filename):
    try:
        df = pd.read_csv(filename)

        print("\n" + "="*60)
        print("DATASET IMPORTED")
        print("="*60)
        
        print(f"File name: {filename}")
        print(f"Rows: {len(df)} | Columns: {len(df.columns)}")
        print(df.columns.tolist())

        return df

    except Exception as e:
        print("Caught exception:", repr(e))

df = read_dataset("BGP Network dataset.csv")

all_rows = ollama.generate_rows(df, n=3)
syn_df = pd.DataFrame(all_rows)

evaluate(df, syn_df)

print("\n" + "="*60)
print("ROW SELECTION")
print("="*60)

counter = 1

for row in all_rows:
    print(str(counter))
    print(row)
    counter += 1

accepted_rows = [
    int(x.strip()) for x in input(
        "\nEnter index numbers of the rows you want to keep, separated by commas: "
    ).split(",")
]

print("\n" + "="*60)
print("DATASET EXPORTED")
print("="*60)

selected = []

for i in accepted_rows:
    selected.append(all_rows[i - 1])

df = pd.concat([df, pd.DataFrame(selected)], ignore_index=True)


output_filename = "BGP Network dataset NEW.csv"
df.to_csv(output_filename, index=False)

print(f"File name: {output_filename}")
print(f"Total rows: {len(df)}")
print(f"Original rows: {len(df) - len(selected)}")
print(f"New generated rows: {len(selected)}")