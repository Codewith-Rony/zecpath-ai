
from parsers.skill_extractor import (
    extract_skills,
    find_spelling_variations,
    load_skill_dictionary,
)


def test_extracts_and_normalizes_skills():
    result = extract_skills(
        "Skills: PyTHON, JavaScript, React.js, MongoDB, teamwork."
    )
    names = {skill["name"] for skill in result["skills"]}

    assert "Python" in names
    assert "JavaScript" in names
    assert "React" in names
    assert "MongoDB" in names
    assert "Teamwork" in names


def test_expands_mern_stack():
    result = extract_skills("Experienced with the MERN stack.")
    names = {skill["name"] for skill in result["skills"]}

    assert "MERN" in names
    assert "MongoDB" in names
    assert "Express.js" in names
    assert "React" in names
    assert "Node.js" in names


def test_skill_confidence_is_valid():
    result = extract_skills("Python and communication skills.")

    assert result["total_skills"] > 0
    for skill in result["skills"]:
        assert 0 <= skill["confidence"] <= 1


def test_spelling_suggestions():
    dictionary = load_skill_dictionary()
    suggestions = find_spelling_variations(
        "I know Pyhton and JavScript", dictionary
    )

    mapping = {
        item["text"]: item["suggested_skill"]
        for item in suggestions
    }

    assert mapping["pyhton"] == "Python"
    assert mapping["javscript"] == "JavaScript"


def test_duplicate_skills_are_removed():
    result = extract_skills("Python, PYTHON, python")
    python_skills = [
        skill for skill in result["skills"]
        if skill["name"] == "Python"
    ]

    assert len(python_skills) == 1
