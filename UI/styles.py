class Theme:
    # Color Palette
    BACKGROUND = "#0b0f19"      # Deep Navy/Charcoal
    PRIMARY = "#00f3ff"         # Cyan Neon
    SECONDARY_GREEN = "#00ff9d" # Success Green
    SECONDARY_RED = "#ff4d4d"   # Alert Red
    DANGER_RED = SECONDARY_RED  # Alias
    TEXT_WHITE = "#ffffff"
    TEXT_GRAY = "#a0a0a0"
    
    # Glassmorphism
    PANEL_BG = "rgba(11, 15, 25, 200)" # Semi-transparent dark
    BORDER_COLOR = "rgba(0, 243, 255, 50)" # Faint cyan border
    
    @staticmethod
    def get_stylesheet():
        return f"""
        QMainWindow {{
            background-color: {Theme.BACKGROUND};
        }}
        
        QWidget {{
            color: {Theme.TEXT_WHITE};
            font-family: 'Segoe UI', 'Roboto', sans-serif;
            font-size: 14px;
        }}
        
        /* Sidebar Styling */
        QFrame#sidebar {{
            background-color: {Theme.PANEL_BG};
            border-right: 1px solid {Theme.BORDER_COLOR};
        }}
        
        QLabel#logo_text {{
            color: {Theme.PRIMARY};
            font-size: 24px;
            font-weight: bold;
            letter-spacing: 2px;
        }}
        
        QLabel#slogan_text {{
            color: {Theme.TEXT_GRAY};
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        /* Navigation Buttons */
        QPushButton.nav_btn {{
            background-color: transparent;
            border: none;
            color: {Theme.TEXT_GRAY};
            text-align: left;
            padding: 15px 20px;
            font-size: 14px;
            border-left: 3px solid transparent;
        }}
        
        QPushButton.nav_btn:hover {{
            color: {Theme.TEXT_WHITE};
            background-color: rgba(255, 255, 255, 10);
        }}
        
        QPushButton.nav_btn:checked {{
            color: {Theme.PRIMARY};
            border-left: 3px solid {Theme.PRIMARY};
            background-color: rgba(0, 243, 255, 10);
            /* Outer glow simulation using simple shadow if supported or just color */
        }}
        
        /* Status Bar */
        QFrame#status_bar {{
            border-top: 1px solid {Theme.BORDER_COLOR};
            background-color: transparent;
        }}
        
        QLabel#status_dot {{
            color: {Theme.SECONDARY_GREEN};
            font-size: 16px;
        }}
        
        /* Cards & Panels */
        QFrame.glass_panel {{
            background-color: rgba(255, 255, 255, 5);
            border: 1px solid {Theme.BORDER_COLOR};
            border-radius: 12px;
        }}

        /* Input Fields */
        QLineEdit {{
            background-color: rgba(0, 0, 0, 50);
            border: 1px solid {Theme.BORDER_COLOR};
            border-radius: 6px;
            color: {Theme.TEXT_WHITE};
            padding: 10px;
            font-size: 14px;
        }}
        QLineEdit:focus {{
            border: 1px solid {Theme.PRIMARY};
            background-color: rgba(0, 243, 255, 10);
        }}

        /* Primary CTA Button */
        QPushButton.cta_btn {{
            background-color: {Theme.PRIMARY};
            color: #000000;
            border-radius: 6px;
            padding: 12px 24px;
            font-weight: bold;
            font-size: 15px;
        }}
        QPushButton.cta_btn:hover {{
            background-color: #33f5ff;
        }}
        QPushButton.cta_btn:disabled {{
            background-color: rgba(0, 243, 255, 50);
            color: rgba(0, 0, 0, 100);
        }}

        /* Secondary Outline Button */
        QPushButton.outline_btn {{
            background-color: transparent;
            border: 1px solid {Theme.PRIMARY};
            color: {Theme.PRIMARY};
            border-radius: 6px;
            padding: 12px 24px;
            font-weight: bold;
            font-size: 15px;
        }}
        QPushButton.outline_btn:hover {{
            background-color: rgba(0, 243, 255, 10);
        }}

        /* Utility Classes for Labels */
        QLabel.header_text {{
            font-size: 24px; 
            font-weight: bold;
        }}
        
        QLabel.subheader_text {{
            font-size: 18px; 
            font-weight: bold;
        }}

        QLabel.instruction_text {{
            font-size: 18px; 
            color: {Theme.PRIMARY}; 
            font-weight: bold;
        }}
        """
