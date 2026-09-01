import json
import tkinter as tk
from tkinter import filedialog, messagebox

from Actors import Actor
from open_info_input import DAYS, TIME_SLOTS, open_info_input, save_cast_file
from scheduler_window import open_scheduler_window


root = tk.Tk()
actors = []


#theme colors
m_background_color = "light blue"
p_background_color = "light green"
secondary_color = "blue"

# Setting some window properties for the initial window
root.title("Barnies Scheduler")
root.configure(background=m_background_color)
root.minsize(1000, 600)
root.maxsize(3000, 1000)
root.geometry("1000x600+350+175")

tk.Label(root, text="mostly vibe-coded by Erin Ventrudo, 2026", background=m_background_color).place(relx = 1, rely = 1, anchor = 'se')

def openScheduleWindow():
    open_scheduler_window(
        root,
        m_background_color,
        p_background_color,
        secondary_color,
        actors,
    )



def blank_conflict_grid():
    return [[0] * len(TIME_SLOTS) for _ in DAYS]


def conflict_dict_to_grid(conflicts_by_day):
    conflict_grid = blank_conflict_grid()
    if not isinstance(conflicts_by_day, dict):
        return conflict_grid

    for day_index, day in enumerate(DAYS):
        for time_string in conflicts_by_day.get(day, []):
            if time_string in TIME_SLOTS:
                conflict_grid[day_index][TIME_SLOTS.index(time_string)] = 1
    return conflict_grid


def combine_conflict_grids(first_grid, second_grid):
    return [
        [
            first_grid[day_index][time_index] or second_grid[day_index][time_index]
            for time_index in range(len(TIME_SLOTS))
        ]
        for day_index in range(len(DAYS))
    ]


def update_all_conflicts(actor):
    actor.allConflicts = combine_conflict_grids(
        actor.WeeklyConflicts,
        actor.OneTimeConflicts,
    )


def build_actor_from_json(actor_data, one_time_conflicts):
    actor = Actor(
        actor_data.get("name", ""),
        actor_data.get("characters", []),
    )
    actor.WeeklyConflicts = conflict_dict_to_grid(actor_data.get("weekly_conflicts", {}))
    actor.OneTimeConflicts = one_time_conflicts
    update_all_conflicts(actor)
    return actor


def load_cast_json(filename, one_time_choice):
    with open(filename, "r") as f:
        cast_data = json.load(f)

    loaded_actors = []
    for actor_data in cast_data.get("actors", []):
        imported_one_time = conflict_dict_to_grid(actor_data.get("one_time_conflicts", {}))

        if one_time_choice in ["keep", "add"]:
            one_time_conflicts = imported_one_time
        else:
            one_time_conflicts = blank_conflict_grid()

        loaded_actors.append(build_actor_from_json(actor_data, one_time_conflicts))

    actors.clear()
    actors.extend(loaded_actors)


def populate_time_listboxes(listboxes):
    for box in listboxes:
        for time_string in TIME_SLOTS:
            box.insert(tk.END, time_string)


def show_actor_one_time_conflicts(selected_actor_var, listboxes):
    for box in listboxes:
        box.selection_clear(0, tk.END)

    selected_actor = selected_actor_var.get()
    for actor in actors:
        if actor.name == selected_actor:
            for day_index, box in enumerate(listboxes):
                for time_index, has_conflict in enumerate(actor.OneTimeConflicts[day_index]):
                    if has_conflict:
                        box.selection_set(time_index)
            return


