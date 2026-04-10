import tkinter as tk
from tkinter import messagebox
from popups import show_confirm, show_info
import subprocess
import threading
import re
import json
import os
import math
from datetime import datetime

CHATS_FILE = "C:\\container\\chats.json"

# Modern gradient-based color scheme
BG = "#0a0a0a"
SURFACE = "#1a1a2e"
SURFACE2 = "#16213e"
BORDER = "#0f3460"
ACCENT = "#e94560"
ACCENT_HOVER = "#ff6b6b"
ACCENT_DIM = "#c44569"
TEXT = "#f5f5f5"
TEXT_DIM = "#a8a8a8"
TEXT_MID = "#d3d3d3"
SUCCESS = "#00d9ff"
USER_BG = "#2d3561"
AGENT_BG = "#0f3460"
FONT = ("Segoe UI", 10)
FONT_MONO = ("Cascadia Code", 9)

def load_chats():
    if os.path.exists(CHATS_FILE):
        with open(CHATS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_chats():
    with open(CHATS_FILE, "w") as f:
        json.dump(chats, f, indent=2)

chats = load_chats()
current_chat_id = [None]

def new_chat():
    chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    opener = "Hello! I'm Jarvis, your AI assistant. How can I help you today?"
    chats[chat_id] = {
        "title": "New chat",
        "messages": [{"sender": "Agent", "text": opener}],
        "created": datetime.now().strftime("%b %d, %H:%M")
    }
    save_chats()
    current_chat_id[0] = chat_id
    refresh_sidebar()
    clear_chat_area()
    add_bubble("Agent", opener, AGENT_BG, SUCCESS, save=False)
    return chat_id

def delete_chat(chat_id):
    if chat_id not in chats:
        return
    
    # Show custom confirmation dialog with modern styling
    chat_title = chats[chat_id]["title"]
    result = show_confirm(
        root,
        "Delete Chat",
        f"Are you sure you want to delete this chat?\n\n{chat_title}",
        confirm_text="Delete",
        cancel_text="Cancel"
    )
    
    if result:
        del chats[chat_id]
        save_chats()
        refresh_sidebar()
        if current_chat_id[0] == chat_id:
            if chats:
                load_chat(list(chats.keys())[-1])
            else:
                current_chat_id[0] = None
                clear_chat_area()

def load_chat(chat_id):
    current_chat_id[0] = chat_id
    clear_chat_area()
    for msg in chats[chat_id]["messages"]:
        if msg["sender"] == "You":
            add_bubble("You", msg["text"], USER_BG, "#a89fff", save=False)
        else:
            add_bubble("Agent", msg["text"], AGENT_BG, SUCCESS, save=False)
    refresh_sidebar()

def clear_chat_area():
    for widget in chat_frame.winfo_children():
        widget.destroy()
    chat_canvas.yview_moveto(0)

def refresh_sidebar():
    for widget in sidebar_inner.winfo_children():
        widget.destroy()

    if not chats:
        tk.Label(sidebar_inner, text="No chats yet", font=("Segoe UI", 9),
                 bg=BG, fg=TEXT_DIM).pack(pady=20)
        return

    for chat_id, chat in reversed(list(chats.items())):
        is_active = chat_id == current_chat_id[0]

        row = tk.Frame(sidebar_inner, bg=SURFACE if is_active else BG, cursor="hand2")
        row.pack(fill="x", padx=8, pady=2)

        left = tk.Frame(row, bg=SURFACE if is_active else BG)
        left.pack(side="left", fill="x", expand=True, padx=(10, 0), pady=6)

        tk.Label(left, text=chat["title"][:22],
                 font=("Segoe UI", 9, "bold" if is_active else "normal"),
                 bg=SURFACE if is_active else BG,
                 fg=TEXT if is_active else TEXT_MID,
                 anchor="w").pack(fill="x")

        tk.Label(left, text=chat.get("created", ""),
                 font=("Segoe UI", 7),
                 bg=SURFACE if is_active else BG,
                 fg=TEXT_DIM, anchor="w").pack(fill="x")

        del_btn = tk.Button(row, text="  🗑️", font=("Segoe UI", 8, "bold"),
                            bg=BG,
                            fg=TEXT_DIM,
                            activebackground=SURFACE2,
                            activeforeground=TEXT,
                            relief="flat", bd=0, cursor="hand2",
                            padx=8, pady=4,
                            command=lambda cid=chat_id: delete_chat(cid))
        del_btn.pack(side="right", padx=4)
        add_hover_effect(del_btn, "#ff4757", "#ff6b6b")

        row.bind("<Button-1>", lambda e, cid=chat_id: load_chat(cid))
        left.bind("<Button-1>", lambda e, cid=chat_id: load_chat(cid))
        for child in left.winfo_children():
            child.bind("<Button-1>", lambda e, cid=chat_id: load_chat(cid))

def update_chat_title(chat_id, first_message):
    title = first_message[:24] + ("..." if len(first_message) > 24 else "")
    chats[chat_id]["title"] = title
    save_chats()
    refresh_sidebar()

def clean_line(line):
    line = re.sub(r'\x1b\[[0-9;]*m', '', line)
    line = re.sub(r'\\u[0-9a-fA-F]{4}', '', line)
    skip_patterns = [
        "DEBUG:", "httpx", "HTTP Request", "NoneType", "pydantic",
        "TokenUsage", "input_tokens", "output_tokens",
        "future.result", "runners.py", "base_events", "Adding to agent_lines:",
        "Calling update_agent_bubble", "Line filtered out:", "Process finished",
        "Subprocess started", "Starting execution with task:", "Final text:",
        "Calling finish_run", "No agent_lines", "Error reading output:",
        "DEBUG: Exception occurred"
    ]
    for pattern in skip_patterns:
        if pattern.lower() in line.lower() and len(line.strip()) < 50:
            return None
    cleaned = line.strip()
    if cleaned and len(cleaned) > 0:
        return cleaned
    return None

def fade_in_widget(widget, steps=10, delay=50):
    """Smooth fade-in animation for widgets"""
    def update_alpha(step):
        if step <= steps:
            alpha = step / steps
            # Create a subtle scale effect instead of alpha (tkinter doesn't support alpha)
            scale = 0.9 + (0.1 * alpha)
            widget.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.9, 
                       anchor='center')
            widget.after(delay, lambda: update_alpha(step + 1))
        else:
            widget.place_forget()
            widget.pack(fill="both", expand=True)
    
    widget.after(delay, lambda: update_alpha(1))

