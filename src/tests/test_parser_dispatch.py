"""TDD tests for the format dispatcher, parse_file, and ImportResult.

Tests:
- detect_format correctly identifies all 3 formats and 'unknown'
- parse_file reads files, dispatches correctly, handles read errors
- ImportResult.from_parse_result counts success, incomplete, failures
"""
import pytest
from pathlib import Path

from src.parser.statblock_parser import detect_format, parse_file
from src.parser.models import ParseResult, ParseFailure, ImportResult


# ---------------------------------------------------------------------------
# Inline fixture strings — minimal content for format detection
# ---------------------------------------------------------------------------

FIVETOOLS_CONTENT = """\
>## Goblin
>*Small Humanoid (goblinoid), Neutral Evil*
>___
>- **Armor Class** 15 (leather armor, shield)
>- **Hit Points** 7 (2d6)
>- **Challenge** 1/4 (50 XP)
"""

HOMEBREWERY_CONTENT = """\
___
## Goblin
*Small Humanoid (goblinoid), Neutral Evil*
___
- **Armor Class** 15
- **Hit Points** 7 (2d6)
- **Challenge** 1/4 (50 XP)
"""

PLAIN_CONTENT = """\
## Goblin
*Small Humanoid (goblinoid), Neutral Evil*

- **Armor Class** 15
- **Hit Points** 7 (2d6)
- **Challenge** 1/4 (50 XP)
"""

UNKNOWN_CONTENT = """\
# Some Random Document

This is not a statblock.
Just some text about monsters.
"""


# ---------------------------------------------------------------------------
# detect_format tests
# ---------------------------------------------------------------------------

class TestDetectFormat:
    """Test that detect_format correctly identifies all 3 formats."""

    def test_fivetools_detected(self):
        assert detect_format(FIVETOOLS_CONTENT) == 'fivetools'

    def test_homebrewery_detected(self):
        assert detect_format(HOMEBREWERY_CONTENT) == 'homebrewery'

    def test_plain_detected(self):
        assert detect_format(PLAIN_CONTENT) == 'plain'

    def test_unknown_returns_unknown(self):
        assert detect_format(UNKNOWN_CONTENT) == 'unknown'

    def test_empty_string_is_unknown(self):
        assert detect_format("") == 'unknown'

    def test_fivetools_wins_over_homebrewery(self):
        """Fivetools detection has priority — content with > prefix beats ___."""
        # Content that has both >## heading AND ** fields
        mixed = ">## Monster\n>- **Armor Class** 15\n___\n"
        assert detect_format(mixed) == 'fivetools'

    def test_homebrewery_wins_over_plain(self):
        """___ delimiter makes homebrewery win over plain ## heading."""
        # Has both ___ and ## heading — should be homebrewery
        mixed = "___\n## Monster\n___\n- **Armor Class** 15\n"
        assert detect_format(mixed) == 'homebrewery'


# ---------------------------------------------------------------------------
# parse_file tests
# ---------------------------------------------------------------------------

