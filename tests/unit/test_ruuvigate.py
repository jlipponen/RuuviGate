import ruuvigate
import pytest
import os

TAGS_EMPTY_PATH = os.path.dirname(__file__) + "/TAGS_EMPTY.yml"
TAGS_NONEXISTING_PATH = os.path.dirname(__file__) + "/TAGS_NONEXISTING.yml"
THIS_FILE_PATH = os.path.dirname(__file__)
COMMON_VALID_CMD_ARGS = ['__main__.py', '-r', TAGS_EMPTY_PATH]

# Create new file if doesn't exist, clear if exists
open(TAGS_EMPTY_PATH, "w")
# Delete the file if exists
if os.path.exists(TAGS_NONEXISTING_PATH):
    os.remove(TAGS_NONEXISTING_PATH)

@pytest.mark.parametrize("args", [
    # stdout mode
    ['-m', 'stdout'],
    ['-m', 'stdout', '-i', '123456789'],
    ['-m', 'stdout', '-i', '12345678', '-l', 'CRITICAL'],
    ['-m', 'stdout', '-i', '1234567', '-l', 'ERROR', '-c', THIS_FILE_PATH],
    ['-m', 'stdout', '-i', '123456', '-l', 'WARNING', '-c', THIS_FILE_PATH, '--simulate'],
    # azure mode
    ['-m', 'azure', '-c', THIS_FILE_PATH],
    ['-m', 'azure', '-c', THIS_FILE_PATH, '-i', '09999'],
    ['-m', 'azure', '-c', THIS_FILE_PATH, '-i', '00999', '-l', 'INFO'],
    ['-m', 'azure', '-c', THIS_FILE_PATH, '-i', '00099', '-l', 'DEBUG'],
    ['-m', 'azure', '-c', THIS_FILE_PATH, '-i', '00009', '-l', 'NOTSET', '--simulate'],
    # default mode
    ['-c', THIS_FILE_PATH],
    ['-c', THIS_FILE_PATH, '-i', '4'],
    ['-c', THIS_FILE_PATH, '-i', '3', '-l', 'WARNING'],
    ['-c', THIS_FILE_PATH, '-i', '2', '-l', 'WARNING'],
    ['-c', THIS_FILE_PATH, '-i', '1', '-l', 'WARNING', '--simulate']
])
def test_valid_cmd_args(monkeypatch, args):
    monkeypatch.setattr('sys.argv', COMMON_VALID_CMD_ARGS + args)
    ruuvigate.__main__.parse_args()

@pytest.mark.parametrize("args", [
    [],
    ['--illegelflag'],
    ['-m', 'illegalmode'],
    ['-c', TAGS_NONEXISTING_PATH],
    ['-c', THIS_FILE_PATH, '-i', '0'],
    ['-c', THIS_FILE_PATH, '-i', '-123456789'],
    ['-c', THIS_FILE_PATH, '-l', 'ILLEGALLEVEL']
])
def test_invalid_cmd_args(monkeypatch, capsys, args):
    monkeypatch.setattr('sys.argv', COMMON_VALID_CMD_ARGS + args)
    with pytest.raises(SystemExit) as excinfo:
        ruuvigate.__main__.parse_args()
    assert excinfo.value.code != 0
    captured = capsys.readouterr()
    assert 'usage' in captured.err
