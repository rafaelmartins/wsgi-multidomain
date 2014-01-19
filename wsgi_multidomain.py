# -*- coding: utf-8 -*-
"""
    wsgi_multidomain
    ~~~~~~~~~~~~~~~~
    
    Python module to create a single wsig application object, that can
    dispatches requests for other applications, based on the HTTP_HOST
    environment variable, implementing multi domain support.
    
    :copyright: (c) 2011 by Rafael Goncalves Martins
    :license: BSD, see LICENSE for more details.
"""

__all__ = ['Domain', 'Host', 'Dispatcher']
__author__ = 'Rafael G. Martins'
__email__ = 'rafael@rafaelmartins.eng.br'
__description__ = 'Multi domain WSGI dispatcher.'
__url__ = 'https://github.com/rafaelmartins/wsgi-multidomain'
__copyright__ = '(c) 2011 %s' % __author__
__license__ = 'BSD'
__version__ = '0.1pre'


def get_hostname(environ):
    rv = environ.get('HTTP_HOST', '')
    if rv == '':
        return None
    pos = rv.find(':')
    if pos == -1:
        return rv
    return rv[:pos]


def app_404(environ, start_response):
    start_response('404 NOT FOUND', [])
    return ['Domain not found: %s' % get_hostname(environ)]


class Domain(list):
    
    def __init__(self, domain):
        list.__init__(self, domain.split('.'))
        self.wildcards = []
        self.strings = []
        index = 0
        for piece in self:
            if piece == '*': # wildcard
                self.wildcards.append(index)
            else:
                self.strings.append(index)
            index += 1

    def __repr__(self):
        strings = []
        for i in self.strings:
            strings.append(str(i))
        wildcards = []
        for i in self.wildcards:
            wildcards.append(str(i))
        return '<%s %r: strings=%s; wildcards=%s>' % (
            self.__class__.__name__,
            '.'.join(self),
            ','.join(strings) if len(strings) > 0 else None,
            ','.join(wildcards) if len(wildcards) > 0 else None,
        )


class Host(Domain):
    
    def __init__(self, domain):
        Domain.__init__(self, domain)
        if len(self.wildcards) > 0:
            raise RuntimeError('Wildcards not supported by %r' % \
                self.__class__.__name__)

    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, '.'.join(self))


class Dispatcher(object):
    
    _domains = []
    
    def __init__(self, domains):
        for domain, app in domains:
            self.add_domain(domain, app)
    
    def add_domain(self, domain, app):
        self._domains.append((Domain(domain), app))
    
    def __call__(self, environ, start_response):
        hostname = get_hostname(environ)
        if hostname is None:
            return app_404(environ, start_response)
        host = Host(hostname)
        for domain, app in self._domains:
            if len(domain) != len(host):
                continue
            counter = 0
            for index in domain.strings:
                if domain[index] == host[index]:
                    counter += 1
            if counter == len(domain.strings):
                return app(environ, start_response)
        return app_404(environ, start_response)
