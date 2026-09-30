import json
from opendecider import load

model = load("manjunathshiva/opendecider-nano")

state = {
    "request": "Fix the empty-input failure in parse_records.",
    "evidence": "The supplied test fails with IndexError on an empty list.",
    "constraint": "Do not change the public function signature."
}

questions = {
    "route": {
        "type": "choice",
        "instructions": "Which workflow best matches the request?",
        "criteria": {
            "debugging": "Diagnose and repair an existing failure",
            "documentation": "Change explanatory text without code changes",
            "clarification": "Request essential missing information"
        }
    },
    "has_reproduction": {
        "type": "noul",
        "instructions": "Does the state identify a concrete failing input?"
    }
}

result = model.system_one(state, questions)
answers = result["answers"]

if result.get("warnings") or any(
    answer.get("truncated", False) for answer in answers.values()
):
    raise RuntimeError("Input warning: inspect before relying on this result.")

print(json.dumps(answers, indent=2))
