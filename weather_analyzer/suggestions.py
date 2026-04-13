from __future__ import annotations

from difflib import get_close_matches
import re

COMMON_CITIES = [
    "Ahmedabad",
    "Amritsar",
    "Athens",
    "Atlanta",
    "Auckland",
    "Bangalore",
    "Bangkok",
    "Barcelona",
    "Beijing",
    "Berlin",
    "Bhopal",
    "Bhubaneswar",
    "Birmingham",
    "Boston",
    "Brisbane",
    "Brussels",
    "Buenos Aires",
    "Cairo",
    "Calgary",
    "Canberra",
    "Cape Town",
    "Chandigarh",
    "Chennai",
    "Chicago",
    "Colombo",
    "Copenhagen",
    "Dallas",
    "Delhi",
    "Denver",
    "Dhaka",
    "Dubai",
    "Dublin",
    "Edinburgh",
    "Frankfurt",
    "Geneva",
    "Goa",
    "Gurgaon",
    "Hamburg",
    "Helsinki",
    "Hong Kong",
    "Honolulu",
    "Houston",
    "Hyderabad",
    "Indore",
    "Istanbul",
    "Jaipur",
    "Jakarta",
    "Jammu",
    "Johannesburg",
    "Kanpur",
    "Kochi",
    "Kolkata",
    "Kuala Lumpur",
    "Kyoto",
    "Las Vegas",
    "Lisbon",
    "London",
    "Los Angeles",
    "Lucknow",
    "Ludhiana",
    "Madrid",
    "Melbourne",
    "Mexico City",
    "Miami",
    "Milan",
    "Montreal",
    "Moscow",
    "Mumbai",
    "Munich",
    "Nagpur",
    "Nairobi",
    "New Delhi",
    "New York",
    "Osaka",
    "Oslo",
    "Ottawa",
    "Paris",
    "Patna",
    "Philadelphia",
    "Prague",
    "Pune",
    "Raipur",
    "Reykjavik",
    "Rome",
    "San Diego",
    "San Francisco",
    "Sao Paulo",
    "Seattle",
    "Seoul",
    "Shanghai",
    "Shimla",
    "Singapore",
    "Stockholm",
    "Surat",
    "Sydney",
    "Taipei",
    "Tel Aviv",
    "Tokyo",
    "Toronto",
    "Udaipur",
    "Vadodara",
    "Varanasi",
    "Vienna",
    "Warsaw",
    "Washington",
    "Zurich",
]


def _normalize_city_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _deduplicate(candidates: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for name in candidates:
        normalized = _normalize_city_name(name)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(name)
    return ordered


def _match_candidates(query: str, candidates: list[str], limit: int, cutoff: float) -> list[str]:
    if not candidates:
        return []

    normalized_query = _normalize_city_name(query)
    lookup = {_normalize_city_name(name): name for name in candidates}
    direct = [name for name in candidates if normalized_query in _normalize_city_name(name)]
    fuzzy_keys = get_close_matches(normalized_query, list(lookup.keys()), n=limit, cutoff=cutoff)

    matches: list[str] = []
    for name in direct + [lookup[key] for key in fuzzy_keys]:
        if name not in matches:
            matches.append(name)
        if len(matches) >= limit:
            break
    return matches


def suggest_city_names(query: str, history_candidates: list[str] | None = None, limit: int = 5) -> list[str]:
    normalized_query = _normalize_city_name(query)
    if not normalized_query:
        return []

    history_pool = _deduplicate(history_candidates or [])
    common_pool = _deduplicate(COMMON_CITIES)

    suggestions: list[str] = []
    for name in _match_candidates(query, history_pool, limit=limit, cutoff=0.4):
        if name not in suggestions:
            suggestions.append(name)

    for name in _match_candidates(query, common_pool, limit=limit, cutoff=0.55):
        if name not in suggestions:
            suggestions.append(name)
        if len(suggestions) >= limit:
            break
    return suggestions
