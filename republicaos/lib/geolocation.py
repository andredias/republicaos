# -*- coding: utf-8 -*-

from __future__ import unicode_literals

#from geopy import geocoders
#from geopy.geocoders.google import GQueryError

import logging

log = logging.getLogger(__name__)

#google_maps_key = 'ABQIAAAAHRqgRmxQbkyHyirlX_JpPRQoPehvsauJ6O2L6pog4iZEmTcm-BTJGzUeSM_AGG7HJPaKsOHKxmPGVw'
#geocoder = geocoders.Google(google_maps_key)

def geolocation(endereco):
    log.debug('endereco: %s', endereco)
    return (0, 0)
    if isinstance(endereco, unicode):
        endereco = endereco.encode('utf-8')
    try:
        place, (latitude, longitude) = geocoder.geocode(endereco)
        log.debug('place: %s, latitude: %s, longitude: %s', place, latitude, longitude)
        return (latitude, longitude)
    except GQueryError as e:
        raise ValueError(e.message)
