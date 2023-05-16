from tests.factories import MediaFileFactory
from chowda.models import MediaFile
from pytest import fixture, mark, raises
from typing import Literal


@fixture
def valid_guid():
    return 'cpb-aacip-191-29b5mpvv'


@fixture
def media_file_valid_guid(valid_guid: Literal['cpb-aacip-191-29b5mpvv']):
    return MediaFileFactory.create(guid=valid_guid)


@fixture
def media_file_with_sonyci_asset(valid_guid: Literal['cpb-aacip-191-29b5mpvv']):
    return MediaFileFactory.create(guid=valid_guid)


@mark.vcr()
def test_sonyci_asset(media_file_with_sonyci_asset: MediaFile):
    assert type(media_file_with_sonyci_asset.sonyci_asset) == dict


def test_media_file_ci_asset(media_file_valid_guid: MediaFile):
    assert type(media_file_valid_guid.sonyci_asset) == dict


def test_has_media_validation():
    with raises(TypeError) as error_info:
        MediaFileFactory.create(guid='not-a-guid')
    assert error_info.text == 'blerg'
