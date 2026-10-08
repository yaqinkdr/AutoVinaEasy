```markdown
# AutoVinaEasy

**Automated Molecular Docking Pipeline with Adaptive Search Grid Box Protocol for Medical Research**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![DOI](https://img.shields.io/badge/DOI-10.xxxx%2Fxxxxx-blue)](https://doi.org/10.xxxx/xxxxx)

---

## 📖 Overview

**AutoVinaEasy** is an open-source, reproducible virtual screening pipeline designed for medical researchers, pharmacologists, and clinicians who require automated molecular docking without specialized bioinformatics training.

The pipeline implements an **adaptive grid box protocol** based on the ligand's radius of gyration (Rg), following the empirically optimized relationship of **2.9 × Rg** established by Feinstein & Brylinski (2015). This eliminates user-dependent bias in search space selection—a critical source of irreproducibility in blind docking studies (Chen, 2015).

AutoVinaEasy functions as a **grounded hypothesis generator**: it produces ranked ligand candidates, deterministic interaction profiles, and structured reports suitable for downstream AI/LLM interpretation, all while maintaining full traceability and reproducibility.

> **Note:** AutoVinaEasy is a computational tool for preliminary screening. Results require experimental validation before any clinical or biological conclusion.

---

## ✨ Key Features

- **Automated preparation** — Receptor (PDB → PDBQT) and ligand (SMILES/SDF/MOL2 → PDBQT 3D) using OpenBabel, RDKit, and Meeko
- **Adaptive grid box** — Protein envelope + 2.9 × Rg per ligand, with geometric center at protein centroid
- **Parallelized docking** — AutoDock Vina executed in parallel via ThreadPoolExecutor (default: 8 workers)
- **Deterministic interaction analysis** — Euclidean distance-based (d ≤ 4.0 Å), no probabilistic AI inference
- **Structured reports** — JSON, CSV, and human-readable TXT summary; includes AI-ready prompt
- **Grounded AI input** — Contact residues are extracted mathematically, safe from LLM hallucination (Roomi et al., 2025)
- **Reproducible by design** — All parameters logged; configurable via GUI
- **Cross-platform** — Windows, Linux, macOS

---

## 🚀 Quick Start

### Prerequisites

| Software | Version | Purpose |
| :--- | :--- | :--- |
| Python | 3.9+ | Pipeline core |
| [AutoDock Vina](https://vina.scripps.edu/) | 1.1.2 or 1.2.x | Docking engine |
| [OpenBabel](https://openbabel.org/) | 3.x | Format conversion |
| [RDKit](https://www.rdkit.org/) | 2022+ | Ligand 3D generation |

### Installation

```bash
# Clone repository
git clone https://github.com/your-username/AutoVinaEasy.git
cd AutoVinaEasy

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Pipeline

```bash
python autovinaeasy.py
```

1. **Input Protein** — Select a `.pdb` file
2. **Input Ligand Folder** — Select folder containing ligand files (`.sdf`, `.mol2`, `.smi`, `.ism`)
3. **Output Folder** — Select where results will be saved
4. **Configure Options** — Auto grid box, exhaustiveness, prepare ligands
5. **Click START SCREENING**

> **First run:** Open **Settings** to specify the path to `vina` and `obabel` if they are not in your system PATH.

---

## 📁 Output Structure

```
vina_screening_<protein>/
├── <protein>.pdbqt                    # Prepared receptor
├── ligands_pdbqt/                     # Prepared ligands
│   ├── ligand1.pdbqt
│   └── ...
├── output/                            # Docking output
│   ├── ligand1_out.pdbqt
│   ├── ligand1.log
│   └── ...
├── complexes/                         # Protein-ligand complexes
│   ├── ligand1_<protein>.pdb
│   └── ...
├── summary_results.json               # Full results (machine-readable)
├── top_ligands.csv                    # Top 10 ranked ligands
├── hotspot_frequency.csv              # Contact residue frequency
├── prompt_for_ai.txt                  # Grounded prompt for LLM
├── <protein>_laporan.txt              # Human-readable summary
└── failed_docking.txt                 # Ligands that failed (if any)
```

---

## 🧪 Methodology

### Grid Box Protocol

The grid box center is the geometric center of the protein:

$$ \text{Center}_d = \frac{\min(d_i) + \max(d_i)}{2} $$

The box size is calculated adaptively per ligand:

$$ \text{Box Size}_d = \text{Protein Envelope}_d + 2.9 \times R_g $$

where $R_g$ is the ligand's radius of gyration:

$$ R_g = \sqrt{\frac{1}{N} \sum_{k=1}^{N} \left| \vec{r}_k - \vec{r}_{\text{center}} \right|^2} $$

This protocol follows Feinstein & Brylinski (2015), who demonstrated that 2.9 × Rg maximizes docking accuracy for AutoDock Vina.

### Interaction Analysis

Protein-ligand contacts are identified deterministically using Euclidean distance:

$$ d = \sqrt{(x_p - x_l)^2 + (y_p - y_l)^2 + (z_p - z_l)^2} $$

Residues with any atom within d ≤ 4.0 Å are reported as contact residues.

---

## 📊 Benchmarking

AutoVinaEasy has been benchmarked on 10 DUD-E targets:

