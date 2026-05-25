"""
Petal: Scheduling Application 
"""

import tkinter as tk
from tkinter import font, Toplevel
import json
import os
import math
from datetime import datetime, date, timedelta


BG_OUTER = "#fce4ec"
BG_CARD = "#fdf2f5"
PINK_DARK = "#e89aae"
PINK_MED = "#f4a8bd"
PINK_LIGHT = "#fad4df"
PINK_PALE = "#fce8ee"
TEXT_DARK = "#c76a85"
TEXT_BODY = "#8b5566"
WHITE = "#ffffff"
YELLOW = "#fff2a8"
GREEN_LEAF = "#a8d5a2"

DATA_FILE = os.path.join(os.path.expanduser("~"), ".daily_todo_data.json")


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def normalize_day(day_data):
    if isinstance(day_data, list):
        return {"tasks": day_data, "notes": ""}
    return day_data


def draw_flower(canvas, cx, cy, size=12, petal_color=PINK_MED, center_color=YELLOW, leaf=False):
    r = size
    for i in range(5):
        angle = (i * 72) * math.pi / 180
        px = cx + r * 0.7 * math.cos(angle)
        py = cy + r * 0.7 * math.sin(angle)
        canvas.create_oval(
            px - r * 0.55, py - r * 0.55, px + r * 0.55, py + r * 0.55,
            fill=petal_color, outline=PINK_DARK, width=1,
        )
    canvas.create_oval(
        cx - r * 0.35, cy - r * 0.35, cx + r * 0.35, cy + r * 0.35,
        fill=center_color, outline=PINK_DARK, width=1,
    )
    if leaf:
        canvas.create_oval(
            cx + r * 0.4, cy + r * 0.8, cx + r * 1.6, cy + r * 1.4,
            fill=GREEN_LEAF, outline="", width=0,
        )


def draw_star(canvas, cx, cy, size=4, color=PINK_MED):
    canvas.create_polygon(
        cx, cy - size,
        cx + size * 0.3, cy - size * 0.3,
        cx + size, cy,
        cx + size * 0.3, cy + size * 0.3,
        cx, cy + size,
        cx - size * 0.3, cy + size * 0.3,
        cx - size, cy,
        cx - size * 0.3, cy - size * 0.3,
        fill=color, outline="",
    )


def draw_heart(canvas, cx, cy, size=6, color=PINK_MED):
    s = size
    canvas.create_oval(cx - s, cy - s * 0.5, cx, cy + s * 0.3, fill=color, outline="")
    canvas.create_oval(cx, cy - s * 0.5, cx + s, cy + s * 0.3, fill=color, outline="")
    canvas.create_polygon(
        cx - s + 1, cy + s * 0.1,
        cx + s - 1, cy + s * 0.1,
        cx, cy + s,
        fill=color, outline="",
    )


