import pytest

from substra.sdk import rest_client, exceptions

from .utils import mock_requests


CONFIG = {
    'url': 'http://foo.com',
    'version': '1.0',
    'auth': False,
    'insecure': False,
}

CONFIG_SECURE = {
    'url': 'http://foo.com',
    'version': '1.0',
    'auth': {
        'user': 'foo',
        'password': 'bar',
    },
    'insecure': False,
}

CONFIG_INSECURE = {
    'url': 'http://foo.com',
    'version': '1.0',
    'auth': {
        'user': 'foo',
        'password': 'bar',
    },
    'insecure': True,
}

CONFIGS = [CONFIG, CONFIG_SECURE, CONFIG_INSECURE]


@pytest.mark.parametrize("config", CONFIGS)
def test_post_success(mocker, config):
    m = mock_requests(mocker, "post", response={})
    rest_client.Client(config).add('http://foo', {})
    assert len(m.call_args_list) == 1


@pytest.mark.parametrize("status_code, http_response, sdk_exception", [
    (400, {"message": "Invalid Request"}, exceptions.InvalidRequest),

    (404, {"message": "Not Found"}, exceptions.NotFound),

    (408, {"pkhash": "a-key"}, exceptions.RequestTimeout),
    (408, {}, exceptions.RequestTimeout),

    (409, {"pkhash": "a-key"}, exceptions.AlreadyExists),
    (409, {"pkhash": ["a-key", "other-key"]}, exceptions.AlreadyExists),

    (500, "CRASH", exceptions.InternalServerError),
])
def test_request_http_errors(mocker, status_code, http_response, sdk_exception):
    m = mock_requests(mocker, "post", response=http_response, status=status_code)
    with pytest.raises(sdk_exception):
        rest_client.Client(CONFIG).add('http://foo', {})
    assert len(m.call_args_list) == 1


def test_add_timeout_with_retry(mocker):
    asset_name = "traintuple"
    m_post = mock_requests(mocker, "post", response={"pkhash": "a-key"}, status=408)
    m_get = mock_requests(mocker, "get", response={"pkhash": "a-key"})
    asset = rest_client.Client(CONFIG).add(asset_name)
    assert len(m_post.call_args_list) == 1
    assert len(m_get.call_args_list) == 1
    assert asset == {"pkhash": "a-key"}


def test_add_exist_ok(mocker):
    asset_name = "traintuple"
    m_post = mock_requests(mocker, "post", response={"pkhash": "a-key"}, status=409)
    m_get = mock_requests(mocker, "get", response={"pkhash": "a-key"})
    asset = rest_client.Client(CONFIG).add(asset_name, exist_ok=True)
    assert len(m_post.call_args_list) == 1
    assert len(m_get.call_args_list) == 1
    assert asset == {"pkhash": "a-key"}
