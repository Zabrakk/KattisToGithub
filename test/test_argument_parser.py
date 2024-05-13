from src.argument_parser import parse_arguments


def test_parse_short_arguments():
    parser = parse_arguments(['-u', 'my_username', '-p', 'my_password', '-d', '../../Solutions'])
    assert parser.user == 'my_username'
    assert parser.password == 'my_password'
    assert parser.directory == '../../Solutions'
    assert parser.update is False


def test_long_arguments():
    parser = parse_arguments(['--user', 'my_username', '--password', 'my_password', '--directory', '../../Solutions', '--update'])
    assert parser.user == 'my_username'
    assert parser.password == 'my_password'
    assert parser.directory == '../../Solutions'
    assert parser.update is True
