import os
import cairosvg
import traceback
import datetime

# --- Base URL for Database Image Links (IMPORTANT: CHANGE THIS LATER) ---
# This should be the URL path where the generated images will be accessible
# For local testing, you might use a relative path or file:/// URL,
# but for a web application, it will be something like '/static/images/map_errors/'

# --- Directory Setup ---
output_folder = "F:/local_server/ai_mapcheck/error_examples"
os.makedirs(output_folder, exist_ok=True) # Create folder if it doesn't exist

# --- Function to convert SVG to PNG ---
def save_svg_as_png(svg_content, filename):
    """Converts SVG string to PNG and saves it."""
    print(f"  Generating {os.path.basename(filename)}...")
    try:
        # Ensure SVG content is bytes
        cairosvg.svg2png(bytestring=svg_content.encode('utf-8'), write_to=filename)
        return True
    except ImportError:
         print("\nERROR: CairoSVG library not found or not properly installed.")
         print("Please install it: pip install cairosvg")
         print("You might also need to install system dependencies (libcairo2 etc.). See cairosvg documentation.")
         return False # Indicate failure
    except FileNotFoundError: # Handle potential Cairo/system library issues
        print(f"\nERROR: Cannot find system library required by CairoSVG (e.g., libcairo-2.dll on Windows).")
        print("Please ensure Cairo runtime is installed and in your system's PATH.")
        return False
    except Exception as e:
        print(f"    ERROR generating {os.path.basename(filename)}: {e}")
        # traceback.print_exc() # Uncomment for full error details
        return False

