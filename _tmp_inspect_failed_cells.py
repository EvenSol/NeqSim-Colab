import json
from pathlib import Path

files = [
    "notebooks/gasvaluechain/energystatistics.ipynb",
    "notebooks/gasvaluechain/useOfNaturalGas.ipynb",
    "notebooks/thermodynamics/EquationsOfState.ipynb",
    "notebooks/thermodynamics/ChemicalEquilibrium.ipynb",
    "notebooks/thermodynamics/c1_co2_h2s_flash_test.ipynb",
]
needles = ["read_csv", "http", "umr", "google.colab", "for ", "while "]

for file_name in files:
    print("\n==== " + file_name)
    notebook = json.loads(Path(file_name).read_text(encoding="utf-8"))
    for index, cell in enumerate(notebook.get("cells", []), start=1):
        source = cell.get("source", "")
        if isinstance(source, list):
            source = "\n".join(source)
        if cell.get("cell_type") == "code" and any(needle in source for needle in needles):
            cell_id = cell.get("id") or cell.get("metadata", {}).get("id")
            print(f"-- cell {index} id={cell_id}")
            print(source[:3000].replace("\r", ""))
            print()
