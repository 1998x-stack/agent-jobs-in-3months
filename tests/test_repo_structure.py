"""Repository-level contracts for the scaffold."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_all_thirty_atomic_skills_have_four_files():
    tracks = list((ROOT / "curriculum").glob("s[123]_*"))
    assert len(tracks) == 3
    paths = []
    for track in tracks:
        paths.extend(p for p in track.iterdir() if p.is_dir())
    assert len(paths) == 30
    for folder in paths:
        for filename in ("README.md", "concept.md", "exercise.py", "check_exercise.py"):
            assert (folder / filename).is_file(), folder / filename

def test_all_three_projects_have_entrypoints():
    expected = {
        "p1_agent_harness": "agent_harness",
        "p2_cloud_runtime": "agent_runtime",
        "p3_eval_learning_lab": "agent_eval",
    }
    for project, package in expected.items():
        root = ROOT / "projects" / project
        assert (root / "README.md").is_file()
        assert (root / "src" / package / "demo.py").is_file()

def test_all_twelve_weekly_sprints_exist():
    for week in range(1, 13):
        assert (ROOT / "weeks" / f"w{week:02d}" / "README.md").is_file()