| Target | EF1% | ROC-AUC | BEDROC (α=20) |
|--------|------|---------|---------------|
| EGFR   | —    | —       | —             |
| CDK2   | —    | —       | —             |
| FXA    | —    | —       | —             |
| HDAC2  | —    | —       | —             |
| GHSR   | —    | —       | —             |
| AA2AR  | —    | —       | —             |
| PPARG  | —    | —       | —             |
| AR     | —    | —       | —             |
| KCNQ1  | —    | —       | —             |
| TRPV1  | —    | —       | —             |

> **Full benchmark results:** See `benchmark/` folder.

---

## 🛠️ Configuration

AutoVinaEasy saves settings to `vina_settings.json`:

```json
{
  "vina_path": "C:/path/to/vina.exe",
  "obabel_path": "C:/path/to/obabel.exe"
}
```

| Option | Description | Default |
| :--- | :--- | :--- |
| **Auto Grid Box** | Adaptive 2.9 × Rg + protein envelope | Enabled |
| **Auto Add H** | Add hydrogens and fix bonds | Enabled |
| **Prepare Ligands** | Convert ligands to PDBQT | Enabled |
| **Exhaustiveness** | Vina search thoroughness | 32 |
| **Hotspot from Top** | Hotspot frequency from top 20 only | Disabled |

---

## ⚠️ Limitations

- **Rigid receptor** — Protein flexibility is not modeled (Chen, 2015)
- **Scoring function** — AutoDock Vina's empirical scoring is an approximation of binding free energy
- **Rg approximation** — Assumes ligand's Rg adequately represents conformational space
- **Benchmark scope** — Currently validated on 10 DUD-E targets
- **Not a substitute for experiments** — All predictions require in vitro/in vivo validation

---

## 📚 Citation

If you use AutoVinaEasy in your research, please cite:

```bibtex
@article{yaqin2026autovinaeasy,
  title={AutoVinaEasy: A Reproducible Automated Docking Pipeline with an Adaptive Grid Box Protocol for Preliminary Ligand Screening in Medical Research},
  author={Yaqin, A. N. and others},
  journal={Smart Medical Journal},
  year={2026},
  volume={},
  pages={},
  doi={}
}
```

### Key References

- Feinstein, W. P., & Brylinski, M. (2015). Calculating an optimal box size for ligand docking and virtual screening. *Journal of Cheminformatics, 7*(1), 18.
- Trott, O., & Olson, A. J. (2010). AutoDock Vina: Improving the speed and accuracy of docking. *Journal of Computational Chemistry, 31*(2), 455–461.
- O'Boyle, N. M., et al. (2011). Open Babel: An open chemical toolbox. *Journal of Cheminformatics, 3*(1), 33.
- Mysinger, M. M., et al. (2012). Directory of Useful Decoys, Enhanced (DUD-E). *Journal of Medicinal Chemistry, 55*(14), 6582–6594.
- Chen, Y.-C. (2015). Beware of docking! *Trends in Pharmacological Sciences, 36*(2), 71–80.
- Roomi, M. S., et al. (2025). Docking in the dark: Insights into blind docking. *Pharmaceuticals, 18*(12), 1777.

See `CITATION.cff` for full list.

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

For major changes, please open an issue first.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **AutoDock Vina** — Trott & Olson (2010)
- **OpenBabel** — O'Boyle et al. (2011)
- **RDKit** — Landrum (2016)
- **DUD-E** — Mysinger et al. (2012)
- Smart Medical Journal, Faculty of Medicine, Universitas Sebelas Maret (UNS)

---

## 📬 Contact

- **Author:** A. N. Yaqin
- **Institution:** Universitas Sebelas Maret (UNS)
- **Email:** [your-email@example.com]
- **Issues:** [GitHub Issues](https://github.com/your-username/AutoVinaEasy/issues)

---

## 🔗 Related Resources

- [AutoDock Vina Documentation](https://vina.scripps.edu/manual/)
- [OpenBabel Documentation](https://openbabel.org/docs/)
- [DUD-E Dataset](https://dude.docking.org/)
- [Feinstein & Brylinski (2015)](https://doi.org/10.1186/s13321-015-0067-5)

---

<p align="center">
  <i>AutoVinaEasy — Bridging computational complexity and practical accessibility for medical research</i>
</p>
```

---

## 📝 File Tambahan yang Perlu Kamu Buat

### `requirements.txt`
```
numpy>=1.24.0
pandas>=2.0.0
biopython>=1.81
customtkinter>=5.2.0
rdkit>=2023.9.1
Pillow>=10.0.0
```

### `LICENSE` (MIT)
```
MIT License

Copyright (c) 2026 A. N. Yaqin

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### `CITATION.cff`
```yaml
cff-version: 1.2.0
message: "If you use AutoVinaEasy in your research, please cite it as below."
authors:
  - family-names: "Yaqin"
    given-names: "A. N."
    affiliation: "Universitas Sebelas Maret"
title: "AutoVinaEasy: A Reproducible Automated Docking Pipeline with Adaptive Grid Box Protocol"
version: 1.0.0
doi: 10.5281/zenodo.xxxxxxx
date-released: 2026-01-01
license: MIT
```

---
