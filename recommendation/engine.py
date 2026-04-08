import math
from dataclasses import dataclass


EPSILON = 1e-9


@dataclass
class ScoredPackage:
    package: object
    cps: float
    distance: float
    computed_distance_km: float
    cost_efficiency: float
    time_efficiency: float
    final_score: float


@dataclass
class ScoredDestination:
    destination: object
    distance_km: float
    preference_score: float
    geo_score: float
    package_support_score: float
    final_score: float


def _safe_positive(value, default=0.0):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    return parsed if parsed >= 0 else float(default)


def _safe_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_weights(weights):
    total = sum(float(v) for v in weights.values() if v is not None)
    if total <= 0:
        size = len(weights) if weights else 1
        return {key: 1.0 / size for key in weights}
    return {key: float(value) / total for key, value in weights.items()}


def _preference_similarity(user_value, item_value):
    user_v = _safe_positive(user_value)
    item_v = _safe_positive(item_value)
    scale = max(user_v, item_v, 1.0)
    return max(0.0, 1.0 - (abs(user_v - item_v) / scale))


def _travel_type_similarity(user_type, package_type):
    if not user_type:
        return 1.0
    return 1.0 if str(user_type).strip().lower() == str(package_type).strip().lower() else 0.0


def _euclidean_geo_distance_km(lat1, lon1, lat2, lon2):
    avg_lat_rad = math.radians((lat1 + lat2) / 2.0)
    delta_lon_km = (lon1 - lon2) * 111.32 * math.cos(avg_lat_rad)
    delta_lat_km = (lat1 - lat2) * 110.57
    return math.sqrt((delta_lat_km ** 2) + (delta_lon_km ** 2))


def _user_to_destination_distance_km(user_context, destination):
    user_lat = _safe_float(user_context.get("user_latitude"))
    user_lon = _safe_float(user_context.get("user_longitude"))
    destination_lat = _safe_float(getattr(destination, "latitude", None))
    destination_lon = _safe_float(getattr(destination, "longitude", None))

    if None in (user_lat, user_lon, destination_lat, destination_lon):
        return _safe_positive(user_context.get("distance"), 0.0)

    return _euclidean_geo_distance_km(user_lat, user_lon, destination_lat, destination_lon)


def compute_cps(user_context, package, preference_weights, distance_km):
    score_budget = _preference_similarity(user_context.get("budget"), package.budget)
    score_distance = _preference_similarity(user_context.get("distance"), distance_km)
    score_duration = _preference_similarity(user_context.get("duration"), package.days)
    score_travel_type = _travel_type_similarity(user_context.get("travel_type"), package.package_type)

    return (
        preference_weights["budget"] * score_budget
        + preference_weights["distance"] * score_distance
        + preference_weights["duration"] * score_duration
        + preference_weights["travel_type"] * score_travel_type
    )


def compute_weighted_distance(user_context, package, context_weights, distance_km):
    budget_delta = _safe_positive(user_context.get("budget")) - _safe_positive(package.budget)
    distance_delta = _safe_positive(user_context.get("distance")) - _safe_positive(distance_km)
    duration_delta = _safe_positive(user_context.get("duration")) - _safe_positive(package.days)

    return math.sqrt(
        context_weights["budget"] * (budget_delta ** 2)
        + context_weights["distance"] * (distance_delta ** 2)
        + context_weights["duration"] * (duration_delta ** 2)
    )


def compute_efficiencies(package, distance_km):
    distance = max(_safe_positive(distance_km), EPSILON)
    duration = max(_safe_positive(package.days), EPSILON)
    cost = _safe_positive(package.budget)

    cost_efficiency = cost / distance
    time_efficiency = distance / duration
    return cost_efficiency, time_efficiency


