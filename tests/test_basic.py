import logging


async def test_disabling_access_logging(no_log_test_cli, caplog):
    """
    GET request
    """
    caplog.set_level(logging.INFO)

    resp = await no_log_test_cli.get('/test_get')
    assert resp.status == 200
    resp = await no_log_test_cli.get('/test_get')
    assert resp.status == 200

    # We should get no access logging
    for record in caplog.records:
        assert record.name not in ('access', 'sanic.access')


async def test_json_access_logging(test_cli, caplog):
    """
    GET request
    """
    caplog.set_level(logging.INFO)

    resp = await test_cli.get('/test_get')
    assert resp.status == 200

    # We should get no access logging
    for record in caplog.records:
        if record.name == 'sanic.access':
            # Check log record has data passed from access logging middleware
            assert hasattr(record, 'request')
            assert hasattr(record, 'response')
            assert hasattr(record, 'time')
            assert hasattr(record, 'req_id')

# Currently cant get pytest to do tasklocal
# async def test_normal_log_has_req_id(test_cli, caplog):
#     """
#     GET request
#     """
#     caplog.set_level(logging.INFO)
#
#     resp = await test_cli.get('/test_get')
#     assert resp.status == 200
#
#     # We should get no access logging
#     for record in caplog.records:
#         if record.name == 'root':
#             assert hasattr(record, 'req_id')
