import asyncio
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import mcp_server  # noqa: E402
from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402
from mcp.server.fastmcp.exceptions import ToolError  # noqa: E402


TOOL_NAMES = {
    "comic_doctor",
    "comic_init",
    "comic_status",
    "comic_transition",
    "comic_validate",
    "comic_resume_plan",
    "comic_invalidate",
    "comic_record_stage",
    "comic_record_attempt",
    "comic_promote_attempt",
    "comic_override_panel",
    "comic_letter",
    "comic_compose",
    "comic_export",
}


class McpServerUnitTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name) / "output"
        mcp_server._configure_root(self.root.absolute())

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_root_must_be_absolute(self):
        with self.assertRaisesRegex(ValueError, "absolute"):
            mcp_server._configure_root(Path("relative-output"))

    def test_project_id_rejects_absolute_traversal_and_sibling_prefix(self):
        for project_id in ("/tmp/outside", "../outside", "project/child", "C:\\outside"):
            with self.subTest(project_id=project_id):
                with self.assertRaisesRegex(ToolError, "invalid project ID"):
                    mcp_server._resolve_project(project_id)

    def test_project_symlink_cannot_escape_root(self):
        outside = Path(self.temporary_directory.name) / "outside"
        outside.mkdir()
        try:
            (self.root / "escape").symlink_to(outside, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"symlink unavailable: {error}")

        with self.assertRaisesRegex(ToolError, "outside output root"):
            mcp_server._resolve_project("escape")

    def test_file_symlink_cannot_escape_project(self):
        project = self.root / "project"
        project.mkdir()
        outside = Path(self.temporary_directory.name) / "secret.txt"
        outside.write_text("outside output root")
        try:
            (project / "arbitrary-file.txt").symlink_to(outside)
        except OSError as error:
            self.skipTest(f"symlink unavailable: {error}")

        with self.assertRaisesRegex(ToolError, "symlink"):
            mcp_server._resolve_project("project")

    def test_exposes_exact_approved_tool_surface(self):
        tools = asyncio.run(mcp_server.mcp.list_tools())
        self.assertEqual(TOOL_NAMES, {tool.name for tool in tools})

    def test_init_rejects_oversized_utf8_before_project_allocation(self):
        before = list(self.root.iterdir())
        with self.assertRaisesRegex(ToolError, "at most 200 KiB"):
            mcp_server.comic_init("Too Large", "a" * (200 * 1024 + 1), {})
        self.assertEqual(before, list(self.root.iterdir()))

    def test_attempt_tools_reject_same_drive_relative_path_as_cli(self):
        project = self.root / "project"
        project.mkdir()
        for tool, arguments in (
            (mcp_server.comic_record_attempt, ("project", "p01-01", "initial", "C:outside.png")),
            (mcp_server.comic_promote_attempt, ("project", "p01-01", "C:outside.png")),
        ):
            with self.subTest(tool=tool.__name__):
                with self.assertRaisesRegex(ToolError, "relative project path"):
                    tool(*arguments)


class McpProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_stdio_protocol_exercises_all_tools(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_root = Path(temporary_directory) / "output"
            output_root.mkdir()
            sample = ROOT / "samples/sunlight-courier"
            project = output_root / "sunlight-courier"
            shutil.copytree(sample, project)
            attempt = project / "panels/raw/p01-01-attempt.png"
            shutil.copy2(project / "panels/raw/p01-01.png", attempt)

            parameters = StdioServerParameters(
                command=sys.executable,
                args=[
                    str(ROOT / "scripts/mcp_server.py"),
                    "--root",
                    str(output_root),
                ],
            )
            async with stdio_client(parameters) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    listed = await session.list_tools()
                    self.assertEqual(TOOL_NAMES, {tool.name for tool in listed.tools})

                    async def call(
                        name: str,
                        arguments: dict[str, Any] | None = None,
                        *,
                        error: bool = False,
                    ) -> Any:
                        result = await session.call_tool(name, arguments or {})
                        self.assertEqual(error, result.isError, name)
                        if error:
                            self.assertIsNone(result.structuredContent)
                        else:
                            self.assertIsNotNone(result.structuredContent)
                        return result.structuredContent

                    health = await call("comic_doctor")
                    self.assertTrue(health["healthy"])
                    self.assertTrue(any("PASS Python 3.11" in item for item in health["messages"]))

                    created = await call("comic_init", {
                        "title": "Wire Test",
                        "source_text": "A protocol smoke test.",
                        "request_settings": {"language": "en", "mode": "short_prompt"},
                    })
                    self.assertEqual("wire-test", created["result"])
                    status = await call("comic_status", {"project_id": "wire-test"})
                    self.assertEqual("INIT", status["status"])
                    transitioned = await call("comic_transition", {
                        "project_id": "wire-test", "target": "PLANNED",
                    })
                    self.assertEqual("PLANNED", transitioned["status"])

                    validated = await call("comic_validate", {
                        "project_id": "sunlight-courier", "stage": "panels",
                    })
                    self.assertEqual([], validated["result"])
                    resume = await call("comic_resume_plan", {
                        "project_id": "sunlight-courier",
                    })
                    self.assertGreaterEqual(len(resume["result"]), 6)
                    recorded = await call("comic_record_stage", {
                        "project_id": "sunlight-courier", "stage": "planning",
                    })
                    self.assertEqual("planning", recorded["stage"])
                    counters = await call("comic_record_attempt", {
                        "project_id": "sunlight-courier",
                        "panel_id": "p01-01",
                        "kind": "initial",
                        "relative_path": "panels/raw/p01-01-attempt.png",
                    })
                    self.assertEqual(1, counters["initial"])
                    promoted = await call("comic_promote_attempt", {
                        "project_id": "sunlight-courier",
                        "panel_id": "p01-01",
                        "relative_path": "panels/raw/p01-01-attempt.png",
                    })
                    self.assertEqual("panels/raw/p01-01.png", promoted["result"])
                    await call("comic_override_panel", {
                        "project_id": "sunlight-courier",
                        "panel_id": "p01-01",
                        "reason": "protocol smoke test",
                    }, error=True)
                    lettered = await call("comic_letter", {
                        "project_id": "sunlight-courier",
                    })
                    self.assertEqual(4, len(lettered["result"]))
                    pages = await call("comic_compose", {
                        "project_id": "sunlight-courier",
                    })
                    self.assertEqual(2, len(pages["result"]))
                    exported = await call("comic_export", {
                        "project_id": "sunlight-courier",
                    })
                    self.assertEqual("exports/sunlight-courier.pdf", exported["result"])
                    invalidated = await call("comic_invalidate", {
                        "project_id": "sunlight-courier", "stage": "export",
                    })
                    self.assertIn("qa_report", invalidated["result"])


if __name__ == "__main__":
    unittest.main()
