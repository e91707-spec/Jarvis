import tkinter as tk
from tkinter import ttk
import threading
import time

# Custom popup system with modern styling
BG = "#0a0a0a"
SURFACE = "#1a1a2e"
SURFACE2 = "#16213e"
BORDER = "#0f3460"
ACCENT = "#e94560"
ACCENT_HOVER = "#ff6b6b"
TEXT = "#f5f5f5"
TEXT_DIM = "#a8a8a8"
SUCCESS = "#00d9ff"
DANGER = "#ff4757"

class CustomPopup:
    def __init__(self, parent, title="Jarvis", width=400, height=200):
        self.parent = parent
        self.result = None
        self.closed = False
        
        # Create popup window
        self.popup = tk.Toplevel(parent)
        self.popup.title(title)
        self.popup.geometry(f"{width}x{height}")
        self.popup.configure(bg=BG)
        self.popup.resizable(False, False)
        
        # Center the popup
        self.popup.transient(parent)
        self.popup.grab_set()
        
        # Make popup modal
        self.popup.focus_set()
        
        # Add fade-in effect
        self.popup.attributes('-alpha', 0.0)
        self.fade_in()
        
        # Create content frame
        self.content_frame = tk.Frame(self.popup, bg=BG)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
    def fade_in(self, steps=5, delay=15):
        """Smooth fade-in animation"""
        def update_alpha(step):
            if step <= steps:
                alpha = step / steps
                self.popup.attributes('-alpha', alpha)
                self.popup.after(delay, lambda: update_alpha(step + 1))
            else:
                self.popup.attributes('-alpha', 1.0)
        
        self.popup.after(delay, lambda: update_alpha(1))
    
    def fade_out(self, steps=10, delay=30, callback=None):
        """Smooth fade-out animation"""
        def update_alpha(step):
            if step <= steps:
                alpha = 1.0 - (step / steps)
                self.popup.attributes('-alpha', alpha)
                self.popup.after(delay, lambda: update_alpha(step + 1))
            else:
                self.popup.destroy()
                if callback:
                    callback()
        
        self.popup.after(delay, lambda: update_alpha(1))
    
    def add_message(self, text, icon="ℹ️", color=TEXT):
        """Add a message to the popup"""
        # Message frame with icon
        msg_frame = tk.Frame(self.content_frame, bg=BG)
        msg_frame.pack(fill="x", pady=(0, 10))
        
        # Icon label
        icon_label = tk.Label(msg_frame, text=icon, font=("Segoe UI", 16),
                            bg=BG, fg=color)
        icon_label.pack(side="left", padx=(0, 10))
        
        # Text label
        text_label = tk.Label(msg_frame, text=text, font=("Segoe UI", 10),
                             bg=BG, fg=color, wraplength=300, justify="left")
        text_label.pack(side="left", fill="x", expand=True)
        
        return msg_frame
    
    def add_button(self, text, command=None, bg_color=ACCENT, 
                 text_color="white", hover_color=ACCENT_HOVER):
        """Add a button to the popup"""
        btn = tk.Button(self.content_frame, text=text, font=("Segoe UI", 9, "bold"),
                       bg=bg_color, fg=text_color, activebackground=hover_color,
                       activeforeground=text_color, relief="flat", bd=0, cursor="hand2",
                       padx=20, pady=8, command=command)
        btn.pack(fill="x", pady=5)
        
        # Add hover effect
        def on_enter(e):
            btn.config(bg=hover_color)
        
        def on_leave(e):
            btn.config(bg=bg_color)
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
    
    def add_progress_bar(self, steps=100):
        """Add an animated progress bar"""
        progress_frame = tk.Frame(self.content_frame, bg=BG)
        progress_frame.pack(fill="x", pady=10)
        
        # Progress bar container
        bar_container = tk.Frame(progress_frame, bg=SURFACE2, relief="flat", bd=1)
        bar_container.pack(fill="x", pady=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            bar_container, variable=self.progress_var, maximum=steps,
            style="Custom.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(fill="x", padx=5, pady=5)
        
        # Configure progress bar style
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Custom.Horizontal.TProgressbar",
                     background=ACCENT,
                     troughcolor=SURFACE2,
                     bordercolor=BORDER,
                     lightcolor=ACCENT_HOVER,
                     darkcolor=ACCENT)
        
        return progress_frame
    
    def update_progress(self, current, total):
        """Update progress bar"""
        if hasattr(self, 'progress_var'):
            progress = (current / total) * 100
            self.progress_var.set(progress)
            self.popup.update()
    
    def close_with_fade(self, delay=1000):
        """Close popup with fade-out effect"""
        self.fade_out(callback=lambda: setattr(self, 'closed', True))
    
    def show(self):
        """Show the popup"""
        self.popup.deiconify()
        self.popup.lift()
        self.popup.attributes('-topmost', True)
        self.popup.after(100, lambda: self.popup.attributes('-topmost', False))
    
    def hide(self):
        """Hide the popup"""
        self.fade_out()

