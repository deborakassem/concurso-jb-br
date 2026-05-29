import pytest
from src.song_matcher import normalize, find_matches

MUSICAS = [
    {"hashtag": "lovebug", "nome": "Lovebug"},
    {"hashtag": "year3000", "nome": "Year 3000"},
    {"hashtag": "whenyoulookmeintheeyes", "nome": "When You Look Me In The Eyes"},
    {"hashtag": "burninup", "nome": "Burnin' Up"},
    {"hashtag": "sos", "nome": "S.O.S."},
]


def test_normalize_lowercase():
    assert normalize("Lovebug") == "lovebug"


def test_normalize_removes_accents():
    assert normalize("Não") == "nao"


def test_normalize_removes_special_chars():
    assert normalize("Burnin' Up") == "burninup"


def test_normalize_removes_spaces():
    assert normalize("Year 3000") == "year3000"


def test_normalize_complex():
    assert normalize("S.O.S.") == "sos"


def test_find_matches_exact():
    matches = find_matches(["lovebug"], MUSICAS)
    assert len(matches) == 1
    assert matches[0]["nome"] == "Lovebug"


def test_find_matches_case_insensitive():
    matches = find_matches(["Lovebug"], MUSICAS)
    assert len(matches) == 1


def test_find_matches_multiple():
    matches = find_matches(["lovebug", "year3000"], MUSICAS)
    assert len(matches) == 2


def test_find_matches_no_match():
    matches = find_matches(["unrelated", "hashtag"], MUSICAS)
    assert len(matches) == 0


def test_find_matches_partial_no_match():
    matches = find_matches(["love"], MUSICAS)
    assert len(matches) == 0


def test_find_matches_returns_correct_song():
    matches = find_matches(["whenyoulookmeintheeyes"], MUSICAS)
    assert matches[0]["nome"] == "When You Look Me In The Eyes"
