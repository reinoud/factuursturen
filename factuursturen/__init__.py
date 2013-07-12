#!/usr/bin/env python
"""
a class to access the REST API of the website www.factuursturen.nl

"""
import collections
import ConfigParser
from datetime import datetime, date
import re
import requests
from os.path import expanduser
import copy

__author__ = 'Reinoud van Leeuwen'
__copyright__ = "Copyright 2013, Reinoud van Leeuwen"
__license__ = "BSD"
__maintainer__ = "Reinoud van Leeuwen"
__email__ = "reinoud.v@n.leeuwen.net"

CONVERTABLEFIELDS = {
    'clients' : {'clientnr': 'int',
                 'showcontact': 'bool',
                 'tax_shifted': 'bool',
                 'lastinvoice': 'date',
                 'top': 'int',
                 'stddiscount': 'float',
                 'notes_on_invoice': 'bool',
                 'active': 'bool',
                 'default_email': 'int',
                 'timestamp': 'date'},
    'products': {'id': 'int',
                 'price': 'float',
                 'taxes': 'int'},
    'invoices': {'profile': 'int',
                 'discount': 'float',
                 'paymentperiod': 'int',
                 'collection': 'bool',
                 'tax': 'float',
                 'totalintax': 'float',
                 'sent': 'date',
                 'uncollectible': 'date',
                 'lastreminder': 'date',
                 'open': 'float',
                 'paiddate': 'float',
                 'duedate': 'date',
                 'overwrite_if_exist': 'bool',
                 'initialdate': 'date',
                 'finalsenddate': 'date'},
    'invoices_payment': {'date': 'date'},
    'invoices_saved': {'id': 'int',
                       'profile': 'int',
                       'discount': 'float',
                       'paymentperiod': 'int',
                       'totaldiscount': 'float',
                       'totalintax': 'float',
                       'clientnr': 'int'},
    'invoices_repeated': {'id': 'int',
                          'profile': 'int',
                          'discount': 'float',
                          'paymentperiod': 'int',
                          'datesaved': 'date',
                          'totalintax': 'float',
                          'initialdate': 'date',
                          'nextsenddate': 'date',
                          'finalsenddate': 'date',
                          'clientnr': 'int'},
    'profiles': {'id': 'int'},
    'countrylist' : {'id': 'int'},
    'taxes': {'percentage': 'int',
              'default': 'bool'}
}

API = {'getters' : ['clients',
                    'products',
                    'invoices',
                    'invoices_saved',
                    'invoices_repeated',
                    'profiles',
                    'balance',
                    'countrylist',
                    'taxes'],
       'single_getters' : ['invoices_pdf'],
       'posters' : ['clients',
                    'products',
                    'invoices'],
       'putters' : ['clients',
                    'products',
                    'invoices_payment'],
       'deleters' : ['clients',
                     'products',
                     'invoices',
                     'invoices_saved',
                     'invoices_repeated']}


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

class FactuursturenNoAuth(FactuursturenError):
    pass

class FactuursturenConversionError(FactuursturenError):
    pass

class FactuursturenWrongCall(FactuursturenError):
    pass


