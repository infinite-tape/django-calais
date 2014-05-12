django-calais: a semantic tool for Django
=========================================

Django-calais is a reusable Django application for interacting with
Thomson-Reuter's OpenCalais web service. It was created during the
development of the Quotd semantic news and opinion aggregator.

OpenCalais provides rich, semantic metadata for any piece of content
accessible on the web. It can also analyze plain text information and
XML data. It is accessible via a RESTful API and can return results
data in JSON, RDF, and several Microformats.

Django-calais utilizes the OpenCalais API to provide automatic
semantic analysis for any Django model. This metadata comes in four
flavors:

Entity extraction
   An entity usually represents a "noun extraction" that OpenCalais
   identified as related to the analyzed document. This includes
   people, companies, products, etc. Click here for a full list of
   entities.

   Entity results include a relevance score that can be used to
   determine the relative importance of an entity in a document.

Events and Facts
   An event or fact usually represents a "verb extraction" that
   OpenCalais identified as related to the analyzed document. This
   includes business acquisitions, stock buybacks, natural disasters,
   arrests, bankruptcy filings, and numerous other events and facts.

Social Tags
   Social tags are Calais's mechanism for automatically "tagging" a
   piece of analyzed content. They are comparable to "good guesses" as
   to what a human being might tag the content. Read more about social
   tags.

Document Categorization
   Calais will attempt to categorize a piece of content into one or
   more of a dozen or so categories. These are broad and attempt to
   capture a general "aboutness." You can see the current list of
   categories here.


Downloads & Requirements
========================

The most recent django-calais files are available from the Github 
repository:

   git clone https://github.com/jesselegg/django-calais.git

In addition, django-calais requires:

   * Django version 1.0 or higher

   * cjson Python library


**Important Note**

