import json
import tkinter as tk

from Actors import Actor


DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
TIME_SLOTS = [
    f"{hour}:{quarter_hour:02d} AM"
    for hour in range(9, 12)
    for quarter_hour in range(0, 60, 15)
] + [
    f"{12 if hour == 0 else hour}:{quarter_hour:02d} PM"
    for hour in range(0, 11)
    for quarter_hour in range(0, 60, 15)
]


def selected_times_by_day(conflict_grid):
    conflicts = {}
    for day, times in zip(DAYS, conflict_grid):
        conflicts[day] = [
            TIME_SLOTS[index]
            for index, has_conflict in enumerate(times)
            if has_conflict
        ]
    return conflicts


def build_cast_export(actors):
    return {
        "editing_notes": [
            "Actor names and character names can be edited directly.",
            "Edit weekly_conflicts or one_time_conflicts to change availability.",
            "To add a conflict, add a time from time_slots to that day list.",
            "To remove a conflict, delete that time from the day list.",
            "all_conflicts is a generated summary of weekly and one-time conflicts.",
            "Keep day names and time spelling exactly as shown.",
        ],
        "time_slots": TIME_SLOTS,
        "actors": [
            {
                "name": actor.name,
                "characters": actor.characters,
                "weekly_conflicts": selected_times_by_day(actor.WeeklyConflicts),
                "one_time_conflicts": selected_times_by_day(actor.OneTimeConflicts),
                "all_conflicts": selected_times_by_day(
                    [
                        [
                            actor.WeeklyConflicts[day_index][time_index]
                            or actor.OneTimeConflicts[day_index][time_index]
                            for time_index in range(len(TIME_SLOTS))
                        ]
                        for day_index in range(len(DAYS))
                    ]
                ),
            }
            for actor in actors
        ],
    }


def save_cast_file(filename, actors):
    with open(filename, "w") as f:
        json.dump(build_cast_export(actors), f, indent=4)
        f.write("\n")


