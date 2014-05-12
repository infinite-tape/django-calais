from datetime import datetime
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from djangocalais.fields import PickledObjectField
from djangocalais.calaisapi import OpenCalais


CONTENT_FIELDS = (models.CharField, models.TextField, models.XMLField)

def is_content_field(obj, field_name):
    opts = obj._meta
    return isinstance(opts.get_field_by_name(field_name)[0], CONTENT_FIELDS)

def is_url_field(obj, field_name):
    opts = obj._meta
    return isinstance(opts.get_field_by_name(field_name)[0], models.URLField)

def analyze_url_field(obj, field_name, content_type='text/html', api=None):
    if api is None:
        api = OpenCalais(settings.CALAIS_API_KEY)
    url = getattr(obj, field_name)
    return api.analyze_url(url, content_type=content_type)

def analyze_content_field(obj, field_name, content_type='text/txt', api=None):
    if api is None:
        api = OpenCalais(settings.CALAIS_API_KEY)
    content = getattr(obj, field_name)
    return api.analyze(content, content_type=content_type)

def analyze_content(obj, content, content_type='text/txt', api=None):
    if api is None:
        api = OpenCalais(settings.CALAIS_API_KEY)
    return api.analyze(content, content_type=content_type)
        
class Entity(models.Model):
    """
    A model class to represent OpenCalais entities. In OpenCalais,
    entities generally share the same schema, but there are at least
    four cases where they do not. This occurs for entity types
    Company, Organization, Product, and Person. Each of these entities
    include extra data attributes, while all other entities have a
    name field only.

    Calais entities will (likely) always share the name field, but new
    Entity types may include unanticipated additional data (see
    above-mentioned entities).  To simplify the model design, we have
    pickled the Calais response data.  This allows the extra data from
    the above mentioned entity types to remain accessible via a
    wrapper class, while preventing an overly complex model design. We
    originally implemented this as a chain of Django inheritance
    models and the results were very difficult to manage.

    The trade-off here is that it's not possible to query over extra
    attributes for entities that have them. If you require this
    functionality it is recommended that you implement a container
    class that wraps the appropriate ``Entity`` objects and extracts the
    necessary fields from the ``PickledObjectField`` into true Django
    ORM fields. For example::

        class PersonEntityWrapper(models.Model):
            entity = models.ForeignKey(Entity)
            person_type = models.CharField(max_length=300) # Could be FK too
            nationality = models.CharField(max_length=300)

    You can then overload save methods to extract the relevant data
    from the ``Entity`` object's ``attributes`` field. This will enable
    you to query over these extra fields. Such an implementation may
    be added to Djangocalais in the near future.
    """
    urlhash = models.URLField()
    type = models.ForeignKey('EntityType')
    name = models.CharField(max_length=300)
    attributes = PickledObjectField()

    def __unicode__(self):
        return u'%s:%s' % (self.type.name, self.name)

class EntityType(models.Model):
    """
    ``EntityType`` represents the kinds of entities the OpenCalais API
    can analyze. All entity types are identified by Calais with a
    unique reference ID in the form of a URL. Type references look
    like this:

    http://s.opencalais.com/1/type/em/e/Person

    In Djangocalais's implementation of the OpenCalais JSON API, the
    entity type is also available as an attribute of the API response
    data. This corresponds to the last portion of the URL hash
    (ie. "Person" above). This representation is also stored in the
    ``EntityType`` model.
    """
    urlhash = models.URLField()
    name = models.CharField(max_length=300)

    def __unicode__(self):
        return u'%s' % self.name

