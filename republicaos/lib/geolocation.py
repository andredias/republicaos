# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from geopy import geocoders

import logging

log = logging.getLogger(__name__)

google_maps_key = 'ABQIAAAAHRqgRmxQbkyHyirlX_JpPRQoPehvsauJ6O2L6pog4iZEmTcm-BTJGzUeSM_AGG7HJPaKsOHKxmPGVw'
geocoder = geocoders.Google(google_maps_key)

def geolocation(endereco):
    log.debug('endereco: %s', endereco)
    if isinstance(endereco, unicode):
        endereco = endereco.encode('utf-8')
    place, (latitude, longitude) = geocoder.geocode(endereco)
    log.debug('place: %s, latitude: %s, longitude: %s', place, latitude, longitude)
    return (latitude, longitude)
