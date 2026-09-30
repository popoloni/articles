import laya_mlx as laya

agent = laya.load("aac6fef/laya-mlx")
result = agent.predict(
    "The task is to correct a typo in the installation guide.",
    {
        "route": {
            "type": "choice",
            "instructions": "Which workflow fits this task?",
            "criteria": ["debugging", "documentation", "clarification"]
        }
    }
)
print(result["answers"]["route"])
