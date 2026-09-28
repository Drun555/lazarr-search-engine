from lazarr.sdk import MetadataItem, TorrentFile
from lazarr_search_engine.associations import related_files
from lazarr_search_engine.provider_utils import search_titles


def files(*paths):
    return [TorrentFile(index=i, path=path, size=100, offset=i * 100) for i, path in enumerate(paths)]


def test_smart_groups_without_episode_metadata():
    assert related_files(files("Pilot.mkv", "Pilot.ru.flac", "Pilot.en.srt", "Finale.mkv")) == {
        0: [1, 2],
        3: [],
    }


def test_ambiguous_sidecars_are_not_assigned():
    assert related_files(files("1080/Show.S01E01.mkv", "720/Show.S01E01.mkv", "Show.S01E01.srt")) == {
        0: [],
        1: [],
    }


def test_search_titles_are_deduplicated():
    media = MetadataItem(id="1", kind="tv", title="Example", original_title="Example", year=2020)
    titles = search_titles(media)
    assert titles
    assert len(titles) == len(set(titles))
