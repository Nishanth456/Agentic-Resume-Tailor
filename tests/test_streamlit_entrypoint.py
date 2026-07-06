from src.ui.app import main


def test_ui_entrypoint_is_callable():
    assert callable(main)