class EventFact(models.Model):
    """
    This model class represents OpenCalais responses for Events and
    Facts. These include complicated references to a variety of data
    related to the object under analysis. Examples include:
    Bankruptcy, IPO, CompanyLayoffs, StockSplit, NaturalDisaster,
    etc. These are sometimes called "relations."

    Because of the nature of this data, there is no generic, simple
    mapping to the Django ORM. As a result, a similar approach has
    been used to that of the entities with extra data discussed in the
    the ``Entity`` model. A ``PickledObjectField`` is used to pickle the
    OpenCalais API response.

    As a result, it is not possible to use Django's ORM to query the
    events and facts results. It is recommend that you implement a
    wrapper class for the events and facts data that you are
    interested in for your application. This may be added to
    Djangocalais in the future. For example::

        class CompanyEarningsGuidance(models.Model):
            event = models.ForeignKey(EventFact)
            company = models.ForeignKey(Entity) # This could also be CharField
            quarter = models.CharField(max_length=25)
            year = models.DateField()
            financial_trend = models.CharField(max_length=100)
            financial_metric = models.CharField(max_length=100)

    The additional field information can be extracted from the
    ``EventFact`` object's ``PickledObjectField`` at ``save()`` and
    the data used to fill in the extra fields of the wrapper model. It
    is recommended not to use Django's model inheritance to implement
    these relationships.

    Event and Fact objects are stored based on the unique URL
    identifier, which means that there can appear to be 'duplicate'
    ``EventFact`` objects in the database. However, these seemingly
    identical objects will differ in the contents of their
    ``attributes`` field. This is an unavoidable result of the
    aforementioned design decisions. Implementing a wrapper class
    around an ``EventFact`` object will reveal their distinctness.

    Unique relationships between ``CalaisDocument`` objects and
    ``EventFact`` objects *are* maintained in this design as long as the
    provided methods for analyzing Django objects are used
    (ie. :meth:`CalaisDocumentManager.analyze`).

    In many Event and Fact data responses, the documented fields are
    optional. Optional fields without Calais data do not contain keys
    in the response dictionary or ``PickledObjectField``.

    URL IDs for Events and Facts look like this:
    
    http://d.opencalais.com/genericHasher-1/fbb7a225-b658-3253-913a-bdf18108841f
    """
    urlhash = models.URLField()
    type = models.ForeignKey('EventFactType')
    attributes = PickledObjectField()
    
    def __unicode__(self):
        return u'%s' % self.type

class EventFactType(models.Model):
    """
    ``EventFactType`` represents the kinds of events and facts that
    OpenCalais can detect. This model is mostly a place to hold the
    two representations of Events and Facts that Calais uses: a URL
    and a text name. URL references are stored in the ``urlhash`` field
    and look like this:

    http://s.opencalais.com/1/type/em/r/PersonCareer

    The text version is just the last portion of the URL above
    (ie. "PersonCareer") and is stored in the ``name`` field.
    """
    urlhash = models.URLField()
    name = models.CharField(max_length=300)

    def __unicode__(self):
        return u'%s' % self.name
    
class SocialTag(models.Model):
    """
    OpenCalais will attempt to "tag" the content you analyze by
    returning a set of "social tags." These are based on the most
    prominent topics found in the document analysis and works as a
    quick way of tagging data. There are occasional false-positives.

    Like all other data provided by Calais, Social Tags can be
    identified by a URL hash value.
    """
    urlhash = models.URLField()
    name = models.CharField(max_length=300)

    def __unicode__(self):
        return u'%s' % self.name

class Topic(models.Model):
    """
    Representation of Calais's document categorization
    analysis. Calais uses both category and topic in references to
    these values. We have chosen to call the model ``Topic``.
    """
    urlhash = models.URLField()
    name = models.CharField(max_length=300)

    def __unicode__(self):
        return u'%s' % self.name

def make_entity(data, uri):
    try:
        obj = Entity.objects.get(urlhash=uri)
    except ObjectDoesNotExist:
        if data.has_key('instances'): del data['instances']
        if data.has_key('resolutions'): del data['resolutions']
        etype, created = EntityType.objects.get_or_create(
            name=data['_type'],
            defaults={'name': data['_type'],
                      'urlhash': data['_typeReference']})
        obj = Entity(urlhash=uri,
                     type=etype,
                     name=data['name'],
                     attributes=data)
        obj.save()
    return obj

def make_event(data, uri):
    try:
        obj = EventFact.objects.get(urlhash=uri)
    except ObjectDoesNotExist:
        if data.has_key('instances'): del data['instances']
        etype, create = EventFactType.objects.get_or_create(
            name=data['_type'],
            defaults={'name': data['_type'], 'urlhash': data['_typeReference']})
        obj = EventFact(urlhash=uri,
                        type=etype,
                        attributes=data)
        obj.save()
    return obj

def make_social_tag(data):
    obj, created = SocialTag.objects.get_or_create(
        urlhash=data['socialTag'],
        defaults={'urlhash': data['socialTag'], 'name': data['name']})
    return obj

def make_topic(data):
    obj, created = Topic.objects.get_or_create(
        urlhash=data['category'],
        defaults={'urlhash': data['category'],
                  'name': data['categoryName']})
    return obj

