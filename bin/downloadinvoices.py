#!/usr/local/bin/env python

import argparse
import os
import errno
import logging
import factuursturen

def do_options():
    """parse commandline options and get defaults from configfile

    """
    description = "Download all invoices from factuursturen per year"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-d', '--directory', help='directory to save invoices. Use quotes when it contains spaces',
                        required=True)
    parser.add_argument('-y', '--year', help='make subdirectories per year', action='store_true')
    parser.add_argument('-v', '--verbose', help='debuglevel', action='count')
    parser.add_argument('-l', '--logfile', help='logile (none for terminal')
    parser.add_argument('-u', '--username', help='username from factuursturen.nl')
    parser.add_argument('-k', '--apikey', help='apikey from factuursturen.nl')
    parser.add_argument('-i', '--id', help='only download invoice(s) with this id(s)', action='append')
    return parser.parse_args()

def mkdir_p(dirname):
    try:
        os.makedirs(dirname)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(dirname):
            pass
        else: raise

def setLogger(options):
    """set up a logfile

    :param options: parsed options
    """
    loglevel = 'WARNING'
    if options.verbose:
        loglevel = logging.getLevelName(loglevel) - 10 * options.verbose
        if loglevel < 10:
            loglevel = 10

    logger = logging.getLogger('main')
    logger.setLevel(loglevel)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')

    if options.logfile:
        file_logger = logging.FileHandler(options.logfile)
    else:
        file_logger = logging.StreamHandler()
    file_logger.setLevel(loglevel)
    file_logger.setFormatter(formatter)
    logger.addHandler(file_logger)

    return logger

if __name__ == '__main__':
    arguments = do_options()
    logger = setLogger(arguments)

    mkdir_p(arguments.directory)

    fact = factuursturen.Client(apikey=arguments.apikey, username=arguments.username)
    logger.debug("using username {}".format(fact._username))

    invoices = fact.get('invoices')
    logger.debug("got {} invoices from API".format(len(invoices)))

    for invoice in invoices:
        invoicenr = invoice[u'invoicenr']
        invoicefilename = invoicenr.replace('/','_')
        year = invoice[u'sent'].year
        if arguments.id is None or invoicenr in arguments.id:
            logger.debug("invoice {} from year {}".format(invoicenr, year))
            if arguments.year:
                mkdir_p('{}/{}'.format(arguments.directory, year))
                filename = '{}/{}/{}.pdf'.format(arguments.directory, year, invoicefilename)
            else:
                filename = '{}/{}.pdf'.format(arguments.directory, invoicenr)
            logger.debug("filename: {}".format(filename))
            #if not os.path.exists(filename):
            if 1:
                try:
                    logger.debug("trying to get invoice {}".format(invoicenr))
                    pdf = fact.get('invoices_pdf', invoicenr)
                    with open(filename, 'w') as f:
                        f.write(pdf)
                    logger.debug("written file {}".format(filename))
                except factuursturen.FactuursturenEmptyResult:
                    logger.debug("factuur {} is empty".format(invoicenr))
                except factuursturen.FactuursturenNotFound:
                    logger.error("invoice {} not found".format(invoicenr))
                except factuursturen.FactuursturenNoMoreApiCalls:
                    logger.error("no more remaining API calls")
                finally:
                    logger.debug("API calls remaining: {}".format(fact.remaining))
            else:
                logger.debug("file exists.")
