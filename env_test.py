import pathlib

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


def test_envrc(mocker):
    mocker.patch("env.__CACHE", new=None)
    mocker.patch("env.RCFILE", new=pathlib.Path("testdata/envrc"))
    assert env.getenv("FOO") == "bar"
    assert env.getenv("BAZ") == "baz"
    assert env.getenv("BAT") == "bat"
    assert env.getenv("COOKIE") == "0^CB4SLQj6xJnJB..._WJO9m9lcEBQ=="