class CalaisDocumentManager(models.Manager):
    def analyze(self, obj, fields=None, api=None):
        """
        Analyze a Django object. The optional ``fields`` parameter is
        a list of 2-tuples that represent the field names to use as
        content for analysis and their content type. For example::

            [('title', 'text/txt'), ('extra_data', 'text/xml'),
             ('name', 'text/raw'), ('url', 'text/html')]

        Only the following Django field types can be analyzed:
        ``CharField``, ``TextField``, ``XMLField``, and
        ``URLField``. URLFields are a special case in which the URL
        will be retrieved and the resulting content is processed
        according to the Calais content type specified in the
        ``fields`` list. All other Django field types will be ignored.

        In addition, Calais only supports the following content types:
        ``text/txt``, ``text/raw``, ``text/html``, ``text/xml``. It is
        important to choose the appropriate content type because
        Calais will perform some pre-processing accordingly. No
        pre-processing will occur for the ``text/raw`` content type.
        
        An alternative method of specifying the fields to analyze is
        by adding a class attribute to your Django model called
        ``calais_content_fields``. For example::

            calais_content_fields = [('title', 'text/txt'), ('url', 'text/html')]
        """
        if fields is None:
            # try to get fields list from class attribute
            if not hasattr(obj.__class__, 'calais_content_fields'):
                raise TypeError('Must include fields argument or add calais_content_fields class attribute.')
            fields = obj.__class__.calais_content_fields
        # get URLFields
        url_fields = filter(lambda x: is_url_field(obj, x[0]), fields)
        # ignore "non-content" fields
        content_fields = filter(lambda x: is_content_field(obj, x[0]), fields)
        # analyze with OpenCalais API
        url_results = map(
            lambda x: analyze_url_field(obj, x[0], x[1], api),
            url_fields)
        content_results = map(
            lambda x: analyze_content_field(obj, x[0], x[1], api),
            content_fields)
        results = url_results + content_results
        content_type = ContentType.objects.get_for_model(obj)
        document, created = self.get_or_create(
            content_type=content_type,
            object_id=obj.pk,
            defaults={'content_type': content_type, 'object_id': obj.pk})
        map(lambda x: self.add_entities(document, x), results)
        map(lambda x: self.add_events(document, x), results)
        map(lambda x: self.add_social_tags(document, x), results)
        map(lambda x: self.add_topics(document, x), results)
        return document

    def add_entities(self, document, result):
        get_or_create = EntityDetection.objects.get_or_create
        for etype, entities in result.get('entities', {}).items():
            for uri, entity_data in entities.items():
                entity = make_entity(entity_data, uri)
                get_or_create(
                    entity=entity,
                    document=document,
                    defaults={'entity': entity, 'document': document,
                              'urlhash': uri,
                              'relevance': entity_data['relevance']})
            
    def add_events(self, document, result):
        get_or_create = EventDetection.objects.get_or_create
        for etype, events in result.get('relations', {}).items():
            for uri, event_data in events.items():
                event = make_event(event_data, uri)
                get_or_create(
                    event_or_fact=event,
                    document=document,
                    defaults={'event_or_fact': event, 'document': document,
                              'urlhash': uri})

    def add_social_tags(self, document, result):
        get_or_create = SocialTagDetection.objects.get_or_create
        for uri, social_tag_data in result.get('socialTag', {}).items():
            social_tag = make_social_tag(social_tag_data)
            get_or_create(
                social_tag=social_tag,
                document=document,
                defaults={'social_tag': social_tag,
                          'document': document,
                          'urlhash': uri,
                          'importance': social_tag_data['importance']})

    def add_topics(self, document, result):
        get_or_create = TopicDetection.objects.get_or_create
        for uri, topic_data in result.get('topics', {}).items():
            topic = make_topic(topic_data)
            score = topic_data.get('score', 0)
            get_or_create(
                topic=topic,
                document=document,
                defaults={'topic': topic, 'document': document,
                          'urlhash': uri, 'score': score})
 
    def get_document_for_object(self, obj):
        """
        Return the ``CalaisDocument`` for the given Django model object,
        ``obj``. If no document exists, raises a ``DoesNotExist``
        exception.
        """
        content_type = ContentType.objects.get_for_model(obj)
        return self.get(content_type=content_type, object_id=obj.pk)
        
