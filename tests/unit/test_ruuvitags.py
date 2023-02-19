from ruuvigate.__main__ import RuuviTags
import asyncio
import pytest
import os

TAGS_EMPTY_PATH = os.path.dirname(__file__) + "/TAGS_EMPTY.yml"
TAGS_NONEXISTING_PATH = os.path.dirname(__file__) + "/TAGS_NONEXISTING.yml"
TAGS_MALFORMED_PATH = os.path.dirname(__file__) + "/TAGS_MALFORMED.yml"
TAGS_PATH = os.path.dirname(__file__) + "/TAGS.yml"
MAC_VALID1 = "12:34:56:78:90:AB"
MAC_VALID2 = "12:34:56:78:90:AC"
MAC_VALID3 = "aa:34:ab:78:90:ac"
MAC_MALFORMED1 = "12:34:5X:78:90:AB"
MAC_MALFORMED2 = "12:34:56:78:90:A"
MAC_MALFORMED3 = "12:34:56:78:90:AB:12"

@pytest.mark.asyncio
async def test_open_empty():
    # Create new file if doesn't exist, clear if exists
    open(TAGS_EMPTY_PATH, "w")
    tags = RuuviTags(TAGS_EMPTY_PATH)
    assert len(open(TAGS_EMPTY_PATH, "r").read()) == 0
    assert len(await tags.get_macs()) == 0

@pytest.mark.asyncio
@pytest.mark.parametrize("content", [
    [MAC_VALID1 + "\n"],
    [MAC_VALID2],
    [MAC_VALID1 + "\n", MAC_VALID2],
    [MAC_VALID1 + "\n", MAC_VALID2 + "\n", MAC_VALID1 + "\n", MAC_VALID2 + "\n"]
])
async def test_open_non_empty(content: list):
    open(TAGS_PATH, "w").writelines(content)
    # Strip the newlines from test input list
    content = [line.rstrip() for line in content]
    assert content == await RuuviTags(TAGS_PATH).get_macs()

@pytest.mark.asyncio
async def test_open_new():
    # Delete the file if exists
    if os.path.exists(TAGS_NONEXISTING_PATH):
        os.remove(TAGS_NONEXISTING_PATH)
    macs = await RuuviTags(TAGS_NONEXISTING_PATH).get_macs()
    assert os.path.exists(TAGS_NONEXISTING_PATH) == True
    assert len(macs) == 0

@pytest.mark.parametrize("content", [
    ["illegal line\n"],
    [MAC_VALID1 + "\n", "legal and illegal line"],
    [MAC_VALID1 + "\n", "            legal and illegal line"],
    [MAC_VALID1 + "\n", "\n", "legal, empty and illegal line"],
    ["\n", "\n", "\n", "empty lines and illegal line"],
    [MAC_VALID1, MAC_VALID1 + "\n"],
    [MAC_MALFORMED1 + "\n"],
    [MAC_MALFORMED1],
    [MAC_MALFORMED2 + "\n"],
    [MAC_MALFORMED2],
    [MAC_MALFORMED3 + "\n"],
    [MAC_MALFORMED3]
])
def test_open_malformed(content: list):
    open(TAGS_MALFORMED_PATH, "w").writelines(content)
    with pytest.raises(ValueError):
        RuuviTags(TAGS_MALFORMED_PATH)

@pytest.mark.asyncio
@pytest.mark.parametrize("macs", [
    [MAC_VALID1],
    [MAC_VALID1, MAC_VALID2],
    [MAC_VALID1, MAC_VALID2, MAC_VALID3]
])
async def test_add_unique_macs(macs: list):
    # Create new file if doesn't exist, clear if exists
    open(TAGS_EMPTY_PATH, "w")
    tags = RuuviTags(TAGS_EMPTY_PATH)
    for mac in macs:
        assert await tags.add_mac(mac)
    assert macs == await tags.get_macs()

@pytest.mark.asyncio
@pytest.mark.parametrize("macs", [
    [MAC_VALID1, MAC_VALID1],
    [MAC_VALID1, MAC_VALID2, MAC_VALID1],
    [MAC_VALID1, MAC_VALID2, MAC_VALID3, MAC_VALID3]
])
async def test_add_non_unique_macs(macs: list):
    open(TAGS_EMPTY_PATH, "w")
    tags = RuuviTags(TAGS_EMPTY_PATH)
    for mac in macs:
        if (await tags.get_macs()).count(mac) == 0:
            assert await tags.add_mac(mac)
        else:
            assert not await tags.add_mac(mac)
    assert list(dict.fromkeys(macs)) == await tags.get_macs()

@pytest.mark.parametrize("macs", [
    [MAC_MALFORMED1],
    [MAC_MALFORMED2],
    [MAC_MALFORMED3]
])
def test_detect_malformed_macs(macs: list):
    for mac in macs:
        assert not RuuviTags.is_legal_mac(mac)

@pytest.mark.asyncio
@pytest.mark.parametrize("macs", [
    [MAC_VALID1, MAC_MALFORMED1],
    [MAC_VALID1, MAC_VALID2, MAC_VALID3, MAC_MALFORMED1],
    [MAC_VALID1, MAC_VALID2, MAC_VALID3, MAC_MALFORMED1, MAC_VALID3],
])
async def test_add_malformed_mac(macs: list):
    open(TAGS_EMPTY_PATH, "w")
    tags = RuuviTags(TAGS_EMPTY_PATH)
    for mac in macs:
        if not RuuviTags.is_legal_mac(mac):
            with pytest.raises(ValueError):
                await tags.add_mac(mac)
        else:
            await tags.add_mac(mac)
