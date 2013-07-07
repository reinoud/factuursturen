#!/usr/bin/env python
"""
a class to access the REST API of the website www.factuursturen.nl

"""
import collections
import re
import requests

__author__ = 'Reinoud van Leeuwen'
__copyright__ = "Copyright 2013, Reinoud van Leeuwen"
__license__ = "BSD"
__version__ = "0.1"
__maintainer__ = "Reinoud van Leeuwen"
__email__ = "reinoud.v@n.leeuwen.net"
__status__ = "Development"


class FactuursturenError(Exception):
    """Base class for exceptions in this module."""
    def __init__(self, value = ''):
        self.value = value

    def __str__(self):
        return repr(self.value)


class FactuursturenGetError(FactuursturenError):
    pass


class FactuursturenPostError(FactuursturenError):
    pass


class FactuursturenWrongPostvalue(FactuursturenError):
    pass


class FactuursturenWrongPutvalue(FactuursturenError):
    pass


class FactuursturenEmptyResult(FactuursturenError):
    pass


class Client:
    """
    client class to access www.factuursturen.nl though REST API
    """

    def __init__(self,
                 apikey,
                 username,
                 host='www.factuursturen.nl',
                 protocol='https',
                 apipath='/api',
                 version='v0'):
        self._url = protocol + '://' + host + apipath + '/' + version + '/'
        self._apikey = apikey
        self._username = username
        self._remaining = None

        self._headers = {'content-type': 'application/json',
                         'accept': 'application/json'}
        self._getters = ['clients',
                         'products',
                         'invoices',
                         'invoices_saved',
                         'invoices_repeated',
                         'profiles',
                         'balance',
                         'countrylist',
                         'taxes']
        self._single_getters = ['invoices_pdf']
        self._posters = ['clients',
                         'products',
                         'invoices']
        self._putters = ['clients',
                         'products',
                         'invoices_payment']
        self._deleters = ['clients',
                          'products',
                          'invoices',
                          'invoices_saved',
                          'invoices_repeated']
        # booleanfields will have to be converted from and to strings
        self._booleanfields = {'clients': ['showcontact',
                                           'tax_shifted',
                                           'notes_on_invoice',
                                           'active'],
                               'invoices': ['collection',
                                            'overwrite_if_exist'],
                               'taxes': ['default']}
        # TODO: when username and apikey are not present, try to read ~/.factuursturen_rc

    # conversions
    # The API expects (and returns) booleans as lowercase
    # strings ('true', 'false'). Convert this to be true
    # booleans, which is easier to work with in Python

    # single value
    def _singlestr2bool(self, value):
        """Convert string 'True' to a decent boolean True """
        return value.lower() in ("yes", "true", "t", "1")

    # fields in a dict
    def _booleans_to_strings(self, singledict, function):
        """convert the booleans to strings in a dict """
        if function in self._booleanfields.keys():
            for key in self._booleanfields[function]:
                singledict[key] = str(singledict[key]).lower()
        return singledict

    def _boolean_strings_to_real_booleans(self, singledict, function):
        """convert the boolean string fields in a dict to true booleans"""
        if function in self._booleanfields.keys():
            for key in self._booleanfields[function]:
                if key in singledict:
                    singledict[key] = self._singlestr2bool(singledict[key])
        return singledict

    # list of dicts (when put or get is called without ID)
    def _booleans_to_strings_in_list(self, alist, function):
        """convert each element of the list"""
        for index, entry in enumerate(alist):
            alist[index] = self._booleans_to_strings(alist[index], function)
        return alist

    def _boolean_strings_to_real_booleans_in_list(self, alist, function):
        """convert each element of the list"""
        for index, entry in enumerate(alist):
            alist[index] = self._boolean_strings_to_real_booleans(alist[index], function)
        return alist

    def _flatten(self, adict, parent_key=''):
        """flatten a nested dict

        {'lines': {'line1': {'amount': 1,
                             'tax': 21},
                   'line2': {'amount': 2,
                             'tax': 21}
                   }
        }
        to
        {'lines[line1][amount]': 1,
         'lines[line1][tax]': 21,
         'lines[line2][amount]': 2,
         'lines[line2][tax]': 21
        }
        """
        items = []
        for k, v in adict.items():
            new_key = parent_key + '[' + k + ']' if parent_key else k
            if isinstance(v, collections.MutableMapping):
                items.extend(self._flatten(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def _fixkeynames(self, adict):
        """replace keynames in dict

        replace keys like 'lines[line0][amount_desc]'
        with 'lines[0][amount_desc]'
        (keeping the same value)
        """
        for key, val in adict.items():
            fields = re.split('\]\[', key)
            if len(fields) > 1:
                leftfields = re.split('\[', fields[0])
                middlefield = re.sub("[^0-9]", "", leftfields[1])
                newfield = leftfields[0] + '[' + middlefield + '][' + fields[1]
                adict[newfield] = val
                del adict[key]
        return adict

    def _translated(self, adict):
        """fix dict so it can be posted
        """
        return self._fixkeynames(self._flatten(adict))

    @property
    def remaining(self):
        """return remaining allowed API calls (for this hour)"""
        return self._remaining

    def post(self, function, objData):
        """Generic wrapper for all POSTable functions

        errors from server during post (like wrong values) are propagated to the exceptionclass
        """
        fullUrl = self._url + function
        if function not in self._posters:
            raise FactuursturenPostError("{function} not in available POSTable functions".format(function=function))

        if isinstance(objData, dict):
            objData = self._translated(objData)

        response = requests.post(fullUrl,
                                 data=objData,
                                 auth=(self._username, self._apikey))
        if response.ok:
            self._remaining = int(response.headers['x-ratelimit-remaining'])
            return response.content
        else:
            raise FactuursturenWrongPostvalue(response.content)

    def put(self, function, objId, objData):
        """Generic wrapper for all PUTable functions

        errors from server during post (like wrong values) are propagated to the exceptionclass
        """
        fullUrl = self._url + function + '/{objId}'.format(objId=objId)

        if function not in self._putters:
            raise FactuursturenPostError("{function} not in available PUTable functions".format(function=function))

        response = requests.post(fullUrl,
                                 data=objData,
                                 auth=(self._username, self._apikey))
        if response.ok:
            self._remaining = int(response.headers['x-ratelimit-remaining'])
            return
        else:
            raise FactuursturenWrongPutvalue(response.content)

    def delete(self, function, objId):
        """Generic wrapper for all DELETEable functions

        errors from server during post (like wrong values) are propagated to the exceptionclass
        """
        fullUrl = self._url + function + '/{objId}'.format(objId=objId)

        if function not in self._deleters:
            raise FactuursturenPostError("{function} not in available DELETEable functions".format(function=function))

        response = requests.post(fullUrl,
                                 auth=(self._username, self._apikey))
        if response.ok:
            self._remaining = int(response.headers['x-ratelimit-remaining'])
        else:
            raise FactuursturenError(response.content)


    def get(self, function, objId=None):
        """Generic wrapper for all GETtable functions"""

        # TODO: some errorchecking:
        # - on function
        # - on return
        # - on network error
        # - on password
        # - on remaining allowed requests

        fullUrl = self._url + function
        # check function against self.getters and self.singleGetters
        if function not in self._getters + self._single_getters:
            raise FactuursturenGetError("{function} not in available GETtable functions".format(function=function))

        if objId:
            fullUrl += '/{objId}'.format(objId=objId)

        response = requests.get(fullUrl,
                                auth=(self._username, self._apikey),
                                headers=self._headers)

        # when one record is returned, acces it normally so
        # return the single element of the dict that is called 'client'
        # when the functioncall was 'clients/<id>

        singlefunction = function[:-1]
        if response.ok:
            self._remaining = int(response.headers['x-ratelimit-remaining'])
            try:
                raw_structure = response.json()
                if isinstance(raw_structure, dict):
                    retval = self._boolean_strings_to_real_booleans(raw_structure[singlefunction], function)
                else:
                    retval = self._boolean_strings_to_real_booleans_in_list(raw_structure, function)
            except FactuursturenError:
                retval = response.content
            return retval
        else:
            # TODO: more checking
            raise FactuursturenEmptyResult (response.content)
