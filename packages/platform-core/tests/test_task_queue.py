from shared_orchestrator.task_queue import Task


def test_task_contract_is_serializable():
    task = Task(task_id="t-1", kind="triage", payload={"domain": "cybersecurity"})
    assert task.task_id == "t-1"
    assert task.payload["domain"] == "cybersecurity"
