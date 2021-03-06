# -*- coding: utf-8
from __future__ import print_function
from ConfigParser import ConfigParser
import math
import tweepy
import os

class TwitterBot:
    """Just tweet!
    """

    def __init__(self, config = 'config.ini', verbose=0):
        # TODO: load from config
        try:
            cp = ConfigParser()
            cp.read(config)
            self._auth = tweepy.OAuthHandler(
                cp.get('General', 'twitter_consumer_key'),
                cp.get('General', 'twitter_consumer_secret'))
            self._auth.set_access_token(
                cp.get('General', 'twitter_access_token'),
                cp.get('General', 'twitter_access_secret'))
            self._api = tweepy.API(self._auth)
            self._verbose = verbose
            self._idstr = 'TwitterBot'
            if verbose > 0:
                print('[{0}] Initialized'.format(self._idstr))
        except Exception as e:
            # TODO: log.aterror
            print('An error occurred while loading config: {0}'.format(str(e)))
            raise

    """Tweeeeeeeeeet
    """
    def tweet(self, entry):
        tweets = self.prepare(entry)
        for i in xrange(len(tweets)):
            tweet = tweets[i]
            if self._verbose > 0:
                # TODO:log
                print('  Tweeting {0}/{1}'.format(i, len(tweets)))
            if self._verbose > 2:
                print(tweet)
            self._api.update_status(
                status = tweet["text"],
                media_ids = tweet["image_ids"])

    def prepare(self, entry):
        # Cannot include more than 4 images or 1 gif
        # return a list of prepared tweets, including text and pics
        if self._verbose > 0:
            print('  Filtering images...', end='')
        images_to_upload = filter(
            # TODO: handle oversize images
            lambda i: os.stat(i).st_size <= 3000000,
            map(
                lambda i: i.get_local_url(),
                filter(
                    lambda i: i.get_extension() != '.gif',
                    entry.get_images())))
        if self._verbose > 0:
            print('{0}[ok]'.format(str(len(images_to_upload))))
            print(
                '  Uploading {0} images...'.format(str(len(images_to_upload))),
                end='')
        image_ids = map(
            lambda m: m.media_id,
            map(self._api.media_upload, images_to_upload))
        if self._verbose > 0:
            print('[ok]')

        tweets = []
        n = len(image_ids)
        count = int(math.ceil(1.0 * n / 4))
        idx = 1
        while n > 0:
            if self._verbose > 1:
                print('  Preparing {0}/{1}...'.format(str(count), str(idx)),
                      end='')
            tweet = {
                "text": TwitterBot._format_text(entry, count, idx),
                "image_ids": image_ids[(idx - 1) * 4:idx * 4]
            }
            tweets.append(tweet)
            n -= 4
            idx += 1
            if self._verbose > 1:
                print('[ok]')

        return tweets

    @staticmethod
    def _format_text(entry=None, count=1, idx=1):
        # PATTERN: #乃木坂46 #$AUTHOR「$TITLE」：$CONTENT… $LINK[ $IDX/$COUNT]
        author = unicode(entry.get_author(), 'utf8')
        title = unicode(entry.get_title(), 'utf8')
        link = unicode(entry.get_permalink(), 'utf8')
        content = unicode(entry.get_text(), 'utf8')

        author_length = len(author)
        title_length = len(title)
        content_length = len(content)
        link_length = len(link)

        pattern = u'#乃木坂46 #{0}「{1}」：{2} {3}'.format
        counter_pattern = u''.format
        reserved_length = 12 + link_length
        if count > 1:
            counter_pattern = u' {0}/{1}'.format
            reserved_length += 6 # Extra counter reserves 6 chars

        # Prepare title
        space_for_title = 140 - reserved_length - author_length
        if title_length > space_for_title:
            title = title[0:space_for_title - 1] + u'…'
            title_length = len(title)

        # Prepare content
        space_for_content = 140 - reserved_length - author_length - title_length
        if content_length > space_for_content:
            content = content[0:space_for_content - 1] + u'…'

        text = (pattern(author, title, content, link)
            + counter_pattern(idx, count))
        return text.encode('utf8')