This project was recently migrated from its former home on
[Google Code](https://code.google.com/p/django-calais/). The
project is well debugged and documented, but is not actively maintained.

Installation
============

To install django-calais, run the following command from the location
where you unpacked the source download:

   python setup.py install

Alternatively you can simply put the included ``djangocalais``
directory on your ``$PYTHONPATH``.

After installing, you can begin using djangocalais by adding it to
your application's ``INSTALLED_APPS`` setting:

   INSTALLED_APPS = (
       ...
       'djangocalais'
       )

It is also recommended to use the following settings variable to store
your API key:

   CALAIS_API_KEY = '23kljas1s23f_d311'


Example usage
=============

Say you have a Django blog engine with blog posts. You can obtain a
wealth of data by analyzing your posts via the Calais API:

   >>> post = BlogEntry.objects.get(id=100)
   >>> print post.title
   Apple rumor: iPhones and iPod touches may add micro projectors

   # Analyze this blog post for semantic metadata
   >>> document = CalaisDocument.objects.analyze(post, fields=[('title', 'text/txt')])
   >>> document
   <CalaisDocument: Apple rumor: iPhones and iPod touches may add micro projectors>

   # list of entities related to this document
   >>> document.entities.all()
   [<Entity: IndustryTerm:form-factor handheld devices>, <Entity: IndustryTerm:rumor site>,
    <Entity: IndustryTerm:Online Backup>, <Entity: IndustryTerm:micro projector technology>,
    <Entity: IndustryTerm:preferred online storage>, <Entity: Product:iPod>,
    <Entity: Product:iPhone>, <Entity: Country:Taiwan>, <Entity: Company:Apple>,
    <Entity: Company:Samsung>, <Entity: Company:Foxlink>, <Entity: Company:Nokia>,
    <Entity: Person:Foxconn>, <Entity: Technology:digital video>,
    <Entity: Technology:micro projector technology>]

    # list of events and facts related to this document
    >>> document.events_and_facts.all()
    [<EventFact: CompanyAffiliates>, <EventFact: Alliance>]

    # list of social tags for this document
    >>> document.social_tags.all()
    [<SocialTag: Technology_Internet>]

Information about the relationship is also stored and available via
the usual Django ORM calls. Say you want to sort entities in a
document from most to least relevant:

   >>> sorted([(x.entity.name, '%.3f' % x.score)
               for x in document.entity_detections.all()],
               key=lambda x: (x[1], x[0]), reverse=True)
   [(u'iPod', '0.857'), (u'iPhone', '0.506'), (u'Apple', '0.380'),
    (u'digital video', '0.343'), (u'rumor site', '0.322'),
    (u'micro projector technology', '0.322'), (u'micro projector technology', '0.322'),
    (u'Foxlink', '0.322'), (u'Foxconn', '0.322'), (u'Taiwan', '0.267'),
    (u'Samsung', '0.267'), (u'Nokia', '0.267'), (u'form-factor handheld devices', '0.200'),
    (u'preferred online storage', '0.099'), (u'Online Backup', '0.099')]

And you can filter document entities over a threshold value:

   >>> document.entities.filter(entitydetection__relevance__gt=0.5)
   [<Entity: Product:iPod>, <Entity: Product:iPhone>]


Indices and tables
==================

* *Index*

* *Module Index*

* *Search Page*

* *Model documentation*

* *Manager documentation*

* *OpenCalais API Interface*


Models Documentation
********************

class djangocalais.models.CalaisDocument(*args, **kwargs)

   A ``CalaisDocument`` is anything that has been analyzed by the
   OpenCalais API. It acts as a local cache of the result data so that
   you only scan your Django objects once. It wraps the analyzed
   Django object in a ``GenericForeignKey`` for convenience.

   It is recommend you do not create ``CalaisDocument`` objects
   directly, but analyze all of your model objects using the
   ``analyze`` method of the ``CalaisDocumentManager`` like so:

      CalaisDocument.objects.analyze(some_django_obj, fields=[('description', 'text/txt')])

   Django-calais currently only analyzes Django model objects.

class djangocalais.models.SocialTag(*args, **kwargs)

   OpenCalais will attempt to "tag" the content you analyze by
   returning a set of "social tags." These are based on the most
   prominent topics found in the document analysis and works as a
   quick way of tagging data. There are occasional false-positives.

   Like all other data provided by Calais, Social Tags can be
   identified by a URL hash value.

class djangocalais.models.SocialTagDetection(*args, **kwargs)

   A Django intermediary model representing a specific instance of a
   Social Tag in a document. This includes the document's
   ``importance`` value for a particular social tag.

   This model handles the ``ManyToManyField`` relationship for all
   ``CalaisDocument`` and ``SocialTag`` models.

class djangocalais.models.Topic(*args, **kwargs)

   Representation of Calais's document categorization analysis. Calais
   uses both category and topic in references to these values. We have
   chosen to call the model ``Topic``.

class djangocalais.models.TopicDetection(*args, **kwargs)

   A Django intermediary model representing a specific instance of a
   topic category on a document. This includes the document's
   ``score`` value for the particular topic.

   This model handles the ``ManyToManyField`` relationship for all
   ``CalaisDocument`` and ``Topic`` models.


Entities
========

class djangocalais.models.Entity(*args, **kwargs)

   A model class to represent OpenCalais entities. In OpenCalais,
   entities generally share the same schema, but there are at least
   four cases where they do not. This occurs for entity types Company,
   Organization, Product, and Person. Each of these entities include
   extra data attributes, while all other entities have a name field
   only.

   Calais entities will (likely) always share the name field, but new
   Entity types may include unanticipated additional data (see above-
   mentioned entities).  To simplify the model design, we have pickled
   the Calais response data.  This allows the extra data from the
   above mentioned entity types to remain accessible via a wrapper
   class, while preventing an overly complex model design. We
   originally implemented this as a chain of Django inheritance models
   and the results were very difficult to manage.

   The trade-off here is that it's not possible to query over extra
   attributes for entities that have them. If you require this
   functionality it is recommended that you implement a container
   class that wraps the appropriate ``Entity`` objects and extracts
   the necessary fields from the ``PickledObjectField`` into true
   Django ORM fields. For example:

      class PersonEntityWrapper(models.Model):
          entity = models.ForeignKey(Entity)
          person_type = models.CharField(max_length=300) # Could be FK too
          nationality = models.CharField(max_length=300)

   You can then overload save methods to extract the relevant data
   from the ``Entity`` object's ``attributes`` field. This will enable
   you to query over these extra fields. Such an implementation may be
   added to Djangocalais in the near future.

class djangocalais.models.EntityType(*args, **kwargs)

   ``EntityType`` represents the kinds of entities the OpenCalais API
   can analyze. All entity types are identified by Calais with a
   unique reference ID in the form of a URL. Type references look like
   this:

   http://s.opencalais.com/1/type/em/e/Person

   In Djangocalais's implementation of the OpenCalais JSON API, the
   entity type is also available as an attribute of the API response
   data. This corresponds to the last portion of the URL hash (ie.
   "Person" above). This representation is also stored in the
   ``EntityType`` model.

class djangocalais.models.EntityDetection(*args, **kwargs)

   A specific entity detected within a document. This includes the
   OpenCalais hash URL as a unique identifier for a particular
   detection. Also stores the *relevance* field, a floating point
   value repesenting the entity's relevance to the document.

   Example usage:

      # CalaisDocument contains an article about Apple iPods...
      >>> print d.content_object
      Apple rumor: iPhones and iPod touches may add micro projectors

      # List the entities and their relevance scores for document d        
      >>> [(x.entity.name, '%.3f' % x.relevance) for x in d.entity_detections.all()]
      [(u'form-factor handheld devices', '0.200'), (u'rumor site', '0.322'), (u'Online Backup', '0.099'), (u'micro projector technology', '0.322'), (u'preferred online storage', '0.099'), (u'iPod', '0.582'), (u'iPhone', '0.506'), (u'Taiwan', '0.267'), (u'Apple', '0.380'), (u'Samsung', '0.267'), (u'Foxlink', '0.322'), (u'Nokia', '0.267'), (u'Foxconn', '0.322'), (u'digital video', '0.343'), (u'micro projector technology', '0.322'), (u'iPod', '0.857')]

   This model handles the ``ManyToManyField`` relationship for all
   ``CalaisDocument`` and ``Entity`` models.


Events and Facts
================

class djangocalais.models.EventFact(*args, **kwargs)

   This model class represents OpenCalais responses for Events and
   Facts. These include complicated references to a variety of data
   related to the object under analysis. Examples include: Bankruptcy,
   IPO, CompanyLayoffs, StockSplit, NaturalDisaster, etc. These are
   sometimes called "relations."

   Because of the nature of this data, there is no generic, simple
   mapping to the Django ORM. As a result, a similar approach has been
   used to that of the entities with extra data discussed in the the
   ``Entity`` model. A ``PickledObjectField`` is used to pickle the
   OpenCalais API response.

   As a result, it is not possible to use Django's ORM to query the
   events and facts results. It is recommend that you implement a
   wrapper class for the events and facts data that you are interested
   in for your application. This may be added to Djangocalais in the
   future. For example:

      class CompanyEarningsGuidance(models.Model):
          event = models.ForeignKey(EventFact)
          company = models.ForeignKey(Entity) # This could also be CharField
          quarter = models.CharField(max_length=25)
          year = models.DateField()
          financial_trend = models.CharField(max_length=100)
          financial_metric = models.CharField(max_length=100)

   The additional field information can be extracted from the
   ``EventFact`` object's ``PickledObjectField`` at ``save()`` and the
   data used to fill in the extra fields of the wrapper model. It is
   recommended not to use Django's model inheritance to implement
   these relationships.

   Event and Fact objects are stored based on the unique URL
   identifier, which means that there can appear to be 'duplicate'
   ``EventFact`` objects in the database. However, these seemingly
   identical objects will differ in the contents of their
   ``attributes`` field. This is an unavoidable result of the
   aforementioned design decisions. Implementing a wrapper class
   around an ``EventFact`` object will reveal their distinctness.

   Unique relationships between ``CalaisDocument`` objects and
   ``EventFact`` objects *are* maintained in this design as long as
   the provided methods for analyzing Django objects are used (ie.
   ``CalaisDocumentManager.analyze()``).

   In many Event and Fact data responses, the documented fields are
   optional. Optional fields without Calais data do not contain keys
   in the response dictionary or ``PickledObjectField``.

   URL IDs for Events and Facts look like this:

   http://d.opencalais.com/genericHasher-1/fbb7a225-b658-3253-913a-
   bdf18108841f

class djangocalais.models.EventFactType(*args, **kwargs)

   ``EventFactType`` represents the kinds of events and facts that
   OpenCalais can detect. This model is mostly a place to hold the two
   representations of Events and Facts that Calais uses: a URL and a
   text name. URL references are stored in the ``urlhash`` field and
   look like this:

   http://s.opencalais.com/1/type/em/r/PersonCareer

   The text version is just the last portion of the URL above (ie.
   "PersonCareer") and is stored in the ``name`` field.


Entities in Events and Facts
----------------------------

Events and Facts (also called "relations") contain complicated
relationships with entities. As stated earlier, these relationships
are not captured directly by the ``EventFact`` Django model, but they
are preserved in the ``attributes`` field. This is a
``PickledObjectField`` that stores the original dictionary of Calais
response data.

There is a lot of powerful information in the relationships between
events and entities. It is also the most difficult aspect of Calais
data to work with. An example usage may be helpful here.

Obtain an Event or Fact object and examine its attributes (portions of
the data removed for clarity):

   >>> document.events_and_facts.all()[0]
   <EventFact: CompanyAffiliates>
   >>> af.attributes
   {'affiliaterelationtype': 'subsidiary',
    'company_affiliate':
        {'_type': 'Company', 'name': 'Foxlink', 'relevance': 0.322},
    'company_parent':
        {'_type': 'Company', 'name': 'Apple', 'relevance': 0.380}}

This describes a "Company Affiliate" relationship between two Company
entities, Apple and Foxlink. These entities are not stored as
``Entity`` objects in the ``attributes`` field, but can be converted
by looking up these ``name`` and ``_type`` fields in the ``Entity``
table.

These relationship fields and sub-fields are documented in the
OpenCalais metadata documentation. Clearly, they are very powerful,
but using them is complex and will probably be specific to your
application. That is why we recommend implementing a wrapper class
(see example in ``EventFact``) or other utility function that can
handle the interpretation of these extra relationship fields.


Model Managers
**************

class djangocalais.models.CalaisDocumentManager

   analyze(obj, fields=None, api=None)

      Analyze a Django object. The optional ``fields`` parameter is a
      list of 2-tuples that represent the field names to use as
      content for analysis and their content type. For example:

         [('title', 'text/txt'), ('extra_data', 'text/xml'),
          ('name', 'text/raw'), ('url', 'text/html')]

      Only the following Django field types can be analyzed:
      ``CharField``, ``TextField``, ``XMLField``, and ``URLField``.
      URLFields are a special case in which the URL will be retrieved
      and the resulting content is processed according to the Calais
      content type specified in the ``fields`` list. All other Django
      field types will be ignored.

      In addition, Calais only supports the following content types:
      ``text/txt``, ``text/raw``, ``text/html``, ``text/xml``. It is
      important to choose the appropriate content type because Calais
      will perform some pre-processing accordingly. No pre-processing
      will occur for the ``text/raw`` content type.

      An alternative method of specifying the fields to analyze is by
      adding a class attribute to your Django model called
      ``calais_content_fields``. For example:

         calais_content_fields = [('title', 'text/txt'), ('url', 'text/html')]

   get_document_for_object(obj)

      Return the ``CalaisDocument`` for the given Django model object,
      ``obj``. If no document exists, raises a ``DoesNotExist``
      exception.


OpenCalais API Interface
************************

An alternative CalaisAPI interface.

As part of implementing django-calais, we developed a general Python
API interface that may be of use as a standalone utility.

This interface to OpenCalais's API supports GZIP results, uses urllib2
openers to handle errors and timeouts, supports JSON, and returns
everything as Python dictionaries.

Requires cjson, which is available from: http://pypi.python.org/pypi
/python-cjson

class djangocalais.calaisapi.OpenCalais(api_key, submitter='Generic django-calais script', allow_distribution=False, allow_search=False)

   analyze(text, content_type='text/html', output_format='application/json', encoding='utf8', size_limit=100000, raw=False)

      Analayze arbitrary text data. Default to content-type of
      'text/html', other options include: 'text/xml', 'text/txt',
      'text/raw'.

      All content-types except 'text/raw' will be cleaned by the
      OpenCalais API. Only 'text/raw' will submit data as is, without
      any post-submit processing. It is recommend that 'text/raw' only
      be used for plain text content when exact offsets and lengths
      are needed in the results.

      The size limit for OpenCalais content submissions is 100,000
      chars.

      *application/json* output will automatically translate to Python
      dictionaries.

   analyze_url(url, content_type='text/html', output_format='application/json', encoding='utf8')

      Retrieve a document from the given URL and submit it to
      OpenCalais for semantic analysis. Defaults to 'text/html'
      content-type.

      *application/json* output format will automatically translate to
      Python dictionaries.