def recommend_packages(
    user_context,
    packages,
    k=5,
    top_n=5,
    preference_weights=None,
    context_weights=None,
    alpha=0.4,
    beta=0.4,
    gamma=0.2,
):
    preference_weights = preference_weights or {
        "budget": 0.3,
        "distance": 0.3,
        "duration": 0.2,
        "travel_type": 0.2,
    }
    context_weights = context_weights or {
        "budget": 0.4,
        "distance": 0.3,
        "duration": 0.3,
    }

    preference_weights = _normalize_weights(preference_weights)
    context_weights = _normalize_weights(context_weights)
    blend_weights = _normalize_weights({"alpha": alpha, "beta": beta, "gamma": gamma})

    scored_by_distance = []
    for package in packages:
        computed_distance_km = _user_to_destination_distance_km(user_context, package.end_location)
        cps = compute_cps(user_context, package, preference_weights, computed_distance_km)
        distance = compute_weighted_distance(user_context, package, context_weights, computed_distance_km)
        ce, te = compute_efficiencies(package, computed_distance_km)
        scored_by_distance.append((package, cps, distance, computed_distance_km, ce, te))

    scored_by_distance.sort(key=lambda row: row[2])
    neighbors = scored_by_distance[: max(1, int(k))]

    ranked = []
    for package, cps, distance, computed_distance_km, ce, te in neighbors:
        inverse_distance = 1.0 / max(distance, EPSILON)
        efficiency_term = 1.0 / max((ce + te), EPSILON)

        final_score = (
            blend_weights["alpha"] * cps
            + blend_weights["beta"] * inverse_distance
            + blend_weights["gamma"] * efficiency_term
        )

        ranked.append(
            ScoredPackage(
                package=package,
                cps=cps,
                distance=distance,
                computed_distance_km=computed_distance_km,
                cost_efficiency=ce,
                time_efficiency=te,
                final_score=final_score,
            )
        )

    ranked.sort(key=lambda item: item.final_score, reverse=True)
    return ranked[: max(1, int(top_n))]


def _destination_preference_score(user_destination_preferences, destination, destination_weights):
    culture_score = _preference_similarity(user_destination_preferences.get("culture"), destination.culture)
    adventure_score = _preference_similarity(user_destination_preferences.get("adventure"), destination.adventure)
    wildlife_score = _preference_similarity(user_destination_preferences.get("wildlife"), destination.wildlife)
    sightseeing_score = _preference_similarity(user_destination_preferences.get("sightseeing"), destination.sightseeing)
    history_score = _preference_similarity(user_destination_preferences.get("history"), destination.history)

    return (
        destination_weights["culture"] * culture_score
        + destination_weights["adventure"] * adventure_score
        + destination_weights["wildlife"] * wildlife_score
        + destination_weights["sightseeing"] * sightseeing_score
        + destination_weights["history"] * history_score
    )


def recommend_destinations(
    user_destination_preferences,
    user_context,
    destinations,
    ranked_packages,
    destination_top_n=5,
    destination_weights=None,
    destination_alpha=0.5,
    destination_beta=0.3,
    destination_gamma=0.2,
):
    destination_weights = destination_weights or {
        "culture": 0.2,
        "adventure": 0.2,
        "wildlife": 0.2,
        "sightseeing": 0.2,
        "history": 0.2,
    }

    destination_weights = _normalize_weights(destination_weights)
    blend = _normalize_weights(
        {
            "preference": destination_alpha,
            "geo": destination_beta,
            "package": destination_gamma,
        }
    )

    destination_to_package_scores = {}

    for scored in ranked_packages:
        package = scored.package
        destination = package.end_location
        if destination is None:
            continue
        destination_to_package_scores.setdefault(destination.id, []).append(scored.final_score)

    ranked_destinations = []
    for destination in destinations:
        preference_score = _destination_preference_score(
            user_destination_preferences,
            destination,
            destination_weights,
        )
        distance_km = _user_to_destination_distance_km(user_context, destination)
        geo_score = 1.0 / max(distance_km, EPSILON)
        scores = destination_to_package_scores.get(destination.id, [])
        package_support_score = sum(scores) / len(scores) if scores else 0.0
        final_score = (
            blend["preference"] * preference_score
            + blend["geo"] * geo_score
            + blend["package"] * package_support_score
        )

        ranked_destinations.append(
            ScoredDestination(
                destination=destination,
                distance_km=distance_km,
                preference_score=preference_score,
                geo_score=geo_score,
                package_support_score=package_support_score,
                final_score=final_score,
            )
        )

    ranked_destinations.sort(key=lambda item: item.final_score, reverse=True)
    return ranked_destinations[: max(1, int(destination_top_n))]
