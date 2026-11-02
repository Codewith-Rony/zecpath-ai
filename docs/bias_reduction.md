
# Fairness, Normalization & Bias Reduction

## 1. Objective

The objective of this document is to describe the fairness improvements introduced in Zecpath AI during Day 15.

The improvements focus on:
- Standardizing resume text before evaluation.
- Reducing unnecessary exposure of personal identifiers.
- Identifying potential sources of bias in resume scoring.
- Improving transparency and encouraging human review.

These improvements aim to support fairer and more consistent candidate evaluation. They do not guarantee a completely unbiased recruitment system.

## 2. Resume Normalization

### Implementation

A resume normalization utility was introduced in:

`parsers/resume_normalizer.py`

The `normalize_resume_text()` function performs the following operations:

- Applies Unicode NFKC normalization.
- Standardizes Windows and Unix line endings.
- Removes unwanted control characters.
- Normalizes repeated whitespace.
- Preserves meaningful line breaks and section boundaries.
- Removes excessive blank lines.

### Benefits

Different resume formatting styles can produce inconsistent text during extraction.

Normalization provides a more consistent text representation before skill extraction and evaluation.

The normalizer is integrated into `scoring/skill_matcher.py` before resume skill extraction.

## 3. Privacy Masking

### Implementation

A privacy masking utility was introduced in:

`parsers/privacy_masker.py`

The `mask_personal_attributes()` function currently masks:

| Attribute | Replacement |
|---|---|
| Email address | [EMAIL] |
| Phone number | [PHONE] |

### Integration

Privacy masking is integrated into the main ATS evaluation pipeline in `main_ats_scorer.py`.

The original extracted resume text is passed through the masking utility before being used for:

- Skill matching.
- Experience relevance evaluation.
- Education alignment evaluation.
- Semantic similarity evaluation.

### Benefits

- Reduces unnecessary exposure of common contact identifiers during candidate evaluation.
- Preserves technical skills, education and experience information.
- Applies masking consistently across the main ATS evaluation stages.

### Limitations

The current implementation does not detect or mask every personal identifier.

It does not reliably mask:
- Candidate names.
- Residential addresses.
- Age or date of birth.
- Gender-related information.
- Other indirectly identifying details.

Therefore, this is basic personal-identifier masking, not complete anonymization or a guarantee against bias.

## 4. Keyword Dependency

The existing skill matcher uses the shared skill dictionary and extracts skills from resume and job-description text.

Required skills contribute 80% of the skill-match score, while preferred skills contribute 20%, when both categories are available.

### Potential fairness concern

Candidates may describe equivalent skills using different terminology.

For example:
- JavaScript and JS.
- Machine Learning and ML.
- PostgreSQL and Postgres.

Exact matching can fail to recognize equivalent terminology when the relevant aliases are not represented in the skill dictionary.



### Existing Improvements

The existing skill dictionary supports alternative terminology for several technical skills.

Additional test coverage was introduced to verify that:
- Common skill aliases are recognized.
- Unrelated words are not incorrectly identified as skills.
- Skills inferred from broader terms such as MERN are distinguished from directly mentioned skills.

Directly mentioned skills retain a higher confidence value than inferred skills.

### Remaining Limitations

The current matcher still relies primarily on dictionary-based keyword matching. Full semantic skill equivalence and context-aware matching have not yet been implemented.

### Proposed improvements

- Expand the skill dictionary with verified aliases.
- Introduce semantic skill matching.
- Evaluate equivalent skill descriptions consistently.
- Avoid treating incidental keyword mentions as confirmed requirements.
- Review fallback extraction from the full job description.

These improvements require further implementation and testing.

## 5. Scoring Fairness and Missing Components

The ATS scorer uses weighted components:

| Component | Default Weight |
|---|---:|
| Skill Match | 40% |
| Experience Relevance | 25% |
| Education Alignment | 15% |
| Semantic Similarity | 20% |

Role-specific weights are also supported.

When a component score is unavailable, the current scorer excludes that component and renormalizes the remaining available weights.

### Implemented Improvements

The scoring system now includes a minimum coverage threshold of 80%.

The scorer:
- Calculates the percentage of available scoring coverage.
- Reports missing scoring components.
- Identifies candidates whose scoring coverage falls below the configured threshold.
- Sets `manual_review_required` to `True` when coverage is insufficient.
- Supports a configurable minimum coverage threshold.

The shortlisting logic uses this flag to classify candidates requiring manual review rather than automatically placing them in the usual shortlist categories.

### Remaining Fairness Considerations

- Candidates with different coverage levels may not be directly comparable.
- Scoring weights should be reviewed periodically.
- A numerical ATS score should not be treated as an automatic hiring decision.
- Consistent evaluation criteria should be applied across candidates.

## 6. Bias Indicators

The following indicators should be monitored during evaluation:

| Bias indicator | Potential issue |
|---|---|
| Keyword dependency | Equivalent skills may be missed |
| Resume formatting | Different layouts may affect extraction |
| Missing information | Candidates may receive scores with different coverage |
| Personal identifiers | Unnecessary personal details may influence reviewers |
| Education emphasis | Different educational backgrounds may be evaluated inconsistently |
| Experience representation | Non-traditional experience may be underrepresented |

These are potential risk indicators, not evidence that discrimination has already occurred.
## 7. Initial Fairness Consistency Evaluation

### Objective

An initial evaluation was performed using synthetic resume samples to check whether equivalent candidate information produces consistent scoring results despite differences in formatting and skill terminology.

### Evaluation Scenarios

| Test scenario | Evaluation |
|---|---|
| Resume formatting variation | Compared skill-match scores across different resume layouts |
| Skill terminology variation | Compared full skill names with recognized aliases |
| Combined variation | Tested formatting and terminology changes together |
| Weighted ATS score consistency | Compared overall ATS scores and scoring coverage |

### Results

All four automated consistency tests passed.

The evaluation demonstrated consistent results for the specific synthetic examples tested.

### Limitations

- The evaluation uses synthetic resume samples rather than real candidate data.
- Only a limited number of formatting and terminology variations were tested.
- Experience, education and semantic scores were held constant in the weighted ATS aggregation test.
- The tests do not measure demographic disparities or establish the absence of hiring bias.

Further evaluation using diverse and appropriately governed datasets is required.

## 8. Human Review Recommendations

Zecpath AI should be used as a decision-support system rather than an autonomous hiring authority.

Recommended practices:

1. Review candidates flagged with missing scoring components.
2. Examine matched and missing skills before making decisions.
3. Consider relevant experience beyond exact keyword matches.
4. Avoid rejecting candidates solely based on an automated score.
5. Apply consistent evaluation criteria to all candidates.
6. Review scoring outcomes periodically for unexpected disparities.

## 9. Future Improvements

The following improvements are recommended for future development:

- Context-aware semantic skill matching.
- More comprehensive personal-identifier detection and masking.
- Evaluation of scoring consistency across different resume formats.
- Bias evaluation using appropriately collected and governed datasets.
- Comparison of scoring outcomes across relevant candidate groups where lawful and appropriate.
- Improved explanations for individual scoring decisions.
- Periodic evaluation and adjustment of scoring weights.
- More comprehensive fairness testing using diverse resume samples.

## 10. Conclusion

Day 15 introduced resume text normalization and a basic privacy masking utility into Zecpath AI.

The changes improve text consistency and reduce exposure of common contact identifiers.

Potential fairness issues involving keyword dependency, missing scoring components, and personal attributes have also been documented.

Further implementation, testing, and evaluation are necessary before making claims about the fairness or bias performance of the system.
