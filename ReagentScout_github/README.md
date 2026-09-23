# MolDash 🧪

**ReagentScout**

Identify molecules. Understand safety. Find trusted suppliers.

ReagentScout is a Streamlit app that helps users identify molecules, generate and validate SMILES strings, retrieve PubChem data, and visualize molecular structures in 2D and 3D.
---

## What MolDash Does

MolDash provides a simple workflow:

1. Describe a molecule in natural language
2. Identify the likely molecule name
3. Generate a canonical SMILES string
4. Validate the SMILES string with RDKit
5. Display a 2D structural diagram
6. Generate a 3D ball-and-stick molecular visualization

---

## Demo

Screenshot or GIF coming soon.

Recommended file location:

```text
assets/demo.gif
```

Then display it here with:

```markdown
![MolDash Demo](assets/demo.gif)
```

---

## Features

* Natural-language molecule identification
* SMILES string generation
* RDKit-based SMILES validation
* 2D molecular structure rendering
* 3D ball-and-stick visualization
* Interactive 3D HTML export
* OpenAI model selection
* Modular Python codebase

---

## Tech Stack

* Python
* Streamlit
* OpenAI API
* RDKit
* PyVista
* NumPy

---

## Project Structure

```text
moldash/
  app.py
  config.py
  prompts.py
  state.py
  llm_service.py
  chemistry_utils.py
  visualization.py
  export_molecule_html.py
  requirements.txt
  README.md
  assets/
```

---

## Run Locally

Clone the repository and install the required packages:

```bash
pip install -r requirements.txt
```

Run the Streamlit app:

```bash
streamlit run app.py
```

---

## API Key

MolDash uses the OpenAI API for molecule-name identification and SMILES generation.

For local development, provide your OpenAI API key using your preferred local method. Do not hard-code API keys into the public repository.

---

## Example Molecules to Try

* Caffeine
* Aspirin
* Ibuprofen
* Benzene
* Ethanol
* Fluoxetine
* Taxol

---

## Important Disclaimer

MolDash is an educational and portfolio demo project.

It is not intended for clinical, regulatory, pharmaceutical, safety-critical, or production scientific use. Generated molecule names and SMILES strings should be independently verified using trusted chemistry databases and expert review.

---

## Why This Project Exists

MolDash is a demonstration of how modern AI tools can be combined with cheminformatics and scientific visualization libraries to create useful, interactive chemistry applications.

The project combines:

* AI-assisted scientific search
* Molecular representation with SMILES
* RDKit cheminformatics
* 2D and 3D visualization
* Streamlit-based product design

---

## Author

Created by Carl Barrelet.

---
