from unittest import TestCase
import factuursturen
import ConfigParser
from os.path import expanduser
from datetime import datetime


class test_client(TestCase):
    def setUp(self):
        try:
            config = ConfigParser.RawConfigParser()
            config.read(['.factuursturen_rc', expanduser('~/.factuursturen_rc')])
            self._apikey = config.get('default', 'apikey')
            self._username = config.get('default', 'username')
        except ConfigParser.NoSectionError:
            self.fail('testsuite needs a file .factuursturen_rc in your homedirectory')
        except ConfigParser.NoOptionError:
            self.fail('.factuursturen_rc needs a [default] section')

    def test__wrongauth(self):
        apikey = 'foo'
        try:
            fact = factuursturen.Client(apikey)
            self.fail("test should fail when only half auth is passed")
        except factuursturen.FactuursturenNoAuth:
            pass

    def test__string2bool(self):
        apikey = 'foo'
        username = 'foo'
        fact = factuursturen.Client(apikey, username)
        test_input = 'true'
        test_output = fact._string2bool(test_input)
        self.assertEqual(test_output, True)
        self.assertIsInstance(test_output, bool)

    def test__string2float(self):
        apikey = 'foo'
        username = 'foo'
        fact = factuursturen.Client(apikey, username)
        test_input = '123.450'
        test_output = fact._string2float(test_input)
        self.assertEqual(test_output, 123.45)
        self.assertIsInstance(test_output, float)
        test_input = 'A123.450'
        try:
            test_output = fact._string2float(test_input)
        except factuursturen.FactuursturenConversionError:
            pass

    def test__string2int(self):
        apikey = 'foo'
        username = 'foo'
        fact = factuursturen.Client(apikey, username)
        test_input = '123'
        test_output = fact._string2int(test_input)
        self.assertEqual(test_output, 123)
        self.assertIsInstance(test_output, int)
        test_input = '123.24'
        try:
            test_output = fact._string2int(test_input)
        except factuursturen.FactuursturenConversionError:
            pass
        test_input = 'A123'
        try:
            test_output = fact._string2int(test_input)
        except factuursturen.FactuursturenConversionError:
            pass

    def test__string2date(self):
        apikey = 'foo'
        username = 'foo'
        fact = factuursturen.Client(apikey, username)
        test_input = "2013-12-31"
        test_output = fact._string2date(test_input)
        self.assertEqual(test_output, datetime(2013, 12, 31, 0, 0))
        self.assertIsInstance(test_output, datetime)
        test_input = "2013-12-32"
        try:
            test_output = fact._string2date(test_input)
            self.fail('2013-12-32 should throw exception when converted to')
        except factuursturen.FactuursturenConversionError:
            pass


    def test__int2string(self):
        apikey = 'foo'
        username = 'foo'
        fact = factuursturen.Client(apikey, username)
        test_input = 123
        test_output = fact._int2string(test_input)
        self.assertEqual(test_output, '123')
        self.assertIsInstance(test_output, str)
        test_input = 123.45
        try:
            test_output = fact._int2string(test_input)
            self.fail('123.45 should throw exception when converted from int to string')
        except factuursturen.FactuursturenConversionError:
            pass

    def test__bool2string(self):
        apikey = 'foo'
        username = 'foo'
        fact = factuursturen.Client(apikey, username)
        test_input = True
        test_output = fact._bool2string(test_input)
        self.assertEqual(test_output, 'true')
        self.assertIsInstance(test_output, str)

    def test__float2string(self):
        apikey = 'foo'
        username = 'foo'
        fact = factuursturen.Client(apikey, username)
        test_input = 123.45
        test_output = fact._float2string(test_input)
        self.assertEqual(test_output, '123.45')
        self.assertIsInstance(test_output, str)


    def test__date2string(self):
        apikey = 'foo'
        username = 'foo'
        fact = factuursturen.Client(apikey, username)
        test_input = datetime(2013, 12, 31, 0, 0)
        test_output = fact._date2string(test_input)
        self.assertEqual(test_output, "2013-12-31")
        self.assertIsInstance(test_output, str)

    def test__convertstringfields_in_dict(self):
        apikey = 'foo'
        username = 'foo'
        fact = factuursturen.Client(apikey, username)
        test_input = {'clientnr': 123,
                      'showcontact': True,
                      'timestamp': datetime(2013, 12, 31, 0, 0)}
        expected_output = {'clientnr': '123',
                           'showcontact': 'true',
                           'timestamp': '2013-12-31'}
        test_output = fact._convertstringfields_in_dict(test_input, 'clients', 'tostring')
        self.assertDictEqual(test_output, expected_output)
        try:
            test_output = fact._convertstringfields_in_dict(test_input, 'clients', 'wrongargument')
            self.fail("_convertstringfields_in_dict should throw exception when called wrong")
        except factuursturen.FactuursturenWrongCall:
            pass

    def test__convertstringfields_in_list_of_dicts(self):
        apikey = 'foo'
        username = 'foo'
        fact = factuursturen.Client(apikey, username)
        test_input = [{'clientnr': 123,
                      'showcontact': True,
                      'timestamp': datetime(2013, 12, 31, 0, 0)},
                      {'clientnr': 124,
                      'showcontact': False,
                      'timestamp': datetime(2012, 1, 1, 0, 0)}]
        expected_output = [{'clientnr': '123',
                           'showcontact': 'true',
                           'timestamp': '2013-12-31'},
                           {'clientnr': '124',
                           'showcontact': 'false',
                           'timestamp': '2012-01-01'}]
        test_output = fact._convertstringfields_in_list_of_dicts(test_input, 'clients', 'tostring')
        self.assertListEqual(test_output, expected_output)
        try:
            test_output = fact._convertstringfields_in_list_of_dicts(test_input, 'clients', 'wrongargument')
            self.fail("_convertstringfields_in_dict should throw exception when called wrong")
        except factuursturen.FactuursturenWrongCall:
            pass

    def test__flatten(self):
        apikey = 'foo'
        username = 'foo'
        fact = factuursturen.Client(apikey, username)
        test_input = {'lines': {'line1': {'amount': 1,
                                          'tax': 21},
                                'line2': {'amount': 2,
                                          'tax': 21}}}
        expected_output = {'lines[line1][amount]': 1,
                           'lines[line1][tax]': 21,
                           'lines[line2][amount]': 2,
                           'lines[line2][tax]': 21}
        test_output = fact._flatten(test_input)
        self.assertDictEqual(test_output, expected_output)

    def test__fixkeynames(self):
        apikey = 'foo'
        username = 'foo'
        fact = factuursturen.Client(apikey, username)
        testinput = {'lines[line0][amount_desc]': 1,
                     'lines[line0][tax]': 1,
                     'lines[line1][amount_desc]': 1,
                     'lines[line1][tax]': 1,
                     'lines[line2][amount_desc]': 1,
                     'lines[line2][tax]': 1}
        expected_output = {'lines[0][amount_desc]': 1,
                           'lines[0][tax]': 1,
                           'lines[1][amount_desc]': 1,
                           'lines[1][tax]': 1,
                           'lines[2][amount_desc]': 1,
                           'lines[2][tax]': 1}
        test_output = fact._fixkeynames(testinput)
        self.assertDictEqual(test_output, expected_output)

    def test__translated(self):
        apikey = 'foo'
        username = 'foo'
        fact = factuursturen.Client(apikey, username)
        test_input = {'clientnr': 123,
                      'showcontact': True,
                      'reference': {'line1': 'remark1',
                                    'line2': 'remark2'}}

        expected_output = {'clientnr': '123',
                           'showcontact': 'true',
                           'reference[line1]': 'remark1',
                           'reference[line2]': 'remark2'}
        test_output = fact._prepare_for_send(test_input, 'clients')
        self.assertDictEqual(test_output, expected_output)


    def test_remaining(self):
        apikey = 'foo'
        username = 'foo'
        fact = factuursturen.Client(apikey, username)
        fact._remaining = 1234
        self.assertEqual(fact.remaining, 1234)

    def test_post_get_put_delete(self):
        fact = factuursturen.Client()
        test_product = {u'code': u'TEST123',
                        u'name': u'Test produkt via API',
                        u'price': 123.450,
                        u'taxes': 21}
        added_id = int(fact.post('products', test_product))
        self.assertTrue(fact.ok)

        try:
            added_id = fact.post('wrongfunction', test_product)
            self.fail("calling post with wrong function should raise an exception")
        except factuursturen.FactuursturenPostError:
            pass

        test_product[u'id'] = added_id
        test_returned_product = fact.get('products', added_id)
        self.assertEqual(test_product, test_returned_product)

        fact.put('products', added_id, {'id': added_id, 'price': 10})
        self.assertTrue(fact.ok)

        test_returned_product = fact.get('products', added_id)
        self.assertEqual(test_returned_product['price'], 10)

        fact.delete('products', added_id)
        self.assertTrue(fact.ok)

        try:
            test_returned_product = fact.get('products', added_id)
            self.fail('an exception should be raised when trying to get a deleted object')
        except factuursturen.FactuursturenEmptyResult:
            self.assertFalse(fact.ok)