class TestParseFile:
    """Test parse_file reads, detects format, and dispatches correctly."""

    def test_fivetools_file_returns_monster(self, tmp_path):
        """parse_file with a minimal fivetools content file returns ParseResult with monster."""
        f = tmp_path / "goblin.md"
        f.write_text(FIVETOOLS_CONTENT, encoding='utf-8')
        result = parse_file(f)
        assert isinstance(result, ParseResult)
        assert len(result.monsters) >= 1
        assert result.monsters[0].name == "Goblin"

    def test_homebrewery_file_returns_monster(self, tmp_path):
        """parse_file with homebrewery content dispatches to parse_homebrewery."""
        f = tmp_path / "hb_goblin.md"
        f.write_text(HOMEBREWERY_CONTENT, encoding='utf-8')
        result = parse_file(f)
        assert isinstance(result, ParseResult)
        assert len(result.monsters) >= 1
        assert result.monsters[0].name == "Goblin"

    def test_plain_file_returns_monster(self, tmp_path):
        """parse_file with plain content dispatches to parse_plain."""
        f = tmp_path / "plain_goblin.md"
        f.write_text(PLAIN_CONTENT, encoding='utf-8')
        result = parse_file(f)
        assert isinstance(result, ParseResult)
        assert len(result.monsters) >= 1
        assert result.monsters[0].name == "Goblin"

    def test_nonexistent_file_returns_failure(self, tmp_path):
        """parse_file with nonexistent path returns ParseResult with 1 failure."""
        nonexistent = tmp_path / "does_not_exist.md"
        result = parse_file(nonexistent)
        assert isinstance(result, ParseResult)
        assert result.monsters == []
        assert len(result.failures) == 1
        assert isinstance(result.failures[0], ParseFailure)

    def test_nonexistent_file_failure_has_path(self, tmp_path):
        """Failure from nonexistent file includes the file path in source_file."""
        nonexistent = tmp_path / "missing.md"
        result = parse_file(nonexistent)
        assert str(nonexistent) in result.failures[0].source_file

    def test_unknown_format_returns_warning(self, tmp_path):
        """parse_file with unrecognized format returns empty monsters with warning."""
        f = tmp_path / "unknown.md"
        f.write_text(UNKNOWN_CONTENT, encoding='utf-8')
        result = parse_file(f)
        assert isinstance(result, ParseResult)
        assert result.monsters == []
        assert len(result.warnings) >= 1

    def test_unknown_format_no_crash(self, tmp_path):
        """parse_file with unknown format must not raise."""
        f = tmp_path / "unknown.md"
        f.write_text(UNKNOWN_CONTENT, encoding='utf-8')
        try:
            parse_file(f)
        except Exception as e:
            pytest.fail(f"parse_file raised on unknown format: {e}")


# ---------------------------------------------------------------------------
# ImportResult tests
# ---------------------------------------------------------------------------

class TestImportResult:
    """Test ImportResult.from_parse_result counts correctly."""

    def _make_monster(self, incomplete: bool = False):
        """Helper: create a minimal Monster object."""
        from src.domain.models import Monster
        return Monster(name="Test", ac=15, hp=10, cr="1", incomplete=incomplete)

    def test_from_parse_result_success_count(self):
        """success_count equals len(result.monsters)."""
        monsters = [self._make_monster(), self._make_monster(), self._make_monster()]
        result = ParseResult(monsters=monsters, failures=[], warnings=[])
        ir = ImportResult.from_parse_result("test.md", result)
        assert ir.success_count == 3

    def test_from_parse_result_incomplete_count(self):
        """incomplete_count counts monsters with incomplete=True."""
        monsters = [
            self._make_monster(incomplete=False),
            self._make_monster(incomplete=True),
            self._make_monster(incomplete=False),
        ]
        result = ParseResult(monsters=monsters, failures=[], warnings=[])
        ir = ImportResult.from_parse_result("test.md", result)
        assert ir.incomplete_count == 1

    def test_from_parse_result_three_monsters_one_incomplete(self):
        """Spec example: 3 monsters, 1 incomplete."""
        monsters = [
            self._make_monster(incomplete=False),
            self._make_monster(incomplete=True),
            self._make_monster(incomplete=False),
        ]
        result = ParseResult(monsters=monsters, failures=[], warnings=[])
        ir = ImportResult.from_parse_result("test.md", result)
        assert ir.success_count == 3
        assert ir.incomplete_count == 1

    def test_from_parse_result_failures_preserved(self):
        """Failures from ParseResult are preserved in ImportResult.failures."""
        failure = ParseFailure(source_file="test.md", monster_name="Goblin", reason="Bad format")
        result = ParseResult(monsters=[], failures=[failure], warnings=[])
        ir = ImportResult.from_parse_result("test.md", result)
        assert len(ir.failures) == 1
        assert ir.failures[0].monster_name == "Goblin"

    def test_from_parse_result_filename_stored(self):
        """filename is stored on the ImportResult."""
        result = ParseResult(monsters=[], failures=[], warnings=[])
        ir = ImportResult.from_parse_result("goblin.md", result)
        assert ir.filename == "goblin.md"

    def test_empty_parse_result(self):
        """Empty ParseResult produces zeros."""
        result = ParseResult(monsters=[], failures=[], warnings=[])
        ir = ImportResult.from_parse_result("empty.md", result)
        assert ir.success_count == 0
        assert ir.incomplete_count == 0
        assert ir.failures == []
