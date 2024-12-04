from datetime import datetime

import extractor

#This parameter only allowes or disalowes ?debug and/or ?force query of URL 
debug_enable = True
#Hard coded debug enable or disable, should be disabled in production.
debugging = False

def debug(*args):
    if not debugging:
        return
    now = datetime.now()
    to_print=''
    for data in args:
        to_print += f' {str(data)}'
        
    print(f'[DEBUG][{now}]', to_print)

def extractParameters(event):
    global debugging
    debug('extractParameters')

    still_debugging = False
    param = {}

    if event.get('queryStringParameters'):
        param['queryStringParameters'] = event.get('queryStringParameters')
        if debug_enable:
            if 'debug' in [x.lower() for x in event.get('queryStringParameters').keys()]:
                debug('Debug Enabled')
                still_debugging = True

    if event.get('rawPath'):
        if event.get('rawPath')[1:]:
            param['rawPath'] = event.get('rawPath')[1:].lower()
    
    debugging = still_debugging
    param['debug'] = still_debugging
    return param


def call_extractor(event):
    debug('call_extractor')
    global debugging
    param = extractParameters(event)
    text = ''
    status_code, text = extractor.main(param, event)
    
    return status_code, text  

def check_favicon(arg):
    debug('check_favicon')
    if arg.get('rawPath'):
        if arg.get('rawPath')[1:]:
            if arg.get('rawPath')[1:].lower() == "favicon.ico":
                return True
    return False

def lambda_handler(event, context):
    debug('lambda_handler')
    debug(f'event:{event}')
    ok = True
    if not event.get('requestContext'):
        ok = False
        status_code = 418
        text = 'No request Context passed\nAre you using correct API?'
    elif not event['requestContext'].get('http'):
        ok = False
        status_code = 418
        text = 'No request Context passed\nAre you using correct API?'
    elif not event['requestContext']['http'].get('method'):
        ok = False
        status_code = 418
        text = 'No request Context passed\nAre you using correct API?'
    elif event['requestContext']['http']['method'] != 'GET':
        ok = False
        status_code = 405
        text = 'Only GET is acceptable'
    elif check_favicon(event):
        ok = False
        status_code = 405
        text = 'favicon.ico call disabled.' 
    
    
    if ok:
        text = ''
        status_code, text = call_extractor(event)
    if debugging:
        context_type = 'text/plain'
        if str(status_code)[0] == '2':
            status_code = 200
    elif str(status_code)[0] != '2':
        context_type = 'text/plain'
    else:
        context_type = 'text/xml'
        
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': context_type
        },
        'body': text
    }
