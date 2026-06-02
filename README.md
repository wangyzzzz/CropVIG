# CropVIG

CropVIG is the paper-facing code repository for the manuscript:

**Pheno-genomic fusion enables robust trait prediction across multi-scenarios and critical developmental windows in wheat**

The repository implements the three CropVIG prediction models used in the manuscript. CropVIG combines full-season multispectral vegetation-index (VI) time series with genome-wide genotype information to predict wheat traits under realistic deployment shifts, including novel genotypes, novel years, and joint novel-year plus novel-genotype settings.

## Model Family

The public API is centered on three CropVIG models. Two additional inputs are used as baselines in the manuscript: `G` and `12VI sets`.

| Manuscript name | Input representation | Main role |
| --- | --- | --- |
| `G` baseline | GRM-based genomic branch only | Genomic backbone reference |
| `12VI sets` baseline | Full multispectral VI time series | Full phenomic baseline |
| `CropVIG-1` | GRM-GBLUP G branch plus full VI time series | Full VI+G fusion without AP-VI selection |
| `CropVIG-2` | Adaptive phenology-VI selection only | Compact VI-only model |
| `CropVIG-3` | GRM-GBLUP G branch plus AP-VI-selected VI units | Main CropVIG model |

In the final CropVIG model set, the VI branch uses ridge regression, the G branch uses GRM-GBLUP through `sommer`, and VI+G integration is performed by ordinary least-squares late fusion on inner-validation predictions.

## Adaptive Phenology-VI Selection

Adaptive phenology-VI selection (AP-VI) constructs a compact, trait- and scenario-specific VI representation from the full time series.

- The continuous `gdd_rel_heading` time axis is divided into 20 consecutive bins.
- The midpoint of each bin is used as a representative observation time.
- The basic candidate unit is `representative observation time x VI`.
- A local radius of 0 uses only the representative time point; larger radii include neighboring representative time points for the same VI.
- Candidate groups are scored by the mean of the top three absolute feature-trait correlations (`top3_mean`).
- The retained group number and local radius are selected using inner-validation only.

CropVIG-2 selects AP-VI units in a VI-only context. CropVIG-3 re-selects AP-VI units after genomic information is introduced, so its VI subset is not forced to match CropVIG-2.

## Deployment Scenarios

All main analyses are designed around four breeding-relevant prediction scenarios:

| Scenario | Meaning |
| --- | --- |
| `Reference` | Known year and known genotype background |
| `Genotype-Novel` | Known year, novel genotype |
| `Year-Novel` | Novel year, known genotype fold |
| `Joint-Novel` | Novel year and novel genotype fold |

Model selection, AP-VI selection, hyperparameter tuning, and fusion-weight estimation are performed without using the outer-test samples.

## Repository Layout

```text
scripts/cropvig_1.py              # Run/analyze CropVIG-1
scripts/cropvig_2.py              # Run/analyze CropVIG-2
scripts/cropvig_3.py              # Run/analyze CropVIG-3
src/crophg/public/                # Public CropVIG CLI implementations
src/models/result34/              # Shared CropVIG training and AP-VI engine
configs/3_4a/smoke_run_local.yaml # Minimal local smoke config
configs/pipeline_eight_traits_gpu2/
examples/check_cropvig_entrypoints.py
examples/cropvig_minimal_input/   # Tiny fixture for analysis-entry checks
tests/                            # Regression tests for public entrypoints and split logic
```

The Python package is still named `crophg` internally for compatibility with earlier development history, but the public command-line entrypoints are `cropvig-1`, `cropvig-2`, and `cropvig-3`.

## Environment

The manuscript runs were developed in the `PEG2P` environment.

```bash
conda activate PEG2P
```

For a fresh local installation, use editable mode after creating an environment with the required Python scientific stack:

```bash
pip install -e .
```

Additional requirement for G-branch models:

- `Rscript`
- R package `sommer`

`CropVIG-1` and `CropVIG-3` require the GRM-GBLUP G branch. `CropVIG-2` can be used as a VI-only AP-VI model.

## Expected Data Layout

The code expects prepared model inputs under the following layout:

```text
data/processed/
  grm.npy
  grm_index.parquet
  model_inputs_engineered/gdd_rel_heading/
    X_hyperspectral.parquet
    X_genotype.parquet
    X_climate.parquet
    plot_index.parquet
    y.parquet
  splits_4scenarios/
    *.json
  splits_4scenarios_ood_cell/
    *.json
```

