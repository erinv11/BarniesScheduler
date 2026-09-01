import math

from open_info_input import DAYS, TIME_SLOTS

FIRST_TIME_SLOT_MINUTES = None


def generate_optimal_schedule(required_rehearsals, possible_rehearsals, actors):
    schedule = []

    for rehearsal in prioritized_rehearsals(required_rehearsals):
        slot = find_best_slot_for_rehearsal(
            rehearsal,
            possible_rehearsals,
            schedule,
            actors,
        )

        if slot is None:
            raise ValueError(f"No valid slot found for {rehearsal}")

        schedule.append(slot)

    return schedule


def prioritized_rehearsals(required_rehearsals):
    return sorted(
        required_rehearsals,
        key=lambda rehearsal: (
            len(rehearsal.get("actors", [])),
            rehearsal.get("minutes", 0),
        ),
        reverse=True,
    )


def fits_within_possible_rehearsal(start, end, possible_rehearsals):
    start_minutes = time_to_minutes(start)
    end_minutes = time_to_minutes(end)

    for window in possible_rehearsals:
        if (
            start_minutes >= time_to_minutes(window["start"])
            and end_minutes <= time_to_minutes(window["end"])
        ):
            return True
    return False


def find_best_slot_for_rehearsal(
    rehearsal,
    possible_rehearsals,
    schedule,
    actors,
    max_missing_actor_percent=0.25,
    max_shortening_percent=0.25,
):
    requested_minutes = rehearsal["minutes"]
    minimum_minutes = math.ceil(requested_minutes * (1 - max_shortening_percent))
    required_actors = rehearsal.get("actors", [])
    max_missing_actors = max_missing_actor_count(
        len(required_actors),
        max_missing_actor_percent,
    )
    actor_lookup = {actor.name: actor for actor in actors}
    candidates = []

    for window in possible_rehearsals:
        window_day = window["day"]
        window_start = time_to_minutes(window["start"])
        window_end = time_to_minutes(window["end"])
        window_max_minutes = window.get("max_length", window_end - window_start)
        longest_allowed = min(requested_minutes, window_max_minutes)

        for duration in duration_options(longest_allowed, minimum_minutes):
            latest_start = window_end - duration
            for start in range(window_start, latest_start + 1, 15):
                end = start + duration

                if overlaps_existing_rehearsal(window_day, start, end, schedule):
                    continue

                missing_actor_minutes = unavailable_actor_minutes(
                    required_actors,
                    actor_lookup,
                    window_day,
                    start,
                    end,
                )
                missing_actors = [
                    actor_name
                    for actor_name, minutes_missing in missing_actor_minutes.items()
                    if minutes_missing > 0
                ]

                if len(missing_actors) > max_missing_actors:
                    continue

                shortened_by = requested_minutes - duration
                candidates.append(
                    {
                        "scene": rehearsal["name"],
                        "day": window_day,
                        "start": minutes_to_time(start),
                        "end": minutes_to_time(end),
                        "duration": duration,
                        "requested_minutes": requested_minutes,
                        "shortened_by": shortened_by,
                        "actors": required_actors,
                        "missing_actors": missing_actors,
                        "missing_actor_minutes": missing_actor_minutes,
                        "total_missing_actor_minutes": sum(
                            missing_actor_minutes.values()
                        ),
                        "total_compromise_minutes": total_compromise_minutes(
                            shortened_by,
                            required_actors,
                            missing_actor_minutes,
                        ),
                        "start_minutes": start,
                        "end_minutes": end,
                    }
                )

    if not candidates:
        return None

    return min(candidates, key=slot_score)


def duration_options(longest_allowed, minimum_minutes):
    if longest_allowed < minimum_minutes:
        return []

    durations = []
    duration = longest_allowed
    while duration >= minimum_minutes:
        durations.append(duration)
        duration -= 5
    return durations


def max_missing_actor_count(actor_count, max_missing_actor_percent):
    if actor_count <= 1:
        return 0

    return min(
        actor_count - 1,
        math.floor(actor_count * max_missing_actor_percent),
    )


def unavailable_actor_minutes(actor_names, actor_lookup, day, start, end):
    return {
        actor_name: actor_minutes_unavailable(
            actor_lookup.get(actor_name),
            day,
            start,
            end,
        )
        for actor_name in actor_names
    }


def actor_is_available(actor, day, start, end):
    return actor_minutes_unavailable(actor, day, start, end) == 0


def actor_minutes_unavailable(actor, day, start, end):
    if actor is None:
        return end - start

    day_index = DAYS.index(day)
    start_index = minutes_to_slot_index(start)
    end_index = math.ceil((end - first_time_slot_minutes()) / 15)

    if start_index < 0 or end_index > len(TIME_SLOTS):
        return end - start

    missing_minutes = 0
    for slot_index in range(start_index, end_index):
        if actor.allConflicts[day_index][slot_index]:
            slot_start = first_time_slot_minutes() + slot_index * 15
            slot_end = slot_start + 15
            missing_minutes += max(0, min(end, slot_end) - max(start, slot_start))

    return missing_minutes


def overlaps_existing_rehearsal(day, start, end, schedule):
    for scheduled_slot in schedule:
        if scheduled_slot["day"] != day:
            continue

        scheduled_start = scheduled_slot.get(
            "start_minutes",
            time_to_minutes(scheduled_slot["start"]),
        )
        scheduled_end = scheduled_slot.get(
            "end_minutes",
            time_to_minutes(scheduled_slot["end"]),
        )

        if start < scheduled_end and end > scheduled_start:
            return True

    return False


def slot_score(slot):
    return (
        slot["total_compromise_minutes"],
        len(slot["missing_actors"]),
        slot["total_missing_actor_minutes"],
        DAYS.index(slot["day"]),
        time_to_minutes(slot["start"]),
    )


def total_compromise_minutes(shortened_by, actor_names, missing_actor_minutes):
    actor_count = max(1, len(actor_names))
    full_cast_minutes_lost = shortened_by * actor_count
    return full_cast_minutes_lost + sum(missing_actor_minutes.values())


def time_to_minutes(time_string):
    time_part, meridiem = time_string.split()
    hour_string, minute_string = time_part.split(":")
    hour = int(hour_string)
    minute = int(minute_string)

    if meridiem == "PM" and hour != 12:
        hour += 12
    elif meridiem == "AM" and hour == 12:
        hour = 0

    return hour * 60 + minute


def minutes_to_time(minutes):
    hour_24 = minutes // 60
    minute = minutes % 60
    meridiem = "AM" if hour_24 < 12 else "PM"
    hour = hour_24 % 12
    if hour == 0:
        hour = 12

    return f"{hour}:{minute:02d} {meridiem}"


def first_time_slot_minutes():
    global FIRST_TIME_SLOT_MINUTES
    if FIRST_TIME_SLOT_MINUTES is None:
        FIRST_TIME_SLOT_MINUTES = time_to_minutes(TIME_SLOTS[0])

    return FIRST_TIME_SLOT_MINUTES


def minutes_to_slot_index(minutes):
    return (minutes - first_time_slot_minutes()) // 15
