from apps.api.sourcebrief_api import skill_exports


def test_skill_export_validation_requires_self_improvement_boundary() -> None:
    files = []
    for path in sorted(skill_exports.REQUIRED_PACKAGE_PATHS):
        content = "placeholder\n"
        if path == "examples/smoke-queries.md":
            content = "## One\n## Two\n## Three\n"
        files.append({"path": path, "bytes": len(content), "content": content})

    skill_content = "\n".join(
        [
            "Non-negotiable agent operating contract",
            "MCP-first evidence path",
            "CLI fallback/toolbelt",
            "context_pack_key",
            "context_pack_version",
            "context_pack_snapshot_pin_enforced",
            "sourcebrief.get_agent_context",
            "references/data-structure.md",
            "references/resource-map.md",
            "references/task-playbooks/onboarding.md",
            "citations",
            "Mutation boundary",
        ]
    )

    result = skill_exports._validate_files(files, skill_content)  # noqa: SLF001

    assert result["ok"] is False
    messages = [error["message"] for error in result["errors"]]
    assert any("Self-improvement review loop boundary" in message for message in messages)
    assert any("sourcebrief.review-bundle.v1" in message for message in messages)
    assert any("sourcebrief review stage" in message for message in messages)
