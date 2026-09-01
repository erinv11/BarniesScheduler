import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

from open_info_input import DAYS, TIME_SLOTS
from schedule_optimizer import generate_optimal_schedule, minutes_to_time, time_to_minutes


def format_schedule(schedule, actors):
    if not schedule:
        return "No schedule was generated."

    actor_lookup = {actor.name: actor for actor in actors}
    lines = ["REHEARSAL SCHEDULE", ""]
    current_day = None

    for slot in sorted(
        schedule,
        key=lambda item: (DAYS.index(item["day"]), item["start_minutes"]),
    ):
        if slot["day"] != current_day:
            current_day = slot["day"]
            if len(lines) > 2:
                lines.append("")
            lines.append(current_day)
            lines.append("-" * len(current_day))

        called_characters = characters_for_actor_names(
            slot.get("actors", []),
            actor_lookup,
        )
        character_text = ", ".join(called_characters) or "No characters listed"
        lines.append(
            f"{slot['start']} - {slot['end']}  |  {slot['scene']} "
            f"({slot['duration']} min)"
        )
        lines.append(f"Actors called: {character_text}")

        if slot.get("shortened_by", 0) > 0:
            lines.append(f"Note: shortened by {slot['shortened_by']} minutes")

        missing_details = missing_actor_details(slot, actor_lookup)
        if missing_details:
            lines.extend(missing_details)

        lines.append("")

    return "\n".join(lines).rstrip()


def characters_for_actor_names(actor_names, actor_lookup):
    characters = []
    seen_characters = set()

    for actor_name in actor_names:
        actor = actor_lookup.get(actor_name)
        actor_characters = actor.characters if actor is not None else []
        if not actor_characters:
            actor_characters = [actor_name]

        for character in actor_characters:
            dedupe_key = character.casefold()
            if dedupe_key in seen_characters:
                continue

            characters.append(character)
            seen_characters.add(dedupe_key)

    return characters


def missing_actor_details(slot, actor_lookup):
    details = []
    for actor_name in slot.get("missing_actors", []):
        actor = actor_lookup.get(actor_name)
        missing_ranges = missing_time_ranges_for_actor(actor, slot)
        if not missing_ranges:
            continue

        if (
            len(missing_ranges) == 1
            and missing_ranges[0] == (slot["start_minutes"], slot["end_minutes"])
        ):
            details.append(f"No {actor_name}")
        else:
            range_text = ", ".join(
                f"{minutes_to_time(start)} - {minutes_to_time(end)}"
                for start, end in missing_ranges
            )
            details.append(f"No {actor_name} for {range_text}")

    return details


def missing_time_ranges_for_actor(actor, slot):
    if actor is None:
        return [(slot["start_minutes"], slot["end_minutes"])]

    day_index = DAYS.index(slot["day"])
    missing_ranges = []
    current_start = None
    current_end = None

    for time_index, time_string in enumerate(TIME_SLOTS):
        slot_start = time_to_minutes(time_string)
        slot_end = slot_start + 15
        overlap_start = max(slot["start_minutes"], slot_start)
        overlap_end = min(slot["end_minutes"], slot_end)

        if overlap_start >= overlap_end:
            continue

        if actor.allConflicts[day_index][time_index]:
            if current_start is None:
                current_start = overlap_start
            current_end = overlap_end
        elif current_start is not None:
            missing_ranges.append((current_start, current_end))
            current_start = None
            current_end = None

    if current_start is not None:
        missing_ranges.append((current_start, current_end))

    return missing_ranges


def rehearsal_display_text(rehearsal_time):
    return (
        f"{rehearsal_time['day']}: {rehearsal_time['start']}"
        f" - {rehearsal_time['end']} ({rehearsal_time['max_length']} min max)"
    )


def scene_display_text(scene_goal, actor_lookup=None):
    actor_labels = []
    for actor_name in scene_goal["actors"]:
        actor = actor_lookup.get(actor_name) if actor_lookup is not None else None
        actor_labels.append(actor_display_text(actor) if actor is not None else actor_name)

    actor_text = (
        ", ".join(actor_labels)
        if actor_labels
        else "no actors selected"
    )
    return f"{scene_goal['name']} - {scene_goal['minutes']} min - {actor_text}"


