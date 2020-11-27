import random
import re
import string
from collections import defaultdict
from functools import wraps
from urllib.parse import urlparse

import metadata_parser
from flask import session, url_for, flash, g
from werkzeug.utils import redirect


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_id') is None or g.user is None:
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function


def generate_code(size=10, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def get_image_url_from_metadata(url):
    if is_amazon_domain(url):
        return get_amazon_image_url(url)
    else:
        try:
            page = metadata_parser.MetadataParser(url=url, search_head_only=True)
            return page.get_metadata_link('image')
        except Exception as e:
            from gifted import app
            app.logger.warn(f'Could not fetch image metadata from {urlparse(url).hostname}. {e}')
            return None


def is_amazon_domain(s):
    url = urlparse(s)
    return True if url is not None and url.hostname == 'www.amazon.com' else False


def get_amazon_image_url(url):
    img_url = 'https://ws-na.amazon-adsystem.com/widgets/q?_encoding=UTF8&MarketPlace=US' \
              '&ASIN={}&ServiceVersion=20070822&ID=AsinImage&WS=1&Format=SL250'
    asin_dp = re.search(r'(?<=dp/)[A-Z0-9]{10}', url)
    asin_gp = re.search(r'(?<=gp/product/)[A-Z0-9]{10}', url)
    asin_d = re.search(r'(?<=d/)[A-Z0-9]{10}', url)

    if asin_dp:
        return img_url.format(asin_dp.group(0))
    elif asin_gp:
        return img_url.format(asin_gp.group(0))
    elif asin_d:
        return img_url.format(asin_d.group(0))
    else:
        return None


def group_by(iterable, projection):
    result = defaultdict(list)
    for item in iterable:
        result[projection(item)].append(item)
    return result


def validate(username, password, password_confirm=None, redirect_to='main.login'):
    if not username:
        flash('Username is required!', 'warning')
        return redirect(url_for(redirect_to))
    if not password:
        flash('Password is required!', 'warning')
        return redirect(url_for(redirect_to))
    if password_confirm is not None and password != password_confirm:
        flash('Passwords must match!', 'warning')
        return redirect(url_for(redirect_to))
