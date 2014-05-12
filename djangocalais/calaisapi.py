'''
An alternative CalaisAPI interface.

As part of implementing django-calais, we developed a general Python
API interface that may be of use as a standalone utility.

This interface to OpenCalais's API supports GZIP results, uses urllib2
openers to handle errors and timeouts, supports JSON, and returns
everything as Python dictionaries.

Requires cjson, which is available from:
http://pypi.python.org/pypi/python-cjson
'''
import hashlib, StringIO
import urllib, urllib2, gzip
from django.conf import settings
from djangocalais.parser import CalaisParser


CALAIS_URL = 'http://api.opencalais.com/enlighten/rest/'

class DefaultErrorHandler(urllib2.HTTPDefaultErrorHandler):
    def http_error_default(self, req, fp, code, msg, headers):
	result = urllib2.HTTPError(
	    req.get_full_url(), code, msg, headers, fp)
	result.status = code
	return result

class SmartRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_301(self, req, fp, code, msg, headers):
	result = urllib2.HTTPRedirectHandler.http_error_301(
	    self, req, fp, code, msg, headers)              
	result.status = code
	return result
    
    def http_error_302(self, req, fp, code, msg, headers):
	result = urllib2.HTTPRedirectHandler.http_error_302(
	    self, req, fp, code, msg, headers)
	result.status = code           
	return result

    
class OpenCalais:
    INPUT_PARAMS = """
<c:params xmlns:c="http://s.opencalais.com/1/pred/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
<c:processingDirectives c:contentType="%s" c:outputFormat="%s" c:calculatedRelevanceScore="true" c:enableMetadataType="SocialTags">
</c:processingDirectives><c:userDirectives c:allowDistribution="%s" c:allowSearch="%s" c:externalID="%s" c:submitter="%s"></c:userDirectives><c:externalMetadata></c:externalMetadata></c:params>
"""
    
    def __init__(self, api_key, submitter='Generic django-calais script',
		 allow_distribution=False, allow_search=False):
	"""
	Construct an OpenCalais object using a provided API key.

	Api_key is required.
	"""
	self.api_key = api_key
	self.submitter = submitter
	self.allow_distribution = allow_distribution
	self.allow_search = allow_search

    def _hash_text(self, text, encoding='utf8'):
	h = hashlib.sha1()
	h.update(text.encode(encoding))
	return h.hexdigest()

    def _resolveReferences(self, flatdb):
	for element in flatdb.keys():
	    for attribute in flatdb[element].keys():
		val = flatdb[element][attribute]
		if isinstance(val, basestring):
		    if flatdb.has_key(val):
			flatdb[element][attribute] = flatdb[val]
	return flatdb

    def _createHierarchy(self, flatdb):
	hdb = {}
	for element in flatdb.keys():
	    elementType = flatdb[element].get('_type', None)
	    elementGroup = flatdb[element].get('_typeGroup', None)
	    if elementGroup:
		if not hdb.has_key(elementGroup):
		    hdb[elementGroup] = {}
		if elementType:
		    if not hdb[elementGroup].has_key(elementType):
			hdb[elementGroup][elementType] = {}
		    hdb[elementGroup][elementType][element] = flatdb[element]
		else:
		    hdb[elementGroup][element] = flatdb[element]
	    else:
		hdb[element] = flatdb[element]
	return hdb
    
    def analyze(self, text, content_type='text/html',
                output_format='application/json', encoding='utf8',
                size_limit=100000, raw=False):
	"""
	Analayze arbitrary text data. Default to content-type of 'text/html',
	other options include: 'text/xml', 'text/txt', 'text/raw'.

	All content-types except 'text/raw' will be cleaned by the OpenCalais
	API. Only 'text/raw' will submit data as is, without any post-submit
	processing. It is recommend that 'text/raw' only be used for plain text
	content when exact offsets and lengths are needed in the results.

	The size limit for OpenCalais content submissions is 100,000 chars.

        `application/json` output will automatically translate to Python
        dictionaries.
	"""
	if len(text) > size_limit:
	    text = text[:size_limit]
	
	externalID = self._hash_text(text, encoding=encoding)
	paramsXML = self.INPUT_PARAMS % (
	    content_type, output_format,
	    str(self.allow_distribution).lower(),
	    str(self.allow_search).lower(), externalID,
	    self.submitter)
	param = urllib.urlencode({
		'licenseID': self.api_key,
		'content': text.encode(encoding),
		'paramsXML': paramsXML
		})
	
	request = urllib2.Request(CALAIS_URL, param)
	opener = urllib2.build_opener(DefaultErrorHandler())
	request.add_header('User-Agent', 'Python OpenCalaisAPI')
	request.add_header('Accept-encoding', 'gzip')
	try:
	    f = opener.open(request)
	except IOError, e:
	    if hasattr(e, 'reason'):
		print ">>> calaisapi.py failed to reach the Calais server."
		print ">>> Reason: ", e.reason
	    elif hasattr(e, 'code'):
		print ">>> The server couldn't fulfill the request."
		print ">>> Error code: ", e.code
	    return {}
	except Exception, e:
	    print ">>> Unexpected exception: %s" % e
	    return {}
	else:
	    data = f.read()
	    if f.headers.get('content-encoding', '') == 'gzip':
		data = gzip.GzipFile(fileobj=StringIO.StringIO(data)).read()
	    f.close()
	    
	    if output_format == 'application/json':
		return self.construct_json_response(data)
	    else:
		return self.construct_rdf_response(data)

    def construct_rdf_response(self, data):
	from xml.dom import minidom
	dom = minidom.parseString(data)
	rdfdoc = dom.childNodes[2]
	cp=CalaisParser(rdfdoc)
	return cp.results

    def construct_json_response(self, data):
	import cjson
	try:
	    intermediate_json = cjson.decode(data)
	except cjson.DecodeError:
	    print ">>> OpenCalais Error: %s" % data
	    return {}
	json_data = self._resolveReferences(intermediate_json)
	return self._createHierarchy(json_data)

    def analyze_url(self, url, content_type='text/html',
		    output_format='application/json',
		    encoding='utf8'):
	"""
	Retrieve a document from the given URL and submit it to OpenCalais for
	semantic analysis. Defaults to 'text/html' content-type.

        `application/json` output format will automatically translate to Python
        dictionaries.        
	"""
	request = urllib2.Request(url)
	opener = urllib2.build_opener(DefaultErrorHandler(),
				      SmartRedirectHandler())
	request.add_header('User-Agent', 'Python OpenCalaisAPI')
	request.add_header('Accept-encoding', 'gzip')
	try:
	    f = opener.open(request)
	except IOError, e:
	    if hasattr(e, 'reason'):
		print ">>> analyze_url() failed to load: %s." % url
		print ">>> Reason: ", e.reason
	    elif hasattr(e, 'code'):
		print ">>> analyze_url() failed"
		print ">>> The server couldn't fulfill the request."
		print ">>> Error code: ", e.code
	    return {}
        except ValueError:
            return {}
	else:
	    data = f.read()
	    if f.headers.get('content-encoding', '') == 'gzip':
		data = gzip.GzipFile(fileobj=StringIO.StringIO(data)).read()
	    f.close()
	    content = data.decode(encoding, 'ignore')
	    return self.analyze(content, content_type=content_type,
				output_format=output_format,
				encoding=encoding)