def actor_display_text(actor):
    character_text = ", ".join(actor.characters) if actor.characters else "No character"
    return f"{actor.name} - {character_text}"


def copy_scene_goal(scene_goal):
    return {
        "name": scene_goal["name"],
        "minutes": scene_goal["minutes"],
        "actors": list(scene_goal.get("actors", [])),
    }


def open_schedule_result_window(
    root,
    m_background_color,
    p_background_color,
    secondary_color,
    actors,
    possible_rehearsals,
    scene_goals,
    schedule,
):
    schedule_window = tk.Toplevel(root)
    schedule_window.title("The Schedule")
    schedule_window.geometry("900x700+400+175")
    schedule_window.configure(background=m_background_color)
    schedule_window.minsize(700, 500)
    schedule_window.maxsize(3000, 1000)

    content_panel = tk.Frame(schedule_window, bg=p_background_color)
    content_panel.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    content_panel.grid_columnconfigure(0, weight=1)
    content_panel.grid_rowconfigure(1, weight=1)

    tk.Label(
        content_panel,
        text="Generated schedule",
        bg=p_background_color,
        font=("Helvetica", 14),
    ).grid(padx=10, pady=10, row=0, column=0, sticky="w")

    schedule_text = scrolledtext.ScrolledText(
        content_panel,
        wrap=tk.WORD,
        font=("Courier New", 11),
        bg="white",
        fg="black",
        padx=10,
        pady=10,
    )
    schedule_text.grid(padx=10, pady=5, row=1, column=0, sticky="nsew")
    schedule_text.insert(tk.END, format_schedule(schedule, actors))

    button_panel = tk.Frame(content_panel, bg=p_background_color)
    button_panel.grid(padx=10, pady=10, row=2, column=0, sticky="ew")

    def copy_schedule():
        schedule_window.clipboard_clear()
        schedule_window.clipboard_append(schedule_text.get("1.0", tk.END).strip())
        schedule_window.update()

    def edit_schedule_inputs():
        schedule_window.destroy()
        open_scheduler_window(
            root,
            m_background_color,
            p_background_color,
            secondary_color,
            actors,
            possible_rehearsals,
            scene_goals,
        )

    tk.Button(
        button_panel,
        text="Copy schedule",
        command=copy_schedule,
        bg=secondary_color,
        fg="white",
    ).pack(padx=5, pady=5, side=tk.LEFT)

    tk.Button(
        button_panel,
        text="Edit inputs",
        command=edit_schedule_inputs,
        bg=secondary_color,
        fg="white",
    ).pack(padx=5, pady=5, side=tk.LEFT)

    tk.Button(
        button_panel,
        text="Close",
        command=schedule_window.destroy,
        bg=secondary_color,
        fg="white",
    ).pack(padx=5, pady=5, side=tk.LEFT)

    return schedule_window