class CalaisDocument(models.Model):
    """
    A ``CalaisDocument`` is anything that has been analyzed by the
    OpenCalais API. It acts as a local cache of the result data so
    that you only scan your Django objects once. It wraps the analyzed
    Django object in a ``GenericForeignKey`` for convenience.

    It is recommend you do not create ``CalaisDocument`` objects
    directly, but analyze all of your model objects using the
    ``analyze`` method of the :class:`CalaisDocumentManager` like so::

        CalaisDocument.objects.analyze(some_django_obj, fields=[('description', 'text/txt')])

    Django-calais currently only analyzes Django model objects.
    """
    content_type = models.ForeignKey(ContentType,
                                     related_name='calais_documents')
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    analysis_date = models.DateTimeField(default=datetime.now)
    entities = models.ManyToManyField(Entity, through='EntityDetection')
    events_and_facts = models.ManyToManyField(EventFact,
                                              through='EventDetection')
    social_tags = models.ManyToManyField(SocialTag,
                                         through='SocialTagDetection')
    topics = models.ManyToManyField(Topic, through='TopicDetection')
    objects = CalaisDocumentManager()

    def __unicode__(self):
        return u'%s' % self.content_object

class EntityDetection(models.Model):
    """
    A specific entity detected within a document. This includes the
    OpenCalais hash URL as a unique identifier for a particular
    detection. Also stores the `relevance` field, a floating point
    value repesenting the entity's relevance to the document.

    Example usage::

        # CalaisDocument contains an article about Apple iPods...
        >>> print d.content_object
        Apple rumor: iPhones and iPod touches may add micro projectors

        # List the entities and their relevance scores for document d        
        >>> [(x.entity.name, '%.3f' % x.relevance) for x in d.entity_detections.all()]
        [(u'form-factor handheld devices', '0.200'), (u'rumor site', '0.322'), (u'Online Backup', '0.099'), (u'micro projector technology', '0.322'), (u'preferred online storage', '0.099'), (u'iPod', '0.582'), (u'iPhone', '0.506'), (u'Taiwan', '0.267'), (u'Apple', '0.380'), (u'Samsung', '0.267'), (u'Foxlink', '0.322'), (u'Nokia', '0.267'), (u'Foxconn', '0.322'), (u'digital video', '0.343'), (u'micro projector technology', '0.322'), (u'iPod', '0.857')]

    This model handles the ``ManyToManyField`` relationship for
    all ``CalaisDocument`` and ``Entity`` models.        
    """
    entity = models.ForeignKey(Entity)
    document = models.ForeignKey(CalaisDocument,
                                 related_name='entity_detections')
    urlhash = models.URLField()    
    relevance = models.FloatField()

    def __unicode__(self):
        return u'%s' % self.entity

    def _get_score(self):
        return self.relevance
    score = property(_get_score)

class EventDetection(models.Model):
    """
    A Django intermediary model representing a specific instance of an
    Event or Fact in a document. This is only really useful for the
    ``urlhash`` attribute, which represents the OpenCalais reference
    URL for a particular Event in a specific document.

    This model handles the ``ManyToManyField`` relationship for
    all ``CalaisDocument`` and ``EventFact`` models.
    """
    event_or_fact = models.ForeignKey(EventFact)
    document = models.ForeignKey(CalaisDocument,
                                 related_name='event_detections')
    urlhash = models.URLField()

    def __unicode__(self):
        return u'%s' % self.event_or_fact

class SocialTagDetection(models.Model):
    """
    A Django intermediary model representing a specific instance of a
    Social Tag in a document. This includes the document's
    ``importance`` value for a particular social tag.

    This model handles the ``ManyToManyField`` relationship for
    all ``CalaisDocument`` and ``SocialTag`` models.    
    """
    social_tag = models.ForeignKey(SocialTag)
    document = models.ForeignKey(CalaisDocument,
                                 related_name='social_tag_detections')
    urlhash = models.URLField()
    importance = models.IntegerField()

    def __unicode__(self):
        return u'%s' % self.social_tag

    def _get_score(self):
        return self.importance
    score = property(_get_score)

class TopicDetection(models.Model):
    """
    A Django intermediary model representing a specific instance of a
    topic category on a document. This includes the document's
    ``score`` value for the particular topic.

    This model handles the ``ManyToManyField`` relationship for all
    ``CalaisDocument`` and ``Topic`` models.
    """    
    topic = models.ForeignKey(Topic)
    document = models.ForeignKey(CalaisDocument,
                                 related_name='topic_detections')
    urlhash = models.URLField()
    score = models.FloatField()

    def __unicode__(self):
        return u'%s' % self.topic