def open_info_input(
    root,
    m_background_color,
    p_background_color,
    secondary_color,
    actors,
    open_schedule_window,
    save_one_time_conflicts,
):
    info_input = tk.Toplevel(root)
    info_input.title("New Cast Information")
    info_input.geometry("1200x800+350+175")
    info_input.configure(background=m_background_color)
    info_input.minsize(1000, 600)
    info_input.maxsize(3000, 1000)

    entry_actor = {}
    entry_character = {}

    act_char_panel = tk.Frame(info_input, width=268, height=400, bg=p_background_color)
    act_char_panel.grid_propagate(False)
    act_char_panel.pack_propagate(False)
    act_char_panel.pack(padx=10, pady=10, side=tk.LEFT, fill=tk.Y)
    act_char_panel.grid_columnconfigure(0, weight=1)
    act_char_panel.grid_columnconfigure(1, weight=1)

    tk.Label(
        act_char_panel,
        text="How many actors?",
        background=p_background_color,
        anchor="center",
        justify="center",
    ).grid(padx=5, pady=5, row=0, column=0, columnspan=2, sticky="ew")

    def store_actor_info():
        actors.clear()
        for i in range(int(spinbox_var.get())):
            actor_name = entry_actor[i].get()
            character_name = entry_character[i].get()
            actors.append(Actor(actor_name, [character_name]))

    def on_number_change():
        current_count = len(entry_actor)
        new_count = int(spinbox_var.get())

        if new_count > current_count:
            for i in range(current_count, new_count):
                entry_actor[i] = tk.Entry(act_char_panel)
                entry_actor[i].grid(padx=5, pady=5, row=i + 3, column=0)

                entry_character[i] = tk.Entry(act_char_panel)
                entry_character[i].grid(padx=5, pady=5, row=i + 3, column=1)
        elif new_count < current_count:
            for i in range(new_count, current_count):
                entry_actor[i].destroy()
                entry_character[i].destroy()
                del entry_actor[i]
                del entry_character[i]

    spinbox_var = tk.StringVar(value="0")
    spinbox = tk.Spinbox(
        act_char_panel,
        from_=0,
        to=25,
        textvariable=spinbox_var,
        command=on_number_change,
    )
    spinbox.grid(padx=5, pady=5, row=1, column=0, columnspan=2)

    def export_and_close():
        nonlocal filename
        show_name = show_name_entry.get().strip().replace(" ", "_")
        if show_name == "":
            show_name = "untitled_show"

        filename = f"{show_name}.json"
        save_cast_file(filename, actors)

        info_input.destroy()
        onetime_conflict_window()

    def name_show():
        save_conflicts()

        tk.Label(conflict_panel, text="show name?", bg=p_background_color).grid(
            padx=5, pady=5, row=6, column=0, columnspan=4
        )

        nonlocal show_name_entry
        show_name_entry = tk.Entry(conflict_panel)
        show_name_entry.grid(padx=5, pady=5, row=7, column=0, columnspan=4)

        button_finish = tk.Button(
            conflict_panel,
            text="Finish and Save",
            bg=secondary_color,
            fg="white",
            command=export_and_close,
        )
        button_finish.grid(padx=5, pady=5, row=8, column=0, columnspan=4)

    def edit():
        done_button.config(bg=secondary_color, text="Done", command=when_done)
        for widget in act_char_panel.winfo_children():
            if isinstance(widget, tk.Entry) or isinstance(widget, tk.Spinbox):
                widget.config(state="normal")
        schedule_panel.destroy()
        conflict_panel.destroy()

    def save_conflicts():
        selected_actor = selected_actor_var.get()
        for actor in actors:
            if actor.name == selected_actor:
                for i, box in enumerate(all_listboxes):
                    selected_indices = box.curselection()
                    for index in selected_indices:
                        actor.WeeklyConflicts[i][index] = 1

    def populate_time_listboxes(listboxes):
        for box in listboxes:
            for time_string in TIME_SLOTS:
                box.insert(tk.END, time_string)

    def clear_time_selections(listboxes):
        for box in listboxes:
            box.selection_clear(0, tk.END)

    def build_conflict_panel(parent, save_command, finish_text, finish_command):
        panel = tk.Frame(parent, bg=p_background_color)
        panel.pack(padx=5, pady=5, side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(
            panel,
            bg=p_background_color,
            text="Input actor conflicts (hold ctrl and drag to select multiple)",
        ).grid(padx=5, pady=5, row=0, column=0, columnspan=8)

        for idx, day in enumerate(DAYS):
            row = 1 if idx < 4 else 3
            col = idx if idx < 4 else idx - 4
            tk.Label(panel, bg=p_background_color, text=day).grid(padx=5, pady=5, row=row, column=col)

        scrollbar = tk.Scrollbar(panel)
        scrollbar.grid(padx=5, pady=5, row=2, column=4, sticky="ns")

        listboxes = []
        for idx, _day in enumerate(DAYS):
            row = 2 if idx < 4 else 4
            col = idx if idx < 4 else idx - 4
            listbox = tk.Listbox(panel, selectmode=tk.EXTENDED, yscrollcommand=scrollbar.set, exportselection=False)
            listbox.grid(padx=5, pady=5, row=row, column=col)
            listboxes.append(listbox)
        scrollbar.config(command=lambda *args: [box.yview(*args) for box in listboxes])
        populate_time_listboxes(listboxes)

        button_save_conflicts = tk.Button(
            panel,
            text="save for this actor",
            command=save_command,
            bg=secondary_color,
            fg="white",
        )
        button_save_conflicts.grid(padx=5, pady=5, row=5, column=0, columnspan=2)

        button_save_all = tk.Button(
            panel,
            text=finish_text,
            command=finish_command,
            bg=secondary_color,
            fg="white",
        )
        button_save_all.grid(padx=5, pady=5, row=5, column=2, columnspan=2)

        return panel, listboxes

    def when_done():
        nonlocal schedule_panel, conflict_panel, all_listboxes, selected_actor_var

        done_button.config(bg="gray", text="Edit", command=edit)
        for widget in act_char_panel.winfo_children():
            if isinstance(widget, tk.Entry) or isinstance(widget, tk.Spinbox):
                widget.config(state="disabled")

        store_actor_info()
        if not actors:
            return

        schedule_panel = tk.Frame(info_input, width=700, height=500, bg=p_background_color)
        schedule_panel.pack(padx=10, pady=10, side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(schedule_panel, bg=p_background_color, text="choose an actor to set schedule").pack(
            padx=5, pady=5, side=tk.TOP, anchor="center"
        )

        selected_actor_var = tk.StringVar(value=actors[0].name)
        for actor in actors:
            option = tk.Radiobutton(
                schedule_panel,
                text=actor.name,
                variable=selected_actor_var,
                value=actor.name,
                background=p_background_color,
                command=lambda: clear_time_selections(all_listboxes),
            )
            option.pack(padx=5, pady=1, side=tk.TOP, anchor="w")

        conflict_panel, all_listboxes = build_conflict_panel(
            info_input,
            save_conflicts,
            "save all and move to one-time conflicts",
            name_show,
        )

    def onetime_conflict_window():
        nonlocal selected_actor_var, all_listboxes

        one_time_conflict = tk.Toplevel(root)
        one_time_conflict.title("One Time Conflicts")
        one_time_conflict.configure(background=m_background_color)
        one_time_conflict.minsize(1000, 600)
        one_time_conflict.maxsize(3000, 1000)

        schedule_panel = tk.Frame(one_time_conflict, width=700, height=500, bg=p_background_color)
        schedule_panel.pack(padx=10, pady=10, side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(schedule_panel, bg=p_background_color, text="choose an actor to set schedule").pack(
            padx=5, pady=5, side=tk.TOP, anchor="center"
        )

        selected_actor_var = tk.StringVar(value=actors[0].name if actors else "")
        for actor in actors:
            option = tk.Radiobutton(
                schedule_panel,
                text=actor.name,
                variable=selected_actor_var,
                value=actor.name,
                background=p_background_color,
                command=lambda: clear_time_selections(all_listboxes),
            )
            option.pack(padx=5, pady=1, side=tk.TOP, anchor="w")

        def save_selected_one_time_conflicts():
            save_one_time_conflicts(selected_actor_var, all_listboxes)

        def save_final_cast_file():
            save_selected_one_time_conflicts()
            save_cast_file(filename, actors)
            open_schedule_window()

        _panel, all_listboxes = build_conflict_panel(
            one_time_conflict,
            save_selected_one_time_conflicts,
            "save all and begin scheduling",
            save_final_cast_file,
        )

    schedule_panel = None
    conflict_panel = None
    selected_actor_var = None
    all_listboxes = []
    show_name_entry = None
    filename = "untitled_show.json"

    done_button = tk.Button(
        act_char_panel,
        text="Done",
        command=when_done,
        bg=secondary_color,
        fg="white",
        font=("Helvetica", 14),
    )

    spacer = tk.Frame(act_char_panel, bg=p_background_color)
    spacer.grid(row=98, column=0, columnspan=2, sticky="ns")
    act_char_panel.grid_rowconfigure(98, weight=1)
    done_button.grid(padx=5, pady=5, row=99, column=0, columnspan=2, sticky="s")

    label_entry_instruction = tk.Label(
        act_char_panel,
        text="enter their names and characters",
        background=p_background_color,
    )
    label_entry_instruction.grid(padx=5, pady=5, row=2, column=0, columnspan=2)