class ConfirmDialog(CustomPopup):
    def __init__(self, parent, title, message, confirm_text="Confirm", 
                 cancel_text="Cancel", icon="⚠️"):
        super().__init__(parent, title, width=350, height=180)
        
        # Add icon and message
        self.add_message(message, icon=icon, color=DANGER)
        
        # Add buttons
        button_frame = tk.Frame(self.content_frame, bg=BG)
        button_frame.pack(fill="x", pady=(20, 0))
        
        # Button container for proper layout
        button_container = tk.Frame(button_frame, bg=BG)
        button_container.pack(fill="x")
        
        # Cancel button
        cancel_btn = self.add_button(cancel_text, 
                                   command=lambda: self.set_result(False),
                                   bg_color=SURFACE2, text_color=TEXT_DIM)
        cancel_btn.pack(side="left", padx=(0, 5))
        
        # Confirm button
        confirm_btn = self.add_button(confirm_text, 
                                   command=lambda: self.set_result(True))
        confirm_btn.pack(side="right", padx=(5, 0))
        
        self.result = None
    
    def set_result(self, result):
        """Set the result and close"""
        self.result = result
        self.close_with_fade()
    
    def get_result(self):
        """Get the result (blocks until result is available)"""
        while not self.closed:
            time.sleep(0.05)  # Reduced delay for faster response
            self.popup.update()
        return self.result

class InfoDialog(CustomPopup):
    def __init__(self, parent, title, message, button_text="OK", icon="ℹ️"):
        super().__init__(parent, title, width=400, height=160)
        
        # Add icon and message
        self.add_message(message, icon=icon, color=SUCCESS)
        
        # Add button
        self.add_button(button_text, 
                     command=lambda: self.set_result(True))
        
        self.result = None
    
    def set_result(self, result):
        """Set the result and close"""
        self.result = result
        self.close_with_fade()
    
    def get_result(self):
        """Get the result (blocks until result is available)"""
        while not self.closed:
            time.sleep(0.1)
            self.popup.update()
        return self.result

class ProgressDialog(CustomPopup):
    def __init__(self, parent, title="Processing...", message="Please wait", steps=100):
        super().__init__(parent, title, width=450, height=150)
        
        # Add message
        self.add_message(message, icon="⏳", color=TEXT)
        
        # Add progress bar
        self.add_progress_bar(steps)
        self.current_step = 0
        self.total_steps = steps
    
    def update_progress(self, step):
        """Update progress"""
        self.current_step = step
        self.update_progress(step, self.total_steps)
    
    def complete(self):
        """Mark as complete and close"""
        self.update_progress(self.total_steps)
        self.popup.after(500, lambda: self.close_with_fade())
    
    def cancel(self):
        """Cancel the progress dialog"""
        self.close_with_fade()

# Utility functions for easy popup creation
def show_confirm(parent, title, message, confirm_text="Confirm", cancel_text="Cancel"):
    """Show a confirmation dialog"""
    dialog = ConfirmDialog(parent, title, message, confirm_text, cancel_text)
    dialog.show()
    return dialog.get_result()

def show_info(parent, title, message, button_text="OK"):
    """Show an info dialog"""
    dialog = InfoDialog(parent, title, message, button_text)
    dialog.show()
    return dialog.get_result()

def show_progress(parent, title="Processing...", message="Please wait", steps=100):
    """Show a progress dialog"""
    dialog = ProgressDialog(parent, title, message, steps)
    dialog.show()
    return dialog
