"""
Tests for jarvis_brain.py — intent matching and command routing.
All external calls (Ollama, subprocess, webbrowser) are mocked.
"""
import pytest
from unittest.mock import patch, MagicMock

import jarvis_brain as brain


@pytest.fixture(autouse=True)
def _mock_externals(tmp_path):
    """Mock Ollama, subprocess, webbrowser, and finance file for all tests."""
    fpath = tmp_path / "config" / "finances.json"
    import finance_engine as fe
    with patch.object(fe, "FINANCE_FILE", fpath), \
         patch.object(brain, "is_ollama_available", return_value=False), \
         patch("subprocess.Popen"), \
         patch("webbrowser.open"):
        yield


class TestOpenAppCommands:

    def test_apri_chrome(self):
        result = brain.execute_action("apri chrome")
        assert result is not None
        assert "chrome" in result.lower()

    def test_apri_spotify(self):
        result = brain.execute_action("apri spotify")
        assert result is not None
        assert "spotify" in result.lower()

    def test_apri_notepad(self):
        result = brain.execute_action("apri notepad")
        assert result is not None
        assert "notepad" in result.lower()

    def test_avvia_chrome(self):
        result = brain.execute_action("avvia chrome")
        assert result is not None
        assert "chrome" in result.lower()

    def test_lancia_youtube(self):
        result = brain.execute_action("lancia youtube")
        assert result is not None
        assert "youtube" in result.lower()


class TestWebsiteCommands:

    def test_apri_youtube(self):
        result = brain.execute_action("apri youtube")
        assert result is not None
        assert "youtube" in result.lower()

    def test_apri_google(self):
        result = brain.execute_action("apri google")
        assert result is not None
        assert "google" in result.lower()


class TestSystemCommands:

    @patch("jarvis_brain.get_system_info_tool", return_value="CPU al 30 percento")
    def test_stato_sistema(self, mock_sys):
        result = brain.execute_action("stato sistema")
        assert result is not None
        assert "CPU" in result or "percento" in result

    @patch("jarvis_brain.get_system_info_tool", return_value="CPU al 30 percento")
    def test_cpu_query(self, mock_sys):
        result = brain.execute_action("come va la cpu")
        assert result is not None

    def test_screenshot(self):
        with patch("jarvis_brain.screenshot_tool", return_value="Screenshot salvato"):
            result = brain.execute_action("fai uno screenshot")
            assert result is not None
            assert "screenshot" in result.lower()


class TestFinanceCommands:

    def test_situazione_affitto(self):
        assert brain._fuzzy_match("situazione affitto", brain.FINANCE_TRIGGERS)

    def test_come_sto_affitto(self):
        assert brain._fuzzy_match("come sto con l'affitto", brain.FINANCE_TRIGGERS)

    def test_report_finanziario(self):
        assert brain._fuzzy_match("report finanziario", brain.FINANCE_TRIGGERS)

    def test_quanto_manca(self):
        assert brain._fuzzy_match("quanto manca per l'affitto", brain.FINANCE_TRIGGERS)

    def test_finance_process_input(self):
        """Full pipeline: finance trigger → get_report output."""
        result = brain.process_input("situazione affitto")
        assert result is not None
        assert "euro" in result.lower() or "sir" in result.lower()


class TestRecipeCommands:

    def test_cosa_cucino(self):
        assert brain._fuzzy_match("cosa cucino", brain.RECIPE_TRIGGERS)

    def test_ricetta_trigger(self):
        assert brain._fuzzy_match("dammi una ricetta", brain.RECIPE_TRIGGERS)

    def test_recipe_process_input(self):
        result = brain.process_input("cosa cucino stasera")
        assert result is not None
        assert len(result) > 10


class TestUnknownCommands:

    def test_gibberish(self):
        """Unknown input → conversation fallback, not crash."""
        result = brain.process_input("xyzzy foobar baz")
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0


class TestItalianVariations:

    def test_has_action_verb_apri(self):
        assert brain.has_action_verb("apri chrome per favore")

    def test_has_action_verb_avvia(self):
        assert brain.has_action_verb("avvia il notepad")

    def test_has_action_verb_lancia(self):
        assert brain.has_action_verb("lancia spotify adesso")

    def test_has_action_verb_metti(self):
        assert brain.has_action_verb("metti musica")

    def test_is_question(self):
        assert brain.is_question("come stai?")
        assert brain.is_question("cosa fai")
        assert brain.is_question("dimmi qualcosa")

    def test_not_action(self):
        assert not brain.has_action_verb("buongiorno jarvis")


class TestFuzzyMatch:

    def test_exact_match(self):
        assert brain._fuzzy_match("situazione affitto", brain.FINANCE_TRIGGERS)

    def test_partial_match(self):
        assert brain._fuzzy_match("fammi vedere la situazione affitto", brain.FINANCE_TRIGGERS)

    def test_no_match(self):
        assert not brain._fuzzy_match("apri chrome", brain.FINANCE_TRIGGERS)
