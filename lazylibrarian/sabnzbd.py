import os
import urllib
import urllib2
import socket
import ssl
import datetime
import json
import lazylibrarian

from lazylibrarian import logger, database, formatter


def checkLink():
    # connection test, check host/port
    auth = SABnzbd(nzburl='auth')
    if not auth:
        return "Unable to talk to SABnzbd, check HOST/PORT"
    # check apikey is valid
    cats = SABnzbd(nzburl='get_cats')
    if not cats:
        return "Unable to talk to SABnzbd, check APIKEY"
    # check category exists
    if lazylibrarian.SAB_CAT:
        if lazylibrarian.SAB_CAT not in cats['categories']:
            msg = "SABnzbd: Unknown category [%s]\n" % lazylibrarian.SAB_CAT
            if catlist:
                msg += "Valid categories:\n"
                msg += str(cats['categories'])
            else:
                msg += "SABnzbd seems to have no categories set"
            return msg
    return "SABnzbd connection successful"


def SABnzbd(title=None, nzburl=None):

    HOST = "%s:%i" % (lazylibrarian.SAB_HOST, lazylibrarian.SAB_PORT)
    if not HOST.startswith("http"):
        HOST = 'http://' + HOST

    if lazylibrarian.SAB_SUBDIR:
        HOST = HOST + "/" + lazylibrarian.SAB_SUBDIR

    params = {}

    if nzburl == 'auth' or nzburl == 'get_cats':
        params['mode'] = nzburl
        params['output'] = 'json'
        if lazylibrarian.SAB_API:
            params['apikey'] = lazylibrarian.SAB_API
        title = 'Test ' + nzburl
        # connection test, check auth mode or get_cats
    else:
        params['mode'] = 'addurl'
        params['output'] = 'json'
        if nzburl:
            params['name'] = nzburl
        if title:
            params['nzbname'] = title
        if lazylibrarian.SAB_USER:
            params['ma_username'] = lazylibrarian.SAB_USER
        if lazylibrarian.SAB_PASS:
            params['ma_password'] = lazylibrarian.SAB_PASS
        if lazylibrarian.SAB_API:
            params['apikey'] = lazylibrarian.SAB_API
        if lazylibrarian.SAB_CAT:
            params['cat'] = lazylibrarian.SAB_CAT
        if lazylibrarian.USENET_RETENTION:
            params["maxage"] = lazylibrarian.USENET_RETENTION

# FUTURE-CODE
#    if lazylibrarian.SAB_PRIO:
#        params["priority"] = lazylibrarian.SAB_PRIO
#    if lazylibrarian.SAB_PP:
#        params["script"] = lazylibrarian.SAB_SCRIPT

    URL = HOST + "/api?" + urllib.urlencode(params)

    # to debug because of api
    logger.debug(u'Request url for <a href="%s">SABnzbd</a>' % URL)

    try:
        request = urllib2.urlopen(URL, timeout=30)
    except (socket.error) as e:
        logger.error(u"Timeout connecting to SAB with URL: %s" % URL)
        return False
    except (EOFError, IOError, urllib2.URLError) as e:
        if hasattr(e, 'reason'):
            errmsg = e.reason
        elif hasattr(e, 'strerror'):
            errmsg = e.strerror
        else:
            errmsg = str(e)

        logger.error(u"Unable to connect to SAB with URL: %s, %s" % (URL, errmsg))
        return False

    except (urllib2.HTTPError, ssl.SSLError) as e:
        logger.error(u"Invalid SAB host, check your config. Current host: %s" % HOST)
        return False

    result = json.loads(request.read())
    if not result:
        log.error("SABnzbd didn't return any json")
        return False

    logger.debug("Result text from SAB: " + str(result))
    if title and title.startswith('Test'):
        return result
    elif result['status'] is True:
        logger.info(title + " sent to SAB successfully.")
        return result['nzo_ids'][0]
    elif result['status'] is False:
        logger.error("SAB returned Error: %s" % result['error'])
        return False
    else:
        logger.error("Unknown error: " + str(result))
        return False
