#!/usr/bin/python3
"""Places API views"""

from flask import jsonify, abort, request
from api.v1.views import app_views
from models import storage, storage_t
from models.city import City
from models.user import User
from models.state import State
from models.place import Place


@app_views.route('/cities/<city_id>/places', methods=['GET'],
                 strict_slashes=False)
def get_places(city_id):
    """Retrieves the list of all Place objects of a City"""
    city = storage.get(City, city_id)
    if not city:
        abort(404)
    places = [place.to_dict() for place in city.places]
    return jsonify(places)


@app_views.route('/places/<place_id>', methods=['GET'], strict_slashes=False)
def get_place(place_id):
    """Retrieves a Place object"""
    place = storage.get(Place, place_id)
    if not place:
        abort(404)
    return jsonify(place.to_dict())


@app_views.route('/places/<place_id>', methods=['DELETE'],
                 strict_slashes=False)
def delete_place(place_id):
    """Deletes a Place object"""
    place = storage.get(Place, place_id)
    if not place:
        abort(404)
    storage.delete(place)
    storage.save()
    return jsonify({}), 200


@app_views.route('/cities/<city_id>/places', methods=['POST'],
                 strict_slashes=False)
def create_place(city_id):
    """Creates a Place"""
    city = storage.get(City, city_id)
    if not city:
        abort(404)
    data = request.get_json()
    if not data:
        abort(400, "Not a JSON")
    if 'user_id' not in data:
        abort(400, "Missing user_id")
    user = storage.get(User, data['user_id'])
    if not user:
        abort(404)
    if 'name' not in data:
        abort(400, "Missing name")
    data['city_id'] = city_id
    place = Place(**data)
    place.save()
    return jsonify(place.to_dict()), 201


@app_views.route('/places/<place_id>', methods=['PUT'], strict_slashes=False)
def update_place(place_id):
    """Updates a Place object"""
    place = storage.get(Place, place_id)
    if not place:
        abort(404)
    data = request.get_json()
    if not data:
        abort(400, "Not a JSON")
    ignored_keys = ['id', 'user_id', 'city_id', 'created_at', 'updated_at']
    for key, value in data.items():
        if key not in ignored_keys:
            setattr(place, key, value)
    place.save()
    return jsonify(place.to_dict()), 200


@app_views.route('/places_search', methods=['POST'], strict_slashes=False)
def place_search():
    """
        Searching for a place using filters: State, City & Amenity
    """
    info = request.get_json(silent=True)
    if info is None:
        abort(400, 'Not a JSON')

    places = storage.all(Place)
    place_list = []

    count = 0
    for key in info.keys():
        if len(info[key]) > 0 and key in ['states', 'cities', 'amenities']:
            count = 1
            break
    if len(info) == 0 or count == 0 or not info:
        for place in places.values():
            place_list.append(place.to_dict())
        return jsonify(place_list)

    if 'amenities' in info and len(info['amenities']) > 0:
        for place in places.values():
            for a_id in info['amenities']:
                amenity = storage.get(Amenity, a_id)
                if amenity in place.amenities and place not in place_list:
                    place_list.append(place)
                elif amenity not in place.amenities:
                    if place in place_list:
                        place_list.remove(place)
                    break
    else:
        for place in places.values():
            place_list.append(place)

    if 'cities' in info and len(info['cities']) > 0:
        tmp = []
        for c_id in info['cities']:
            for place in place_list:
                if place.city_id == c_id:
                    tmp.append(place)
        if 'states' in info and len(info['states']) > 0:
            for s_id in info['states']:
                state = storage.get(State, s_id)
                for city in state.cities:
                    if city.id in info['cities']:
                        count = 2
                        break
                if count == 2:
                    continue
                for place in place_list:
                    city_id = place.city_id
                    city = storage.get(City, city_id)
                    if city.state_id == s_id and place not in tmp:
                        tmp.append(place)
        place_list = tmp
    elif 'states' in info and len(info['states']) > 0:
        tmp = []
        for s_id in info['states']:
            for place in place_list:
                city_id = place.city_id
                city = storage.get(City, city_id)
                if city.state_id == s_id:
                    tmp.append(place)
        place_list = tmp

    tmp = []
    for place in place_list:
        result = place.to_dict()
        if 'amenities' in result:
            del result['amenities']
        tmp.append(result)
    return jsonify(tmp)
