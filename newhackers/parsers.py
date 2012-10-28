import re
import time

from bs4 import BeautifulSoup
from parsedatetime import parsedatetime as pdt
import redis

from newhackers import config


cal = pdt.Calendar()
rdb = redis.Redis(db=8)


def parse_comments(page):
    """Parse comments from an HN comments page

    :page: an HTML document with comments

    Returns a dict of metadata about the story and a list of comments. E.g.

    {'title': "I sooo don't like Apple anymore",
     'link': "http://iwoz.woo",
     'comments_no': 1337,
     'score': 42,
     'time': 1350901062.0,
     'author': 'woz',
     'comments': [
        {'author': 'foo',
         'body': 'lorem ipsum',
         'link': '123123123',
         'time': 1350901232.0},
        {'author': 'bar',
         'body': 'lorem ipsum',
         'link': '321321321',
         'time': 1350901244.0},
         ...]
     }

    """
    soup = BeautifulSoup(page)
    more, titles = _parse_links(soup)
    assert more is None
    assert len(titles) == 1
    
    subtexts = _parse_subtexts(soup)
    assert len(subtexts) == 1

    resp = titles[0]
    resp.update(subtexts[0])

    resp['comments'] = _parse_comments(soup)
    if not resp['comments_no']:
        assert len(resp['comments']) == 0
    if resp['comments_no'] != -1:
        assert len(resp['comments']) == resp['comments_no']

    return resp


def _parse_comments(soup):
    """Extract all the comments from a comments page.

    Returns None if this page has no comments.

    """
    com_spans = soup.find_all('span', 'comhead')
    if not com_spans:
        return None

    # first comhead belongs to the story title
    com_spans.pop(0)

    comment_bodies = soup.find_all('span', 'comment')

    comments = []
    for head, body in zip(com_spans, comment_bodies):
        comment = {}
        try:
            comment['author'], c_time = re.search(
                '\s+(\w+)\s+((?:\w+ )+)', head.text).groups()
        except AttributeError:
            # ignore deleted comments
            assert not head.text
            continue
        comment['time'] = _decode_time(c_time)
        comment['link'] = head.find_all('a')[1]['href'].split('item?id=')[1]
        comment['body'] = body.text.strip()
        comments.append(comment)

    return comments
    

def parse_stories(page):
    """Parse stories from an HN stories page

    :page: an HTML document which contains 30 stories

    Returns a dict with a more link and a list of stories dicts. E.g.

    {'more': '4AVKeJz9TP',
     'stories': [
          {'title': "I sooo don't like Apple anymore",
           'link': "http://iwoz.woo",
           'comments_no': 1337,
           'score': 42,
           'time': 1350901062.0,
           'author': 'woz'},

          {'title': "Work for my startup for free",
           'link': "item?id=1111",
           'time': 1351333328.0,
           'score': None,
           'author': None,
           'comments_no': None},

           ...]}

    """
    soup = BeautifulSoup(page)

    more, stories = _parse_links(soup)
    assert len(stories) == config.STORIES_PER_PAGE

    subtexts = _parse_subtexts(soup)
    assert len(subtexts) == config.STORIES_PER_PAGE

    for story, subtext in zip(stories, subtexts):
        story.update(subtext)
    
    return dict(stories=stories, more=more)


def _parse_links(soup):
    """Return a more link and a list of title/link dicts

    Returns e.g.

    ('RDXC3fdF',
     [{'title': "I sooo don't like Apple anymore",
       'link': "http://iwoz.woo"},
      {'title': "Work for my startup for free",
       'link': "item?id=1111"}
       ...]
    )

    """
    # each story link is divided into two <td>s:
    # - the number of the story (first story on the first page is 1.)
    # - the title and link of the story
    # The title and the link don't have a valign attribute
    # Finally there is a 'More' link to the next page of stories.
    titles = soup.find_all("td", "title", valign=False)

    # comments pages have only one title and no 'More' link
    if len(titles) == 1:
        more = None
    else:
        more = _extract_more(titles.pop(-1))
        
    stories = [{'title': title.text.strip().split('\n')[0],
                'link': title.find("a")["href"]}
               for title in titles]

    return more, stories


def _parse_subtexts(soup):
    """Returns a list of dictionaries with stories metadata

    Returns e.g.
    
     [{'comments_no': 1337,
       'score': 42,
       'time': 1350901062.0,
       'author': 'woz'},

      {'time': 1351333328.0,
       'score': None,
       'author': None,
       'comments_no': None},
      ...]

    Returns None if no comments were found

    """
    # Some other data about each submission is stored in <td
    # class="subtext"> elements
    metadata = soup.find_all("td", "subtext")
    if not metadata:
        return None

    stories = [{} for i in range(len(metadata))]

    # The content of the <td class="subtext"> differs. There are three classes:
    # 1. normal stories with all the metadata (Ask HNs included)
    # 2. stories without comments - contain a discuss link instead of
    # number of comments
    # 3. Jobs - no comments, no author, no score
    for s, meta in enumerate(metadata):
        # Jobs post
        if 'point' in meta.text:
            story_time = re.search('\s+(.*?)\s+\|', meta.text).group(1)
            stories[s]['time'] = _decode_time(story_time)
            stories[s]['score'] = int(re.search(
                    "(\d+)\s+points?", meta.text).group(1))
            stories[s]['author'] = meta.a.text.strip()
            if 'discuss' in meta.text:  # Zero comments
                stories[s]['comments_no'] = 0
            else:
                try:
                    stories[s]['comments_no'] = int(re.search(
                            "(\d+)\s+comments?", meta.text).group(1))
                except AttributeError:
                    # I found an instance where there was just the text
                    # 'comments', without any count. I'm assuming that
                    # even stranger things could happen
                    stories[s]['comments_no'] = -1

        else:  # Jobs post
            stories[s]['time'] = _decode_time(meta.text.strip())
            stories[s]['comments_no'] = None
            stories[s]['score'] = None
            stories[s]['author'] = None

    return stories


def _extract_more(more_soup):
    """Extract a page identifier from the <a> element in a BeautifulSoup"""
    return more_soup.find("a")['href'].split('fnid=')[-1]


def _decode_time(timestamp):
    """Decode time from a relative timestamp to a localtime float"""
    return time.mktime(cal.parse(timestamp)[0])

