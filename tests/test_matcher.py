from unittest.mock import MagicMock, patch

import pytest
from what_cli.matcher import match


class MockEntity:
    def __init__(self, name, match_result=None):
        self.name = name
        self.match = MagicMock(return_value=match_result)


def test_match_first_candidate_wins():
    entity1 = MockEntity("entity1")
    entity2 = MockEntity("entity2", match_result=MagicMock())
    entity3 = MockEntity("entity3", match_result=MagicMock())

    result = match("test", [entity1, entity2, entity3])

    assert result == entity2.match.return_value
    entity1.match.assert_called_once_with("test")
    entity2.match.assert_called_once_with("test")
    entity3.match.assert_not_called()


def test_match_checks_all_until_match():
    entity1 = MockEntity("entity1")
    entity2 = MockEntity("entity2")
    entity3 = MockEntity("entity3", match_result=MagicMock())

    result = match("test", [entity1, entity2, entity3])

    assert result == entity3.match.return_value
    entity1.match.assert_called_once_with("test")
    entity2.match.assert_called_once_with("test")
    entity3.match.assert_called_once_with("test")


def test_match_no_match_raises_exception():
    entity1 = MockEntity("entity1")
    entity2 = MockEntity("entity2")

    with pytest.raises(Exception) as exc_info:
        match("no_match", [entity1, entity2])

    assert str(exc_info.value) == "No match found for no_match"
    entity1.match.assert_called_once_with("no_match")
    entity2.match.assert_called_once_with("no_match")


def test_match_uses_default_candidates_when_none_provided():
    with (
        patch("what_cli.matcher.File") as mock_file,
        patch("what_cli.matcher.Process") as mock_process,
        patch("what_cli.matcher.User") as mock_user,
    ):

        mock_file.match.return_value = None
        mock_process.match.return_value = MagicMock()
        mock_user.match.return_value = None

        result = match("test")

        mock_file.match.assert_called_once_with("test")
        mock_process.match.assert_called_once_with("test")
        mock_user.match.assert_not_called()
        assert result == mock_process.match.return_value


def test_match_empty_candidates_raises_exception():
    with pytest.raises(Exception) as exc_info:
        match("test", [])

    assert str(exc_info.value) == "No match found for test"


def test_match_single_candidate():
    entity = MockEntity("entity", match_result=MagicMock())

    result = match("test", [entity])

    assert result == entity.match.return_value
    entity.match.assert_called_once_with("test")