# --- SVG Data for Examples 1-50 ---
# (Includes 1-10 from previous response + new ones for 11-50)
# NOTE: SVGs for 11-50 are simplified illustrations.
all_svg_examples = [
    # --- Examples 1-10 (Copied from previous response) ---
    {
        "id": 1,
        "before_svg": """<svg width="200" height="100" viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg"><title>Error 1: Vegetation over Road</title><path d="M 10 50 Q 50 30, 100 50 T 190 50" stroke="grey" stroke-width="3" fill="none"/><text x="10" y="70" font-size="10">Road Path</text><path d="M 60 10 C 80 60, 140 60, 160 90 L 60 90 Z" fill="green" fill-opacity="0.7"/><text x="80" y="80" font-size="10" fill="darkgreen">Vegetation</text></svg>""",
        "after_svg": """<svg width="200" height="100" viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 1: Road over Vegetation</title><path d="M 60 10 C 80 60, 140 60, 160 90 L 60 90 Z" fill="green" fill-opacity="0.7"/><text x="80" y="80" font-size="10" fill="darkgreen">Vegetation</text><path d="M 10 50 Q 50 30, 100 50 T 190 50" stroke="grey" stroke-width="3" fill="none"/><text x="10" y="70" font-size="10">Road Path</text></svg>"""
    },
    {
        "id": 2,
        "before_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Error 2: Dangling Node</title><line x1="10" y1="50" x2="140" y2="50" stroke="black" stroke-width="4"/><text x="15" y="45" font-size="10">Main Rd</text><line x1="75" y1="90" x2="75" y2="55" stroke="dimgray" stroke-width="3"/><text x="80" y="85" font-size="10">Branch</text><circle cx="75" cy="55" r="3" fill="red"/><text x="80" y="65" font-size="10" fill="red">Gap!</text></svg>""",
        "after_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 2: Connected Node</title><line x1="10" y1="50" x2="140" y2="50" stroke="black" stroke-width="4"/><text x="15" y="45" font-size="10">Main Rd</text><line x1="75" y1="90" x2="75" y2="50" stroke="dimgray" stroke-width="3"/><text x="80" y="85" font-size="10">Branch</text><circle cx="75" cy="50" r="3" fill="green"/></svg>"""
    },
    {
        "id": 3,
        "before_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Error 3: Building Position Offset</title><rect x="30" y="30" width="60" height="40" fill="none" stroke="lightgrey" stroke-dasharray="4 2"/><text x="35" y="25" font-size="10" fill="grey">Correct Footprint</text><rect x="45" y="40" width="60" height="40" fill="orange" stroke="black" fill-opacity="0.8"/><text x="50" y="60" font-size="10">Mapped Bldg (Offset)</text><line x1="60" y1="35" x2="75" y2="45" stroke="red" stroke-width="1"/><polygon points="72,42 75,45 72,48" fill="red"/></svg>""",
        "after_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 3: Building Position Aligned</title><rect x="30" y="30" width="60" height="40" fill="none" stroke="lightgrey" stroke-dasharray="4 2"/><text x="35" y="25" font-size="10" fill="grey">Correct Footprint</text><rect x="30" y="30" width="60" height="40" fill="orange" stroke="black" fill-opacity="0.8"/><text x="35" y="55" font-size="10">Mapped Bldg (Aligned)</text></svg>"""
    },
    {
        "id": 4,
        "before_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Error 4: Self-Intersecting Water Body</title><path d="M 30 20 L 120 20 L 75 80 L 120 80 L 30 80 L 75 20 Z" fill="lightblue" stroke="blue"/><text x="40" y="50" font-size="10">Lake (Self-Intersecting)</text><circle cx="75" cy="50" r="4" fill="none" stroke="red" stroke-width="2"/></svg>""",
        "after_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 4: Valid Water Body Geometry</title><path d="M 30 20 Q 75 10, 120 20 Q 130 50, 120 80 Q 75 90, 30 80 Q 20 50, 30 20 Z" fill="lightblue" stroke="blue"/><text x="40" y="50" font-size="10">Lake (Valid Shape)</text></svg>"""
    },
    {
        "id": 5,
        "before_svg": """<svg width="200" height="70" viewBox="0 0 200 70" xmlns="http://www.w3.org/2000/svg"><title>Error 5: Incorrect Road Name Attribute</title><line x1="10" y1="35" x2="190" y2="35" stroke="black" stroke-width="4"/><text x="20" y="55" font-size="12" fill="red">Label: 未命名道路</text><text x="20" y="15" font-size="10" fill="grey">(Correct: 校园中路)</text></svg>""",
        "after_svg": """<svg width="200" height="70" viewBox="0 0 200 70" xmlns="http://www.w3.org/2000/svg"><title>Corrected 5: Correct Road Name Attribute</title><line x1="10" y1="35" x2="190" y2="35" stroke="black" stroke-width="4"/><text x="20" y="55" font-size="12" fill="black">Label: 校园中路</text></svg>"""
    },
    {
        "id": 6,
        "before_svg": """<svg width="200" height="100" viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg"><title>Error 6: Boundary Gap</title><rect x="10" y="10" width="80" height="80" fill="lightblue" stroke="black"/><text x="20" y="55" font-size="12">Area A</text><rect x="95" y="10" width="80" height="80" fill="lightgreen" stroke="black"/><text x="105" y="55" font-size="12">Area B</text><rect x="90" y="10" width="5" height="80" fill="none" stroke="red" stroke-dasharray="2,2"/><text x="98" y="50" font-size="10" fill="red" transform="rotate(90 98 50)">Gap</text></svg>""",
        "after_svg": """<svg width="200" height="100" viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 6: Shared Boundary (No Gap)</title><rect x="10" y="10" width="80" height="80" fill="lightblue" stroke="black"/><text x="20" y="55" font-size="12">Area A</text><rect x="90" y="10" width="80" height="80" fill="lightgreen" stroke="black"/><text x="100" y="55" font-size="12">Area B</text><line x1="90" y1="10" x2="90" y2="90" stroke="blue" stroke-width="2"/></svg>"""
    },
    {
        "id": 7,
        "before_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Error 7: Missing POI (Admin Building)</title><rect x="40" y="30" width="70" height="50" fill="tan" stroke="black"/><text x="50" y="20" font-size="10" fill="red">(POI missing)</text><text x="55" y="60" font-size="10">Building</text></svg>""",
        "after_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 7: POI Added (Admin Building)</title><rect x="40" y="30" width="70" height="50" fill="tan" stroke="black"/><circle cx="75" cy="55" r="4" fill="purple"/><text x="85" y="60" font-size="10">行政楼</text></svg>"""
    },
    {
        "id": 8,
        "before_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Error 8: Road Intersects Building</title><rect x="40" y="20" width="70" height="60" fill="salmon" stroke="black"/><text x="50" y="55" font-size="10">Building</text><line x1="10" y1="50" x2="140" y2="50" stroke="grey" stroke-width="5" stroke-opacity="0.8"/><text x="15" y="70" font-size="10">Road</text></svg>""",
        "after_svg": """<svg width="150" height="120" viewBox="0 0 150 120" xmlns="http://www.w3.org/2000/svg"><title>Corrected 8: Road Goes Around Building</title><rect x="40" y="20" width="70" height="60" fill="salmon" stroke="black"/><text x="50" y="55" font-size="10">Building</text><path d="M 10 95 L 40 95 C 40 95, 40 105, 50 105 L 100 105 C 110 105, 110 95, 110 95 L 140 95" stroke="grey" stroke-width="5" fill="none"/><text x="15" y="115" font-size="10">Road</text></svg>"""
    },
    {
        "id": 9,
        "before_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Error 9: Duplicate Building Feature</title><rect x="30" y="30" width="90" height="40" fill="lightblue" stroke="black"/><rect x="30" y="30" width="90" height="40" fill="lightblue" stroke="red" stroke-width="1" fill-opacity="0.5"/><text x="40" y="55" font-size="10">Duplicate</text><text x="40" y="20" font-size="10" fill="red">(Red=Top)</text></svg>""",
        "after_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 9: Single Building Feature</title><rect x="30" y="30" width="90" height="40" fill="lightblue" stroke="black"/><text x="40" y="55" font-size="10">Single Building</text></svg>"""
    },
    {
        "id": 10,
        "before_svg": """<svg width="200" height="100" viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg"><title>Error 10: Label Overlap</title><rect x="30" y="40" width="40" height="30" fill="tan" stroke="black"/><rect x="80" y="50" width="40" height="30" fill="tan" stroke="black"/><text x="50" y="60" font-size="12">枫1舍</text><text x="70" y="70" font-size="12">枫2舍</text><rect x="50" y="48" width="38" height="15" fill="none" stroke="red" stroke-dasharray="2 2"/><rect x="70" y="58" width="38" height="15" fill="none" stroke="red" stroke-dasharray="2 2"/></svg>""",
        "after_svg": """<svg width="200" height="100" viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 10: Labels Repositioned</title><rect x="30" y="40" width="40" height="30" fill="tan" stroke="black"/><rect x="80" y="50" width="40" height="30" fill="tan" stroke="black"/><text x="35" y="35" font-size="12">枫1舍</text><text x="85" y="90" font-size="12">枫2舍</text></svg>"""
    },
    # --- Examples 11-50 (New Simplified SVGs) ---
    {
        "id": 11, # Bridge/Road Hierarchy
        "before_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Error 11: Road over Bridge</title><rect x="30" y="45" width="90" height="10" fill="lightgrey" stroke="black"/><text x="35" y="65" font-size="10">Bridge</text><line x1="75" y1="10" x2="75" y2="90" stroke="blue" stroke-width="6"/><text x="80" y="30" font-size="10">Road (Over)</text></svg>""",
        "after_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 11: Bridge over Road</title><line x1="75" y1="10" x2="75" y2="90" stroke="blue" stroke-width="6"/><text x="80" y="30" font-size="10">Road</text><rect x="30" y="45" width="90" height="10" fill="lightgrey" stroke="black"/><text x="35" y="65" font-size="10">Bridge (Over)</text></svg>"""
    },
    {
        "id": 12, # Contour Intersection
        "before_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Error 12: Contour Intersection</title><path d="M 10 30 Q 75 50 140 30" stroke="brown" fill="none"/><text x="15" y="25" font-size="10">50m</text><path d="M 10 70 Q 75 50 140 70" stroke="orange" fill="none"/><text x="15" y="85" font-size="10">55m</text><circle cx="75" cy="50" r="4" fill="none" stroke="red" stroke-width="2"/><text x="80" y="60" font-size="10" fill="red">X</text></svg>""",
        "after_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 12: Contours Not Intersecting</title><path d="M 10 30 Q 75 40 140 30" stroke="brown" fill="none"/><text x="15" y="25" font-size="10">50m</text><path d="M 10 70 Q 75 60 140 70" stroke="orange" fill="none"/><text x="15" y="85" font-size="10">55m</text></svg>"""
    },
    {
        "id": 13, # Contour Attribute Error
        "before_svg": """<svg width="150" height="60" viewBox="0 0 150 60" xmlns="http://www.w3.org/2000/svg"><title>Error 13: Incorrect Contour Value</title><path d="M 10 30 Q 75 40 140 30" stroke="brown" fill="none"/><text x="15" y="25" font-size="10" fill="red">Value: -50m</text></svg>""",
        "after_svg": """<svg width="150" height="60" viewBox="0 0 150 60" xmlns="http://www.w3.org/2000/svg"><title>Corrected 13: Correct Contour Value</title><path d="M 10 30 Q 75 40 140 30" stroke="brown" fill="none"/><text x="15" y="25" font-size="10" fill="black">Value: 50m</text></svg>"""
    },
    {
        "id": 14, # Label Mismatch
        "before_svg": """<svg width="200" height="100" viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg"><title>Error 14: Label Mismatch</title><rect x="30" y="40" width="40" height="30" fill="tan" stroke="black"/><text x="35" y="30" font-size="10">工7舍</text><rect x="100" y="40" width="40" height="30" fill="tan" stroke="black"/><text x="105" y="30" font-size="10">工8舍</text><text x="40" y="85" font-size="12" fill="red">Label: 工8舍</text><line x1="60" y1="75" x2="50" y2="70" stroke="red" stroke-width="1"/><polygon points="50,70 53,73 53,67" fill="red"/></svg>""",
        "after_svg": """<svg width="200" height="100" viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 14: Label Corrected</title><rect x="30" y="40" width="40" height="30" fill="tan" stroke="black"/><text x="35" y="30" font-size="10">工7舍</text><rect x="100" y="40" width="40" height="30" fill="tan" stroke="black"/><text x="105" y="30" font-size="10">工8舍</text><text x="110" y="85" font-size="12" fill="black">Label: 工8舍</text><line x1="130" y1="75" x2="120" y2="70" stroke="black" stroke-width="1"/><polygon points="120,70 123,73 123,67" fill="black"/></svg>"""
    },
     {
        "id": 15, # Naming Inconsistent
        "before_svg": """<svg width="200" height="100" viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg"><title>Error 15: Inconsistent Naming</title><rect x="20" y="40" width="60" height="30" fill="tan"/><text x="25" y="60" font-size="10" fill="red">1教学楼</text><rect x="100" y="40" width="60" height="30" fill="tan"/><text x="105" y="60" font-size="10" fill="red">第二教学楼</text></svg>""",
        "after_svg": """<svg width="200" height="100" viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 15: Consistent Naming</title><rect x="20" y="40" width="60" height="30" fill="tan"/><text x="25" y="60" font-size="10">第一教学楼</text><rect x="100" y="40" width="60" height="30" fill="tan"/><text x="105" y="60" font-size="10">第二教学楼</text></svg>"""
    },
    {
        "id": 16, # Symbology Error (Road)
        "before_svg": """<svg width="200" height="70" viewBox="0 0 200 70" xmlns="http://www.w3.org/2000/svg"><title>Error 16: Incorrect Road Symbol</title><line x1="10" y1="35" x2="190" y2="35" stroke="grey" stroke-width="3" stroke-dasharray="5 3"/><text x="20" y="55" font-size="10" fill="red">Main Road (Shown as path)</text></svg>""",
        "after_svg": """<svg width="200" height="70" viewBox="0 0 200 70" xmlns="http://www.w3.org/2000/svg"><title>Corrected 16: Correct Road Symbol</title><line x1="10" y1="35" x2="190" y2="35" stroke="black" stroke-width="5"/><text x="20" y="55" font-size="10">Main Road (Correct symbol)</text></svg>"""
    },
    {
        "id": 17, # Feature Overlap (Buildings)
        "before_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Error 17: Building Overlap</title><rect x="20" y="30" width="60" height="50" fill="lightblue" stroke="black"/><text x="30" y="60" font-size="10">Bldg A</text><rect x="70" y="40" width="60" height="50" fill="lightgreen" stroke="black" fill-opacity="0.7"/><text x="80" y="70" font-size="10">Bldg B</text><rect x="70" y="40" width="10" height="40" fill="red" fill-opacity="0.5"/><text x="72" y="35" font-size="10" fill="red">Overlap</text></svg>""",
        "after_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 17: Buildings Adjacent</title><rect x="20" y="30" width="60" height="50" fill="lightblue" stroke="black"/><text x="30" y="60" font-size="10">Bldg A</text><rect x="80" y="30" width="50" height="50" fill="lightgreen" stroke="black"/><text x="90" y="60" font-size="10">Bldg B</text></svg>"""
    },
    {
        "id": 18, # Feature Gap (Vegetation)
        "before_svg": """<svg width="200" height="100" viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg"><title>Error 18: Vegetation Gap</title><rect x="10" y="10" width="80" height="80" fill="lightgreen" stroke="darkgreen"/><text x="20" y="55" font-size="12">Grass A</text><rect x="95" y="10" width="80" height="80" fill="lightgreen" stroke="darkgreen"/><text x="105" y="55" font-size="12">Grass B</text><rect x="90" y="10" width="5" height="80" fill="none" stroke="red" stroke-dasharray="2,2"/><text x="98" y="50" font-size="10" fill="red" transform="rotate(90 98 50)">Gap</text></svg>""",
        "after_svg": """<svg width="200" height="100" viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 18: Vegetation Adjacent</title><rect x="10" y="10" width="80" height="80" fill="lightgreen" stroke="darkgreen"/><text x="20" y="55" font-size="12">Grass A</text><rect x="90" y="10" width="80" height="80" fill="lightgreen" stroke="darkgreen"/><text x="100" y="55" font-size="12">Grass B</text></svg>"""
    },
    {
        "id": 19, # POI Symbol Error
        "before_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Error 19: Incorrect POI Symbol</title><circle cx="75" cy="50" r="10" fill="none" stroke="red" stroke-width="2"/><text x="70" y="55" font-size="15">?</text><text x="40" y="75" font-size="10">校医院 (Wrong Symbol)</text></svg>""",
        "after_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 19: Correct POI Symbol</title><path d="M 70 45 H 80 M 75 40 V 50" stroke="red" stroke-width="3"/><circle cx="75" cy="50" r="10" fill="none" stroke="green" stroke-width="2"/><text x="40" y="75" font-size="10">校医院 (Correct Symbol)</text></svg>""" # Simple cross symbol
    },
    {
        "id": 20, # Overshoot Node
        "before_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Error 20: Overshoot Node</title><line x1="10" y1="50" x2="140" y2="50" stroke="black" stroke-width="4"/><text x="15" y="45" font-size="10">Main Rd</text><line x1="75" y1="90" x2="75" y2="45" stroke="dimgray" stroke-width="3"/><text x="80" y="85" font-size="10">Branch</text><line x1="75" y1="50" x2="75" y2="45" stroke="red" stroke-width="3"/><text x="80" y="45" font-size="10" fill="red">Overshoot!</text></svg>""",
        "after_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 20: Trimmed Node</title><line x1="10" y1="50" x2="140" y2="50" stroke="black" stroke-width="4"/><text x="15" y="45" font-size="10">Main Rd</text><line x1="75" y1="90" x2="75" y2="50" stroke="dimgray" stroke-width="3"/><text x="80" y="85" font-size="10">Branch</text><circle cx="75" cy="50" r="3" fill="green"/></svg>"""
    },
    # ... Continue designing simple SVGs for 21-50 ...
    # Example for simplicity:
    {
        "id": 21, # Building in Water
        "before_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Error 21: Building in Water</title><rect x="10" y="40" width="130" height="50" fill="lightblue"/><text x="20" y="70">Water</text><rect x="60" y="30" width="50" height="40" fill="tan" stroke="red"/><text x="65" y="55" fill="red">Bldg</text></svg>""",
        "after_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 21: Building on Land</title><rect x="10" y="40" width="130" height="50" fill="lightblue"/><text x="20" y="70">Water</text><rect x="60" y="10" width="50" height="30" fill="tan" stroke="black"/><text x="65" y="30">Bldg</text></svg>"""
    },
     {
        "id": 22, # Missing Attribute
        "before_svg": """<svg width="200" height="70" viewBox="0 0 200 70" xmlns="http://www.w3.org/2000/svg"><title>Error 22: Missing Road Name</title><line x1="10" y1="35" x2="190" y2="35" stroke="grey" stroke-width="3"/><text x="20" y="55" font-size="12" fill="red">Label: [NULL]</text></svg>""",
        "after_svg": """<svg width="200" height="70" viewBox="0 0 200 70" xmlns="http://www.w3.org/2000/svg"><title>Corrected 22: Road Name Added</title><line x1="10" y1="35" x2="190" y2="35" stroke="grey" stroke-width="3"/><text x="20" y="55" font-size="12" fill="black">Label: 湖滨小路</text></svg>"""
    },
    {
        "id": 23, # POI Offset
        "before_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Error 23: POI Offset</title><rect x="40" y="30" width="70" height="50" fill="lightgreen" stroke="darkgreen"/><text x="55" y="60">操场</text><circle cx="100" cy="20" r="4" fill="red"/><text x="105" y="25" fill="red">POI (Offset)</text></svg>""",
        "after_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 23: POI Centered</title><rect x="40" y="30" width="70" height="50" fill="lightgreen" stroke="darkgreen"/><text x="55" y="60">操场</text><circle cx="75" cy="55" r="4" fill="green"/><text x="80" y="50" fill="green">POI (Centered)</text></svg>"""
    },
    {
        "id": 24, # Unclosed Polygon
        "before_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Error 24: Unclosed Polygon</title><polyline points="40,80 40,30 110,30 110,80 50,80" fill="none" stroke="red" stroke-width="2"/><text x="45" y="60" fill="red">Not Closed!</text><circle cx="45" cy="80" r="3" stroke="red" fill="none"/></svg>""",
        "after_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 24: Closed Polygon</title><polygon points="40,80 40,30 110,30 110,80 40,80" fill="tan" stroke="black" stroke-width="2"/><text x="45" y="60">Closed</text></svg>"""
    },
     {
        "id": 25, # Incorrect One-Way
        "before_svg": """<svg width="200" height="70" viewBox="0 0 200 70" xmlns="http://www.w3.org/2000/svg"><title>Error 25: Incorrect One-Way</title><line x1="10" y1="35" x2="190" y2="35" stroke="black" stroke-width="4"/><text x="20" y="55" font-size="12" fill="red">Attr: 双向</text><text x="20" y="15" font-size="10" fill="grey">(Actual: -> One Way)</text></svg>""",
        "after_svg": """<svg width="200" height="70" viewBox="0 0 200 70" xmlns="http://www.w3.org/2000/svg"><title>Corrected 25: Correct One-Way</title><line x1="10" y1="35" x2="190" y2="35" stroke="black" stroke-width="4"/><text x="20" y="55" font-size="12" fill="black">Attr: 单向 (->)</text><polygon points="180,30 190,35 180,40" fill="black"/></svg>"""
    },
    {
        "id": 26, # Redundant Vertices
        "before_svg": """<svg width="200" height="50" viewBox="0 0 200 50" xmlns="http://www.w3.org/2000/svg"><title>Error 26: Redundant Vertices</title><polyline points="10,25 30,25 50,25 70,25 90,25 110,25 130,25 150,25 170,25 190,25" fill="none" stroke="black" stroke-width="2"/><circle cx="30" cy="25" r="2" fill="red"/><circle cx="50" cy="25" r="2" fill="red"/><circle cx="70" cy="25" r="2" fill="red"/><circle cx="90" cy="25" r="2" fill="red"/><circle cx="110" cy="25" r="2" fill="red"/><circle cx="130" cy="25" r="2" fill="red"/><circle cx="150" cy="25" r="2" fill="red"/><circle cx="170" cy="25" r="2" fill="red"/><text x="10" y="45" font-size="10" fill="red">Too many vertices</text></svg>""",
        "after_svg": """<svg width="200" height="50" viewBox="0 0 200 50" xmlns="http://www.w3.org/2000/svg"><title>Corrected 26: Simplified Vertices</title><line x1="10" y1="25" x2="190" y2="25" stroke="black" stroke-width="2"/><text x="10" y="45" font-size="10">Simplified line</text></svg>"""
    },
    {
        "id": 27, # Label Scale/Size
        "before_svg": """<svg width="150" height="70" viewBox="0 0 150 70" xmlns="http://www.w3.org/2000/svg"><title>Error 27: Label Too Small</title><rect x="30" y="20" width="90" height="40" fill="tan"/><text x="60" y="45" font-size="5" fill="red">图书馆</text><text x="35" y="15" font-size="10" fill="red">Label too small</text></svg>""",
        "after_svg": """<svg width="150" height="70" viewBox="0 0 150 70" xmlns="http://www.w3.org/2000/svg"><title>Corrected 27: Label Readable</title><rect x="30" y="20" width="90" height="40" fill="tan"/><text x="55" y="45" font-size="12">图书馆</text><text x="35" y="15" font-size="10">Readable label</text></svg>"""
    },
    {
        "id": 28, # Outdated Feature
        "before_svg": """<svg width="150" height="70" viewBox="0 0 150 70" xmlns="http://www.w3.org/2000/svg"><title>Error 28: Outdated Building</title><rect x="30" y="20" width="90" height="40" fill="lightgrey" stroke="red" stroke-dasharray="4 2"/><text x="40" y="45" font-size="10" fill="red">Old Admin (Demolished)</text></svg>""",
        "after_svg": """<svg width="150" height="70" viewBox="0 0 150 70" xmlns="http://www.w3.org/2000/svg"><title>Corrected 28: Feature Removed</title><text x="30" y="40" font-size="10">(Building Removed)</text></svg>"""
    },
    {
        "id": 29, # Feature Type Error
        "before_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Error 29: Area as Line</title><polygon points="40,80 40,30 110,30 110,80 40,80" fill="none" stroke="red" stroke-width="2"/><text x="45" y="60" fill="red">Playground (as line)</text></svg>""",
        "after_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 29: Area as Polygon</title><polygon points="40,80 40,30 110,30 110,80 40,80" fill="lightgreen" stroke="black" stroke-width="1"/><text x="45" y="60">Playground (as area)</text></svg>"""
    },
    {
        "id": 30, # POI Symbol Direction
        "before_svg": """<svg width="100" height="70" viewBox="0 0 100 70" xmlns="http://www.w3.org/2000/svg"><title>Error 30: Incorrect POI Direction</title><text x="10" y="15" font-size="10">Entrance</text><rect x="40" y="20" width="10" height="30" fill="grey"/><circle cx="30" cy="35" r="5" fill="blue"/><polygon points="30,30 35,35 30,40" fill="red"/> <text x="40" y="60" font-size="10" fill="red">Points Wrong Way</text></svg>""",
        "after_svg": """<svg width="100" height="70" viewBox="0 0 100 70" xmlns="http://www.w3.org/2000/svg"><title>Corrected 30: Correct POI Direction</title><text x="10" y="15" font-size="10">Entrance</text><rect x="40" y="20" width="10" height="30" fill="grey"/><circle cx="30" cy="35" r="5" fill="blue"/><polygon points="35,30 40,35 35,40" fill="green"/> <text x="40" y="60" font-size="10">Points Correct Way</text></svg>"""
    },
    {
        "id": 31, # Contour Interruption
        "before_svg": """<svg width="150" height="70" viewBox="0 0 150 70" xmlns="http://www.w3.org/2000/svg"><title>Error 31: Contour Interrupted</title><path d="M 10 30 Q 75 40 120 30" stroke="brown" fill="none" stroke-width="2"/><circle cx="120" cy="30" r="3" fill="none" stroke="red"/><text x="10" y="55" font-size="10" fill="red">Stops abruptly</text></svg>""",
        "after_svg": """<svg width="150" height="70" viewBox="0 0 150 70" xmlns="http://www.w3.org/2000/svg"><title>Corrected 31: Contour Continuous</title><path d="M 10 30 Q 75 40 140 30" stroke="brown" fill="none" stroke-width="2"/><text x="10" y="55" font-size="10">Continues to edge</text></svg>"""
    },
    {
        "id": 32, # Tile Edge Misalignment
        "before_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Error 32: Tile Misalignment</title><line x1="75" y1="0" x2="75" y2="100" stroke="grey" stroke-dasharray="5 3"/><text x="20" y="15">Tile 1</text><text x="80" y="15">Tile 2</text><rect x="20" y="30" width="55" height="40" fill="lightblue"/><rect x="75" y="35" width="55" height="40" fill="lightblue"/><line x1="75" y1="30" x2="75" y2="75" stroke="red" stroke-width="2"/><text x="80" y="60" font-size="10" fill="red">Misaligned</text></svg>""",
        "after_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 32: Tile Aligned</title><line x1="75" y1="0" x2="75" y2="100" stroke="grey" stroke-dasharray="5 3"/><text x="20" y="15">Tile 1</text><text x="80" y="15">Tile 2</text><rect x="20" y="30" width="55" height="40" fill="lightblue"/><rect x="75" y="30" width="55" height="40" fill="lightblue"/><line x1="75" y1="30" x2="75" y2="70" stroke="green" stroke-width="1"/></svg>"""
    },
    {
        "id": 33, # Z-Value/Level Error
        "before_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Error 33: Level Ambiguous</title><line x1="20" y1="50" x2="130" y2="50" stroke="black" stroke-width="5"/><line x1="75" y1="20" x2="75" y2="80" stroke="grey" stroke-width="5"/><text x="25" y="70" font-size="10" fill="red">Which is on top?</text></svg>""",
        "after_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 33: Level Clear</title><line x1="75" y1="20" x2="75" y2="80" stroke="grey" stroke-width="5"/><line x1="20" y1="50" x2="70" y2="50" stroke="black" stroke-width="5"/><line x1="80" y1="50" x2="130" y2="50" stroke="black" stroke-width="5"/><text x="25" y="70" font-size="10">Black road on top</text></svg>""" # Simple break, could also use dashed lines
    },
    {
        "id": 34, # Unreasonable Adjacency
        "before_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Error 34: Veg Touching Building</title><rect x="50" y="20" width="50" height="60" fill="tan" stroke="black"/><text x="60" y="55">Bldg</text><rect x="100" y="20" width="40" height="60" fill="lightgreen" stroke="darkgreen"/><text x="105" y="55" fill="red">Grass</text><line x1="100" y1="20" x2="100" y2="80" stroke="red" stroke-width="2"/></svg>""",
        "after_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 34: Gap Added</title><rect x="50" y="20" width="50" height="60" fill="tan" stroke="black"/><text x="60" y="55">Bldg</text><rect x="105" y="20" width="35" height="60" fill="lightgreen" stroke="darkgreen"/><text x="110" y="55">Grass</text><rect x="100" y="20" width="5" height="60" fill="lightgrey"/><text x="108" y="15" font-size="8">Path</text></svg>"""
    },
    {
        "id": 35, # Label Spelling Error
        "before_svg": """<svg width="150" height="50" viewBox="0 0 150 50" xmlns="http://www.w3.org/2000/svg"><title>Error 35: Spelling Error</title><text x="10" y="30" font-size="14" fill="red">信息管理学阮</text></svg>""",
        "after_svg": """<svg width="150" height="50" viewBox="0 0 150 50" xmlns="http://www.w3.org/2000/svg"><title>Corrected 35: Spelling Corrected</title><text x="10" y="30" font-size="14">信息管理学院</text></svg>"""
    },
     {
        "id": 36, # Improper Generalization
        "before_svg": """<svg width="200" height="100" viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg"><title>Error 36: Over-simplified</title><path d="M 30 70 L 30 30 L 70 30 L 70 20 L 130 20 L 130 30 L 170 30 L 170 70 Z" fill="none" stroke="grey" stroke-dasharray="3 2"/><text x="35" y="15" font-size="10">Actual Shape</text><rect x="30" y="20" width="140" height="50" fill="salmon" stroke="red"/><text x="40" y="50" fill="red">Mapped Shape (Too Simple)</text></svg>""",
        "after_svg": """<svg width="200" height="100" viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 36: Detailed Shape</title><path d="M 30 70 L 30 30 L 70 30 L 70 20 L 130 20 L 130 30 L 170 30 L 170 70 Z" fill="salmon" stroke="black"/><text x="40" y="50">Mapped Shape (Detailed)</text></svg>"""
    },
    {
        "id": 37, # Pseudo Node
        "before_svg": """<svg width="200" height="50" viewBox="0 0 200 50" xmlns="http://www.w3.org/2000/svg"><title>Error 37: Pseudo Node</title><line x1="10" y1="25" x2="100" y2="25" stroke="black" stroke-width="2"/><line x1="100" y1="25" x2="190" y2="25" stroke="black" stroke-width="2"/><circle cx="100" cy="25" r="4" fill="red"/><text x="10" y="45" font-size="10" fill="red">Unnecessary node</text></svg>""",
        "after_svg": """<svg width="200" height="50" viewBox="0 0 200 50" xmlns="http://www.w3.org/2000/svg"><title>Corrected 37: Continuous Line</title><line x1="10" y1="25" x2="190" y2="25" stroke="black" stroke-width="2"/><text x="10" y="45" font-size="10">Continuous line</text></svg>"""
    },
    {
        "id": 38, # Missing Relationship
        "before_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Error 38: Missing Relation</title><rect x="40" y="30" width="70" height="50" fill="tan"/><text x="50" y="60">教学楼</text><circle cx="100" cy="20" r="4" fill="purple"/><text x="105" y="25">POI</text><text x="10" y="85" font-size="10" fill="red">No link shown</text></svg>""",
        "after_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 38: Relation Shown</title><rect x="40" y="30" width="70" height="50" fill="tan"/><text x="50" y="60">教学楼</text><circle cx="100" cy="20" r="4" fill="purple"/><text x="105" y="25">POI</text><line x1="75" y1="30" x2="100" y2="20" stroke="grey" stroke-dasharray="3 2"/><text x="10" y="85" font-size="10">Link shown</text></svg>"""
    },
    {
        "id": 39, # Missing Feature (Fence)
        "before_svg": """<svg width="150" height="70" viewBox="0 0 150 70" xmlns="http://www.w3.org/2000/svg"><title>Error 39: Missing Fence</title><rect x="10" y="10" width="130" height="50" fill="lightyellow" stroke="none"/><text x="20" y="40">Campus Area</text><text x="20" y="65" font-size="10" fill="red">(Fence line missing)</text></svg>""",
        "after_svg": """<svg width="150" height="70" viewBox="0 0 150 70" xmlns="http://www.w3.org/2000/svg"><title>Corrected 39: Fence Added</title><rect x="10" y="10" width="130" height="50" fill="lightyellow" stroke="black" stroke-dasharray="4 2" stroke-width="1.5"/><text x="20" y="40">Campus Area</text><text x="20" y="65" font-size="10">(Fence line added)</text></svg>"""
    },
    {
        "id": 40, # Improper Stair Symbol
        "before_svg": """<svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><title>Error 40: Path not Stairs</title><rect x="10" y="10" width="80" height="20" fill="lightgrey"/><text x="15" y="25" font-size="10">Level 1</text><rect x="10" y="70" width="80" height="20" fill="lightgrey"/><text x="15" y="85" font-size="10">Level 2</text><line x1="50" y1="30" x2="50" y2="70" stroke="red" stroke-width="2"/><text x="55" y="55" font-size="10" fill="red">Path?</text></svg>""",
        "after_svg": """<svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 40: Stair Symbol</title><rect x="10" y="10" width="80" height="20" fill="lightgrey"/><text x="15" y="25" font-size="10">Level 1</text><rect x="10" y="70" width="80" height="20" fill="lightgrey"/><text x="15" y="85" font-size="10">Level 2</text><line x1="50" y1="30" x2="50" y2="70" stroke="black" stroke-width="2"/><line x1="45" y1="35" x2="55" y2="35" stroke="black"/><line x1="45" y1="40" x2="55" y2="40" stroke="black"/><line x1="45" y1="45" x2="55" y2="45" stroke="black"/><line x1="45" y1="50" x2="55" y2="50" stroke="black"/><line x1="45" y1="55" x2="55" y2="55" stroke="black"/><line x1="45" y1="60" x2="55" y2="60" stroke="black"/><line x1="45" y1="65" x2="55" y2="65" stroke="black"/><text x="55" y="55" font-size="10">Stairs</text></svg>"""
    },
    {
        "id": 41, # Veg Type Error
        "before_svg": """<svg width="150" height="70" viewBox="0 0 150 70" xmlns="http://www.w3.org/2000/svg"><title>Error 41: Veg Type Mismatch</title><rect x="10" y="10" width="130" height="50" fill="darkgreen"/><text x="20" y="40" fill="red">Type: 草地 (Error: Forest)</text></svg>""",
        "after_svg": """<svg width="150" height="70" viewBox="0 0 150 70" xmlns="http://www.w3.org/2000/svg"><title>Corrected 41: Correct Veg Type</title><rect x="10" y="10" width="130" height="50" fill="darkgreen"/><text x="20" y="40" fill="white">Type: 林地 (Forest)</text></svg>"""
    },
    {
        "id": 42, # Incorrect Road Angle
        "before_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Error 42: Incorrect Angle</title><polyline points="20,80 75,80 75,20" stroke="red" stroke-width="4" fill="none"/><text x="25" y="60" fill="red">Too sharp?</text></svg>""",
        "after_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 42: Smoother Angle</title><path d="M 20 80 Q 75 80, 75 50 T 75 20" stroke="black" stroke-width="4" fill="none"/><text x="25" y="60">Corrected angle</text></svg>"""
    },
    {
        "id": 43, # Duplicate Label
        "before_svg": """<svg width="150" height="70" viewBox="0 0 150 70" xmlns="http://www.w3.org/2000/svg"><title>Error 43: Duplicate Label</title><rect x="30" y="20" width="90" height="40" fill="tan"/><text x="55" y="35" font-size="12" fill="red">体育馆</text><text x="55" y="55" font-size="12" fill="red">体育馆</text></svg>""",
        "after_svg": """<svg width="150" height="70" viewBox="0 0 150 70" xmlns="http://www.w3.org/2000/svg"><title>Corrected 43: Single Label</title><rect x="30" y="20" width="90" height="40" fill="tan"/><text x="55" y="45" font-size="12">体育馆</text></svg>"""
    },
    {
        "id": 44, # Incorrect Flow Direction
        "before_svg": """<svg width="150" height="70" viewBox="0 0 150 70" xmlns="http://www.w3.org/2000/svg"><title>Error 44: Incorrect Flow</title><line x1="10" y1="50" x2="140" y2="20" stroke="blue" stroke-width="2"/><polygon points="15,50 10,45 5,50" fill="red"/><text x="20" y="15" font-size="10" fill="grey">Higher Ground</text><text x="20" y="65" font-size="10" fill="red">Flows Up?</text></svg>""",
        "after_svg": """<svg width="150" height="70" viewBox="0 0 150 70" xmlns="http://www.w3.org/2000/svg"><title>Corrected 44: Correct Flow</title><line x1="10" y1="20" x2="140" y2="50" stroke="blue" stroke-width="2"/><polygon points="135,50 140,55 145,50" fill="green"/><text x="20" y="15" font-size="10" fill="grey">Higher Ground</text><text x="20" y="65" font-size="10">Flows Down</text></svg>"""
    },
    {
        "id": 45, # Island/Hole Error
        "before_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Error 45: Courtyard Separate</title><rect x="20" y="20" width="110" height="60" fill="tan" stroke="black"/><rect x="50" y="40" width="50" height="20" fill="lightgreen" stroke="red"/><text x="55" y="15" font-size="10" fill="red">Courtyard as separate feature</text></svg>""",
        "after_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 45: Courtyard as Hole</title><path d="M 20 20 H 130 V 80 H 20 Z M 50 40 V 60 H 100 V 40 Z" fill-rule="evenodd" fill="tan" stroke="black"/><text x="55" y="15" font-size="10">Courtyard as hole</text></svg>"""
    },
    {
        "id": 46, # Outdated POI Info
        "before_svg": """<svg width="150" height="70" viewBox="0 0 150 70" xmlns="http://www.w3.org/2000/svg"><title>Error 46: Outdated POI</title><circle cx="75" cy="35" r="4" fill="orange"/><text x="40" y="55" font-size="10" fill="red">XX打印店 (已关闭)</text></svg>""",
        "after_svg": """<svg width="150" height="70" viewBox="0 0 150 70" xmlns="http://www.w3.org/2000/svg"><title>Corrected 46: POI Removed/Updated</title><text x="40" y="40" font-size="10">(POI Removed)</text></svg>"""
    },
    {
        "id": 47, # Incomplete Road Attribute
        "before_svg": """<svg width="200" height="70" viewBox="0 0 200 70" xmlns="http://www.w3.org/2000/svg"><title>Error 47: Missing Road Grade</title><line x1="10" y1="35" x2="190" y2="35" stroke="grey" stroke-width="4"/><text x="20" y="55" font-size="12" fill="red">Grade: [NULL]</text></svg>""",
        "after_svg": """<svg width="200" height="70" viewBox="0 0 200 70" xmlns="http://www.w3.org/2000/svg"><title>Corrected 47: Road Grade Added</title><line x1="10" y1="35" x2="190" y2="35" stroke="black" stroke-width="4"/><text x="20" y="55" font-size="12">Grade: Primary</text></svg>"""
    },
    {
        "id": 48, # Improper Area Color
        "before_svg": """<svg width="200" height="100" viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg"><title>Error 48: Similar Colors</title><rect x="10" y="10" width="85" height="80" fill="#D0E0D0" stroke="black"/><text x="20" y="55">Zone A</text><rect x="95" y="10" width="85" height="80" fill="#D5E5D5" stroke="black"/><text x="105" y="55">Zone B</text><text x="15" y="95" font-size="10" fill="red">Colors too similar</text></svg>""",
        "after_svg": """<svg width="200" height="100" viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 48: Distinct Colors</title><rect x="10" y="10" width="85" height="80" fill="lightblue" stroke="black"/><text x="20" y="55">Zone A</text><rect x="95" y="10" width="85" height="80" fill="lightyellow" stroke="black"/><text x="105" y="55">Zone B</text><text x="15" y="95" font-size="10">Colors distinct</text></svg>"""
    },
    {
        "id": 49, # Spike/Kickback
        "before_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Error 49: Spike in Polygon</title><polygon points="30,80 30,30 80,30 100,10 120,30 120,80 30,80" fill="tan" stroke="red" stroke-width="2"/><circle cx="100" cy="10" r="4" fill="none" stroke="red"/><text x="80" y="50" fill="red">Spike!</text></svg>""",
        "after_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 49: Smooth Corner</title><polygon points="30,80 30,30 80,30 120,30 120,80 30,80" fill="tan" stroke="black" stroke-width="1"/><text x="50" y="50">Smoothed</text></svg>"""
    },
    {
        "id": 50, # Missing Legend Item
        "before_svg": """<svg width="200" height="100" viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg"><title>Error 50: Missing Legend Item</title><rect x="10" y="10" width="100" height="60" fill="lightgrey"/><text x="20" y="30">Map Area</text><path d="M 50 40 L 60 50 L 70 40 Z" fill="orange" stroke="black"/><text x="120" y="20">Legend</text><rect x="125" y="30" width="10" height="10" fill="lightblue"/><text x="140" y="40" font-size="10">Water</text><text x="120" y="70" fill="red" font-size="10">Symbol missing</text></svg>""",
        "after_svg": """<svg width="200" height="100" viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 50: Complete Legend</title><rect x="10" y="10" width="100" height="80" fill="lightgrey"/><text x="20" y="30">Map Area</text><path d="M 50 40 L 60 50 L 70 40 Z" fill="orange" stroke="black"/><text x="120" y="20">Legend</text><rect x="125" y="30" width="10" height="10" fill="lightblue"/><text x="140" y="40" font-size="10">Water</text><path d="M 125 55 L 130 60 L 135 55 Z" fill="orange" stroke="black"/><text x="140" y="62" font-size="10">Construction</text></svg>"""
    },
    {
        "id": 51, # 道路转角处断开
        "before_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Error 51: Road disconnected at corner</title><polyline points="20,80 70,80 70,30" fill="none" stroke="black" stroke-width="4"/><circle cx="70" cy="80" r="4" fill="none" stroke="red"/><text x="20" y="20" font-size="10" fill="red">Gap at corner</text></svg>""",
        "after_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 51: Road connected at corner</title><polyline points="20,80 75,80 75,30" fill="none" stroke="black" stroke-width="4"/><circle cx="75" cy="80" r="2" fill="green"/><text x="20" y="20" font-size="10">Connected</text></svg>"""
    },
    {
        "id": 52, # 注记重叠 (类似 #10, 但用 POI)
        "before_svg": """<svg width="200" height="100" viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg"><title>Error 52: Annotation Overlap (POI)</title><circle cx="80" cy="50" r="5" fill="blue"/><text x="85" y="55" font-family="sans-serif" font-size="14" fill="black">兴趣点A</text><circle cx="100" cy="60" r="5" fill="red"/><text x="75" y="68" font-family="sans-serif" font-size="14" fill="black">兴趣点B</text><rect x="75" y="48" width="60" height="28" fill="none" stroke="red" stroke-dasharray="2 2"/></svg>""",
        "after_svg": """<svg width="200" height="100" viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 52: Annotations Repositioned</title><circle cx="80" cy="50" r="5" fill="blue"/><text x="85" y="45" font-family="sans-serif" font-size="14" fill="black">兴趣点A</text><circle cx="100" cy="60" r="5" fill="red"/><text x="105" y="75" font-family="sans-serif" font-size="14" fill="black">兴趣点B</text></svg>"""
    },
    {
        "id": 53, # 注记缺失
        "before_svg": """<svg width="150" height="70" viewBox="0 0 150 70" xmlns="http://www.w3.org/2000/svg"><title>Error 53: Annotation Missing</title><rect x="30" y="20" width="90" height="40" fill="tan"/><text x="35" y="15" font-size="10" fill="red">Label Missing!</text></svg>""",
        "after_svg": """<svg width="150" height="70" viewBox="0 0 150 70" xmlns="http://www.w3.org/2000/svg"><title>Corrected 53: Annotation Added</title><rect x="30" y="20" width="90" height="40" fill="tan"/><text x="55" y="45" font-size="12">教学楼X</text></svg>"""
    },
    { # 建筑名称缺失 (与注记缺失类似)
        "id": 54,
        "before_svg": """<svg width="150" height="70" viewBox="0 0 150 70" xmlns="http://www.w3.org/2000/svg"><title>Error 54: Building Name Missing</title><rect x="30" y="20" width="90" height="40" fill="tan"/><text x="35" y="15" font-size="10" fill="red">Name Missing!</text></svg>""",
        "after_svg": """<svg width="150" height="70" viewBox="0 0 150 70" xmlns="http://www.w3.org/2000/svg"><title>Corrected 54: Building Name Added</title><rect x="30" y="20" width="90" height="40" fill="tan"/><text x="55" y="45" font-size="12">行政楼</text></svg>"""
    },
    {
        "id": 55, # 建筑压盖道路
        "before_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Error 55: Building Over Road</title><line x1="10" y1="50" x2="140" y2="50" stroke="grey" stroke-width="5"/><text x="15" y="70" font-size="10">Road</text><rect x="40" y="30" width="70" height="40" fill="salmon" stroke="black" fill-opacity="0.8"/><text x="50" y="55" font-size="10">Building (Over)</text></svg>""",
        "after_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 55: Road Over Building</title><rect x="40" y="30" width="70" height="40" fill="salmon" stroke="black"/><text x="50" y="55" font-size="10">Building</text><line x1="10" y1="50" x2="140" y2="50" stroke="grey" stroke-width="5"/><text x="15" y="70" font-size="10">Road (Over)</text></svg>"""
    },
    {
        "id": 56, # 道路交叉口断开
        "before_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Error 56: Intersection Disconnected</title><line x1="20" y1="50" x2="130" y2="50" stroke="black" stroke-width="4"/><line x1="75" y1="20" x2="75" y2="85" stroke="dimgray" stroke-width="4"/><circle cx="75" cy="50" r="4" fill="none" stroke="red"/><text x="80" y="40" font-size="10" fill="red">Gap/No Node</text></svg>""",
        "after_svg": """<svg width="150" height="100" viewBox="0 0 150 100" xmlns="http://www.w3.org/2000/svg"><title>Corrected 56: Intersection Connected</title><line x1="20" y1="50" x2="130" y2="50" stroke="black" stroke-width="4"/><line x1="75" y1="20" x2="75" y2="80" stroke="dimgray" stroke-width="4"/><circle cx="75" cy="50" r="3" fill="green"/><text x="80" y="40" font-size="10">Connected</text></svg>"""
    },
    {
        "id": 57, # 道路断裂
        "before_svg": """<svg width="200" height="50" viewBox="0 0 200 50" xmlns="http://www.w3.org/2000/svg"><title>Error 57: Road Broken</title><line x1="10" y1="25" x2="90" y2="25" stroke="black" stroke-width="4"/><line x1="110" y1="25" x2="190" y2="25" stroke="black" stroke-width="4"/><rect x="90" y="20" width="20" height="10" fill="none" stroke="red" stroke-dasharray="2 2"/><text x="95" y="15" font-size="10" fill="red">Gap!</text></svg>""",
        "after_svg": """<svg width="200" height="50" viewBox="0 0 200 50" xmlns="http://www.w3.org/2000/svg"><title>Corrected 57: Road Continuous</title><line x1="10" y1="25" x2="190" y2="25" stroke="black" stroke-width="4"/><text x="10" y="15" font-size="10">Continuous</text></svg>"""
    }
    
]

