.PHONY: setup test smoke demo-p1 demo-p2 demo-p3
setup:
	python -m pip install -e '.[dev]'
test:
	python -m pytest
smoke:
	python scripts/validate_structure.py
demo-p1:
	PYTHONPATH=projects/p1_agent_harness/src python -m agent_harness.demo
demo-p2:
	PYTHONPATH=projects/p2_cloud_runtime/src python -m agent_runtime.demo
demo-p3:
	PYTHONPATH=projects/p3_eval_learning_lab/src python -m agent_eval.demo
