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
__version__ = "0.2"
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
            self._apikey = apikey
            self._username = username

        # remaining allowed calls to API
        self._remaining = None
        self._lastresponse = None

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
        self._convertablefields = {
            'clients' : {'clientnr': 'int',
                         'showcontact': 'bool',
                         'tax_shifted': 'bool',
                         'lastinvoice': 'date',
                         'top': 'int',
                         'stddiscount': 'int',
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
        try:
            return datetime.strptime(string, '%Y-%m-%d')
        except ValueError:
            raise FactuursturenConversionError('cannot convert {} to date'.format(string))

    def _int2string(self, number):
        return str(number)

    def _bool2string(self, booleanvalue):
        return str(booleanvalue).lower()

    def _float2string(self, number):
        return str(number)

    def _date2string(self, date):
        return date.strftime("%Y-%m-%d")

    def _convertstringfields_in_dict(self, adict, function, direction):
        """convert fields of a single dict either from or to strings
        :param adict:
        :param function:
        :param direction:
        """
        if direction not in self._convertfunctions:
            raise FactuursturenWrongCall ('_convertstringfields_in_dict called with {}'.format(direction))
        if function in self._convertablefields:
            for key, value in adict.iteritems():
                if key in self._convertablefields[function]:
                    # note: target is something like 'int'. Depending
                    # on conversion direction, this is the source or the target
                    target = self._convertablefields[function][key]
                    conversion_function = self._convertfunctions[direction][target]
                    adict[key] = conversion_function(value)
        return adict

    def _convertstringfields_in_list_of_dicts(self, alist, function, direction):
        """convert each dict in the list

        :param alist:
        :param function:
        :param direction:
        """
        if direction not in self._convertfunctions:
            raise FactuursturenWrongCall ('_convertstringfields_in_list_of_dicts called with {}'.format(direction))
        for index, entry in enumerate(alist):
            alist[index] = self._convertstringfields_in_dict(alist[index], function, direction)
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

        :param adict:
        :param parent_key:
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

        :param adict:
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

        :param adict:
        :param function:
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
        :param function:
        :param objData_local:
        """
        fullUrl = self._url + function
        objData_local = copy.deepcopy(objData)
        if function not in self._posters:
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
        :param function:
        :param objId:
        :param objData:
        """
        fullUrl = self._url + function + '/{objId}'.format(objId=objId)

        if function not in self._putters:
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
        :param function:
        :param objId:
        """
        fullUrl = self._url + function + '/{objId}'.format(objId=objId)

        if function not in self._deleters:
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

        :param function:
        :param objId:
        """

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
        self._lastresponse = response.ok

        # when one record is returned, acces it normally so
        # return the single element of the dict that is called 'client'
        # when the functioncall was 'clients/<id>

        singlefunction = function[:-1]
        if response.ok:
            self._remaining = int(response.headers['x-ratelimit-remaining'])
            try:
                raw_structure = response.json()
                if isinstance(raw_structure, dict):

                    retval = self._convertstringfields_in_dict(raw_structure[singlefunction], function, 'fromstring')
                else:
                    retval = self._convertstringfields_in_list_of_dicts(raw_structure, function, 'fromstring')
            except FactuursturenError:
                retval = response.content
            return retval
        else:
            # TODO: more checking
            raise FactuursturenEmptyResult (response.content)
