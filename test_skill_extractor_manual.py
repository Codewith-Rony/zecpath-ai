
from parsers.skill_extractor import extract_skills, find_spelling_variations, load_skill_dictionary


sample_resume = """
Skills: Python, JavaScript, React.js, Node.js, MongoDB, GitHub.
I worked with the MERN stack and have strong communication and teamwork skills.
I also know Figma and UI/UX design.
"""

dictionary = load_skill_dictionary()
result = extract_skills(sample_resume)

print("Extracted skills:")
for skill in result["skills"]:
    print(skill)

print("\nTotal skills:", result["total_skills"])

print("\nSpelling suggestions:")
print(find_spelling_variations("I know Pyhton and JavScript", dictionary))
