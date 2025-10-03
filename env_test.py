import env


def test_require_env_ok():
    path = env.require_env("PATH")
    assert ":" in path


def test_require_env_fail(capfd):
    try:
        env.require_env("ASDASDHLKASH")
        assert False, "expected system exit"
    except SystemExit as e:
        captured = capfd.readouterr()
        assert "environment variable ASDASDHLKASH is not specified" in captured.err
        assert e.code == 1