def animate_status_dot(color, steps=8):
    """Animate status dot with pulsing effect"""
    def pulse(step):
        if step <= steps:
            # Create pulsing effect by changing size
            size = 8 + 2 * math.sin(step * math.pi / 4)
            status_dot.config(font=("Segoe UI", int(size)), fg=color)
            root.after(100, lambda: pulse(step + 1))
        else:
            status_dot.config(font=("Segoe UI", 9), fg=color)
    
    pulse(1)

def create_gradient_frame(parent, color1, color2, height=30):
    """Create a gradient effect frame"""
    gradient_frame = tk.Frame(parent, height=height, bg=color1)
    
    # Simulate gradient with multiple frames
    for i in range(height):
        ratio = i / height
        # Interpolate between colors
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
        
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        
        color = f"#{r:02x}{g:02x}{b:02x}"
        line = tk.Frame(gradient_frame, height=1, bg=color)
        line.pack(fill="x")
    
    return gradient_frame

def add_hover_effect(widget, bg_color, hover_color):
    """Add hover effect to widgets"""
    def on_enter(e):
        widget.config(bg=hover_color)
    
    def on_leave(e):
        widget.config(bg=bg_color)
    
    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)

def send_message(event=None):
    task = chat_input.get("1.0", tk.END).strip()
    if not task or is_running[0]:
        return
    chat_input.delete("1.0", tk.END)
    if current_chat_id[0] is None:
        new_chat()
    is_first = len(chats[current_chat_id[0]]["messages"]) <= 1
    add_bubble("You", task, USER_BG, "#a89fff")
    if is_first:
        update_chat_title(current_chat_id[0], task)
    run_task(task)

