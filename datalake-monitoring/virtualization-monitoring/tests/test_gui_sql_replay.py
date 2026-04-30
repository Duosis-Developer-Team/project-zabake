from pathlib import Path

from sql_loader.gui_replay import load_gui_sql_strings


def test_gui_sql_replay_loads_expected_strings():
    repo = Path(__file__).resolve().parents[4] / "Datalake-Platform-GUI"
    sql_map = load_gui_sql_strings(str(repo))
    assert "CLASSIC_METRICS" in sql_map
    assert "SELECT" in sql_map["CLASSIC_METRICS"].upper()