def open_scheduler_window(
    root,
    m_background_color,
    p_background_color,
    secondary_color,
    actors,
    initial_possible_rehearsals=None,
    initial_scene_goals=None,
):
    scheduler_window = tk.Toplevel(root)
    scheduler_window.title("Scheduler")
    scheduler_window.geometry("1200x800+350+175")
    scheduler_window.configure(background=m_background_color)
    scheduler_window.minsize(1000, 600)
    scheduler_window.maxsize(3000, 1000)

    possible_rehearsals = [
        rehearsal.copy()
        for rehearsal in (initial_possible_rehearsals or [])
    ]
    scene_goals = [
        copy_scene_goal(scene_goal)
        for scene_goal in (initial_scene_goals or [])
    ]
    actor_lookup = {actor.name: actor for actor in actors}

    rehearsal_panel = tk.Frame(
        scheduler_window,
        width=420,
        height=700,
        bg=p_background_color,
    )
    rehearsal_panel.pack(padx=10, pady=10, side=tk.LEFT, fill=tk.BOTH)
    rehearsal_panel.pack_propagate(False)

    scene_panel = tk.Frame(scheduler_window, bg=p_background_color)
    scene_panel.pack(padx=10, pady=10, side=tk.LEFT, fill=tk.BOTH, expand=True)

    tk.Label(
        rehearsal_panel,
        text="Possible rehearsal times",
        bg=p_background_color,
        font=("Helvetica", 14),
    ).pack(padx=5, pady=10)

    day_var = tk.StringVar(value=DAYS[0])
    start_time_var = tk.StringVar(value=TIME_SLOTS[0])
    end_time_var = tk.StringVar(value=TIME_SLOTS[-1])
    max_length_var = tk.StringVar(value="120")

    rehearsal_form = tk.Frame(rehearsal_panel, bg=p_background_color)
    rehearsal_form.pack(padx=5, pady=5, fill=tk.X)
    rehearsal_form.grid_columnconfigure(1, weight=1)

    tk.Label(rehearsal_form, text="Day", bg=p_background_color).grid(
        padx=5,
        pady=5,
        row=0,
        column=0,
        sticky="e",
    )
    ttk.Combobox(
        rehearsal_form,
        textvariable=day_var,
        values=DAYS,
        state="readonly",
    ).grid(padx=5, pady=5, row=0, column=1, sticky="ew")

    tk.Label(rehearsal_form, text="Start", bg=p_background_color).grid(
        padx=5,
        pady=5,
        row=1,
        column=0,
        sticky="e",
    )
    ttk.Combobox(
        rehearsal_form,
        textvariable=start_time_var,
        values=TIME_SLOTS,
        state="readonly",
    ).grid(padx=5, pady=5, row=1, column=1, sticky="ew")

    tk.Label(rehearsal_form, text="End", bg=p_background_color).grid(
        padx=5,
        pady=5,
        row=2,
        column=0,
        sticky="e",
    )
    ttk.Combobox(
        rehearsal_form,
        textvariable=end_time_var,
        values=TIME_SLOTS,
        state="readonly",
    ).grid(padx=5, pady=5, row=2, column=1, sticky="ew")

    tk.Label(rehearsal_form, text="Max length (minutes)", bg=p_background_color).grid(
        padx=5,
        pady=5,
        row=3,
        column=0,
        sticky="e",
    )
    tk.Spinbox(
        rehearsal_form,
        from_=15,
        to=600,
        increment=15,
        textvariable=max_length_var,
    ).grid(padx=5, pady=5, row=3, column=1, sticky="ew")

    rehearsal_listbox = tk.Listbox(rehearsal_panel, height=18)
    rehearsal_listbox.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    for rehearsal_time in possible_rehearsals:
        rehearsal_listbox.insert(tk.END, rehearsal_display_text(rehearsal_time))

    def clear_rehearsal_form():
        day_var.set(DAYS[0])
        start_time_var.set(TIME_SLOTS[0])
        end_time_var.set(TIME_SLOTS[-1])
        max_length_var.set("120")
        rehearsal_listbox.selection_clear(0, tk.END)

    def add_rehearsal_time():
        start_index = TIME_SLOTS.index(start_time_var.get())
        end_index = TIME_SLOTS.index(end_time_var.get())
        if end_index <= start_index:
            return

        rehearsal_length = (end_index - start_index) * 15
        max_length = min(int(max_length_var.get()), rehearsal_length)
        rehearsal_time = {
            "day": day_var.get(),
            "start": start_time_var.get(),
            "end": end_time_var.get(),
            "max_length": max_length,
        }
        possible_rehearsals.append(rehearsal_time)
        rehearsal_listbox.insert(tk.END, rehearsal_display_text(rehearsal_time))

    def load_selected_rehearsal_time():
        selected_indices = rehearsal_listbox.curselection()
        if not selected_indices:
            return

        rehearsal_time = possible_rehearsals[selected_indices[0]]
        day_var.set(rehearsal_time["day"])
        start_time_var.set(rehearsal_time["start"])
        end_time_var.set(rehearsal_time["end"])
        max_length_var.set(str(rehearsal_time["max_length"]))

    def update_selected_rehearsal_time():
        selected_indices = rehearsal_listbox.curselection()
        if not selected_indices:
            return

        start_index = TIME_SLOTS.index(start_time_var.get())
        end_index = TIME_SLOTS.index(end_time_var.get())
        if end_index <= start_index:
            return

        rehearsal_length = (end_index - start_index) * 15
        rehearsal_time = {
            "day": day_var.get(),
            "start": start_time_var.get(),
            "end": end_time_var.get(),
            "max_length": min(int(max_length_var.get()), rehearsal_length),
        }
        selected_index = selected_indices[0]
        possible_rehearsals[selected_index] = rehearsal_time
        rehearsal_listbox.delete(selected_index)
        rehearsal_listbox.insert(selected_index, rehearsal_display_text(rehearsal_time))
        clear_rehearsal_form()

    def remove_rehearsal_time():
        for index in reversed(rehearsal_listbox.curselection()):
            rehearsal_listbox.delete(index)
            del possible_rehearsals[index]

    rehearsal_buttons = tk.Frame(rehearsal_panel, bg=p_background_color)
    rehearsal_buttons.pack(padx=10, pady=5, fill=tk.X)

    tk.Button(
        rehearsal_buttons,
        text="Add time",
        command=add_rehearsal_time,
        bg=secondary_color,
        fg="white",
    ).pack(padx=5, pady=5, side=tk.LEFT, fill=tk.X, expand=True)

    tk.Button(
        rehearsal_buttons,
        text="Load selected",
        command=load_selected_rehearsal_time,
        bg=secondary_color,
        fg="white",
    ).pack(padx=5, pady=5, side=tk.LEFT, fill=tk.X, expand=True)

    tk.Button(
        rehearsal_buttons,
        text="Update selected",
        command=update_selected_rehearsal_time,
        bg=secondary_color,
        fg="white",
    ).pack(padx=5, pady=5, side=tk.LEFT, fill=tk.X, expand=True)

    tk.Button(
        rehearsal_buttons,
        text="Remove selected",
        command=remove_rehearsal_time,
        bg=secondary_color,
        fg="white",
    ).pack(padx=5, pady=5, side=tk.LEFT, fill=tk.X, expand=True)

    tk.Label(
        scene_panel,
        text="Scenes to accomplish",
        bg=p_background_color,
        font=("Helvetica", 14),
    ).grid(padx=5, pady=10, row=0, column=0, columnspan=2)

    scene_panel.grid_columnconfigure(0, weight=1)
    scene_panel.grid_columnconfigure(1, weight=1)
    scene_panel.grid_rowconfigure(5, weight=1)

    scene_form = tk.Frame(scene_panel, bg=p_background_color)
    scene_form.grid(padx=10, pady=5, row=1, column=0, columnspan=2, sticky="ew")
    scene_form.grid_columnconfigure(1, weight=1)

    scene_name_var = tk.StringVar()
    scene_time_var = tk.StringVar(value="30")

    tk.Label(scene_form, text="Scene", bg=p_background_color).grid(
        padx=5,
        pady=5,
        row=0,
        column=0,
        sticky="e",
    )
    tk.Entry(scene_form, textvariable=scene_name_var).grid(
        padx=5,
        pady=5,
        row=0,
        column=1,
        sticky="ew",
    )

    tk.Label(scene_form, text="Time to spend (minutes)", bg=p_background_color).grid(
        padx=5,
        pady=5,
        row=1,
        column=0,
        sticky="e",
    )
    tk.Spinbox(
        scene_form,
        from_=5,
        to=600,
        increment=5,
        textvariable=scene_time_var,
    ).grid(padx=5, pady=5, row=1, column=1, sticky="ew")

    tk.Label(
        scene_panel,
        text="Actors needed",
        bg=p_background_color,
    ).grid(padx=5, pady=5, row=2, column=0, sticky="w")

    def generate_schedule():
        if not possible_rehearsals:
            messagebox.showerror(
                "Error",
                "Please add at least one possible rehearsal time before generating the schedule.",
            )
            return

        if not scene_goals:
            messagebox.showerror(
                "Error",
                "Please add at least one scene goal before generating the schedule.",
            )
            return

        try:
            schedule = generate_optimal_schedule(scene_goals, possible_rehearsals, actors)
        except ValueError as error:
            messagebox.showerror("Could Not Generate Schedule", str(error))
            return

        scheduler_window.destroy()
        open_schedule_result_window(
            root,
            m_background_color,
            p_background_color,
            secondary_color,
            actors,
            possible_rehearsals,
            scene_goals,
            schedule,
        )

    tk.Button(
        scene_panel,
        text="Generate schedule",
        command=generate_schedule,
        bg=secondary_color,
        fg="white",
    ).grid(padx=10, pady=10, row=5, column=0, columnspan=1, sticky="s")

    actor_listbox = tk.Listbox(scene_panel, selectmode=tk.EXTENDED, exportselection=False)
    actor_listbox.grid(padx=10, pady=5, row=3, column=0, sticky="nsew")

    actor_names_by_index = []
    for actor in actors:
        actor_names_by_index.append(actor.name)
        actor_listbox.insert(tk.END, actor_display_text(actor))

    scene_listbox = tk.Listbox(scene_panel)
    scene_listbox.grid(padx=10, pady=5, row=3, column=1, rowspan=3, sticky="nsew")

    for scene_goal in scene_goals:
        scene_listbox.insert(tk.END, scene_display_text(scene_goal, actor_lookup))

    def clear_scene_form():
        scene_name_var.set("")
        scene_time_var.set("30")
        actor_listbox.selection_clear(0, tk.END)
        scene_listbox.selection_clear(0, tk.END)

    def add_scene_goal():
        scene_name = scene_name_var.get().strip()
        if scene_name == "":
            return
        if scene_name in [scene_goal["name"] for scene_goal in scene_goals]:
            return

        selected_actor_names = [
            actor_names_by_index[index]
            for index in actor_listbox.curselection()
        ]
        scene_goal = {
            "name": scene_name,
            "minutes": int(scene_time_var.get()),
            "actors": selected_actor_names,
        }
        scene_goals.append(scene_goal)

        scene_listbox.insert(tk.END, scene_display_text(scene_goal, actor_lookup))
        clear_scene_form()

    def load_selected_scene_goal():
        selected_indices = scene_listbox.curselection()
        if not selected_indices:
            return

        scene_goal = scene_goals[selected_indices[0]]
        scene_name_var.set(scene_goal["name"])
        scene_time_var.set(str(scene_goal["minutes"]))
        actor_listbox.selection_clear(0, tk.END)

        selected_actor_names = set(scene_goal.get("actors", []))
        for index, actor_name in enumerate(actor_names_by_index):
            if actor_name in selected_actor_names:
                actor_listbox.selection_set(index)

    def update_selected_scene_goal():
        selected_indices = scene_listbox.curselection()
        if not selected_indices:
            return

        scene_name = scene_name_var.get().strip()
        if scene_name == "":
            return

        selected_index = selected_indices[0]
        if scene_name in [
            scene_goal["name"]
            for index, scene_goal in enumerate(scene_goals)
            if index != selected_index
        ]:
            return

        selected_actor_names = [
            actor_names_by_index[index]
            for index in actor_listbox.curselection()
        ]
        scene_goal = {
            "name": scene_name,
            "minutes": int(scene_time_var.get()),
            "actors": selected_actor_names,
        }
        scene_goals[selected_index] = scene_goal
        scene_listbox.delete(selected_index)
        scene_listbox.insert(
            selected_index,
            scene_display_text(scene_goal, actor_lookup),
        )
        clear_scene_form()

    def remove_scene_goal():
        for index in reversed(scene_listbox.curselection()):
            scene_listbox.delete(index)
            del scene_goals[index]

    scene_buttons = tk.Frame(scene_panel, bg=p_background_color)
    scene_buttons.grid(padx=10, pady=5, row=4, column=0, sticky="ew")

    tk.Button(
        scene_buttons,
        text="Add scene",
        command=add_scene_goal,
        bg=secondary_color,
        fg="white",
    ).pack(padx=5, pady=5, side=tk.LEFT, fill=tk.X, expand=True)

    tk.Button(
        scene_buttons,
        text="Load selected",
        command=load_selected_scene_goal,
        bg=secondary_color,
        fg="white",
    ).pack(padx=5, pady=5, side=tk.LEFT, fill=tk.X, expand=True)

    tk.Button(
        scene_buttons,
        text="Update selected",
        command=update_selected_scene_goal,
        bg=secondary_color,
        fg="white",
    ).pack(padx=5, pady=5, side=tk.LEFT, fill=tk.X, expand=True)

    tk.Button(
        scene_buttons,
        text="Remove selected",
        command=remove_scene_goal,
        bg=secondary_color,
        fg="white",
    ).pack(padx=5, pady=5, side=tk.LEFT, fill=tk.X, expand=True)

    return scheduler_window
