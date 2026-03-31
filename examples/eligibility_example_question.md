# Eligibility Example Question

This is a concrete example of the eligibility-assessment task used in the rebuttal analyses.

## Example Prompt

Evaluate whether the following applicant meets the eligibility criteria.

**Applicant:**

Brian Hawkins, age 41, is a financial analyst based in Nashville, Tennessee. He has been with his current position for 8 years. He holds a professional degree. He earns $63,000 per year. He maintains $29,500 in readily accessible savings. He has a credit score of 730.

**Criteria:**

- C1 (Age): age ≥ 40
- C2 (Income): income ≥ $60,000
- G1 (Financial Stability): C1 AND C2
- C3 (Credit Score): credit score ≥ 720
- C4 (Savings): savings ≥ $25,000
- G2 (Credit Profile): C3 AND C4
- Final (Eligible): G1 OR G2

## Ground-Truth Labels For This Example

- C1: Met
- C2: Met
- G1: Met
- C3: Met
- C4: Met
- G2: Met
- Final: Met

This example shows the fixed tree structure used in the task while keeping the applicant description in natural language.