# --- Text Data for All 50 Examples (for SQL Generation) ---
all_examples_data = [
    {'id': 1, 'layer_name': '道路, 植被', 'error_category': '逻辑一致性 / 表达与符号化', 'error_type': '要素压盖/层级关系错误', 'description': '植被图层压盖了上山的小路。', 'solution': '调整图层渲染顺序或裁剪植被。', 'severity': '一般'},
    {'id': 2, 'layer_name': '道路', 'error_category': '逻辑一致性 / 拓扑关系', 'error_type': '网络连通性错误 (悬挂)', 'description': '支路与主干道未精确连接，存在悬空。', 'solution': '编辑节点，使支路末端精确捕捉。', 'severity': '严重'},
    {'id': 3, 'layer_name': '建筑物', 'error_category': '位置精度', 'error_type': '要素位置偏移', 'description': '建筑物轮廓与实际位置存在偏移。', 'solution': '对照底图或实测数据，移动要素。', 'severity': '一般'},
    {'id': 4, 'layer_name': '水体', 'error_category': '几何精度', 'error_type': '无效几何 (自相交)', 'description': '水体边界多边形存在自相交。', 'solution': '使用几何修复工具编辑顶点，消除自相交。', 'severity': '一般'},
    {'id': 5, 'layer_name': '道路', 'error_category': '属性精度', 'error_type': '属性值错误', 'description': '道路“名称”属性错误或缺失。', 'solution': '查询确认并更新属性表中的“名称”字段。', 'severity': '一般'},
    {'id': 6, 'layer_name': '建筑物 (分区)', 'error_category': '逻辑一致性 / 拓扑关系', 'error_type': '边界缝隙', 'description': '相邻管理范围面要素间存在缝隙。', 'solution': '编辑边界，使相邻面要素共享边界。', 'severity': '严重'},
    {'id': 7, 'layer_name': 'POI', 'error_category': '完整性', 'error_type': '要素缺失', 'description': '缺少重要地物（如行政楼）的POI点。', 'solution': '添加缺失的POI点要素及属性。', 'severity': '一般'},
    {'id': 8, 'layer_name': '建筑物, 道路', 'error_category': '逻辑一致性', 'error_type': '要素关系错误', 'description': '道路与建筑物发生不合理重叠。', 'solution': '精确化编辑轮廓或线形，消除重叠。', 'severity': '一般'},
    {'id': 9, 'layer_name': '建筑物', 'error_category': '几何精度', 'error_type': '重复要素', 'description': '同一位置存在两个重合的建筑物要素。', 'solution': '识别并删除重复要素。', 'severity': '轻微'},
    {'id': 10, 'layer_name': '标注', 'error_category': '表达与符号化', 'error_type': '标注压盖/冲突', 'description': '多个文本标注相互压盖，难以辨认。', 'solution': '调整标注引擎规则或手动调整位置。', 'severity': '一般'},
    {'id': 11, 'layer_name': '道路, 桥梁/通道', 'error_category': '逻辑一致性 / 表达与符号化', 'error_type': '要素表达层级错误', 'description': '人行天桥被下方道路压盖。', 'solution': '确保天桥图层在下方道路之上渲染。', 'severity': '一般'},
    {'id': 12, 'layer_name': '等高线', 'error_category': '几何精度 / 拓扑关系', 'error_type': '线条交叉', 'description': '不同高程值的等高线发生交叉。', 'solution': '检查数据源或编辑线条，确保不交叉。', 'severity': '严重'},
    {'id': 13, 'layer_name': '等高线', 'error_category': '属性精度', 'error_type': '属性值错误', 'description': '等高线“高程值”属性错误(如负数)。', 'solution': '对照DEM修正错误的高程值属性。', 'severity': '一般'},
    {'id': 14, 'layer_name': '建筑物, 标注', 'error_category': '属性精度 / 逻辑一致性', 'error_type': '标注与要素不匹配', 'description': '标注文本指向了错误的建筑物。', 'solution': '移动标注到正确要素或修改文本。', 'severity': '一般'},
    {'id': 15, 'layer_name': '建筑物', 'error_category': '属性精度', 'error_type': '属性命名不一致', 'description': '同类建筑命名规范不统一。', 'solution': '统一命名规范并修改属性或标注。', 'severity': '轻微'},
    {'id': 16, 'layer_name': '道路', 'error_category': '表达与符号化', 'error_type': '符号化错误', 'description': '主要车行道使用了人行小道的线型符号。', 'solution': '根据道路等级应用正确的线型符号。', 'severity': '一般'},
    {'id': 17, 'layer_name': '建筑物', 'error_category': '几何精度 / 拓扑关系', 'error_type': '要素重叠', 'description': '相邻的两栋宿舍楼边界存在重叠。', 'solution': '编辑边界，使相邻要素边界不重叠。', 'severity': '轻微'},
    {'id': 18, 'layer_name': '植被', 'error_category': '完整性 / 拓扑关系', 'error_type': '要素缝隙', 'description': '相邻草坪面要素间存在未覆盖缝隙。', 'solution': '编辑多边形边界，使其精确邻接。', 'severity': '轻微'},
    {'id': 19, 'layer_name': 'POI', 'error_category': '表达与符号化', 'error_type': '符号使用错误', 'description': '校医院POI点使用了餐饮服务的符号。', 'solution': '选择并应用正确的医疗设施符号。', 'severity': '一般'},
    {'id': 20, 'layer_name': '道路', 'error_category': '逻辑一致性 / 拓扑关系', 'error_type': '网络连通性错误 (过头)', 'description': '小路连接主路时延伸超过主路(Overshoot)。', 'solution': '编辑线段，将过头端点捕捉到主路。', 'severity': '一般'},
    {'id': 21, 'layer_name': '建筑物, 水体', 'error_category': '逻辑一致性', 'error_type': '要素关系错误', 'description': '建筑物边界错误地延伸到湖水区域内。', 'solution': '编辑建筑物边界，使其不侵入水体。', 'severity': '一般'},
    {'id': 22, 'layer_name': '道路', 'error_category': '属性精度 / 完整性', 'error_type': '属性值缺失', 'description': '多条校园支路缺少“名称”属性值。', 'solution': '补充缺失的道路名称属性。', 'severity': '轻微'},
    {'id': 23, 'layer_name': 'POI', 'error_category': '位置精度', 'error_type': '要素位置偏移', 'description': 'POI标记点偏离了操场的实际中心或入口。', 'solution': '移动POI点到更合适的位置。', 'severity': '轻微'},
    {'id': 24, 'layer_name': '建筑物', 'error_category': '几何精度', 'error_type': '无效几何 (未闭合)', 'description': '建筑物多边形轮廓线未完全闭合。', 'solution': '编辑顶点，使多边形路径闭合。', 'severity': '一般'},
    {'id': 25, 'layer_name': '道路', 'error_category': '逻辑一致性', 'error_type': '属性逻辑错误', 'description': '单行道属性中“通行方向”错误。', 'solution': '核对实际交通规则，修正属性。', 'severity': '严重'},
    {'id': 26, 'layer_name': '道路', 'error_category': '几何精度', 'error_type': '冗余顶点', 'description': '笔直道路包含了大量不必要的共线顶点。', 'solution': '使用简化工具或手动删除冗余顶点。', 'severity': '轻微'},
    {'id': 27, 'layer_name': '标注', 'error_category': '表达与符号化', 'error_type': '标注比例/大小不当', 'description': '主要道路名称标注字体过小。', 'solution': '调整标注显示比例或字体大小。', 'severity': '轻微'},
    {'id': 28, 'layer_name': '建筑物', 'error_category': '时效性 / 完整性', 'error_type': '要素过时/冗余', 'description': '地图显示了已被拆除的建筑。', 'solution': '删除已不存在的地物要素。', 'severity': '一般'},
    {'id': 29, 'layer_name': '区域', 'error_category': '几何精度 / 要素类型错误', 'error_type': '要素类型错误', 'description': '面状区域被错误表示为线要素。', 'solution': '将线要素转换为面要素或重绘。', 'severity': '一般'},
    {'id': 30, 'layer_name': 'POI', 'error_category': '表达与符号化', 'error_type': '符号方向错误', 'description': '指示方向的POI符号方向与实际不符。', 'solution': '旋转符号或使用无方向性符号。', 'severity': '轻微'},
    {'id': 31, 'layer_name': '等高线', 'error_category': '完整性', 'error_type': '线条中断', 'description': '等高线在未到边界或闭合时中断。', 'solution': '检查数据源完整性或补充绘制。', 'severity': '一般'},
    {'id': 32, 'layer_name': '道路, 建筑物', 'error_category': '位置精度 / 逻辑一致性', 'error_type': '要素错位/不匹配 (接边错误)', 'description': '图幅接边处，同要素两侧未对齐。', 'solution': '进行接边处理确保几何连续性。', 'severity': '严重'},
    {'id': 33, 'layer_name': '道路', 'error_category': '属性精度 / 逻辑一致性', 'error_type': 'Z值/层级关系错误', 'description': '立交或下穿通道未正确表达层级。', 'solution': '赋予正确Z值或设置layer属性。', 'severity': '一般'},
    {'id': 34, 'layer_name': '植被, 建筑物', 'error_category': '逻辑一致性', 'error_type': '不合理邻接', 'description': '植被直接贴在建筑墙体上，无缓冲。', 'solution': '创建硬地缓冲或调整植被边界。', 'severity': '轻微'},
    {'id': 35, 'layer_name': '标注', 'error_category': '属性精度', 'error_type': '文本拼写/字符错误', 'description': '标注文本中存在错别字。', 'solution': '校对并修正错误字符。', 'severity': '一般'},
    {'id': 36, 'layer_name': '建筑物', 'error_category': '几何精度', 'error_type': '形状概括不当', 'description': '复杂建筑物被过度简化，丢失特征。', 'solution': '重绘或编辑轮廓以反映实际形状。', 'severity': '一般'},
    {'id': 37, 'layer_name': '道路', 'error_category': '逻辑一致性', 'error_type': '伪节点 (Pseudo Node)', 'description': '连续同属性道路中间存在不必要节点。', 'solution': '合并共享伪节点的线段。', 'severity': '轻微'},
    {'id': 38, 'layer_name': 'POI, 建筑物', 'error_category': '完整性', 'error_type': '要素关系缺失', 'description': 'POI点与其对应建筑物无关联关系。', 'solution': '建立POI与建筑物要素的链接。', 'severity': '轻微'},
    {'id': 39, 'layer_name': '围墙/栅栏', 'error_category': '完整性', 'error_type': '要素缺失', 'description': '缺少校园边界围墙或栅栏线。', 'solution': '补充绘制缺失的围墙/栅栏线。', 'severity': '一般'},
    {'id': 40, 'layer_name': '楼梯/台阶', 'error_category': '表达与符号化', 'error_type': '符号化缺失/不当', 'description': '室外楼梯未用专门符号表示。', 'solution': '使用楼梯线型或点符号替换或标注。', 'severity': '轻微'},
    {'id': 41, 'layer_name': '植被', 'error_category': '属性精度', 'error_type': '类型划分错误', 'description': '树林区域被错误归类为“草地”。', 'solution': '修改植被面要素的“类型”属性。', 'severity': '轻微'},
    {'id': 42, 'layer_name': '道路', 'error_category': '几何精度', 'error_type': '角度/方向错误', 'description': '道路转弯角度与实际严重不符。', 'solution': '编辑顶点，调整转弯几何形状。', 'severity': '一般'},
    {'id': 43, 'layer_name': '标注', 'error_category': '表达与符号化', 'error_type': '标注重复', 'description': '同一个地物出现两次相同标注。', 'solution': '删除重复的多余标注。', 'severity': '轻微'},
    {'id': 44, 'layer_name': '水体', 'error_category': '逻辑一致性', 'error_type': '流向错误', 'description': '小溪流数字化方向与实际流向相反。', 'solution': '翻转线要素方向。', 'severity': '一般'},
    {'id': 45, 'layer_name': '建筑物', 'error_category': '几何精度', 'error_type': '岛洞关系错误', 'description': '内部庭院(洞)被绘制为独立多边形。', 'solution': '确保内院作为外轮廓的“洞”存在。', 'severity': '一般'},
    {'id': 46, 'layer_name': 'POI', 'error_category': '时效性', 'error_type': '信息过时', 'description': 'POI点代表的店铺已关闭或搬迁。', 'solution': '删除POI点或更新状态/位置。', 'severity': '一般'},
    {'id': 47, 'layer_name': '道路', 'error_category': '完整性', 'error_type': '道路属性不完整（缺少等级）', 'description': '部分道路缺少“等级”属性。', 'solution': '为道路补充“等级”属性。', 'severity': '一般'},
    {'id': 48, 'layer_name': '背景/区域填充', 'error_category': '表达与符号化', 'error_type': '颜色/样式使用不当', 'description': '不同功能区背景色易混淆。', 'solution': '调整填充色确保视觉区分度。', 'severity': '轻微'},
    {'id': 49, 'layer_name': '建筑物', 'error_category': '几何精度', 'error_type': '尖角/回刺', 'description': '建筑物轮廓存在不必要尖角或回刺。', 'solution': '编辑顶点，平滑或移除无效结构。', 'severity': '轻微'},
    {'id': 50, 'layer_name': '地图标注/图例', 'error_category': '完整性 / 表达与符号化', 'error_type': '图例缺失或不匹配', 'description': '地图使用了特殊符号但图例未说明。', 'solution': '在图例中添加所有特殊符号的说明。', 'severity': '一般'},
    {'id': 51, 'layer_name': '道路', 'error_category': '拓扑关系', 'error_type': '网络连通性错误', 'description': '道路在转角处未连接，形成断点。', 'solution': '编辑顶点，确保转角处线段精确连接。', 'severity': '一般'},
    {'id': 52, 'layer_name': '注记/POI', 'error_category': '表达与符号化', 'error_type': '标注压盖/冲突', 'description': '两个或多个兴趣点(POI)的文字注记相互重叠，难以阅读。', 'solution': '调整注记放置算法或手动移动重叠的注记。', 'severity': '一般'},
    {'id': 53, 'layer_name': '注记', 'error_category': '完整性', 'error_type': '标注缺失', 'description': '地图上存在地物要素（如建筑、道路），但缺少对应的文字名称注记。', 'solution': '为缺少注记的地物添加文字标注。', 'severity': '一般'},
    {'id': 54, 'layer_name': '建筑物/注记', 'error_category': '完整性', 'error_type': '属性/标注缺失', 'description': '建筑物要素缺少名称信息，或地图上未显示该建筑物的名称注记。', 'solution': '补充建筑物的名称属性，并确保其注记在地图上正确显示。', 'severity': '一般'},
    {'id': 55, 'layer_name': '建筑物, 道路', 'error_category': '逻辑一致性 / 表达与符号化', 'error_type': '要素压盖/层级关系错误', 'description': '建筑物图层压盖在道路图层之上，视觉上不符合常规表达。', 'solution': '调整图层渲染顺序，使道路层在建筑层之上显示；或用建筑边界裁剪道路。', 'severity': '一般'},
    {'id': 56, 'layer_name': '道路', 'error_category': '拓扑关系', 'error_type': '网络连通性错误', 'description': '两条本应相交的道路在交叉口处未形成连接节点，存在断开。', 'solution': '编辑道路线段，确保在交叉口处打断并共享节点。', 'severity': '严重'},
    {'id': 57, 'layer_name': '道路', 'error_category': '几何精度/完整性', 'error_type': '要素中断', 'description': '一条连续的道路在中间无故断开，形成一个缺口。', 'solution': '连接断开处的两个线段，确保道路的连续性。', 'severity': '一般'}
]

