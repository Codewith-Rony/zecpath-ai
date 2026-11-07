# Zecpath AI — Day 17 Synthetic Resume Dataset

This dataset contains 12 entirely fictional candidate resumes created for ATS testing.

## Composition
- 3 tech fresher profiles
- 3 tech senior profiles
- 3 non-tech fresher profiles
- 3 non-tech senior profiles

The resumes are split across PDF and DOCX formats to exercise both parsers.

## Important testing guidance
1. These profiles are synthetic. Names, contact details, education providers, employers, projects and achievements are fictional.
2. All email addresses use the reserved `.test` domain and phone numbers use clearly fictional `90000-100xx` examples. Do not contact them.
3. Do not treat the resume's own target title as proof that the candidate is suitable for a role.
4. For each experiment, select a job description first, then have a human reviewer assess the resume against that job description using a written rubric.
5. Record the human decision before looking at the ATS recommendation where practical, to reduce confirmation bias.
6. Keep this dataset in a test-only folder. Do not mix it with real applicant records.

## Files
- `resumes/`: 12 candidate resumes organized by profile category.
- `candidate_index.csv`: candidate metadata and file paths.
- `manual_evaluation_template.csv`: blank template for human review.

## Suggested human-review labels
- `suitable`: meets the pre-defined minimum requirements for the selected role.
- `not_suitable`: does not meet the pre-defined minimum requirements.
- `borderline`: insufficient or ambiguous evidence; review manually.

For precision and recall, decide in advance whether `borderline` is excluded from binary metrics or counted as a separate manual-review outcome. Do not silently count it as a positive or negative.
