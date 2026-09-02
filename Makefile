.PHONY: test assurance raw manifest

test:
	python -m pytest -q

assurance:
	bash scripts/run_research_assurance.sh

raw:
	python scripts/verify_raw_inputs.py --require-present

manifest:
	python scripts/build_publication_manifest.py
