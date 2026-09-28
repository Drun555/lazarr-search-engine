from lazarr.sdk import TorrentFile
from lazarr_search_engine.selection import assess_candidate, candidate_rank, reject_reason
from lazarr_search_engine.matcher import Matcher
from conftest import request, candidate, audio_claim


def test_title_year_beats_number_alone_and_duplicates_do_not_stack(media):
    media.external_ids = {}
    media.seasons = [{"number": 1, "title": "Northern Lights", "air_date": "2024-01-01"}]
    req = request(media)
    strong = candidate(title="Northern Lights (2024) TV-7 720p", external_ids={}, seeds=1)
    weak = candidate(title="Example Show TV-1 1080p", external_ids={}, seeds=10000)
    assert candidate_rank(strong, [req]) < candidate_rank(weak, [req])
    first = assess_candidate(strong, req)
    repeated = strong.model_copy(
        update={
            "title": strong.title + " / Northern Lights (2024) TV-7",
            "description": "Title: Northern Lights\nYear: 2024",
        }
    )
    assert assess_candidate(repeated, req, 2).total == first.total
    assert len([s for s in first.signals if s.group == "identity"]) == 1


def test_description_can_confirm_identity_without_counting_synopsis_mentions(media):
    media.external_ids = {}
    req = request(media)
    c = candidate(title="Example Show 1080p", external_ids={}, description="Title: Example Show\nYear: 2020")
    assert assess_candidate(c, req, 1).passed
    assert not assess_candidate(c.model_copy(update={"description": ""}), req, 2).passed
    topic = assess_candidate(c, req, 2)
    assert topic.passed
    assert topic.signals[0].source == "description"
    assert Matcher().identity(c, req).result == "MATCH"
    c.description = "A story mentioning Example Show and the year 2020."
    assert not assess_candidate(c, req, 2).passed


def test_absent_episode_is_manual_only_and_never_in_download_plan(media):
    req = request(media, episode=3)
    c = candidate()
    files = [TorrentFile(index=0, path="Show.S01E01.1080p.mkv", size=1000)]
    report = Matcher().evaluate(c, [req], files)
    result = report.evaluations[0]
    assert result.result == "MISMATCH"
    assert result.manual_candidate and result.needs_mapping
    assert not result.scoring[-1].passed
    assert report.plan is None
    assert result.scoring[-1].blockers


def test_unknown_episode_is_manual_only(media):
    req = request(media)
    result = (
        Matcher()
        .evaluate(candidate(), [req], [TorrentFile(index=0, path="video.mkv", size=1000)])
        .evaluations[0]
    )
    assert result.result == "UNKNOWN"
    assert result.manual_candidate and result.needs_mapping


def test_verified_file_evidence_replaces_claims_and_blocks_auto(media):
    req = request(media)
    path = "Show.S01E01.1080p.mkv"
    c = candidate(evidence=[audio_claim(path, ["en"])])
    report = Matcher().evaluate(c, [req], [TorrentFile(index=0, path=path, size=1000)])
    result = report.evaluations[0]
    assert result.score >= result.scoring[-1].threshold
    assert not result.scoring[-1].passed
    assert result.result == "MISMATCH"
    assert not result.manual_candidate
    assert report.plan is None


def test_wrong_external_id_blocks_every_stage_and_recommendation(media):
    req = request(media)
    c = candidate(external_ids={"imdb": "tt999"})
    for stage in (1, 2, 3):
        assert not assess_candidate(c, req, stage).passed
    result = Matcher().evaluate(c, [req], [TorrentFile(index=0, path="video.mkv", size=1000)]).evaluations[0]
    assert not result.manual_candidate


def test_title_missing_episode_is_not_filtered_before_manual_mapping(media):
    req = request(media, episode=3)
    assert reject_reason(candidate(title="Example Show S01E01 (2020) 1080p"), [req]) is None


def test_no_playable_video_is_not_recommended(media):
    result = (
        Matcher()
        .evaluate(candidate(), [request(media)], [TorrentFile(index=0, path="readme.txt", size=10)])
        .evaluations[0]
    )
    assert not result.manual_candidate


def test_exact_series_alias_and_season_year_outweigh_tv_number(media):
    media.external_ids = {}
    media.aliases = ["Example Alias"]
    media.seasons = [{"number": 1, "title": "Season 1", "air_date": "2024-01-01"}]
    req = request(media)
    req.air_date = "2024-01-01"
    c = candidate(
        title="Example Alias (2024) TV-7 1080p", external_ids={}, evidence=[audio_claim("Show - 01.mkv")]
    )
    weak = candidate(title="Example Show TV-1 1080p", external_ids={})
    assert candidate_rank(c, [req]) < candidate_rank(weak, [req])
    assert reject_reason(c, [req]) is None
    result = Matcher().evaluate(c, [req], [TorrentFile(index=0, path="Show - 01.mkv", size=1000)])
    assert result.evaluations[0].result == "MATCH"
    media.seasons.append({"number": 2, "title": "Season 2", "air_date": "2024-05-01"})
    assert reject_reason(c, [req]) == "Указан другой сезон"


def test_series_original_year_does_not_override_later_season_tv_number(media):
    media.external_ids = {}
    media.seasons = [{"number": 1, "title": "Season 1", "air_date": "2024-01-01"}]
    req = request(media)
    req.air_date = "2024-01-01"
    assert (
        reject_reason(candidate(title="Example Show (2020) TV-7", external_ids={}), [req])
        == "Указан другой сезон"
    )
