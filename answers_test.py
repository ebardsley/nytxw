# Run with "pipenv run python -m pytest"
import json

import answers


def test_answers():
    input = open("testdata/2025-09-30.json").read()
    expected = open("testdata/2025-09-30.txt").read()
    data = json.loads(input)
    puzzle = data["body"][0]
    assert expected == answers.puzzle_to_string(puzzle)