class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("To Do List")
        self.root.geometry("420x680")
        self.root.configure(bg=BG_OUTER)
        self.root.minsize(380, 560)
        self.root.attributes("-topmost", True)

        # Hide the native title bar
        self.root.overrideredirect(True)

        self.data = load_data()
        self.today = date.today().isoformat()
        self.ensure_today_exists()

        self.task_widgets = []
        self.build_ui()
        self.refresh_tasks()
        self.load_notes()

    def ensure_today_exists(self):
        for k in list(self.data.keys()):
            self.data[k] = normalize_day(self.data[k])

        if self.today in self.data:
            return

        prior_days = sorted([d for d in self.data.keys() if d < self.today], reverse=True)
        carried = []
        if prior_days:
            last_day = prior_days[0]
            last_tasks = self.data[last_day].get("tasks", [])
            carried = [
                {"text": t["text"], "completed": False}
                for t in last_tasks
                if not t.get("completed", False) and t.get("text", "").strip()
            ]

        self.data[self.today] = {"tasks": carried, "notes": ""}
        save_data(self.data)

    def build_ui(self):
        # Custom pink scrollbar
        scroll_canvas = tk.Canvas(self.root, bg="#fce8ee", highlightthickness=0, width=14)
        scroll_canvas.pack(side="right", fill="y")
        main_canvas = tk.Canvas(self.root, bg=BG_OUTER, highlightthickness=0)
        main_canvas.pack(side="left", fill="both", expand=True)

        def _draw_thumb(*a):
            scroll_canvas.delete("thumb")
            try:
                first, last = main_canvas.yview()
            except Exception:
                return
            h = scroll_canvas.winfo_height()
            if h <= 1:
                return
            y1 = first * h
            y2 = last * h
            if y2 - y1 < h - 2:
                scroll_canvas.create_rectangle(3, max(2, y1), 11, min(h - 2, y2),
                                              fill="#e89aae", outline="", tags="thumb")
        main_canvas.configure(yscrollcommand=lambda *a: _draw_thumb())
        scroll_canvas.bind("<Configure>", lambda e: _draw_thumb())
        def _scroll_click(event):
            h = scroll_canvas.winfo_height()
            if h > 0:
                main_canvas.yview_moveto(max(0, min(1, event.y / h)))
        scroll_canvas.bind("<Button-1>", _scroll_click)
        scroll_canvas.bind("<B1-Motion>", _scroll_click)
        # Refresh thumb on any window/content change
        

        outer = tk.Frame(main_canvas, bg=BG_OUTER)
        content_window = main_canvas.create_window((0, 0), window=outer, anchor="nw")
        def _resize_content(event):
            main_canvas.itemconfig(content_window, width=event.width)
            try: _draw_thumb()
            except Exception: pass
        main_canvas.bind("<Configure>", _resize_content)
        outer.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))

        def on_mw(event):
            main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        main_canvas.bind_all("<MouseWheel>", on_mw)

        card = tk.Frame(outer, bg=BG_CARD)
        card.pack(fill="both", expand=True, padx=4, pady=4)

        # Close button
        main_close = tk.Label(card, text="✕", font=("Helvetica", 12, "bold"),
                              bg=BG_CARD, fg=PINK_DARK, cursor="hand2")
        main_close.place(relx=1.0, x=-10, y=6, anchor="ne")
        main_close.bind("<Button-1>", lambda e: self.root.destroy())

        # === TITLE AREA ===
        title_canvas = tk.Canvas(
            card, bg=BG_CARD, height=130, highlightthickness=0
        )
        title_canvas.pack(fill="x")

        def _start_drag(event):
            self._drag_x = event.x_root - self.root.winfo_x()
            self._drag_y = event.y_root - self.root.winfo_y()
        def _do_drag(event):
            self.root.geometry(f"+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}")
        title_canvas.bind("<Button-1>", _start_drag)
        title_canvas.bind("<B1-Motion>", _do_drag)

        # Make the whole title area draggable
        def start_drag(event):
            self._drag_x = event.x_root - self.root.winfo_x()
            self._drag_y = event.y_root - self.root.winfo_y()

        def do_drag(event):
            x = event.x_root - self._drag_x
            y = event.y_root - self._drag_y
            self.root.geometry(f"+{x}+{y}")

        title_canvas.bind("<Button-1>", start_drag)
        title_canvas.bind("<B1-Motion>", do_drag)

        # Small close button in top right
        close_btn = tk.Label(
            card,
            text="\u2715",
            font=("Helvetica", 13, "bold"),
            bg=BG_CARD,
            fg=PINK_DARK,
            cursor="hand2",
        )
        close_btn.place(relx=1.0, x=-12, y=8, anchor="ne")
        close_btn.bind("<Button-1>", lambda e: self.root.destroy())

        # Small minimize button next to close
        min_btn = tk.Label(
            card,
            text="\u2013",
            font=("Helvetica", 14, "bold"),
            bg=BG_CARD,
            fg=PINK_DARK,
            cursor="hand2",
        )
        min_btn.place(relx=1.0, x=-36, y=8, anchor="ne")
        min_btn.bind("<Button-1>", lambda e: self.root.withdraw())


        def _draw_main_title(event=None):
            title_canvas.delete("all")
            w = title_canvas.winfo_width()
            if w <= 1:
                return
            cx = w / 2

            # Sparkles on left side
            draw_star(title_canvas, 22, 30, size=4)
            draw_star(title_canvas, 45, 55, size=3)
            draw_heart(title_canvas, 30, 80, size=4, color=PINK_DARK)

            # Flower on right side
            draw_flower(title_canvas, w - 28, 32, size=9, leaf=True)
            draw_star(title_canvas, w - 12, 65, size=3)

            # Cloud-shaped title bubble, centered
            title_canvas.create_oval(cx - 100, 30, cx - 50, 90, fill=PINK_LIGHT, outline="")
            title_canvas.create_oval(cx + 50, 30, cx + 100, 90, fill=PINK_LIGHT, outline="")
            title_canvas.create_oval(cx - 80, 18, cx + 80, 102, fill=PINK_LIGHT, outline="")
            title_canvas.create_text(
                cx, 60,
                text="TO DO LIST",
                font=("Helvetica", 18, "bold"),
                fill=TEXT_DARK,
            )
        title_canvas.bind("<Configure>", _draw_main_title)
        self.root.after(50, _draw_main_title)

        # === DAY STRIP ===
        days_frame = tk.Frame(card, bg=BG_CARD)
        days_frame.pack(pady=(0, 14))

        today_weekday = datetime.now().weekday()
        day_letters = ["M", "T", "W", "T", "F", "S", "S"]
        for i, letter in enumerate(day_letters):
            is_today = (i == today_weekday)
            bg = PINK_MED if is_today else WHITE
            fg = WHITE if is_today else TEXT_DARK
            tk.Label(
                days_frame,
                text=letter,
                font=("Helvetica", 10, "bold"),
                bg=bg,
                fg=fg,
                width=2,
                pady=3,
            ).pack(side="left", padx=2)

        # === TASKS CARD ===
        # Use a canvas-based card so the corner flower can sit cleanly
        tasks_wrap = tk.Frame(card, bg=BG_CARD)
        tasks_wrap.pack(fill="x", padx=18, pady=(0, 12))

        tasks_card = tk.Frame(
            tasks_wrap,
            bg=WHITE,
            highlightbackground=PINK_LIGHT,
            highlightthickness=2,
        )
        tasks_card.pack(fill="x")

        # Small top spacer
        tk.Frame(tasks_card, bg=WHITE, height=14).pack(fill="x")

        # Tasks list area
        self.tasks_inner = tk.Frame(tasks_card, bg=WHITE)
        self.tasks_inner.pack(fill="x", padx=15)

        # Add row button
        add_btn_frame = tk.Frame(tasks_card, bg=WHITE)
        add_btn_frame.pack(pady=(10, 10))

        tk.Button(
            add_btn_frame,
            text="+ add row",
            font=("Helvetica", 10, "italic"),
            bg=WHITE,
            fg=PINK_DARK,
            activebackground=PINK_PALE,
            activeforeground=PINK_DARK,
            highlightbackground=PINK_LIGHT,
            relief="flat",
            bd=1,
            padx=14,
            pady=2,
            cursor="hand2",
            command=self.add_task_row,
        ).pack()

        # Heart in bottom corner of tasks card
        heart_canvas = tk.Canvas(tasks_card, bg=WHITE, height=22, highlightthickness=0)
        heart_canvas.pack(fill="x")
        heart_canvas.bind(
            "<Configure>",
            lambda e: (heart_canvas.delete("all"), draw_heart(heart_canvas, e.width - 25, 11, size=7, color=PINK_DARK))
        )

        # Corner flower sits ON the white card, not overlapping outside
        corner_flower = tk.Canvas(
            tasks_card, bg=WHITE, width=36, height=36, highlightthickness=0
        )
        corner_flower.place(relx=1.0, y=4, anchor="ne", x=-4)
        draw_flower(corner_flower, 18, 18, size=10, leaf=True)

        # === NOTES BANNER ===
        notes_banner_canvas = tk.Canvas(
            card, bg=BG_CARD, height=44, highlightthickness=0
        )
        notes_banner_canvas.pack(fill="x", pady=(4, 0))

        # Center the banner using configure event
        def draw_banner(event):
            notes_banner_canvas.delete("all")
            w = event.width
            cx = w / 2
            notes_banner_canvas.create_polygon(
                cx - 70, 10,
                cx + 70, 10,
                cx + 70, 34,
                cx - 70, 34,
                cx - 80, 22,
                fill=PINK_MED, outline="",
            )
            notes_banner_canvas.create_text(
                cx, 22,
                text="NOTES",
                font=("Helvetica", 11, "bold"),
                fill=WHITE,
            )
            draw_heart(notes_banner_canvas, cx + 95, 22, size=5, color=PINK_DARK)

        notes_banner_canvas.bind("<Configure>", draw_banner)

        # === NOTES CARD ===
        notes_outer = tk.Frame(card, bg=BG_CARD)
        notes_outer.pack(fill="x", padx=18, pady=(4, 12))

        notes_card = tk.Frame(
            notes_outer,
            bg=WHITE,
            highlightbackground=PINK_LIGHT,
            highlightthickness=2,
        )
        notes_card.pack(fill="x")

        self.notes_text = tk.Text(
            notes_card,
            font=("Helvetica", 11, "italic"),
            bg=WHITE,
            fg=TEXT_BODY,
            relief="flat",
            bd=0,
            height=5,
            wrap="word",
            padx=14,
            pady=10,
            insertbackground=PINK_DARK,
            highlightthickness=0,
        )
        self.notes_text.pack(fill="x")
        self.notes_placeholder = ""
        self.notes_text.bind("<FocusIn>", self.notes_focus_in)
        self.notes_text.bind("<FocusOut>", self.notes_focus_out)
        self.notes_text.bind("<KeyRelease>", lambda e: self.save_notes())

        # Flowers at bottom corners - keep them inside the white card with proper sizing
        notes_flowers = tk.Canvas(notes_card, bg=WHITE, height=36, highlightthickness=0)
        notes_flowers.pack(fill="x")

        def draw_notes_flowers(event):
            notes_flowers.delete("all")
            w = event.width
            draw_flower(notes_flowers, 22, 18, size=9, leaf=True)
            draw_flower(notes_flowers, w - 22, 18, size=9, leaf=True)

        notes_flowers.bind("<Configure>", draw_notes_flowers)

        # === FOOTER ===
        footer = tk.Frame(card, bg=BG_CARD)
        footer.pack(fill="x", padx=18, pady=(0, 18))

        progress_box = tk.Frame(
            footer,
            bg=WHITE,
            highlightbackground=PINK_LIGHT,
            highlightthickness=1,
        )
        progress_box.pack(side="left")

        progress_inner = tk.Frame(progress_box, bg=WHITE)
        progress_inner.pack(padx=10, pady=3)

        heart_icon = tk.Canvas(progress_inner, bg=WHITE, width=14, height=14, highlightthickness=0)
        heart_icon.pack(side="left")
        draw_heart(heart_icon, 7, 7, size=5, color=PINK_DARK)

        self.progress_label = tk.Label(
            progress_inner,
            text="  0 of 0 done",
            font=("Helvetica", 10, "bold"),
            bg=WHITE,
            fg=TEXT_DARK,
        )
        self.progress_label.pack(side="left")

        archive_btn = tk.Button(
            footer,
            text="\u2691 archive",
            font=("Helvetica", 10, "italic"),
            bg=WHITE,
            fg=PINK_DARK,
            activebackground=PINK_PALE,
            highlightbackground=PINK_LIGHT,
            relief="flat",
            bd=1,
            padx=12,
            pady=3,
            cursor="hand2",
            command=self.open_archive,
        )
        archive_btn.pack(side="right")

    def refresh_tasks(self):
        for w in self.task_widgets:
            w["frame"].destroy()
            w["underline"].destroy()
        self.task_widgets = []

        tasks = self.data[self.today]["tasks"]
        for i, task in enumerate(tasks):
            self.render_task_row(i, task)

        self.update_progress()

    def render_task_row(self, index, task):
        row = tk.Frame(self.tasks_inner, bg=WHITE)
        row.pack(fill="x", pady=(2, 0))

        check_var = tk.BooleanVar(value=task["completed"])

        def toggle():
            self.data[self.today]["tasks"][index]["completed"] = check_var.get()
            save_data(self.data)
            self.refresh_tasks()

        check = tk.Checkbutton(
            row,
            variable=check_var,
            command=toggle,
            bg=WHITE,
            activebackground=WHITE,
            selectcolor=WHITE,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )
        check.pack(side="left", padx=(0, 6))

        entry_font = font.Font(family="Helvetica", size=11, slant="italic")
        if task["completed"]:
            entry_font.config(overstrike=1)
            fg_color = PINK_MED
        else:
            fg_color = TEXT_BODY

        entry = tk.Entry(
            row,
            font=entry_font,
            bg=WHITE,
            fg=fg_color,
            relief="flat",
            bd=0,
            insertbackground=PINK_DARK,
            highlightthickness=0,
        )
        entry.insert(0, task["text"])
        entry.pack(side="left", fill="x", expand=True, ipady=2)

        underline = tk.Frame(self.tasks_inner, bg=PINK_LIGHT, height=1)
        underline.pack(fill="x", padx=(28, 4), pady=(2, 4))

        def on_edit(event=None):
            self.data[self.today]["tasks"][index]["text"] = entry.get()
            save_data(self.data)
            self.update_progress()

        def on_enter(event=None):
            on_edit()
            self.add_task_row()
            return "break"

        def delete_row(event=None):
            del self.data[self.today]["tasks"][index]
            save_data(self.data)
            self.refresh_tasks()

        entry.bind("<KeyRelease>", on_edit)
        entry.bind("<Return>", on_enter)
        entry.bind("<Button-3>", delete_row)
        entry.bind("<Control-Button-1>", delete_row)

        # Visible × delete button on the right
        del_btn = tk.Label(
            row, text="\u2715", font=("Helvetica", 11),
            bg=WHITE, fg=PINK_MED, cursor="hand2",
        )
        del_btn.pack(side="right", padx=(4, 0))
        del_btn.bind("<Button-1>", delete_row)
        del_btn.bind("<Enter>", lambda e: del_btn.config(fg=PINK_DARK))
        del_btn.bind("<Leave>", lambda e: del_btn.config(fg=PINK_MED))

        self.task_widgets.append({
            "frame": row,
            "underline": underline,
            "entry": entry,
        })

    def add_task_row(self):
        self.data[self.today]["tasks"].append({"text": "", "completed": False})
        save_data(self.data)
        self.refresh_tasks()
        if self.task_widgets:
            self.task_widgets[-1]["entry"].focus_set()

    def update_progress(self):
        tasks = self.data[self.today]["tasks"]
        filled = [t for t in tasks if t["text"].strip()]
        done = sum(1 for t in filled if t["completed"])
        total = len(filled)
        self.progress_label.config(text=f"  {done} of {total} done")

    def load_notes(self):
        notes = self.data[self.today].get("notes", "")
        if notes:
            self.notes_text.insert("1.0", notes)
            self.notes_text.config(fg=TEXT_BODY)
        else:
            self.notes_text.insert("1.0", self.notes_placeholder)
            self.notes_text.config(fg=PINK_MED)

    def notes_focus_in(self, event):
        current = self.notes_text.get("1.0", "end-1c")
        if current == self.notes_placeholder:
            self.notes_text.delete("1.0", "end")
            self.notes_text.config(fg=TEXT_BODY)

    def notes_focus_out(self, event):
        current = self.notes_text.get("1.0", "end-1c")
        if not current.strip():
            self.notes_text.delete("1.0", "end")
            self.notes_text.insert("1.0", self.notes_placeholder)
            self.notes_text.config(fg=PINK_MED)

    def save_notes(self):
        current = self.notes_text.get("1.0", "end-1c")
        if current == self.notes_placeholder:
            self.data[self.today]["notes"] = ""
        else:
            self.data[self.today]["notes"] = current
        save_data(self.data)

    def open_archive(self):
        ArchiveWindow(self.root, self.data, self.today)


