import pytest
from lazarr.config import Requirements
from lazarr.sdk import MetadataItem, SubtaskRequest, Evidence
from lazarr_search_engine.matcher import Matcher
from lazarr_search_engine.selection import reject_reason
from conftest import candidate


@pytest.fixture
def rezero():
    media = MetadataItem(
        id="65942",
        kind="tv",
        title="Re:Zero",
        year=2016,
        episode_numbering={"1:39": [{"season": 2, "episode": 14}]},
    )
    return SubtaskRequest(
        id=1,
        media=media,
        season=1,
        episode=39,
        air_date="2021-01-06",
        requirements=Requirements(
            audio_languages=["ja"], subtitle_languages=["ru"], min_resolution=1080, max_resolution=2160
        ),
    )


@pytest.mark.parametrize(
    "title",
    [
        "Re:Zero (ТВ-1) [1080p]",
        "Re:Zero 3rd Season [1080p]",
        "Re:Zero / Сезон: 03 / Серии: 1-8 [1080p]",
        "Re:Zero [Movie] [1080p]",
        "Re:Zero (ТВ-2, часть 2) [720p]",
        "Re:Zero [manga]",
        "Re:Zero [PDF, RUS]",
        "(OST) Re:Zero FLAC tracks lossless",
        "Re:Zero (ТВ-2) [RUS(Dub)] [2020, ААС]",
        "[DL] Re:Zero [P] [ENG] [Scene]",
    ],
)
def test_explicit_contradictions_are_filtered_before_network(rezero, title):
    assert reject_reason(candidate(title=title, external_ids={}), [rezero])


def test_unknown_claims_partial_coverage_and_anime_numbering_are_kept(rezero):
    item = candidate(title="Re:Zero (ТВ-2, часть 2) [2021] [1080p]", external_ids={})
    assert reject_reason(item, [rezero]) is None
    assert reject_reason(candidate(title="Re:Zero / Сезон: 02 / [1080p]"), [rezero]) is None
    assert reject_reason(candidate(title="Re:Zero", external_ids={}), [rezero]) is None
    other = rezero.model_copy(update={"season": 3, "episode": 1})
    assert reject_reason(item, [other, rezero]) is None
    item.evidence = [
        Evidence(field="audio_languages", value=["ru"], source="description", scope="all_video_files")
    ]
    assert reject_reason(item, [rezero], detailed=True) is None
    item.evidence[0].complete = True
    assert reject_reason(item, [rezero], detailed=True)


def test_keyword_waits_for_description_and_subtitles_never_exclude(rezero):
    rezero.requirements.keyword = "Group"
    item = candidate(title="Re:Zero (ТВ-2) [1080p]", external_ids={})
    assert reject_reason(item, [rezero]) is None
    assert reject_reason(item, [rezero], detailed=True)
    item.description = "Released by GROUP"
    assert reject_reason(item, [rezero], detailed=True) is None


def test_season_identity_requires_title_season_and_episode_year(rezero):
    item = candidate(title="Re:Zero (ТВ-2, часть 2) [2021] [1080p]", external_ids={})
    assert Matcher().identity(item, rezero).result == "MATCH"
    assert Matcher().identity(item, rezero.model_copy(update={"air_date": None})).result == "UNKNOWN"
    assert (
        Matcher().identity(item.model_copy(update={"title": "Re:Zero (ТВ-3) [2021]"}), rezero).result
        == "UNKNOWN"
    )
    assert (
        Matcher().identity(item.model_copy(update={"title": "Unrelated (ТВ-2) [2021]"}), rezero).result
        == "UNKNOWN"
    )
    rezero.media.external_ids = {"imdb": "tt1"}
    assert (
        Matcher().identity(item.model_copy(update={"external_ids": {"imdb": "tt2"}}), rezero).result
        == "MISMATCH"
    )


def test_season_and_episode_ranges_keep_partial_coverage(rezero):
    assert reject_reason(candidate(title="Re:Zero S01-S03 1080p"), [rezero]) is None
    assert reject_reason(candidate(title="Re:Zero S02E01-E13 1080p"), [rezero])
    assert reject_reason(candidate(title="Re:Zero S02E14-E25 1080p"), [rezero]) is None


def test_conflicting_complete_audio_claims_remain_unknown(rezero):
    item = candidate(
        title="Re:Zero (ТВ-2) 1080p",
        external_ids={},
        evidence=[
            Evidence(
                field="audio_languages",
                value=[code],
                source="description",
                scope="all_video_files",
                complete=True,
            )
            for code in ["ru", "ja"]
        ],
    )
    assert reject_reason(item, [rezero], detailed=True) is None
