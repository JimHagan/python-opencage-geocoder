import requests
import collections
import six
from datetime import datetime


class OpenCageGeocodeException(Exception):
    pass


class OpenCageGeocodeInvalidInputException(OpenCageGeocodeException):
    pass


class OpenCageGeocodeRateLimitExceededException(OpenCageGeocodeException):
    def __init__(self, reset_time, reset_to):
        self.reset_time = reset_time
        self.reset_to = reset_to
        
    def __str__(self):
        return self.__unicode__()
    
    def __unicode__(self):
        return "Your rate limit has expired. It will reset to {0} on {1}".format(self.reset_to, self.reset_time.isoformat())



class OpenCageGeocode(object):
    url = 'http://prototype.opencagedata.com/geocode/v1/json'
    key = ''

    def __init__(self, key):
        self.key = key

    def geocode(self, query):
        if six.PY2:
            try:
                query = unicode(query)
            except UnicodeDecodeError:
                raise OpenCageGeocodeInvalidInputException("Input query must be unicode string")

        if not isinstance(query, six.text_type):
            raise OpenCageGeocodeInvalidInputException("Input query must be unicode string")

        data = {
            'q': query,
            'key': self.key
        }
        url = self.url
        response = requests.get(url, params=data)

        # check for non-json
        response_json = response.json()

        if response.status_code == 429:
            # Rate limit exceeded
            reset_time = datetime.utcfromtimestamp(response_json['rate']['reset'])
            raise OpenCageGeocodeRateLimitExceededException(reset_to=int(response_json['rate']['limit']), reset_time=reset_time)
        # TODO check for rate limiting
        # TODO check for errors
        return floatify_latlng(response.json()['results'])

        #return response.json()


def floatify_latlng(input_value):
    """
    Given anything (list/dict/etc) it will return that thing again, *but* any
    dict (at any level) that has only 2 elements lat & lng, will be replaced
    with the lat & lng turned into floats.

    If the API returns the lat/lng as strings, and not numbers, then this
    function will 'clean them up' to be floats.
    """
    if isinstance(input_value, collections.Mapping):
        if len(input_value) == 2 and sorted(input_value.keys()) == ['lat', 'lng']:
            # This dict has only 2 keys 'lat' & 'lon'
            return {'lat': float(input_value['lat']), 'lng': float(input_value['lng'])}
        else:
            return dict((key, floatify_latlng(value)) for key, value in input_value.items())
    elif isinstance(input_value, collections.MutableSequence):
        return [floatify_latlng(x) for x in input_value]
    else:
        return input_value
