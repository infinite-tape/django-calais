from xml.dom import minidom
from xml.dom.minidom import Comment


class CalaisParser:
    results = {}

    def __init__(self, rdfdoc):
	self.rdfdoc = rdfdoc
	self.parseRelevance(rdfdoc.childNodes)
	self.parseInstances(rdfdoc.childNodes)
	self.results['entities'] = self.parseEntities(rdfdoc.childNodes)
	self.results['relations'] = self.parseRelations(rdfdoc.childNodes)

    def getText(self, nodeList):
	rc = ""
	for node in nodeList:
	    if node.nodeType == node.TEXT_NODE:
		rc = rc + node.data
	return rc
    
    def getNodeType(self, node):
	try:
	    nodeType = node.getElementsByTagName('rdf:type')[0]
	    resource = nodeType.getAttribute('rdf:resource').split('/')
	    return resource[-2], resource[-1]
	except:
	    return None, None
	
    def lookupEntity(self, uri):
	for etype, entities in self.results.get('entities', {}).items():
	    for entity_uri, data in entities.items():
		if uri == entity_uri:
		    return data

    def lookupRelevance(self, uri):
	for resource_uri, score in self.results.get('relevance', {}).items():
	    if uri == resource_uri:
		return score

    def lookupInstances(self, uri):
	for resource_uri, data in self.results.get('instances', {}).items():
	    if uri == resource_uri:
		return data

    def filterByType(self, node, nodeType):
	main_type, sub_type = self.getNodeType(node)
	if sub_type == nodeType:
	    return True
	return False

    def getMetaData(self, nodeList, entities=True,
		    relevance=False, instances=False):
	data = {}
	for node in filter(lambda x: x.prefix=='c', nodeList):
	    text = self.getText(node.childNodes)
	    if text:
		if data.has_key(node.localName):
		    if not isinstance(data[node.localName], list):
			temp = data[node.localName]
			data[node.localName] = list()
			data[node.localName].append(temp)
			data[node.localName].append(text)
		    else:
			data[node.localName].append(text)
		else:
		    data[node.localName] = text
	    else:
		resource_uri = node.getAttribute('rdf:resource')
		if resource_uri and entities:
		    entity_data = self.lookupEntity(resource_uri)
		    entity_data['uri'] = resource_uri
		    if relevance:
			entity_data['relevance'] = \
			    self.lookupRelevance(resource_uri)
		    if data.has_key(node.localName):
			if not isinstance(data[node.localName], list):
			    temp = data[node.localName]
			    data[node.localName] = list()
			    data[node.localName].append(temp)
			    data[node.localName].append(entity_data)
			else:
			    data[node.localName].append(entity_data)
		    else:
			data[node.localName] = entity_data
	return data
    
    def parseEntities(self, nodeList):
	data = {}
	print "Parsing entities..."
	for node in nodeList:
	    uri = node.getAttribute('rdf:about')
	    ntype, etype = self.getNodeType(node)
	    if ntype != 'e': continue
	    if not data.has_key(etype):
		data[etype] = {}
	    data[etype].update({uri: self.getMetaData(
			node.childNodes, relevance=True)})
	    data[etype][uri]['_type'] = etype
	    data[etype][uri]['relevance'] = self.lookupRelevance(uri)
	return data

    def parseRelations(self, nodeList):
	data = {}
	print "Parsing relations..."
	for node in nodeList:
	    uri = node.getAttribute('rdf:about')
	    ntype, rtype = self.getNodeType(node)
	    if ntype != 'r': continue
	    if not data.has_key(rtype):
		data[rtype] = {}
	    data[rtype].update({uri: self.getMetaData(
			node.childNodes, relevance=True)})
	    data[rtype][uri]['_type'] = rtype
	    data[rtype][uri]['relevance'] = self.lookupRelevance(uri)
	return data

    def getSubjectURI(self, node):
	subject_node = node.getElementsByTagName('c:subject')[0]
	return subject_node.getAttribute('rdf:resource')	
    
    def parseRelevance(self, nodeList):
	for node in nodeList:
	    ntype, rtype = self.getNodeType(node)
	    if not rtype == 'RelevanceInfo': continue
	    if not self.results.has_key("relevance"):
		self.results['relevance'] = {}
	    subject_uri = self.getSubjectURI(node)
	    relevance_node = node.getElementsByTagName('c:relevance')[0]
	    score = self.getText(relevance_node.childNodes)
	    self.results['relevance'].update({subject_uri: float(score)})

    def parseInstances(self, nodeList):
	for node in nodeList:
	    ntype, rtype = self.getNodeType(node)
	    if not rtype == 'InstanceInfo': continue
	    if not self.results.has_key('instances'):
		self.results['instances'] = {}
	    subject_uri = self.getSubjectURI(node)
	    if not self.results['instances'].has_key(subject_uri):
		self.results['instances'][subject_uri] = []
	    self.results['instances'][subject_uri].append(
		self.getMetaData(node.childNodes, entities=False))
