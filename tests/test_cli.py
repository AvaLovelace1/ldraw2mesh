import pytest

from ldraw2mesh import cli


def test_missing_library_returns_exit_code_2(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("LDRAW_LIBRARY_PATH", raising=False)
    rc = cli.main(
        [
            str(tmp_path / "in.ldr"),
            "-o",
            str(tmp_path / "out.glb"),
            "--ldraw-library",
            str(tmp_path / "missing"),
        ]
    )
    assert rc == 2
    assert "ldraw.org" in capsys.readouterr().err.lower()


def test_invalid_studs_choice_is_rejected(tmp_path):
    with pytest.raises(SystemExit):  # argparse rejects bad choice with exit code 2
        cli.main(
            [
                str(tmp_path / "in.ldr"),
                "-o",
                str(tmp_path / "o.glb"),
                "--studs",
                "bogus",
            ]
        )


def test_calls_convert_with_parsed_args(tmp_path, monkeypatch):
    calls = {}

    def fake_convert(input, output, *, ldraw_library, scale, studs, gaps):
        calls.update(
            input=input,
            output=output,
            ldraw_library=ldraw_library,
            scale=scale,
            studs=studs,
            gaps=gaps,
        )
        return output

    monkeypatch.setattr(cli, "convert", fake_convert)
    rc = cli.main(
        [
            "in.ldr",
            "-o",
            "out.glb",
            "--ldraw-library",
            "/lib",
            "--scale",
            "0.01",
            "--studs",
            "logo",
            "--gaps",
        ]
    )
    assert rc == 0
    assert calls["scale"] == 0.01
    assert calls["studs"] == "logo"
    assert calls["gaps"] is True
    assert calls["ldraw_library"] == "/lib"
