# SegPick

**Evidence-based curation of segmented viral genome assemblies.**

SegPick separates measurements such as protein confidence, length plausibility,
coverage, identity, and fragmentation from the later recommendation logic.

## Run without installing

From the repository root:

```bash
python -m segpick.cli doctor
python -m segpick.cli run --config config.yml
```

Command-line values override the YAML file:

```bash
python -m segpick.cli run \
  --config config.yml \
  --outdir alternative_results \
  --preset asm10 \
  --html
```

Configuration precedence is:

```text
built-in defaults < config.yml < command line
```

Boolean values can also be explicitly disabled from the command line:

```bash
python -m segpick.cli run --config config.yml --no-html --no-align --use-existing-paf
```

## Example config.yml

See `config.example.yml`.

## Main outputs

```text
results/
  gene_fastas/
  anchors/
  paf/
  analysis/
  dashboard/
  summary.tsv
  containment_metrics.tsv
  provenance.yml
```
