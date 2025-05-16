import fitz  # PyMuPDF
import os
import argparse
from PIL import Image
# --- Layer Definitions ---
# Define layers based on the analysis of '道路房屋.pdf'
# Each layer is a list of rules. An element is assigned to the layer
# if it matches ANY rule within that layer's list.
# Colors are RGB tuples (float 0.0-1.0), rounded to 3 decimal places.
# MUST match the precision used in the analysis script.
LAYER_DEFINITIONS = {
    
    "roads_with_buildings": [
        { # Rule 1 for roads
            "match_on": "stroke_color", # Corresponds to 'color' key in get_cdrawings
            "target_colors": [
                (0.306, 0.306, 0.306), 
                (1.0, 1.0, 1.0)
            ],
            "precision": 3
        },
        { # Rule 2 for buildings
            "match_on": "fill_color", # Corresponds to 'fill' key in get_cdrawings
            "target_colors": [
                (1.0, 0.745, 0.745),
                (0.929, 0.757, 0.573),
                (0.949, 0.894, 0.722),
                (0.91, 0.745, 1.0),
                (0.8, 0.8, 0.8),
                (1.0, 0.655, 0.498)
            ],
            "precision": 3
        }
    ],
    "roads": [
        { # Rule 1 for roads
            "match_on": "stroke_color", # Corresponds to 'color' key in get_cdrawings
            "target_colors": [
                (0.306, 0.306, 0.306), 
                (1.0, 1.0, 1.0)
            ],
            "precision": 3
        },
        # Add another rule here if roads also need to match a fill color, e.g.:
        # {
        #    "match_on": "fill_color",
        #    "target_colors": [(0.9, 0.9, 0.9)],
        #    "precision": 3
        # }
    ],
    "buildings": [
        { # Rule 1 for buildings
            "match_on": "fill_color", # Corresponds to 'fill' key in get_cdrawings
            "target_colors": [
                (1.0, 0.745, 0.745),
                (0.929, 0.757, 0.573),
                (0.949, 0.894, 0.722),
                (0.91, 0.745, 1.0),
                (0.8, 0.8, 0.8),
                (1.0, 0.655, 0.498)
            ],
            "precision": 3
        }
    ],
    "water": [
        { # Rule 1 for water
            "match_on": "fill_color", # Corresponds to 'fill' key in get_cdrawings
            "target_colors": [
                (0.745, 0.91, 1.0)
            ],
            "precision": 3
        }
    ],
    "plants": [
        { # Rule 1 for plants
            "match_on": "fill_color", # Corresponds to 'fill' key in get_cdrawings
            "target_colors": [
                (0.718, 0.867, 0.784)
            ],
            "precision": 3
        }
    ],
    # Add more layer definitions here if needed
}

def make_transparent(image_path, output_path):
    # 打开图片
    image = Image.open(image_path).convert("RGBA")
    data = image.getdata()

    # 创建新的像素列表
    new_data = []
    for item in data:
        # 如果是白色（RGB 值为 255, 255, 255），设置透明度为 0
        if item[0] == 255 and item[1] == 255 and item[2] == 255:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)

    # 更新图片数据
    image.putdata(new_data)

    # 保存结果
    image.save(output_path, "PNG")

def compare_colors(color1, color2, precision):
    """Compares two color tuples after rounding to the specified precision."""
    if color1 is None or color2 is None:
        return False
    if len(color1) != len(color2):
         return False # Should not happen for RGB
    try:
        rounded1 = tuple(round(c, precision) for c in color1)
        rounded2 = tuple(round(c, precision) for c in color2)
        return rounded1 == rounded2
    except TypeError:
        return False # Handle non-numeric values just in case

