import pytest

from lazarr.sdk import MatchResult, TorrentFile
from lazarr_search_engine.matcher import Matcher
from lazarr_search_engine.provider_utils import search_queries
from lazarr_search_engine.selection import reject_reason
from conftest import candidate, request, audio_claim


@pytest.fixture
def named(media):
    media.title = "Истории монстров"
    media.original_title = "Monogatari"
    media.year = 2009
    media.seasons = [
        {"number": 1, "title": "Истории монстров", "air_date": "2009-07-03"},
        {"number": 2, "title": "Истории подделок", "air_date": "2012-01-08"},
        {"number": 3, "title": "Другая история", "air_date": "2013-01-01"},
    ]
    req = request(media)
    req.season = 2
    req.air_date = "2012-01-08"
    return req


def test_search_only_requested_season(named):
    assert search_queries(named.media, season=2, year=2012) == [
        "Monogatari 2012",
        "Истории подделок 2012",
        "Monogatari",
        "Истории подделок",
    ]
    assert search_queries(named.media, season=2, year=2009)[1] == "Истории подделок 2012"
    assert search_queries(named.media, year=2009) == ["Monogatari 2009", "Monogatari"]


@pytest.mark.parametrize(
    "title",
    ["", "Season 2", "Сезон 2", "2 сезон", "2nd Season", "Specials", "Спецэпизоды", "Спецматериалы", "S02"],
)
def test_generic_season_titles_not_searched_or_matched(named, title):
    named.media.seasons[1]["title"] = title
    assert search_queries(named.media, season=2, year=2012) == ["Monogatari 2012", "Monogatari"]
    assert (
        Matcher().identity(candidate(title=f"{title} (2012)", external_ids={}), named).result
        == MatchResult.UNKNOWN
    )


@pytest.mark.parametrize(
    "title,expected",
    [
        ("Истории подделок (2012) 1080p", MatchResult.MATCH),
        ("Истории подделок [2012] [1080p]", MatchResult.MATCH),
        ("Истории подделок (2009) 1080p", MatchResult.UNKNOWN),
        ("Истории подделок 1080p", MatchResult.UNKNOWN),
        ("Другая история (2013) 1080p", MatchResult.UNKNOWN),
        ("Истории подделок продолжение (2012)", MatchResult.UNKNOWN),
        ("Monogatari (2009) 1080p", MatchResult.MATCH),
    ],
)
def test_identity_by_season_name_and_year(named, title, expected):
    assert Matcher().identity(candidate(title=title, external_ids={}), named).result == expected


def test_missing_season_date_uses_episode_date(named):
    named.media.seasons[1].pop("air_date")
    assert (
        Matcher().identity(candidate(title="Истории подделок (2012)", external_ids={}), named).result
        == MatchResult.MATCH
    )
    assert "Истории подделок 2012" in search_queries(named.media, season=2, year=2012)


def test_named_season_does_not_override_external_ids(named):
    c = candidate(title="Истории подделок (2012)", external_ids={"tmdb": "999"})
    assert Matcher().identity(c, named).result == MatchResult.MISMATCH


def test_named_season_binds_unnumbered_season_files_and_sidecars(named):
    files = [
        TorrentFile(index=i, path=p, size=1000)
        for i, p in enumerate(
            [
                "Истории подделок - 01.mkv",
                "Истории подделок - 02.mkv",
                "Subs/RUS/Истории подделок - 01.ass",
            ]
        )
    ]
    named.requirements.subtitle_languages = ["ru"]
    c = candidate(
        title="Истории подделок (2012) 1080p", external_ids={}, evidence=[audio_claim(files[0].path)]
    )
    assert reject_reason(c, [named]) is None
    report = Matcher().evaluate(c, [named], files)
    assert report.evaluations[0].result == MatchResult.MATCH
    assert report.plan.bindings[0].video_index == 0
    assert report.plan.bindings[0].tracks[0].file_index == 2


def test_explicit_other_season_is_not_remapped(named):
    c = candidate(title="Истории подделок (2012) S01", external_ids={})
    assert reject_reason(c, [named]) == "Указан другой сезон"
    files = [TorrentFile(index=0, path="Истории подделок S01E01.mkv", size=1000)]
    report = Matcher().evaluate(c, [named], files)
    assert report.evaluations[0].result != MatchResult.MATCH


def test_season_title_equal_to_series_preserves_identity_without_season_date(named):
    named.season = 1
    named.air_date = None
    named.media.seasons[0].pop("air_date")
    assert (
        Matcher().identity(candidate(title="Истории монстров (2009)", external_ids={}), named).result
        == MatchResult.MATCH
    )