# --- PNG Generation Loop ---
print(f"--- Starting PNG Image Generation in folder: {output_folder} ---")
cairosvg_available = True
generated_files = {} # To store paths for SQL generation

# Create a dictionary for faster SVG lookup
svg_dict = {item['id']: item for item in all_svg_examples}

for i in range(1, 58): # Generate for all 50 examples
    if not cairosvg_available:
        print("CairoSVG not available, skipping PNG generation.")
        break # Exit loop if library fails early

    example_id = i
    svg_data = svg_dict.get(example_id)

    if not svg_data:
        print(f"  Warning: SVG data not found for example {example_id}. Skipping image generation.")
        continue

    before_svg_content = svg_data["before_svg"].strip()
    after_svg_content = svg_data["after_svg"].strip()

    # Define filenames relative to the script execution directory
    before_filename_rel = os.path.join(output_folder, f"error{example_id}_before.png")
    after_filename_rel = os.path.join(output_folder, f"error{example_id}_after.png")

    # Generate 'before' image
    if not save_svg_as_png(before_svg_content, before_filename_rel):
        cairosvg_available = False # Stop trying if it fails
        generated_files[f'before_{example_id}'] = None # Mark as failed
    else:
        generated_files[f'before_{example_id}'] = before_filename_rel

    # Generate 'after' image (only if 'before' succeeded and library is ok)
    if cairosvg_available:
        if not save_svg_as_png(after_svg_content, after_filename_rel):
             cairosvg_available = False
             generated_files[f'after_{example_id}'] = None # Mark as failed
        else:
            generated_files[f'after_{example_id}'] = after_filename_rel
    else:
         generated_files[f'after_{example_id}'] = None # Mark as failed