class Client:
    """
    client class to access www.factuursturen.nl though REST API
    """

    def __init__(self,
                 apikey='',
                 username='',
                 configsection='default',
                 host='www.factuursturen.nl',
                 protocol='https',
                 apipath='/api',
                 version='v0'):
        """
        initialize object

        When apikey and username are not present, look for INI-style file .factuursturen_rc
        in current directory and homedirectory to find those values there

        :param apikey: APIkey (string) as generated online on the website http://www.factuursturen.nl
        :param username: accountname for the website
        :param configsection: section in file ~/.factuursturen_rc where apikey and username should be present
        """
        self._url = protocol + '://' + host + apipath + '/' + version + '/'

        # try to read auth details from file when not passed
        if (not apikey) and (not username):
            try:
                config = ConfigParser.RawConfigParser()
                config.read(['.factuursturen_rc', expanduser('~/.factuursturen_rc')])
                self._apikey = config.get(configsection, 'apikey')
                self._username = config.get(configsection, 'username')
            except ConfigParser.NoSectionError:
                raise FactuursturenNoAuth ('key and username not given, nor found in .factuursturen_rc or ~/.factuursturen_rc')
            except ConfigParser.NoOptionError:
                raise FactuursturenNoAuth ('no complete auth found')
        else:
            if not (apikey and username):
                raise FactuursturenNoAuth ('no complete auth passed to factuursturen.Client')
            self._apikey = apikey
            self._username = username

        # remaining allowed calls to API
        self._remaining = None
        self._lastresponse = None

        self._headers = {'content-type': 'application/json',
                         'accept': 'application/json'}

        # keep a list of which functions can be used to convert the fields
        # from and to a string
        self._convertfunctions = {'fromstring': {'int': self._string2int,
                                                 'bool': self._string2bool,
                                                 'float': self._string2float,
                                                 'date': self._string2date},
                                  'tostring': {'int': self._int2string,
                                               'bool': self._bool2string,
                                               'float': self._float2string,
                                               'date': self._date2string}}

    # single value conversionfunctions
    def _string2int(self, string):
        try:
            return int(string)
        except ValueError:
            raise FactuursturenConversionError('cannot convert {} to int'.format(string))

    def _string2bool(self, string):
        return string.lower() in ("yes", "true", "t", "1")

    def _string2float(self, string):
        try:
            return float(string)
        except ValueError:
            raise FactuursturenConversionError('cannot convert {} to float'.format(string))

    def _string2date(self, string):
        if string == '':
            return None
        try:
            return datetime.strptime(string, '%Y-%m-%d')
        except ValueError:
            raise FactuursturenConversionError('cannot convert {} to date'.format(string))

    def _int2string(self, number):
        if not isinstance(number, int):
            raise FactuursturenConversionError('number {} should be of type int'.format(number))
        return str(number)

    def _bool2string(self, booleanvalue):
        if not isinstance(booleanvalue, int):
            raise FactuursturenConversionError('booleanvalue should be of type bool')
        return str(booleanvalue).lower()

    def _float2string(self, number):
         if not (isinstance(number, float) or (isinstance(number, int))):
            raise FactuursturenConversionError('number {} should be of type float'.format(number))
         return str(number)

    def _date2string(self, date):
        if not isinstance(date, datetime):
            raise FactuursturenConversionError('date should be of type datetime')
        return date.strftime("%Y-%m-%d")

    def _convertstringfields_in_dict(self, adict, function, direction):
        """convert fields of a single dict either from or to strings

        fieldnames to convert are read from CONVERTIBLEFIELDS dict, which
        is in essence a datadictionary for this API

        :param adict: dictionary to convert
        :param function: callable function in the API ('clients', 'products' etc)
        :param direction: either 'tostring' or 'fromstring'
        """
        if direction not in self._convertfunctions:
            raise FactuursturenWrongCall ('_convertstringfields_in_dict called with {}'.format(direction))
        if function in CONVERTABLEFIELDS:
            for key, value in adict.iteritems():
                if key in CONVERTABLEFIELDS[function]:
                    # note: target is something like 'int'. Depending
                    # on conversion direction, this is the source or the target
                    target = CONVERTABLEFIELDS[function][key]
                    conversion_function = self._convertfunctions[direction][target]
                    adict[key] = conversion_function(value)
        return adict

    def _convertstringfields_in_list_of_dicts(self, alist, function, direction):
        """convert each dict in the list

        Basically, a loop over the function _convertstringfields_in_dict

        :param alist: a list of dicts
        :param function: callable function in the API ('clients', 'products' etc)
        :param direction: either 'tostring' or 'fromstring'
        """
        if direction not in self._convertfunctions:
            raise FactuursturenWrongCall ('_convertstringfields_in_list_of_dicts called with {}'.format(direction))
        for index, entry in enumerate(alist):
            alist[index] = self._convertstringfields_in_dict(alist[index], function, direction)
        return alist

    def _flatten(self, adict, parent_key=''):
        """flatten a nested dict

        The API expects nested dicts to be flattened when posting

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

        :param adict: a nested dict
        :param parent_key: should be empty, used for recursion
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

        :param adict: dictionary to be changed
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

    def _prepare_for_send(self, adict, function):
        """fix dict so it can be posted

        :param adict: dictionary to be posted
        :param function: callable function from the API ('clients', 'products', etc)
        """
        adict = self._convertstringfields_in_dict(adict, function, 'tostring')
        adict = self._flatten(adict)
        adict = self._fixkeynames(adict)
        return adict

    @property
    def remaining(self):
        """return remaining allowed API calls (for this hour)"""
        return self._remaining

    @property
    def ok(self):
        """return status of last call"""
        return self._lastresponse

    def post(self, function, objData):
        """Generic wrapper for all POSTable functions

        errors from server during post (like wrong values) are propagated to the exceptionclass

        :param function: callabe function from the API ('clients', 'products', etc)
        :param objData: data to be posted
        """
        fullUrl = self._url + function
        objData_local = copy.deepcopy(objData)
        if function not in API['posters']:
            raise FactuursturenPostError("{function} not in available POSTable functions".format(function=function))

        if isinstance(objData_local, dict):
            objData_local = self._prepare_for_send(objData_local, function)

        response = requests.post(fullUrl,
                                 data=objData_local,
                                 auth=(self._username, self._apikey))
        self._lastresponse = response.ok

        if response.ok:
            self._remaining = int(response.headers['x-ratelimit-remaining'])
            return response.content
        else:
            raise FactuursturenWrongPostvalue(response.content)

    def put(self, function, objId, objData):
        """Generic wrapper for all PUTable functions

        errors from server during post (like wrong values) are propagated to the exceptionclass

        :param function: callabe function from the API ('clients', 'products', etc)
        :param objId: id of object to be put (usually retrieved from the API)
        :param objData: data to be posted. All required fields should be present, or the API will not accept the changes
        """
        fullUrl = self._url + function + '/{objId}'.format(objId=objId)

        if function not in API['putters']:
            raise FactuursturenPostError("{function} not in available PUTable functions".format(function=function))

        if isinstance(objData, dict):
            objData = self._prepare_for_send(objData, function)

        response = requests.put(fullUrl,
                                 data=objData,
                                 auth=(self._username, self._apikey))
        self._lastresponse = response.ok

        if response.ok:
            self._remaining = int(response.headers['x-ratelimit-remaining'])
            return
        else:
            raise FactuursturenWrongPutvalue(response.content)

    def delete(self, function, objId):
        """Generic wrapper for all DELETEable functions

        errors from server during post (like wrong values) are propagated to the exceptionclass
        :param function: callabe function from the API ('clients', 'products', etc)
        :param objId: id of object to be put (usually retrieved from the API)
        """
        fullUrl = self._url + function + '/{objId}'.format(objId=objId)

        if function not in API['deleters']:
            raise FactuursturenPostError("{function} not in available DELETEable functions".format(function=function))

        response = requests.delete(fullUrl,
                                 auth=(self._username, self._apikey))
        self._lastresponse = response.ok

        if response.ok:
            self._remaining = int(response.headers['x-ratelimit-remaining'])
        else:
            raise FactuursturenError(response.content)


    def get(self, function, objId=None):
        """Generic wrapper for all GETtable functions

        when no objId is passed, retrieve all objects (in a list of dicts)
        when objId is passed, only retrieve a single object (in a single dict)

        :param function: callabe function from the API ('clients', 'products', etc)
        :param objId: id of object to be put (usually retrieved from the API)
        """

        # TODO: some errorchecking:
        # - on function
        # - on return
        # - on network error
        # - on password
        # - on remaining allowed requests

        fullUrl = self._url + function
        # check function against self.getters and self.singleGetters
        if function not in API['getters'] + API['single_getters']:
            raise FactuursturenGetError("{function} not in available GETtable functions".format(function=function))

        if objId:
            fullUrl += '/{objId}'.format(objId=objId)

        response = requests.get(fullUrl,
                                auth=(self._username, self._apikey),
                                headers=self._headers)
        self._lastresponse = response.ok

        # when one record is returned, acces it normally so
        # return the single element of the dict that is called 'client'
        # when the functioncall was 'clients/<id>

        singlefunction = function[:-1]
        if response.ok:
            self._remaining = int(response.headers['x-ratelimit-remaining'])
            try:
                raw_structure = response.json()
                if objId is None:
                    retval = self._convertstringfields_in_list_of_dicts(raw_structure, function, 'fromstring')
                else:
                    retval = self._convertstringfields_in_dict(raw_structure[singlefunction], function, 'fromstring')
            except FactuursturenError as error:
                print error
                retval = response.content
            return retval
        else:
            # TODO: more checking
            raise FactuursturenEmptyResult (response.content)
