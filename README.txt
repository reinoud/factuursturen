====
factuursturen.nl
====

The factuursturen.nl package is a client for the dutch webservice www.factuursturen.nl API.

To be able to use the API, you will need an API key. You can get one with these steps:
* log in on http://www.factuursturen.nl
* click 'Instellingen'
* click 'Verbindingen'
* click 'Maak API Sleutel'

API documentation can be found at http://www.factuursturen.nl/docs/api_v0_beta.pdf (or there might be a newer version
present at the moment you read this)

Synopsis
========
Typical usage is something like this:

    #!/usr/bin/env python
    import factuursturen

    username = 'foo'
    apikey = 'some_long_string'


    fact = factuursturen.client(apikey, username)

    clients = fact.get('clients')

    new_product = {u'code': 'Productcode',
                   u'name': 'Name of this product',
                   u'price': 123.45,
                   u'taxes': 21}
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

Changes from the API documentation
==================================
This client is pythonic, so some things are translated:
- booleans are returned as true booleans (not as strings with 'true')
- nested dictionaries can be used in posting (will be flattened automatically)
- returned dicts are the same structure as a dict that can be used for posting
