from tests.factories import MediaFileFactory
from chowda.models import MediaFile
from pytest import fixture, mark


@fixture
def valid_guid() -> str:
    return 'cpb-aacip-191-29b5mpvv'


@fixture
def media_file_with_sonyci_asset(valid_guid: str) -> MediaFile:
    return MediaFileFactory.create(guid=valid_guid)


@mark.vcr()
def test_sonyci_asset(media_file_with_sonyci_asset: MediaFile):
    assert type(media_file_with_sonyci_asset.sonyci_asset) == dict
    assert (
        media_file_with_sonyci_asset.sonyci_asset['id']
        == '26013d6bdcce47fc9812bb7dc3ed44ff'
    )