class ArchiveWindow:
    def __init__(self, parent, data, today):
        self.window = Toplevel(parent)
        self.window.title("Archive")
        self.window.geometry("400x560")
        self.window.configure(bg=BG_OUTER)
        self.window.attributes("-topmost", True)
        self.window.overrideredirect(True)

        self.data = data
        self.today = today

        outer = tk.Frame(self.window, bg=BG_OUTER)
        outer.pack(fill="both", expand=True, padx=10, pady=10)

        card = tk.Frame(outer, bg=BG_CARD)
        card.pack(fill="both", expand=True)

        title_canvas = tk.Canvas(card, bg=BG_CARD, height=90, highlightthickness=0)
        title_canvas.pack(fill="x")

        def _arch_start(event):
            self._adx = event.x_root - self.window.winfo_x()
            self._ady = event.y_root - self.window.winfo_y()
        def _arch_drag(event):
            self.window.geometry(f"+{event.x_root - self._adx}+{event.y_root - self._ady}")
        title_canvas.bind("<Button-1>", _arch_start)
        title_canvas.bind("<B1-Motion>", _arch_drag)

        arch_close = tk.Label(card, text="✕", font=("Helvetica", 12, "bold"),
                              bg=BG_CARD, fg=PINK_DARK, cursor="hand2")
        arch_close.place(relx=1.0, x=-10, y=6, anchor="ne")
        arch_close.bind("<Button-1>", lambda e: self.window.destroy())

        def _draw_arch_title(event=None):
            title_canvas.delete("all")
            w = title_canvas.winfo_width()
            if w <= 1:
                return
            cx = w / 2

            draw_star(title_canvas, 22, 28, size=4)
            draw_star(title_canvas, 40, 55, size=3)
            draw_flower(title_canvas, w - 28, 30, size=9, leaf=True)
            draw_star(title_canvas, w - 12, 58, size=3)

            title_canvas.create_oval(cx - 90, 22, cx - 45, 70, fill=PINK_LIGHT, outline="")
            title_canvas.create_oval(cx + 45, 22, cx + 90, 70, fill=PINK_LIGHT, outline="")
            title_canvas.create_oval(cx - 70, 12, cx + 70, 80, fill=PINK_LIGHT, outline="")
            title_canvas.create_text(
                cx, 46,
                text="ARCHIVE",
                font=("Helvetica", 16, "bold"),
                fill=TEXT_DARK,
            )
        title_canvas.bind("<Configure>", _draw_arch_title)
        self.window.after(50, _draw_arch_title)

        list_frame = tk.Frame(card, bg=BG_CARD)
        list_frame.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        canv = tk.Canvas(list_frame, bg=BG_CARD, highlightthickness=0)
        scrl = tk.Scrollbar(list_frame, orient="vertical", command=canv.yview)
        inner = tk.Frame(canv, bg=BG_CARD)

        inner.bind("<Configure>", lambda e: canv.configure(scrollregion=canv.bbox("all")))
        canv.create_window((0, 0), window=inner, anchor="nw", width=440)
        canv.configure(yscrollcommand=scrl.set)
        canv.pack(side="left", fill="both", expand=True)
        scrl.pack(side="right", fill="y")

        def on_mw(event):
            canv.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canv.bind("<MouseWheel>", on_mw)
        inner.bind("<MouseWheel>", on_mw)

        sorted_days = sorted(self.data.keys(), reverse=True)

        if not sorted_days:
            tk.Label(
                inner,
                text="No past days yet \u2661",
                font=("Helvetica", 11, "italic"),
                bg=BG_CARD,
                fg=TEXT_BODY,
                pady=40,
            ).pack()
            return

        for day in sorted_days:
            self.render_day(inner, day)

    def render_day(self, parent, day_iso):
        day_data = normalize_day(self.data[day_iso])
        tasks = day_data.get("tasks", [])
        notes = day_data.get("notes", "")

        if not tasks and not notes.strip():
            return

        d = datetime.fromisoformat(day_iso).date()
        if day_iso == self.today:
            date_label = "Today  \u00b7  " + d.strftime("%B %d, %Y")
        elif day_iso == (date.today() - timedelta(days=1)).isoformat():
            date_label = "Yesterday  \u00b7  " + d.strftime("%B %d, %Y")
        else:
            date_label = d.strftime("%A  \u00b7  %B %d, %Y")

        day_card = tk.Frame(
            parent,
            bg=WHITE,
            highlightbackground=PINK_LIGHT,
            highlightthickness=2,
        )
        day_card.pack(fill="x", pady=8)

        header = tk.Frame(day_card, bg=PINK_PALE)
        header.pack(fill="x")

        tk.Label(
            header,
            text=date_label,
            font=("Helvetica", 11, "bold"),
            bg=PINK_PALE,
            fg=TEXT_DARK,
            padx=12,
            pady=6,
        ).pack(side="left")

        filled = [t for t in tasks if t.get("text", "").strip()]
        done = sum(1 for t in filled if t.get("completed"))
        tk.Label(
            header,
            text=f"{done}/{len(filled)} \u2665",
            font=("Helvetica", 10),
            bg=PINK_PALE,
            fg=TEXT_DARK,
            padx=12,
        ).pack(side="right")

        body = tk.Frame(day_card, bg=WHITE)
        body.pack(fill="x", padx=14, pady=10)

        if filled:
            for t in filled:
                row = tk.Frame(body, bg=WHITE)
                row.pack(fill="x", pady=1)

                symbol = "\u2713" if t.get("completed") else "\u25cb"
                color = PINK_MED if t.get("completed") else TEXT_BODY

                tk.Label(
                    row,
                    text=symbol,
                    font=("Helvetica", 11),
                    bg=WHITE,
                    fg=color,
                    width=2,
                ).pack(side="left")

                task_font = font.Font(family="Helvetica", size=10, slant="italic")
                if t.get("completed"):
                    task_font.config(overstrike=1)

                tk.Label(
                    row,
                    text=t.get("text", ""),
                    font=task_font,
                    bg=WHITE,
                    fg=color,
                    anchor="w",
                    wraplength=360,
                    justify="left",
                ).pack(side="left", fill="x", expand=True)
        else:
            tk.Label(
                body,
                text="(no tasks)",
                font=("Helvetica", 10, "italic"),
                bg=WHITE,
                fg=PINK_MED,
            ).pack(anchor="w")

        if notes.strip():
            tk.Frame(body, bg=PINK_LIGHT, height=1).pack(fill="x", pady=8)
            tk.Label(
                body,
                text="Notes:",
                font=("Helvetica", 9, "bold"),
                bg=WHITE,
                fg=TEXT_DARK,
                anchor="w",
            ).pack(fill="x")
            tk.Label(
                body,
                text=notes,
                font=("Helvetica", 10, "italic"),
                bg=WHITE,
                fg=TEXT_BODY,
                anchor="w",
                wraplength=400,
                justify="left",
            ).pack(fill="x", pady=(2, 0))


def main():
    root = tk.Tk()
    TodoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
