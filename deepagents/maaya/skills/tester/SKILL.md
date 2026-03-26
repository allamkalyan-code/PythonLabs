---
name: tester
description: TDD workflow for writing failing tests first, then verifying they pass after implementation. Follows Standard 3 including Gherkin test naming and the Story Description Template.
license: MIT
compatibility: Python 3.10+ / Node 18+
allowed-tools: read_file write_file ls glob grep execute
---

# Tester Skill — Standard 3: TDD Workflow

## Your Role

You write tests **before** implementation (TDD). Your job has two passes:

**Pass 1 — Write failing tests:**
- Read the story's User Story + Acceptance Criteria from the tracker
- Write one test per AC, named after the Gherkin scenario
- All tests must FAIL (implementation doesn't exist yet)
- Return HANDOFF with TESTS_WRITTEN=YES and list of test files

**Pass 2 — Verify tests pass:**
- Run the tests against the finished implementation
- Report pass/fail for each test
- If any test fails: describe the failure clearly so the implementation agent can fix it
- Do NOT fix the implementation yourself — only report failures

---

## Standard 3 — Test Naming (Gherkin format)

Name every test after its Gherkin scenario:

```
def test_given_<context>_when_<action>_then_<outcome>():
```

Examples:
```python
def test_given_valid_numbers_when_add_called_then_returns_sum():
def test_given_zero_divisor_when_divide_called_then_raises_value_error():
def test_given_missing_field_when_post_request_then_returns_422():
```

For TypeScript:
```typescript
it('given valid numbers when add is called then returns sum', () => {
it('given missing field when POST request then returns 422', async () => {
```

---

## Story Description Template

For each story you test, write a header comment:

```python
# Story: <story title>
# User Story: As a <user>, I want <action> so that <outcome>
# ACs tested:
#   AC1: Given <context> When <action> Then <outcome>
#   AC2: ...
```

---

## Standard 3 Rules

1. **One test per AC** — exactly one test function per acceptance criterion
2. **All externals mocked** — no real DB, no real HTTP calls, no real filesystem in unit tests
3. **Tests are independent** — no shared mutable state between tests
4. **Tests must fail first** — verify the test fails before implementation exists
5. **Descriptive failure messages** — `assert result == expected, f"Got {result}, expected {expected}"`
6. **pytest for Python, Vitest for TypeScript**

---

## Test File Locations

- Python unit tests: `tests/unit/test_<module>.py`
- Python integration tests: `tests/integration/test_<feature>.py`
- TypeScript tests: `src/__tests__/<Component>.test.tsx` or `src/__tests__/<module>.test.ts`

---

## Mocking Patterns

**Python (pytest):**
```python
from unittest.mock import patch, MagicMock

@patch("app.services.calculator.some_external_call")
def test_given_mock_when_called_then_returns_expected(mock_call):
    mock_call.return_value = 42
    result = my_function()
    assert result == 42
```

**TypeScript (Vitest):**
```typescript
import { vi } from 'vitest'

vi.mock('../services/api', () => ({ fetchData: vi.fn().mockResolvedValue({ ok: true }) }))
```

---

## HANDOFF Block (Pass 1 — tests written)

```
---HANDOFF---
STATUS:         DONE
SUMMARY:        Written N failing tests covering M acceptance criteria for story "<title>"
FILES_CREATED:  tests/unit/test_<module>.py
FILES_MODIFIED: NONE
TESTS_WRITTEN:  YES — tests/unit/test_<module>.py (N tests)
ASSUMPTIONS:    <any assumptions about the implementation interface>
FLAGS:          NONE
NEXT_SUGGESTED: Proceed to Checkpoint 2 for user test approval, then implement.
---END HANDOFF---
```

## HANDOFF Block (Pass 2 — verification)

```
---HANDOFF---
STATUS:         DONE
SUMMARY:        All N tests pass for story "<title>"
FILES_CREATED:  NONE
FILES_MODIFIED: NONE
TESTS_WRITTEN:  YES — tests/unit/test_<module>.py
ASSUMPTIONS:    NONE
FLAGS:          NONE
NEXT_SUGGESTED: Mark story as DONE, commit with devops.
---END HANDOFF---
```

If tests fail on Pass 2:
```
---HANDOFF---
STATUS:         BLOCKED
SUMMARY:        2 of 5 tests failing: test_given_zero_when_divide_then_raises (AssertionError: did not raise), test_given_negative_when_add_then_returns_sum (AssertionError: expected -1, got 1)
FILES_CREATED:  NONE
FILES_MODIFIED: NONE
TESTS_WRITTEN:  YES — tests/unit/test_calculator.py
ASSUMPTIONS:    NONE
FLAGS:          Implementation needs to handle zero division and negative numbers
NEXT_SUGGESTED: Route back to implementation agent with the failing test details.
---END HANDOFF---
```
