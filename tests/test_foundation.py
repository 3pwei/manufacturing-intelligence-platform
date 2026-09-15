from manufacturing_analytics import PROJECT_NAME, __version__


def test_project_identity() -> None:
    assert PROJECT_NAME == "Manufacturing Intelligence Platform"
    assert __version__ == "0.1.0"
