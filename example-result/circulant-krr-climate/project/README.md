# circulant-krr-climate

Research project (epic: /workspace/epics/circulant-krr-climate).

PRIMARY research question (algorithmic/methodological ML innovation):
exact kernel ridge regression on regular-grid climate fields via
block-circulant structure exploitation and the FFT - O(N log N) training
and prediction, O(N) memory, no explicit N-by-N kernel matrix - implemented
CPU-only (NumPy/SciPy/scikit-learn) on consumer hardware.

Experimental substrate (AI-for-climate): sea-surface temperature anomaly
fields for masked-field reconstruction (gap-filling) and Nino3.4 (ENSO)
index regression.

Baselines: scikit-learn exact KRR (subsampled), Nystrom approximation,
Random Fourier Features. Honest block cross-validation, calibration,
resource accounting (wall-clock, peak RSS, flops/bytes).

Deliverable: compiled 4-page PDF (main text excluding references),
NeurIPS-workshop LaTeX via tectonic: paper/main.pdf.

## Layout

- docs/literature-review/   stage 1 artifact (review.md)
- ideas/                    stage 2 artifact (proposal-final.json; proposal-v* drafts)
- ideas/experiments/        stage 3 artifact (experiment-plan.json)
- scripts/                  reproducible CPU-only analysis code
- results/                  stage 4/5 artifacts (*_metrics.json, summary json)
- paper/                    stage 6 artifact (main.tex -> main.pdf via compile.sh)
- archive/                  superseded/backup artifacts

## Run bookkeeping

- Makefile target `run-all`: runs the full experiment pipeline end-to-end
  within the 90-minute wall-clock budget.