def run_task(task):
    is_running[0] = True
    send_btn.config(state=tk.DISABLED)
    animate_status_dot("#f4a74a")
    status_label.config(text="Thinking...")
    agent_lines = []

    def execute():
        # Use brains.py for intelligent routing
        script = "brains.py"
        print(f"DEBUG: Starting execution with task: {task}", flush=True)

        try:
            # Simple subprocess execution without stdin for now
            process = subprocess.Popen(
                ["python", "-u", script, task],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=0,  # Unbuffered output
                cwd="C:\\container",
                creationflags=0x08000000
            )
            
            print("DEBUG: Subprocess started", flush=True)
            
            # Read all output with better error handling
            line_count = 0
            full_output = []
            try:
                for line in process.stdout:
                    line_count += 1
                    line_content = line.rstrip('\n\r')
                    full_output.append(line_content)
                    print(f"DEBUG: Line {line_count}: {line_content}", flush=True)
                    cleaned = clean_line(line_content)
                    if cleaned:
                        agent_lines.append(cleaned)
                        print(f"DEBUG: Adding to agent_lines: {cleaned}", flush=True)
                        print(f"DEBUG: Calling update_agent_bubble with: {len(agent_lines)} lines", flush=True)
                        root.after(0, update_agent_bubble, "\n".join(agent_lines))
                    else:
                        print(f"DEBUG: Line filtered out: {line_content}", flush=True)
            except Exception as read_error:
                print(f"DEBUG: Error reading output: {read_error}", flush=True)
                # Try to get any remaining output
                try:
                    remaining_output, _ = process.communicate(timeout=5)
                    if remaining_output:
                        for line in remaining_output.splitlines():
                            cleaned = clean_line(line)
                            if cleaned:
                                agent_lines.append(cleaned)
                except:
                    pass
            
            print(f"DEBUG: Process finished, read {line_count} lines", flush=True)
            
            # Wait for process with timeout
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                print("DEBUG: Process timed out, terminating", flush=True)
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            
            # If no output, try with simple confirmation
            if not agent_lines:
                print("DEBUG: No agent_lines, adding fallback message", flush=True)
                agent_lines.append("Task completed but no output received.")
                root.after(0, update_agent_bubble, "\n".join(agent_lines))
            
        except Exception as e:
            print(f"DEBUG: Exception occurred: {str(e)}", flush=True)
            error_msg = f"Error: {str(e)}"
            agent_lines.append(error_msg)
            root.after(0, update_agent_bubble, "\n".join(agent_lines))
        finally:
            final_text = "\n".join(agent_lines) if agent_lines else "No output."
            print(f"DEBUG: Final text: {final_text}", flush=True)
            if current_chat_id[0]:
                chats[current_chat_id[0]]["messages"].append({
                    "sender": "Agent", "text": final_text
                })
                save_chats()
            print("DEBUG: Calling finish_run", flush=True)
            root.after(0, finish_run)

    add_agent_bubble()
    threading.Thread(target=execute, daemon=True).start()

def copy_to_clipboard(text):
    """Copy text to clipboard with custom feedback"""
    try:
        root.clipboard_clear()
        root.clipboard_append(text)
        show_info(root, "Success", "Text copied to clipboard!", "✅")
    except Exception as e:
        show_info(root, "Error", f"Failed to copy: {str(e)}", "❌")

def copy_text_to_clipboard(text):
    """Copy text to clipboard without feedback for context menu"""
    try:
        root.clipboard_clear()
        root.clipboard_append(text)
    except Exception:
        pass  # Silent fail for context menu