The manuscript formal trait set contains seven traits: `ActualYD`, `CM`, `CPM`, `LM`, `PHM`, `Spike`, and `TKW`. Some development configs may include `Water`, but manuscript summaries should exclude it.

## Quick Start

Check that the three public entrypoints can analyze the minimal fixture and resolve model-specific run configs:

```bash
PYTHONPATH=src python examples/check_cropvig_entrypoints.py
```

Run a local smoke task for CropVIG-2:

```bash
PYTHONPATH=src python scripts/cropvig_2.py run \
  --config configs/3_4a/smoke_run_local.yaml \
  --output-dir outputs/experiments/cropvig2_smoke \
  --allow-overwrite
```

Run CropVIG-1 or CropVIG-3 with GBLUP support available:

```bash
PYTHONPATH=src python scripts/cropvig_1.py run \
  --config configs/3_4a/smoke_run_local.yaml \
  --output-dir outputs/experiments/cropvig1_smoke \
  --allow-overwrite

PYTHONPATH=src python scripts/cropvig_3.py run \
  --config configs/3_4a/smoke_run_local.yaml \
  --output-dir outputs/experiments/cropvig3_smoke \
  --allow-overwrite
```

Use more workers for larger runs:

```bash
PYTHONPATH=src python scripts/cropvig_3.py run \
  --config configs/pipeline_eight_traits_gpu2/3_4a_tie001.yaml \
  --output-dir outputs/experiments/cropvig3_full \
  --n-workers 60 \
  --allow-overwrite
```

Smoke results are for pipeline validation only and should not be interpreted as manuscript evidence.

## Analyze Existing Outputs

Each public entrypoint also provides an `analyze` mode. It expects an experiment directory containing `metrics_summary.csv` and `metrics_by_fold.csv`.

```bash
PYTHONPATH=src python scripts/cropvig_1.py analyze \
  --input-dir outputs/experiments/cropvig1_full \
  --output-dir outputs/reports/cropvig1_full

PYTHONPATH=src python scripts/cropvig_2.py analyze \
  --input-dir outputs/experiments/cropvig2_full \
  --output-dir outputs/reports/cropvig2_full

PYTHONPATH=src python scripts/cropvig_3.py analyze \
  --input-dir outputs/experiments/cropvig3_full \
  --output-dir outputs/reports/cropvig3_full
```

After editable installation, the console scripts can be used directly:

```bash
cropvig-1 run --config <config.yaml> --output-dir <experiment_dir>
cropvig-2 run --config <config.yaml> --output-dir <experiment_dir>
cropvig-3 run --config <config.yaml> --output-dir <experiment_dir>
```

## Main Output Files

Typical model runs write:

| File | Description |
| --- | --- |
| `metrics_summary.csv` | Mean outer-test metrics by scenario, trait, input variant, predictor, and optional growth prefix |
| `metrics_by_fold.csv` | Outer-fold-level metrics and audit fields |
| `metrics_by_year.csv` | Year-level aggregation when available |
| `oof_predictions.parquet` | Outer-test predictions |
| `outer_test_inner_ensemble_predictions.parquet` | Inner-validation/fusion prediction records when available |
| `reduced_h_feature_overview.csv` | AP-VI representation overview |
| `reduced_h_feature_spec.csv` | Selected AP-VI feature metadata |
| `feature_overview.csv` | Input feature counts and availability |
| `run_config.yaml` / `run_config.json` | Resolved config and run snapshot |

## Dynamic Prediction

CropVIG also supports growth-prefix prediction. At observation time `t`, the model uses only VI information available from time points 1 through `t`; the G baseline remains unchanged. Each prefix is trained, selected, fused, and evaluated as a separate task rather than being derived by truncating a final model.

The dynamic analysis uses the same model set: `G`, `12VI sets`, `CropVIG-1`, `CropVIG-2`, and `CropVIG-3`.

## Reproducibility Notes

- Outer-test samples are never used for AP-VI selection, hyperparameter tuning, local-radius selection, group-number selection, or VI+G fusion-weight estimation.
- The formal CropVIG configs use `genotype_representation: grm` and `fusion.g_use_gblup: true`.
- The AP-VI scoring target is the raw phenotype `y`.
- Public manuscript summaries should use the seven formal traits and exclude `Water`.

## Citation

If you use this repository, please cite the associated manuscript once available:

```text
Wang et al. Pheno-genomic fusion enables robust trait prediction across multi-scenarios
and critical developmental windows in wheat.
```