def extract_layers(task_id, base_dir="/local_server/ai_mapcheck/tasks", page_number=0):
    """
    Extracts vector drawings into separate PDF files based on color definitions.

    Args:
        pdf_path (str): Path to the input PDF file.
        output_dir (str): Directory to save the extracted layer PDFs.
        page_number (int): The 0-indexed page number to process.
    """
    pdf_path = os.path.join(base_dir, f"task_{task_id}/original/原地图.pdf")
    output_dir = os.path.join(base_dir, f"task_{task_id}/analysis")
    os.makedirs(output_dir, exist_ok=True)

    try:
        doc_orig = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening original PDF '{pdf_path}': {e}")
        return

    if page_number >= len(doc_orig):
        print(f"Error: Page number {page_number} out of range for '{pdf_path}'.")
        doc_orig.close()
        return

    page_orig = doc_orig[page_number]
    page_rect = page_orig.rect # Get original page dimensions

    # --- Save Original Page as PNG ---
    print(f"\nSaving original page {page_number} as PNG...")
    output_png_original_filename = "original_map.png"
    output_png_original_path = os.path.join(output_dir, output_png_original_filename)
    try:
        dpi_orig = 150 # Choose desired resolution for original map PNG
        pix_orig = page_orig.get_pixmap(dpi=dpi_orig)
        pix_orig.save(output_png_original_path)
        print(f"Saved original map PNG ({pix_orig.width}x{pix_orig.height} px) to: {output_png_original_path}")
    except Exception as e_orig_png:
        print(f"Error saving original map PNG: {e_orig_png}")
    # Continue with layer extraction even if original PNG saving fails

    # Create new PDF documents for each layer
    layer_docs = {}
    layer_pages = {}
    for layer_name in LAYER_DEFINITIONS:
        layer_docs[layer_name] = fitz.open() # Create a new empty doc
        # Add a page with the same dimensions as the original
        layer_pages[layer_name] = layer_docs[layer_name].new_page(width=page_rect.width, height=page_rect.height)
        print(f"Created new PDF for layer: {layer_name}")

    processed_drawing_count = 0
    layer_drawing_counts = {layer_name: 0 for layer_name in LAYER_DEFINITIONS}

    try:
        print(f"Extracting drawings from page {page_number} of '{pdf_path}'...")
        drawings = page_orig.get_cdrawings()
        print(f"Found {len(drawings)} drawing elements to process.")

        for i, drawing in enumerate(drawings):
            print(f"Processing drawing {i+1}/{len(drawings)}...", end='\r')
            # Reset match flag for each drawing
            # matched_layer = None # We no longer need a single matched_layer
            drawing_added_to_any_layer = False # Track if drawn at least once

            # Check against layer definitions
            # Iterate through ALL layers and their rules for EACH drawing
            for layer_name, rules_list in LAYER_DEFINITIONS.items():
                # Check if this drawing matches ANY rule for the current layer
                does_match_current_layer = False
                for rule in rules_list:
                    match_attr = rule["match_on"]
                    target_colors = rule["target_colors"]
                    precision = rule["precision"]
                    drawing_color = None

                    if match_attr == "stroke_color":
                        drawing_color = drawing.get("color")
                    elif match_attr == "fill_color":
                        drawing_color = drawing.get("fill")
                    
                    # Check if the drawing's color matches any target color in this rule
                    if drawing_color is not None and isinstance(drawing_color, (list, tuple)):
                        for target_color in target_colors:
                            if compare_colors(drawing_color, target_color, precision):
                                does_match_current_layer = True
                                break # Color matched within this rule, stop checking target colors for this rule
                    
                    if does_match_current_layer:
                        break # Rule matched within this layer, stop checking other rules for this layer
                
                # REMOVED: if matched_layer: break # Layer found for this drawing, stop checking other layers

                # If the drawing matched ANY rule for this layer, redraw it onto this layer's page
                if does_match_current_layer:
                    target_page = layer_pages[layer_name]
                    shape = target_page.new_shape() # Create a shape object for the target page

                    # Replicate drawing commands
                    for item in drawing["items"]:
                        op = item[0] # Operation: 'l', 'c', 're', 'qu', 'ov'
                        if op == "l": # line
                            shape.draw_line(item[1], item[2]) # p1, p2
                        elif op == "re": # rectangle
                             shape.draw_rect(item[1]) # rect
                        elif op == "c": # curve
                            shape.draw_bezier(item[1], item[2], item[3], item[4]) # p1, p2, p3, p4
                        elif op == "qu": # quad
                             shape.draw_quad(item[1]) # quad
                        elif op == "ov": # oval / circle
                            shape.draw_circle(item[1], item[2]) # center, radius
                        # Add other ops like 's' (spline) if necessary, though less common
                        else:
                             print(f"\nWarning: Unsupported drawing operation '{op}' found. Skipping item.")

                    # Apply properties (color, fill, width etc.) - try to preserve original
                    stroke_c = drawing.get("color")
                    fill_c = drawing.get("fill")
                    width = drawing.get("width", 1.0) # Default width if not specified
                    closePath = drawing.get("closePath", True)
                    lineCap = drawing.get("lineCap", 0)
                    lineJoin = drawing.get("lineJoin", 0)
                    stroke_opacity = drawing.get("stroke_opacity", 1)
                    fill_opacity = drawing.get("fill_opacity", 1)
                    
                    # Ensure lineCap and lineJoin are integers
                    try:
                        lineCap = int(lineCap)
                    except (ValueError, TypeError):
                        print(f"\nWarning: Invalid lineCap value '{lineCap}'. Using default 0.")
                        lineCap = 0
                    try:
                        lineJoin = int(lineJoin)
                    except (ValueError, TypeError):
                        print(f"\nWarning: Invalid lineJoin value '{lineJoin}'. Using default 0.")
                        lineJoin = 0
                    
                    shape.finish(color=stroke_c, 
                                 fill=fill_c, 
                                 width=width,
                                 closePath=closePath,
                                 lineCap=lineCap,
                                 lineJoin=lineJoin,
                                 stroke_opacity=stroke_opacity,
                                 fill_opacity=fill_opacity)
                                 
                    shape.commit() # Draw the shape onto the target layer page
                    layer_drawing_counts[layer_name] += 1 # Increment count for this layer
                    drawing_added_to_any_layer = True # Mark that this drawing was used

            # After checking ALL layers for the current drawing:
            if drawing_added_to_any_layer:
                 processed_drawing_count +=1 # Increment count only if drawn at least once

        print(f"\nFinished processing drawings. {processed_drawing_count} elements were matched and redrawn across all layers.")

    except Exception as e:
        print(f"\nError during drawing processing: {e}")
        import traceback
        traceback.print_exc()

    # Save the new layer PDFs
    print("\nSaving extracted layer PDFs...")
    for layer_name, doc_layer in layer_docs.items():
        output_pdf_filename = f"{layer_name}_layer.pdf"
        output_pdf_path = os.path.join(output_dir, output_pdf_filename)
        output_png_filename = f"{layer_name}_layer.png" # Define PNG filename
        output_png_path = os.path.join(output_dir, output_png_filename) # Define PNG path
        
        try:
            # Save the PDF layer
            doc_layer.save(output_pdf_path, garbage=4, deflate=True)
            print(f"Saved layer '{layer_name}' ({layer_drawing_counts[layer_name]} elements) PDF to: {output_pdf_path}")

            # Now, render and save as PNG
            if len(doc_layer) > 0: # Check if document has pages
                 page_layer = doc_layer[0] # Get the first (and only) page
                 dpi = 150 # Choose desired resolution for PNG
                 try:
                     pix = page_layer.get_pixmap(dpi=dpi)
                     pix.save(output_png_path)
                     make_transparent(output_png_path, output_png_path)
                     print(f"Saved layer '{layer_name}' PNG ({pix.width}x{pix.height} px) to: {output_png_path}")
                 except Exception as e_png:
                     print(f"Error saving PNG for layer '{layer_name}': {e_png}")
            else:
                 print(f"Warning: Cannot save PNG for empty layer '{layer_name}'.")
                 
        except Exception as e_pdf:
            print(f"Error saving PDF for layer '{layer_name}': {e_pdf}")
        finally:
            # Ensure the document is closed regardless of PNG saving success/failure
            doc_layer.close()

    # Close the original document
    doc_orig.close()
    print("Layer extraction process finished.")


if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description='Extract vector drawings from a PDF page into separate layer PDFs based on colors.')
    # parser.add_argument("pdf_file", help="Path to the original PDF file.")
    # parser.add_argument("-o", "--output_dir", required=True, help="Directory to save the extracted layer PDF files.")
    # parser.add_argument("-p", "--page", type=int, default=0, help="Page number to process (0-indexed, default: 0)")
    
    # args = parser.parse_args()
    pdf_file = "C:/Users/nan/Desktop/原地图.pdf"
    extract_layers(pdf_file) 