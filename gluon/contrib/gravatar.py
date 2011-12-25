"""
Python module for interacting with Gravatar.
"""
__author__  = 'Eric Seidel'
__version__ = '0.0.5'
__email__   = 'gridaphobe@gmail.com'

from urllib import urlencode
from urllib2 import urlopen
from hashlib import md5

#try:
#    import json
#except ImportError:
try:
    import simplejson as json
except ImportError:
    from django.utils import simplejson as json

BASE_URL        = 'http://www.gravatar.com/avatar/'
SECURE_BASE_URL = 'https://secure.gravatar.com/avatar/'
PROFILE_URL     = 'http://www.gravatar.com/'
RATINGS         = ['g', 'pg', 'r', 'x']
MAX_SIZE        = 512
MIN_SIZE        = 1
DEFAULTS        = ['404', 'mm', 'identicon', 'monsterid', 'wavatar', 'retro']

class Gravatar(object):
    """
    Represents a Gravatar user.
    """
    
    def __init__(self, email, secure = False, default = None):
        self._email_hash = md5(email.strip().lower()).hexdigest()
        self._secure     = secure
        self._default    = default
        self._thumb      = self._link_to_img()
        self._profile    = None
    
    @property
    def secure(self):
        """Return the secure parameter."""
        return self._secure        

    @property
    def default(self):
        """Return the default parameter."""
        return self._default   

    @property
    def thumb(self):
        """Return the link to the gravatar thumbnail."""
        return self._thumb
    
    def _link_to_img(self):
        """
        Generates a link to the user's Gravatar.
        
        >>> Gravatar('gridaphobe@gmail.com')._link_to_img()
        'http://www.gravatar.com/avatar/16b87da510d278999c892cdbdd55c1b6?s=80&r=g'
        """        
        
        url = ''
        if self.secure:
            url = SECURE_BASE_URL
        else:
            url = BASE_URL

        options = {}
        if self.default is not None:
            options['d'] = self.default
        url += self.hash + '?' + urlencode(options)
        return url
    
   
    @property
    def hash(self):
        """
        Return email hash.
        """
        return self._email_hash

    @property
    def profile(self):
        """
        Return the user's profile.
        """
        return self._profile
    
    @property
    def urls(self):
        """
        Return a list of user's urls.
        """
        try:
            return self.profile['urls']
        except KeyError:
            return []
    
    @property
    def accounts(self):
        """
        Return a list of user's linked accounts.
        """
        try:
            return self.profile['accounts']
        except KeyError:
            return []
    
    @property
    def verified_accounts(self):
        """
        Return a list of user's verified accounts.
        """
        return [a for a in self.accounts if a['verified'] == 'true']
    
    @property
    def ims(self):
        """
        Return a list of user's IM accounts.
        """
        try:
            return self.profile['accounts']
        except KeyError:
            return []
    
    @property
    def photos(self):
        """
        Return a list of user's photos.
        """
        try:
            return self.profile['photos']
        except KeyError:
            return []
    
    @property
    def emails(self):
        """
        Return a list of user's emails.
        """
        try:
            return self.profile['emails']
        except KeyError:
            return []


class InvalidRatingError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value + " is not a valid gravatar rating"

class InvalidSizeError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value + " is not a valid image size"

##############################################################################
if __name__ == '__main__':
    import doctest
    doctest.testmod()
