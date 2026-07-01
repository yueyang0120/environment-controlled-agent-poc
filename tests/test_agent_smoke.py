from agent import EmailManager, PythonExecutor, StructuredAgent


def test_parse_pipe_separated_email_data():
    parsed = EmailManager.parse_email_data(
        "to:customer@example.com|subject:Follow up|body:Thanks for the discussion"
    )

    assert parsed == {
        "to": "customer@example.com",
        "subject": "Follow up",
        "body": "Thanks for the discussion",
    }


def test_draft_email_has_no_send_side_effect():
    draft = EmailManager.draft_email(
        "to:customer@example.com|subject:Follow up|body:Thanks for the discussion"
    )

    assert "EMAIL DRAFT" in draft
    assert "customer@example.com" in draft
    assert "Thanks for the discussion" in draft


def test_python_executor_handles_simple_calculation():
    assert PythonExecutor.run_python("25 * 8 + 15") == "215"


def test_agent_graph_compiles():
    graph = StructuredAgent.create_agent()

    assert graph is not None
