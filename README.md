# factuursturen

The factuursturen package is a client for the dutch webservice www.factuursturen.nl API.

To be able to use the API, you will need an API key. You can get one with these steps:
* log in on http://www.factuursturen.nl
* click 'Instellingen'
* click 'Verbindingen'
* click 'Maak API Sleutel'

API documentation can be found at http://www.factuursturen.nl/docs/api_v0_beta.pdf (or there might be a newer version
present at the moment you read this)

## Synopsis

Typical usage is something like this:

    #!/usr/bin/env python
    import factuursturen

    username = 'foo'
    apikey = 'some_long_string'


    fact = factuursturen.Client(apikey, username)

    clients = fact.get('clients')

    new_product = {'code': 'Productcode',
                   'name': 'Name of this product',
                   'price': 123.45,
                   'taxes': 21}
    try:
        fact.post('products', data)
    except FactuursturenWrongPostvalue as errormessage:
        print "oops! {errormessage}".format(errormessage=errormessage)

    invoices = fact.get('invoices')

    for invoice in invoices:
    invoicenr = invoice[u'invoicenr']
    try:
        pdf = fact.get('invoices_pdf', invoicenr)

        filename = '/tmp/{invoicenr}.pdf'.format(invoicenr=invoicenr)
        with open(filename, 'w') as f:
            f.write(pdf)
        print "{} written".format(filename)
    except factuursturenEmptyResult:
        print "factuur {invoicenr} is empty".format(invoicenr=invoicenr)

## Installation:

Either:

    * type this command:
    sudo pip install factuursturen

or:
    * download source
    * extract
    * cd into directory containing setup.py
    * type this command
    python setup.py install


## Changes from the API documentation

This client is pythonic, so some things are translated:
- booleans are returned as true booleans (not as strings with 'true')
- nested dictionaries can be used in posting (will be flattened automatically)
- returned dicts are the same structure as a dict that can be used for posting

## Examples


### Initialisation

You can either pass username and apikey when instantiating an object:

    import factuursturen
    username = 'foo'
    apikey = 'some_long_string'
    fact = factuursturen.Client(apikey, username)

or create a file named .factuursturen_rc in the current directory or your home directory like this:

    [default]
    username = foo
    apikey = some_long_string

(note: no quotes!), and create the object without explicitely passing them:

    import factuursturen
    fact = factuursturen.Client()


### create a product


    import factuursturen
    fact = factuursturen.Client()
    new_product = {'code': 'Productcode',
                   'name': 'Name of this product',
                   'price': 123.45,
                   'taxes': 21}
    try:
        fact.post('products', new_product)
    except factuursturen.FactuursturenWrongPostvalue as errormessage:
        print "oops! {errormessage}".format(errormessage=errormessage)

### create a client


    client = {'contact' : 'John Doe',
              'showcontact' : True,
              'company' : 'Johnny Bravo Inc.',
              'address' : 'Sir John Road 100',
              'zipcode' : '1337 JB',
              'city' : 'Johnsville',
              'country' : 146,
              'phone' : '010 123 4567',
              'mobile' : '0612 34 56 78',
              'email' : 'johnny@bravo.com',
              'bankcode' : '123456789',
              'taxnumber' : 'NL001234567B01',
              'tax_shifted' : False,
              'sendmethod' : 'email',
              'paymentmethod' : 'bank',
              'top' : 3,
              'stddiscount' : 5.30,
              'mailintro' : 'Dear Johnny,',
              'reference' : {'line1': 'Your ref: ABC123',
                             'line2': 'Our ref: XZX0029/2932/001',
                             'line3': 'Thank you for your order'},
              'notes' : 'This client is always late with his payments',
              'notes_on_invoice' : False
             }

    try:
        clientid = fact.post('clients', client)
        print "client added with id {id}".format(id=clientid)
    except factuursturen.FactuursturenError as errormessage:
        print "oops! {errormessage}".format(errormessage=errormessage)

### send an invoice to a client