def open_one_time_conflict_window(filename):
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

    conflict_panel = tk.Frame(one_time_conflict, bg=p_background_color)
    conflict_panel.pack(padx=5, pady=5, side=tk.LEFT, fill=tk.BOTH, expand=True)

    tk.Label(
        conflict_panel,
        bg=p_background_color,
        text="Input actor conflicts (hold ctrl and drag to select multiple)",
    ).grid(padx=5, pady=5, row=0, column=0, columnspan=8)

    for idx, day in enumerate(DAYS):
        row = 1 if idx < 4 else 3
        col = idx if idx < 4 else idx - 4
        tk.Label(conflict_panel, bg=p_background_color, text=day).grid(
            padx=5,
            pady=5,
            row=row,
            column=col,
        )

    scrollbar = tk.Scrollbar(conflict_panel)
    scrollbar.grid(padx=5, pady=5, row=2, column=4, sticky="ns")

    all_listboxes = []
    for idx, _day in enumerate(DAYS):
        row = 2 if idx < 4 else 4
        col = idx if idx < 4 else idx - 4
        listbox = tk.Listbox(
            conflict_panel,
            selectmode=tk.EXTENDED,
            yscrollcommand=scrollbar.set,
            exportselection=False,
        )
        listbox.grid(padx=5, pady=5, row=row, column=col)
        all_listboxes.append(listbox)
    scrollbar.config(command=lambda *args: [box.yview(*args) for box in all_listboxes])
    populate_time_listboxes(all_listboxes)

    selected_actor_var = tk.StringVar(value=actors[0].name if actors else "")

    for actor in actors:
        option = tk.Radiobutton(
            schedule_panel,
            text=actor.name,
            variable=selected_actor_var,
            value=actor.name,
            background=p_background_color,
            command=lambda: show_actor_one_time_conflicts(selected_actor_var, all_listboxes),
        )
        option.pack(padx=5, pady=1, side=tk.TOP, anchor="w")

    def save_selected_one_time_conflicts():
        save_1Timeconflicts(selected_actor_var, all_listboxes)

    def save_final_cast_file():
        save_selected_one_time_conflicts()
        save_cast_file(filename, actors)
        one_time_conflict.destroy()
        openScheduleWindow()

    tk.Button(
        conflict_panel,
        text="save for this actor",
        command=save_selected_one_time_conflicts,
        bg=secondary_color,
        fg="white",
    ).grid(padx=5, pady=5, row=5, column=0, columnspan=2)

    tk.Button(
        conflict_panel,
        text="save all and begin scheduling",
        command=save_final_cast_file,
        bg=secondary_color,
        fg="white",
    ).grid(padx=5, pady=5, row=5, column=2, columnspan=2)

    show_actor_one_time_conflicts(selected_actor_var, all_listboxes)


def choose_one_time_import_choice(filename):
    choice_window = tk.Toplevel(root)
    choice_window.title("One-Time Conflicts")
    choice_window.configure(background=m_background_color)
    choice_window.geometry("450x250+450+250")

    tk.Label(
        choice_window,
        text="What should happen to one-time conflicts?",
        background=m_background_color,
        font=("Helvetica", 14),
    ).pack(padx=20, pady=20)

    def import_with_choice(choice):
        try:
            load_cast_json(filename, choice)
            choice_window.destroy()
            if choice == "keep":
                openScheduleWindow()
            else:
                open_one_time_conflict_window(filename)
        except (OSError, json.JSONDecodeError) as error:
            messagebox.showerror("Import Failed", str(error))

    tk.Button(
        choice_window,
        text="Keep JSON One-Time Conflicts",
        bg=secondary_color,
        fg="white",
        command=lambda: import_with_choice("keep"),
    ).pack(padx=20, pady=5, fill=tk.X)

    tk.Button(
        choice_window,
        text="Add More One-Time Conflicts",
        bg=secondary_color,
        fg="white",
        command=lambda: import_with_choice("add"),
    ).pack(padx=20, pady=5, fill=tk.X)

    tk.Button(
        choice_window,
        text="Override JSON One-Time Conflicts",
        bg=secondary_color,
        fg="white",
        command=lambda: import_with_choice("override"),
    ).pack(padx=20, pady=5, fill=tk.X)


def import_cast_file():
    filename = filedialog.askopenfilename(
        title="Choose cast JSON file",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
    )
    if filename:
        choose_one_time_import_choice(filename)


def save_1Timeconflicts(selectedActor, allListboxes):
    selected_actor = selectedActor.get()
    for actor in actors:
        if actor.name == selected_actor:
            # Gather selected times from each listbox
            for i, box in enumerate(allListboxes):
                selected_indices = box.curselection()
                for index in selected_indices:
                    # Mark the corresponding time slot as a conflict (1)
                    actor.OneTimeConflicts[i][index] = 1
            update_all_conflicts(actor)







#button to open cast info input window
button = tk.Button(
    root,
    text = "Input New Cast Information",
    bg=secondary_color,
    fg = "white",
    font = ("Helvetica", 14),
    command=lambda: open_info_input(
        root,
        m_background_color,
        p_background_color,
        secondary_color,
        actors,
        openScheduleWindow,
        save_1Timeconflicts,
    )
)
button.pack(padx=20, pady=20)


button_import = tk.Button(
    root,
    text="Import Cast JSON",
    bg=secondary_color,
    fg="white",
    font=("Helvetica", 14),
    command=import_cast_file,
)
button_import.pack(padx=20, pady=20)




root.mainloop()
