"""Public metadata and real paths from rutracker topic 6832176; no credentials."""

import pytest
from lazarr.config import Requirements
from lazarr.sdk import Candidate, MetadataItem, SubtaskRequest, TorrentFile, Evidence
from lazarr_search_engine.matcher import Matcher
from lazarr_search_engine.selection import reject_reason, candidate_rank
from lazarr_search_engine.provider_utils import search_queries

TITLE = (
    "Невероятные приключения ДжоДжо: Гонка «Стальной шар» (ТВ-7) / "
    "Steel Ball Run: JoJo no Kimyou na Bouken / Steel Ball Run: JoJo's Bizarre Adventure / "
    "Джоджо: Гонка стального шара [ONA] [01-02 из XX] [UKR, ENG, JAP+Sub] & "
    "[01 из XX] [RUS(int)] [2026, Экшен, Приключения, WEB-DL] [1080p]"
)
PATH = "Steel Ball Run JoJo no Kimyou na Bouken [WEB-DL 1080p]/Steel Ball Run JoJo no Kimyou na Bouken - {:02} [WEB-DL NF 1080p AVC AAC].mkv"


@pytest.fixture
def case():
    media = MetadataItem(
        id="45790",
        kind="tv",
        title="Невероятные приключения ДжоДжо",
        year=2012,
        seasons=[{"number": 6, "title": "Гонка «Стальной шар»", "air_date": "2026-03-19"}],
    )
    requests = [
        SubtaskRequest(
            id=e,
            media=media,
            season=6,
            episode=e,
            air_date="2026-03-19",
            requirements=Requirements(audio_languages=["ja"], subtitle_languages=["ru"]),
        )
        for e in (1, 2, 3)
    ]
    c = Candidate(
        provider="rutracker",
        id="6832176",
        url="https://rutracker.org/forum/viewtopic.php?t=6832176",
        title=TITLE,
        evidence=[
            Evidence(field="audio_languages", value=["ja"], source="description", scope="all_video_files"),
            Evidence(field="subtitle_languages", value=["ru"], source="description", scope="all_video_files"),
        ],
    )
    files = [
        TorrentFile(index=i, path=PATH.format(i + 1), size=size)
        for i, size in enumerate([2085156445, 965559965])
    ]
    return c, requests, files


def test_real_broadcast_number_maps_only_present_episodes(case):
    c, requests, files = case
    assert reject_reason(c, requests) is None
    assert candidate_rank(c, requests)[0] == -80
    result = Matcher().evaluate(c, requests, files)
    assert [e.result for e in result.evaluations] == ["MATCH", "MATCH", "MISMATCH"]
    assert [(b.subtask_id, b.video_index, b.episode_order) for b in result.plan.bindings] == [
        (1, 0, 60001),
        (2, 1, 60002),
    ]
    queries = search_queries(requests[0].media, season=6, year=2026)
    assert "Гонка «Стальной шар» 2026" in queries
    assert all("TV-6" not in q and "ТВ-6" not in q for q in queries)


@pytest.mark.parametrize("replacement", ["(S07)", "(Сезон 7)", "(ТВ-7 / S07)", "(ТВ-7-8)"])
def test_explicit_season_or_multi_broadcast_is_not_overridden(case, replacement):
    c, requests, _ = case
    c.title = TITLE.replace("(ТВ-7)", replacement)
    assert reject_reason(c, requests) == "Указан другой сезон"


@pytest.mark.parametrize(
    "title",
    [
        "Гонка «Стальной шар» (ТВ-7) [2025]",
        "Гонка «Стальной шар» (ТВ-7)",
        "Гонка «Стальной шар» (ТВ-7) [2025-2026]",
        "Гонка «Стальной шар» продолжение (ТВ-7) [2026]",
    ],
)
def test_broadcast_number_needs_season_name_and_unambiguous_year(case, title):
    c, requests, _ = case
    c.title = title
    assert reject_reason(c, requests) == "Указан другой сезон"


def test_known_episode_mapping_takes_precedence(case):
    c, requests, _ = case
    r = requests[0]
    r.media.episode_numbering = {"6:1": [{"season": 8, "episode": 1}]}
    assert reject_reason(c, [r]) == "Указан другой сезон"


def test_explicit_file_season_is_never_rewritten(case):
    c, requests, _ = case
    files = [TorrentFile(index=0, path="Steel Ball Run S07E01.mkv", size=1000)]
    assert Matcher().evaluate(c, requests[:1], files).evaluations[0].result == "MISMATCH"


def test_existing_metadata_without_season_date_uses_episode_year(case):
    c, requests, files = case
    requests[0].media.seasons[0].pop("air_date")
    assert reject_reason(c, requests[:1]) is None
    assert Matcher().evaluate(c, requests[:1], files).evaluations[0].result == "MATCH"


def test_rule_is_not_specific_to_jojo_or_numbers_six_and_seven(case):
    c, requests, _ = case
    r = requests[0]
    r.season = 3
    r.media.seasons = [{"number": 3, "title": "Northern Lights", "air_date": "2026-01-01"}]
    c.title = "Unrelated Series: Northern Lights (TV-5) [2026] [1080p]"
    files = [TorrentFile(index=0, path="Northern Lights - 01.mkv", size=1000)]
    assert reject_reason(c, [r]) is None
    result = Matcher().evaluate(c, [r], files)
    assert result.evaluations[0].result == "MATCH"
    assert result.plan.bindings[0].episode_order == 30001
