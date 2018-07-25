import datetime

from gidgethub import sansio

from ..webapp import router

class FakeRateLimit:
    def __init__(self, *, remaining=5000, limit=5000, reset_datetime=None):
        self.remaining = remaining
        self.limit = limit
        now = datetime.datetime.now(datetime.timezone.utc)
        self.reset_datetime = reset_datetime or now + datetime.timedelta(hours=1)

class FakeGH:
    def __init__(self, *, getitem=None, getiter=None, rate_limit=None, post=None):
        self._getitem = getitem
        self._getiter = getiter
        self._post = post
        self.getiter_url = None
        self.getitem_url = None
        self.post_urls = []
        self.post_data = []
        self.rate_limit = rate_limit or FakeRateLimit()

    async def getitem(self, url):
        self.getitem_url = url
        return self._getitem_return[self.getitem_url]

    async def getiter(self, url):
        self.getiter_url = url
        for item in self._getiter_return:
            yield item

    async def post(self, url, *, data):
        self.post_urls.append(url)
        self.post_data.append(data)
        return self._post

def _assert_gh_is_empty(gh):
    assert gh._getitem == None
    assert gh._getiter == None
    assert gh._post == None
    assert gh.getiter_url == None
    assert gh.getitem_url == None
    assert gh.post_urls == []
    assert gh.post_data == []

async def test_closed_without_merging():
    gh = FakeGH()
    event_data = {
        'pull_request': {
            'number': 1,
            'state': 'closed',
            },
        }
    closed_event = sansio.Event(event_data, event='pull_request', action='closed')
    synchronize_event = sansio.Event(event_data, event='pull_request', action='synchronize')
    edited_event = sansio.Event(event_data, event='pull_request', action='edited')

    for event in [closed_event, synchronize_event, edited_event]:
        res = await router.dispatch(event, gh)
        assert res is None
        _assert_gh_is_empty(gh)