print("\n--- PNG Image Generation Attempt Complete ---")
if not cairosvg_available:
    print("NOTE: PNG generation failed or was incomplete due to CairoSVG issues.")

# --- SQL INSERT Statement Generation ---
print("\n--- Generating SQL INSERT Statements ---")
print("-- IMPORTANT: Replace '/images/map_errors/' with your actual image hosting path.")
print("-- IMPORTANT: Ensure your database table 'error_examples' exists with the specified columns.")
print("-- IMPORTANT: Ensure your database connection handles UTF-8 encoding for Chinese characters.\n")

sql_statements = []
current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') # Use a fixed time for the batch

# Map severity strings to potential integer values (optional, adjust as needed)
# severity_map = {"严重": 3, "一般": 2, "轻微": 1}

for example_data in all_examples_data:
    example_id = example_data['id']

    # Construct image URLs based on BASE_IMAGE_URL and expected filenames
    img_before_url = f"error{example_id}_before.png"
    img_after_url = f"error{example_id}_after.png"

    # Use get() with default for safety, and replace single quotes in text fields
    layer = example_data.get('layer_name', '').replace("'", "''")
    category = example_data.get('error_category', '').replace("'", "''")
    etype = example_data.get('error_type', '').replace("'", "''")
    desc = example_data.get('description', '').replace("'", "''")
    sol = example_data.get('solution', '').replace("'", "''")
    severity_str = example_data.get('severity', '一般').replace("'", "''") # Keep original string
    # severity_int = severity_map.get(example_data.get('severity', '一般'), 2) # Example if using integers

    # Create SQL statement (using original severity string)
    # Using CURRENT_TIMESTAMP or NOW() is generally preferred in SQL itself
    # but providing a fixed time from Python ensures consistency if run later.
    sql = f"""
INSERT INTO error_examples (layer_name, error_category, error_type, description, solution, image_before_url, image_after_url, severity, created_at)
VALUES ('{layer}', '{category}', '{etype}', '{desc}', '{sol}', '{img_before_url}', '{img_after_url}', '{severity_str}', '{current_time}');
"""
    # If using severity integers:
    # VALUES ('{layer}', '{category}', '{etype}', '{desc}', '{sol}', '{img_before_url}', '{img_after_url}', {severity_int}, NOW());

    sql_statements.append(sql.strip()) # Add the cleaned SQL

# --- Output SQL Statements ---
# You can copy this output and run it in your SQL client
# Or modify the script to connect to your DB and execute directly (using libraries like psycopg2, mysql.connector, etc.)

output_sql_file = "insert_error_examples.sql"
print(f"\nSaving SQL statements to: {output_sql_file}\n")

try:
    with open(output_sql_file, 'w', encoding='utf-8') as f:
        for stmt in sql_statements:
            f.write(stmt + "\n\n") # Add double newline for readability
    print(f"Successfully wrote {len(sql_statements)} INSERT statements to {output_sql_file}")
except Exception as e:
    print(f"Error writing SQL file: {e}")


print("\n--- Script Finished ---")