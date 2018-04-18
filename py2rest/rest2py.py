from __future__ import division

import requests
from requests import Request, Session

DFLT_ROOT_URL = 'https://dev.otosense.ai/'

class Rest2Py(object):
    def __init__(self, root_url, py2rest, attr_list=()):
        self.root_url = root_url
        self.py2rest = py2rest

        if attr_list:
            permissible_attr_set = set(attr_list)
        else:
            if hasattr(self.py2rest.permissible_attr, 'permissible_attrs'):
                permissible_attrs = self.py2rest.permissible_attrs.permissible_attr
                if isinstance(permissible_attrs, dict) and 'include' in permissible_attrs:
                    permissible_attrs = set(permissible_attrs['include']).difference(
                        permissible_attrs.get('exclude', {}))
                elif not isinstance(permissible_attrs, (list, set, tuple)):
                    raise ValueError("Not sure how to get a list of permissiable attributes from: {}".format(
                        permissible_attrs))
                permissible_attr_set = set(permissible_attrs)
            elif isinstance(self.py2rest.permissible_attr, (tuple, list, set)):
                permissible_attr_set = set(self.py2rest.permissible_attr)

    def attr_obj(self, attr):
        pass


class API(object):
    def __init__(self, root_url=DFLT_ROOT_URL, route_root=None):
        if not root_url.endswith('/'):
            root_url += '/'
        if route_root is None:
            route_root = ''
        else:
            if not route_root.endswith('/'):
                route_root += '/'
        self.root_url = root_url + route_root
        self.session = Session()
        self.last_request = None

    def url(self, url_suffix):
        return self.root_url + url_suffix

    def request(self, url_suffix, method=None, **kwargs):
        return Request(method=method, url=self.url(url_suffix), **kwargs)

    def prepare_and_send_request(self, req, **kwargs):
        return self.session.send(req.prepare(), **kwargs)

    def ping(self):
        return requests.get(self.root_url + 'ping')

    def call_attr(self, attr, **kwargs):
        url_suffix = '?attr={attr}'.format(attr=attr)
        req = self.request(method='POST', url_suffix=url_suffix, json=kwargs)
        self.last_request = req
        response = self.prepare_and_send_request(req)
        if response.status_code != 200:
            self.last_non_200_response = response
        return response.content
        # '?attr = can_projects & access = c_citypa_3 @ otosense.com, fv_mgc, prod'

