import env


def test_require_env_ok():
    path = env.require_env("PATH")
    assert ":" in path


def test_require_env_fail():
    try:
        env.require_env("ASDASDHLKASH")
        assert False, "expected system exit"
    except SystemExit as e:
        assert e.code == 1
