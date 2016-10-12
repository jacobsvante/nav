import subprocess as subp


def test_importable():
    from nav_requests import meta  # noqa


def test_runnable():
    proc = subp.run(['navrequest'], stdout=subp.PIPE)
    assert b'{meta,page-results}' in proc.stdout
