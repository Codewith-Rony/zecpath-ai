import json

from utils.file_handler import save_json


def test_save_json(tmp_path):

    data = {
        "candidate": "Rony Thomas",
        "skills": ["Python", "JavaScript"]
    }

    output_file = tmp_path / "test_output.json"

    save_json(data, output_file)

    assert output_file.exists()

    with open(output_file, "r", encoding="utf-8") as file:
        saved_data = json.load(file)

    assert saved_data == data