def calculate_text_dimensions(text, font):
    """Calculate appropriate width and height for text widget based on content"""
    lines = text.split('\n')
    # Calculate width based on longest line - use more generous sizing
    max_line_length = max(len(line) for line in lines) if lines else 0
    # Use a minimum width of 50, and scale up for very long lines
    width = min(max(max_line_length // 6 + 10, 50), 90)  # Min 50, max 90
    
    # Calculate height based on number of lines and text length
    base_height = len(lines)
    # Estimate additional height needed for wrapping (rough approximation)
    avg_chars_per_line = 40  # Approximate chars that fit in width
    estimated_wrapped_lines = max_line_length // avg_chars_per_line
    height = max(base_height, estimated_wrapped_lines)
    
    # Extra height for long text (no maximum limits)
    if len(text) > 200:
        height += 1
    if len(text) > 500:
        height += 2
    if len(text) > 1000:
        height += 3
    if len(text) > 2000:
        height += 5
    
    # Only minimum height constraint, no maximum
    height = max(height, 1)
    
    return width, height

def create_text_with_copy(bubble, text, font, bg_color, fg_color):
    """Create a text widget with copy functionality"""
    # Create a frame for text and copy button
    text_frame = tk.Frame(bubble, bg=bg_color)
    text_frame.pack(fill="both", expand=True)
    
    # Create text widget for better text selection
    text_widget = tk.Text(
        text_frame, 
        font=font, 
        bg=bg_color, 
        fg=fg_color,
        wrap="word",
        relief="flat",
        bd=0,
        padx=0,
        pady=0,
        cursor="arrow",
        width=50,
        height=10
    )
    text_widget.insert("1.0", text)
    text_widget.config(state="normal")  # Allow selection
    text_widget.pack(side="left", fill="both", expand=True)
    
    # Add copy button
    copy_btn = tk.Button(
        text_frame,
        text="Copy",
        font=("Segoe UI", 8),
        bg=ACCENT,
        fg="white",
        activebackground=ACCENT_HOVER,
        activeforeground="white",
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=8,
        pady=4,
        command=lambda: copy_to_clipboard(text)
    )
    copy_btn.pack(side="right", padx=(5, 0))
    
    # Bind right-click for copy
    def show_context_menu(event):
        context_menu = tk.Menu(root, tearoff=0)
        context_menu.add_command(label="Copy", command=lambda: copy_to_clipboard(text))
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    text_widget.bind("<Button-3>", show_context_menu)
    return text_widget


def add_bubble(sender, text, bg_color, name_color, save=True):
    if save and current_chat_id[0]:
        chats[current_chat_id[0]]["messages"].append({
            "sender": sender, "text": text
        })
        save_chats()

    is_user = sender == "You"
    outer = tk.Frame(chat_frame, bg=BG)
    outer.pack(fill="x", padx=20, pady=8, anchor="e" if is_user else "w")
    
    # Enhanced sender label
    sender_label = tk.Label(outer, text=sender, font=("Segoe UI", 8, "bold"),
                        bg=BG, fg=name_color)
    sender_label.pack(anchor="e" if is_user else "w", pady=(0, 3))
    
    # Modern bubble with glassmorphism effect
    bubble = tk.Frame(outer, bg=bg_color, padx=16, pady=12, relief="solid", bd=0)
    bubble.pack(anchor="e" if is_user else "w")
    bubble.config(highlightbackground=ACCENT if is_user else BORDER,
                  highlightthickness=2, relief="solid", bd=1)
    
    # Calculate dimensions
    width, height = calculate_text_dimensions(text, FONT)
    
    # Enhanced text widget
    msg = tk.Text(bubble, font=FONT, bg=bg_color, fg=TEXT,
                   wrap="word", relief="flat", bd=0, padx=10, pady=10, cursor="arrow",
                   width=width, height=height, selectbackground=ACCENT_DIM,
                   spacing1=2, spacing2=2)
    msg.insert("1.0", text)
    msg.config(state="normal")
    msg.pack(fill="x", expand=False)
    
    # Enhanced copy button with hover effect
    copy_btn = tk.Button(bubble, text="📋", font=("Segoe UI", 10),
                       bg=ACCENT, fg="white", activebackground=ACCENT_HOVER,
                       activeforeground="white", relief="flat", bd=0, cursor="hand2",
                       padx=8, pady=4, command=lambda: copy_to_clipboard(text))
    copy_btn.pack(anchor="se", padx=(8, 10), pady=(0, 6))
    add_hover_effect(copy_btn, ACCENT, ACCENT_HOVER)
    
    # Enhanced context menu
    def show_context_menu(event):
        context_menu = tk.Menu(root, tearoff=0, bg=SURFACE2, fg=TEXT,
                              activebackground=ACCENT, activeforeground="white")
        context_menu.add_command(label="📋 Copy All", command=lambda: copy_to_clipboard(text))
        context_menu.add_command(label="📝 Select All", command=lambda: msg.tag_add("sel", "1.0", "end"))
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    msg.bind("<Button-3>", show_context_menu)
    
    # Apply fade-in animation
    fade_in_widget(bubble)
    
    chat_canvas.update_idletasks()
    chat_canvas.yview_moveto(1.0)

def add_agent_bubble():
    outer = tk.Frame(chat_frame, bg=BG)
    outer.pack(fill="x", padx=20, pady=8, anchor="w")
    
    # Enhanced sender label
    tk.Label(outer, text="Agent", font=("Segoe UI", 8, "bold"),
             bg=BG, fg=SUCCESS).pack(anchor="w", pady=(0, 3))
    
    # Modern bubble with glassmorphism effect
    bubble = tk.Frame(outer, bg=AGENT_BG, padx=16, pady=12, relief="solid", bd=0)
    bubble.pack(anchor="w")
    bubble.config(highlightbackground=BORDER, highlightthickness=2, relief="solid", bd=1)
    
    # Calculate dimensions for initial text
    width, height = calculate_text_dimensions("...", FONT_MONO)
    
    # Enhanced text widget
    msg = tk.Text(bubble, font=FONT_MONO, bg=AGENT_BG, fg=TEXT_DIM,
                  wrap="word", relief="flat", bd=0, padx=10, pady=10, cursor="arrow",
                  width=width, height=height, selectbackground=ACCENT_DIM,
                  spacing1=2, spacing2=2)
    msg.insert("1.0", "...")
    msg.config(state="normal")  # Allow text selection
    msg.pack(fill="x", expand=False)
    
    # Enhanced context menu
    def show_context_menu(event):
        context_menu = tk.Menu(root, tearoff=0, bg=SURFACE2, fg=TEXT,
                              activebackground=ACCENT, activeforeground="white")
        context_menu.add_command(label="📋 Copy All", command=lambda: copy_to_clipboard(msg.get("1.0", tk.END).strip()))
        context_menu.add_command(label="📝 Select All", command=lambda: msg.tag_add("sel", "1.0", "end"))
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    msg.bind("<Button-3>", show_context_menu)
    
    # Apply fade-in animation
    fade_in_widget(bubble)
    
    current_agent_label[0] = msg
    chat_canvas.update_idletasks()
    chat_canvas.yview_moveto(1.0)

def update_agent_bubble(text):
    print(f"DEBUG: update_agent_bubble called with text: {text[:100]}...", flush=True)
    if current_agent_label[0]:
        print("DEBUG: current_agent_label exists, updating text", flush=True)
        # Clear existing text and insert new text
        current_agent_label[0].delete("1.0", tk.END)
        current_agent_label[0].insert("1.0", text)
        current_agent_label[0].config(fg=TEXT)
        
        # Adjust dimensions based on content
        width, height = calculate_text_dimensions(text, FONT_MONO)
        current_agent_label[0].config(width=width, height=height)
        
        print("DEBUG: Text updated successfully", flush=True)
    else:
        print("DEBUG: current_agent_label is None", flush=True)
    chat_canvas.update_idletasks()
    chat_canvas.yview_moveto(1.0)

def on_enter_key(event):
    if not event.state & 0x1:
        send_message()
        return "break"

is_running = [False]
current_agent_label = [None]

root = tk.Tk()
root.title("Jarvis, access the mainframe")
root.geometry("940x660")
root.configure(bg=BG)
root.resizable(True, True)

main_layout = tk.Frame(root, bg=BG)
main_layout.pack(fill="both", expand=True)

sidebar = tk.Frame(main_layout, bg=BG, width=210)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

sidebar_top = tk.Frame(sidebar, bg=BG)
sidebar_top.pack(fill="x", padx=12, pady=(18, 10))
tk.Label(sidebar_top, text="Chats", font=("Segoe UI", 11, "bold"),
         bg=BG, fg=TEXT).pack(side="left")
new_btn = tk.Button(sidebar_top, text="+ New", font=("Segoe UI", 8, "bold"),
                    bg=ACCENT, fg="white", activebackground=ACCENT_HOVER,
                    activeforeground="white", relief="flat", bd=0,
                    cursor="hand2", command=new_chat, padx=10, pady=4)
add_hover_effect(new_btn, ACCENT, ACCENT_HOVER)
new_btn.pack(side="right")

tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=12, pady=(0, 8))

sidebar_canvas = tk.Canvas(sidebar, bg=BG, highlightthickness=0)
sidebar_canvas.pack(side="left", fill="both", expand=True)
sidebar_inner = tk.Frame(sidebar_canvas, bg=BG)
sidebar_canvas.create_window((0, 0), window=sidebar_inner, anchor="nw")
sidebar_inner.bind("<Configure>",
    lambda e: sidebar_canvas.configure(scrollregion=sidebar_canvas.bbox("all")))

tk.Frame(main_layout, bg=BORDER, width=1).pack(side="left", fill="y")

chat_panel = tk.Frame(main_layout, bg=BG)
chat_panel.pack(side="left", fill="both", expand=True)

header = tk.Frame(chat_panel, bg=BG)
header.pack(fill="x", padx=24, pady=(16, 0))
tk.Label(header, text="Jarvis Prototype", font=("Segoe UI", 12, "bold"),
         bg=BG, fg=TEXT).pack(side="left")
status_frame = tk.Frame(header, bg=BG)
status_frame.pack(side="right")
status_dot = tk.Label(status_frame, text="●", font=("Segoe UI", 9),
                      bg=BG, fg="#4ec9b0")
status_dot.pack(side="left")
status_label = tk.Label(status_frame, text="Idle", font=("Segoe UI", 9),
                        bg=BG, fg=TEXT_DIM)
status_label.pack(side="left", padx=(4, 0))

tk.Frame(chat_panel, bg=BORDER, height=1).pack(fill="x", padx=24, pady=10)

chat_canvas = tk.Canvas(chat_panel, bg=BG, highlightthickness=0)
scrollbar = tk.Scrollbar(chat_panel, orient="vertical", command=chat_canvas.yview)
chat_canvas.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")
chat_canvas.pack(fill="both", expand=True)
chat_frame = tk.Frame(chat_canvas, bg=BG)
chat_window = chat_canvas.create_window((0, 0), window=chat_frame, anchor="nw")
chat_frame.bind("<Configure>",
    lambda e: chat_canvas.configure(scrollregion=chat_canvas.bbox("all")))
chat_canvas.bind("<Configure>",
    lambda e: chat_canvas.itemconfig(chat_window, width=e.width))

tk.Frame(chat_panel, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(10, 0))

input_area = tk.Frame(chat_panel, bg=BG)
input_area.pack(fill="x", padx=16, pady=12)
input_box = tk.Frame(input_area, bg=SURFACE,
                     highlightbackground=BORDER, highlightthickness=1)
input_box.pack(fill="x", side="left", expand=True, padx=(0, 8))
chat_input = tk.Text(input_box, height=2, font=FONT, bg=SURFACE, fg=TEXT,
                     insertbackground=TEXT, relief="flat", bd=0,
                     padx=12, pady=10, wrap="word")
chat_input.pack(fill="x")
chat_input.bind("<Return>", on_enter_key)
send_btn = tk.Button(input_area, text="➤ Send", font=("Segoe UI", 10, "bold"),
                     bg=ACCENT, fg="white", activebackground=ACCENT_HOVER,
                     activeforeground="white", relief="flat", bd=0,
                     cursor="hand2", command=send_message, padx=20, pady=12)
send_btn.pack(side="right")
add_hover_effect(send_btn, ACCENT, ACCENT_HOVER)

if chats:
    load_chat(list(chats.keys())[-1])
else:
    new_chat()

root.mainloop()