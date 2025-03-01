---
name: Feature Request
description: Suggest a new feature or improvement
labels: ["feature", "triage-needed"]
body:
  - type: textarea
    id: problem
    attributes:
      label: What problem are you solving?
      placeholder: Describe the problem...
    validations:
      required: true
  - type: textarea
    id: solution
    attributes:
      label: Proposed Solution
      placeholder: Describe the solution...
    validations:
      required: true
