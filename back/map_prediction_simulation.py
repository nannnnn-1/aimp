import os
import fitz  # PyMuPDF
from PIL import Image, ImageFont, ImageDraw
import numpy as np
import math
import cv2
# Removed: from ultralytics import YOLO
import re
import shutil # For directory cleanup
from report_generator import create_markdown_report, load_error_examples # Keep report generator
from datetime import datetime
import random
FONT_PATH = "SimHei.ttf"
TASK_FOLDER = '/local_server/ai_mapcheck/tasks'
FONT_SIZE = 15

def draw_text_with_pillow(image_cv, text, position, font_object, color_bgr, font_size_px):
    """
    Draws text (potentially Chinese) onto an OpenCV image using Pillow.

    Args:
        image_cv: The OpenCV image (NumPy array, BGR format).
        text: The string to draw.
        position: Tuple (x, y) for the *reference* point (e.g., top-left of bbox).
                  Text will be drawn slightly above this point.
        font_object: The loaded Pillow ImageFont object.
        color_bgr: Tuple (B, G, R) color for the text.
        font_size_px: The font size in pixels (used for vertical positioning).

    Returns:
        The modified OpenCV image (NumPy array, BGR format).
        Returns the original image if font is not loaded or an error occurs.
    """
    if font_object is None:
        # print("Warning: Font not loaded, cannot draw text with Pillow.")
        # Fallback to OpenCV (will show '?') if font is missing
        try:
             cv2.putText(image_cv, text, (position[0], position[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_bgr, 2)
        except Exception as cv_err:
             print(f"Error during fallback cv2.putText: {cv_err}")
        return image_cv

    try:
        # Convert color BGR to RGB for Pillow
        color_rgb = (color_bgr[2], color_bgr[1], color_bgr[0])
        # Adjust position: Pillow's origin is top-left of text. Draw above the reference point.
        text_position = (position[0], position[1] - font_size_px - 2) # Adjust y based on font size

        # Convert OpenCV BGR image to PIL RGB image
        img_pil = Image.fromarray(cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)

        # Draw text
        draw.text(text_position, text, font=font_object, fill=color_rgb)

        # Convert back to OpenCV BGR image
        image_cv_modified = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        return image_cv_modified

    except Exception as e:
        print(f"Error drawing text '{text}' with Pillow: {e}")
        # Fallback to OpenCV on Pillow error (will show '?')
        try:
             cv2.putText(image_cv, text, (position[0], position[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_bgr, 2)
        except Exception as cv_err:
             print(f"Error during fallback cv2.putText after Pillow error: {cv_err}")
        return image_cv # Return original image on error
# --- Keep MapTiler class ---
class MapTiler:
    def __init__(self, task_id, pdf_path, output_dir_base, tile_size=640, overlap_ratio=0.2, target_zoom=4, map_type="original"):
        """
        初始化地图分块器 (No changes needed here)
        """
        self.task_id = task_id
        self.pdf_path = pdf_path
        self.tile_size = tile_size
        self.overlap_ratio = overlap_ratio
        self.overlap_size = int(tile_size * overlap_ratio)
        self.target_zoom = target_zoom
        self.map_type = map_type
        # 缩放级别对应的 DPI 倍数
        self.zoom_levels = {
            0.5: 72,
            1: 144,
            2: 288,
            4: 600 # Default zoom level for processing
        }
        if target_zoom not in self.zoom_levels:
            raise ValueError(f"Unsupported zoom level: {target_zoom}. Available levels: {list(self.zoom_levels.keys())}")

        # Create specific output directory for this map type and zoom level
        self.output_dir = os.path.join(output_dir_base, f"tiles_{map_type}_zoom{target_zoom}")
        os.makedirs(self.output_dir, exist_ok=True)
        self.full_image_path = os.path.join(output_dir_base, f"{map_type}_map.jpg") # Save full image in review dir
        self.tiles_info = {} # Store tile paths and dimensions

    def process_map_for_target_zoom(self):
        """仅处理目标缩放级别的地图"""
        try:
            print(f"Processing {self.map_type} PDF: {self.pdf_path} for zoom {self.target_zoom}...")
            try:
                doc_orig = fitz.open(self.pdf_path)
            except Exception as e:
                print(f"Error opening original PDF '{self.pdf_path}': {e}")
                return
            page_number = 0
            if page_number >= len(doc_orig):
                print(f"Error: Page number {page_number} out of range for '{self.pdf_path}'.")
                doc_orig.close()
                return

            page_orig = doc_orig[page_number]
            page_rect = page_orig.rect # Get original page dimensions
            output_png_original_filename = "original_map.jpg"
            output_png_original_path = os.path.join(TASK_FOLDER, f'task_{self.task_id}', 'review', output_png_original_filename)
            try:
                dpi_orig = 600 # Choose desired resolution for original map PNG
                pix_orig = page_orig.get_pixmap(dpi=dpi_orig)
                pix_orig.save(output_png_original_path)
                print(f"Saved original map PNG ({pix_orig.width}x{pix_orig.height} px) to: {output_png_original_path}")
            except Exception as e_orig_png:
                print(f"Error saving original map PNG: {e_orig_png}")
            img = Image.open(os.path.join(TASK_FOLDER, f'task_{self.task_id}', 'review', output_png_original_filename))
            img.convert("RGB")
            # 生成瓦片 (Based on the full rendered image)s
            self._generate_tiles(img)
            print(f"  - Generated {len(self.tiles_info.get('tiles', []))} tiles for {self.map_type}.")

            doc_orig.close()
            # Return dimensions along with other info
            dims = {'width': img.width, 'height': img.height}
            return True, f"Map tiling for {self.map_type} zoom {self.target_zoom} completed.", self.full_image_path, self.tiles_info, dims

        except Exception as e:
            import traceback; traceback.print_exc()
            return False, f"Map tiling failed for {self.map_type}: {str(e)}", None, None, None

    def _generate_tiles(self, img):
        """为目标缩放级别生成瓦片 (No changes needed here)"""
        effective_tile_size = self.tile_size - self.overlap_size
        # Ensure effective_tile_size is at least 1 to prevent division by zero or infinite loops
        if effective_tile_size <= 0:
            raise ValueError("Effective tile size must be positive. Check tile_size and overlap_ratio.")

        cols = math.ceil(img.width / effective_tile_size)
        rows = math.ceil(img.height / effective_tile_size)

        self.tiles_info['dimensions'] = {'width': img.width, 'height': img.height, 'rows': rows, 'cols': cols, 'tile_size': self.tile_size, 'overlap_size': self.overlap_size, 'effective_tile_size': effective_tile_size}
        self.tiles_info['tiles'] = []

        for row in range(rows):
            for col in range(cols):
                left = col * effective_tile_size
                top = row * effective_tile_size

                # Apply overlap (except for first row/col)
                tile_left = max(0, left - (self.overlap_size if col > 0 else 0))
                tile_top = max(0, top - (self.overlap_size if row > 0 else 0))

                # Calculate bottom-right ensuring it doesn't exceed image bounds
                tile_right = min(tile_left + self.tile_size, img.width)
                tile_bottom = min(tile_top + self.tile_size, img.height)

                # Adjust left/top if tile goes out of bounds due to overlap calculation near edges
                if tile_right - tile_left < self.tile_size and tile_left > 0:
                     tile_left = max(0, img.width - self.tile_size)
                if tile_bottom - tile_top < self.tile_size and tile_top > 0:
                     tile_top = max(0, img.height - self.tile_size)

                # Recalculate right/bottom after potential left/top adjustment
                tile_right = min(tile_left + self.tile_size, img.width)
                tile_bottom = min(tile_top + self.tile_size, img.height)

                tile = img.crop((tile_left, tile_top, tile_right, tile_bottom))

                # Pad if necessary to make it tile_size x tile_size
                if tile.size[0] < self.tile_size or tile.size[1] < self.tile_size:
                    padded_tile = Image.new('RGB', (self.tile_size, self.tile_size), 'white')
                    padded_tile.paste(tile, (0, 0))
                    tile = padded_tile


                tile_name = f"tile_{row}_{col}.jpg"
                tile_path = os.path.join(self.output_dir, tile_name)
                tile.save(tile_path, "JPEG", quality=95)

                tile_data = {
                    'path': tile_path,
                    'row': row,
                    'col': col,
                    # Coords relative to the *source* image (original, layer1, or layer2)
                    'orig_coords': (tile_left, tile_top, tile_right, tile_bottom),
                    # Effective coords relative to the *source* image
                    'effective_coords': (left, top, min(left + effective_tile_size, img.width), min(top + effective_tile_size, img.height))
                }
                self.tiles_info['tiles'].append(tile_data)

    def get_rendering_matrix(self):
        """获取渲染矩阵 (No changes needed here)"""
        dpi = self.zoom_levels[self.target_zoom]
        return fitz.Matrix(dpi / 72.0, dpi / 72.0)


# --- SIMULATED Main Function ---

def predict_map_layers_simulation(
    task_id,
    model_id,         # User selected Model ID (for reporting - becomes less relevant)
    review_mode,      # User selected Review Mode (for reporting - becomes less relevant)
    tile_size=640,
    overlap_ratio=0.2,
    target_zoom=4,
    ):
    """
    Simulates map prediction by reading manual annotations from demo.txt.
    Generates annotated images and reports based on this simulated data.
    """
    print(f"--- Starting SIMULATED Map Prediction Task {task_id} ---")
    print(f"Reporting Info: Model='{model_id}', Mode='{review_mode}' (Note: Actual prediction is simulated)")
    
    # --- 1. Setup Paths ---
    output_dir = os.path.join(TASK_FOLDER, f'task_{task_id}', "review")
    os.makedirs(output_dir, exist_ok=True)
    demo_txt_path = "models/demo.txt" # Assumed path for manual annotations
    original_pdf_rel_path = 'original/原地图.pdf' # Path relative to task base dir
    original_pdf_path = os.path.join(TASK_FOLDER, f'task_{task_id}', original_pdf_rel_path)
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    # --- Check for required files ---
    if not os.path.exists(original_pdf_path):
        print(f"Error: Original PDF not found at {original_pdf_path}")
        return
    if not os.path.exists(demo_txt_path):
        print(f"Error: Annotation file demo.txt not found at {demo_txt_path}")
        return

    print(f"Output Directory: {output_dir}")
    print(f"Using manual annotations from: {demo_txt_path}")

    # --- Initialize variables needed in finally block ---
    tilers = {} # Still used for matrix lookup

    try:
        # --- 2. Tile ONLY the Original Map ---
        print("--- Starting Tiling Phase (Original Map Only) ---")
        tile_infos = {}
        full_image_paths = {}
        dimensions = {}

        print(f"Tiling layer: original from {original_pdf_path}")
        # Use output_dir for the tiler's base to place full image and tiles subdir there
        tiler = MapTiler(task_id, original_pdf_path, output_dir, tile_size, overlap_ratio, target_zoom, "original")
        success, msg, fp, ti, dim = tiler.process_map_for_target_zoom()

        if not success:
            print(f"Error tiling original layer: {msg}")
            return

        tilers['original'] = tiler # Store tiler for matrix access
        tile_infos['original'] = ti
        full_image_paths['original'] = fp
        dimensions['original'] = dim

        print("--- Tiling Phase Completed ---")
        img_w = dimensions['original']['width']
        img_h = dimensions['original']['height']
        num_tiles = len(tile_infos['original']['tiles'])
        tile_grid_info = tile_infos['original']['dimensions'] # Get rows, cols, etc.

        # --- 3. Load Manual Annotations (Instead of Models) ---
        print("--- Loading Manual Annotations from demo.txt ---")
        manual_annotations = []
        try:
            with open(demo_txt_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f):
                    line = line.strip()
                    if not line or '|' not in line: continue # Skip empty or invalid lines
                    parts = line.split('|')
                    if len(parts) != 5:
                        print(f"Warning: Skipping invalid line {line_num + 1} in demo.txt (expected 5 parts): {line}")
                        continue
                    try:
                        cls_name, x1, y1, x2, y2 = parts
                        manual_annotations.append({
                            'cls_name': cls_name.strip(),
                            'box': tuple(map(int, [x1, y1, x2, y2]))
                        })
                    except ValueError:
                        print(f"Warning: Skipping invalid coordinates in line {line_num + 1} of demo.txt: {line}")
                        continue
            print(f"Loaded {len(manual_annotations)} manual annotations.")
            if not manual_annotations:
                 print("Warning: No valid annotations found in demo.txt. Report may be empty.")

        except Exception as read_e:
             print(f"Error reading or parsing {demo_txt_path}: {read_e}")
             return

        # --- 4. Prepare Colors and Output Images ---
        print("--- Preparing Output Images ---")
        # Define colors here or load from error_examples_map later
        class_color_map = {'default': (0, 0, 255) } # Example
        full_image_orig_bgr = cv2.imread(full_image_paths['original'])
        if full_image_orig_bgr is None: return print("Error: Could not load original full image.")
        output_img_combined = full_image_orig_bgr.copy()
        error_tile_dir = os.path.join(output_dir, f"predicted_error_tiles_zoom{target_zoom}")
        os.makedirs(error_tile_dir, exist_ok=True)
        print(f"Saving error tiles to: {error_tile_dir}")

        # --- 5. Process Annotations (Simulate Detections) ---
        print("--- Processing Manual Annotations ---")
        all_detections_combined_details = []
        processed_tile_images = {} # Cache loaded tile images: {tile_ref: img}

        # Load error examples map for details
        error_examples_map = load_error_examples()

        for annot in manual_annotations:
            cls_name = annot['cls_name']
            x1_orig, y1_orig, x2_orig, y2_orig = annot['box']

            # Calculate center for tile lookup
            center_x_orig = (x1_orig + x2_orig) / 2
            center_y_orig = (y1_orig + y2_orig) / 2

            # --- Determine which tile this annotation belongs to ---
            tile_ref = "unknown_tile"
            found_tile = False
            eff_tile_size = tile_grid_info['effective_tile_size']
            for tile_data in tile_infos['original']['tiles']:
                eff_x, eff_y, eff_x2, eff_y2 = tile_data['effective_coords']
                if eff_x <= center_x_orig < eff_x2 and eff_y <= center_y_orig < eff_y2:
                    tile_row = tile_data['row']
                    tile_col = tile_data['col']
                    tile_ref = f"row{tile_row}_col{tile_col}"
                    tile_orig_x, tile_orig_y, _, _ = tile_data['orig_coords'] # Top-left of the *saved* tile image
                    found_tile = True
                    break # Found the primary tile

            if not found_tile:
                print(f"Warning: Could not determine tile for annotation: {annot}")
                # Assign to a default tile or skip? For now, assign default ref
                tile_ref = "tile_outside_effective_area"
                tile_orig_x, tile_orig_y = 0, 0 # Default for coordinate conversion


            # Get color and details from error map
            example_info = error_examples_map.get(cls_name, {})
            color_bgr = class_color_map.get(cls_name, class_color_map['default'])
            model_name_placeholder = "Annotation" # Placeholder model name

            # --- Draw on Combined Image ---
            label = f"{cls_name}" # Simple label
            cv2.rectangle(output_img_combined, (x1_orig, y1_orig), (x2_orig, y2_orig), color_bgr, 2)
            output_img_combined = draw_text_with_pillow(
                            output_img_combined,
                            label,
                            (x1_orig, y1_orig - 10), # Reference point (top-left of clipped bbox)
                            font,
                            color_bgr,
                            FONT_SIZE
                        )
            # cv2.putText(output_img_combined, label, (x1_orig, y1_orig - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_bgr, 2)

            # --- Prepare detection details for reports ---
            all_detections_combined_details.append({
                'box_orig_px': (x1_orig, y1_orig, x2_orig, y2_orig),
                'conf': random.uniform(0.8, 0.95), # 在0.8-0.95之间随机生成置信度
                'cls_idx': -1, # No real class index from model
                'cls_name': cls_name,
                'model_name': model_name_placeholder,
                'color': color_bgr,
                'tile_ref': tile_ref,
                # Add details needed for report from error_examples_map
                'error_category': example_info.get('error_category', '未知类别'),
                'severity': example_info.get('severity', '未知'),
                'description': example_info.get('description', '-'),
                'solution': example_info.get('solution', '-')
            })

            # --- Draw on Error Tile Snapshot (Optional but good for consistency) ---
            if found_tile:
                error_tile_filename = f"error_tile_{tile_ref}.jpg" # Consistent naming
                error_tile_path = os.path.join(error_tile_dir, error_tile_filename)

                # Load or get cached tile image
                if tile_ref not in processed_tile_images:
                    tile_image_path = tile_infos['original']['tiles'][tile_row * tile_grid_info['cols'] + tile_col]['path']
                    img_bgr = cv2.imread(tile_image_path)
                    if img_bgr is not None:
                        processed_tile_images[tile_ref] = img_bgr.copy() # Store a copy
                    else:
                         processed_tile_images[tile_ref] = None # Mark as failed to load
                         print(f"Warning: Could not read tile image {tile_image_path}")

                output_error_tile_img = processed_tile_images.get(tile_ref)

                if output_error_tile_img is not None:
                    # Convert original box coords to tile-local coords
                    x1_tile = x1_orig - tile_orig_x
                    y1_tile = y1_orig - tile_orig_y
                    x2_tile = x2_orig - tile_orig_x
                    y2_tile = y2_orig - tile_orig_y
                    # Clip coordinates to tile boundaries (0 to tile_size)
                    x1_tile_c = max(0, min(x1_tile, tile_size - 1))
                    y1_tile_c = max(0, min(y1_tile, tile_size - 1))
                    x2_tile_c = max(0, min(x2_tile, tile_size - 1))
                    y2_tile_c = max(0, min(y2_tile, tile_size - 1))

                    # Draw clipped rectangle and text if visible
                    if x1_tile_c < x2_tile_c and y1_tile_c < y2_tile_c:
                        cv2.rectangle(output_error_tile_img, (x1_tile_c, y1_tile_c), (x2_tile_c, y2_tile_c), color_bgr, 2)
                        output_error_tile_img = draw_text_with_pillow(
                            output_error_tile_img,
                            label,
                            (x1_tile_c, y1_tile_c - 10), # Reference point (top-left of clipped bbox)
                            font,
                            color_bgr,
                            FONT_SIZE
                        )
                        # cv2.putText(output_error_tile_img, label, (x1_tile_c, y1_tile_c - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_bgr, 2)
                        processed_tile_images[tile_ref] = output_error_tile_img # Update cached image


        # --- Save all processed error tile snapshots ---
        print("\nSaving processed error tile snapshots...")
        saved_tile_count = 0
        for tile_ref, img_data in processed_tile_images.items():
             if img_data is not None:
                 error_tile_filename = f"error_tile_{tile_ref}.jpg"
                 error_tile_path = os.path.join(error_tile_dir, error_tile_filename)
                 try:
                     cv2.imwrite(error_tile_path, img_data)
                     saved_tile_count += 1
                 except Exception as write_e:
                     print(f"Error saving error tile {error_tile_path}: {write_e}")
        print(f"Saved {saved_tile_count} error tile snapshots.")


        print("\n--- Annotation Processing Finished ---")


        # --- 6. Save Combined Result Image (Annotations Drawn) ---
        print("--- Saving Combined Output Image ---")
        output_image_combined_filename = f"combined_prediction_original_zoom{target_zoom}.jpg"
        output_image_combined_path = os.path.join(output_dir, output_image_combined_filename)
        cv2.imwrite(output_image_combined_path, output_img_combined)
        print(f"Combined prediction image saved to: {output_image_combined_path}")

        # --- 7. Annotate Original PDF (Report 1) ---
        print("--- Annotating Original PDF (Report 1) --- ")
        try:
            # if 'original' not in tilers: raise RuntimeError("Original tiler not available for PDF annotation matrix.")
            # matrix_orig = tilers['original'].get_rendering_matrix()
            # inv_matrix = ~matrix_orig
            # pdf_doc_path_orig = original_pdf_path # Use the correct path
            # pdf_doc = fitz.open(pdf_doc_path_orig)
            # if not pdf_doc: raise RuntimeError("Could not open original PDF for annotation.")

            # page = pdf_doc[0]
            # annot_count = 0
            # for det in all_detections_combined_details: # Use the simulated details
            #     x1_px, y1_px, x2_px, y2_px = det['box_orig_px']
            #     bgr_color = det['color']
            #     rgb_float_color = (bgr_color[2]/255.0, bgr_color[1]/255.0, bgr_color[0]/255.0)
            #     p1 = fitz.Point(x1_px, y1_px) * inv_matrix
            #     p2 = fitz.Point(x2_px, y2_px) * inv_matrix
            #     pdf_rect = fitz.Rect(p1.x, p1.y, p2.x, p2.y); pdf_rect.normalize()
            #     annot = page.add_rect_annot(pdf_rect)
            #     annot.set_colors(stroke=rgb_float_color); annot.set_border(width=1.5)
            #     # Use the placeholder model name and class name
            #     label_text = f"{det['model_name']}:{det['cls_name']}"
            #     annot.set_info(content=label_text); annot.update()
            #     annot_count += 1

            # output_annotated_pdf_filename = f"combined_prediction_annotated_zoom{target_zoom}.pdf"
            # output_annotated_pdf_path = os.path.join(output_dir, output_annotated_pdf_filename)
            # pdf_doc.save(output_annotated_pdf_path, garbage=4, deflate=True); pdf_doc.close()
            # print(f"Annotated PDF saved to: {output_annotated_pdf_path} ({annot_count} annotations added)")
             # 生成目标文件名（保持与原逻辑一致）
            source_pdf_path = "/local_server/ai_mapcheck/combined_prediction_annotated_zoom4.pdf"
            output_annotated_pdf_filename = f"combined_prediction_annotated_zoom{target_zoom}.pdf"
            output_annotated_pdf_path = os.path.join(output_dir, output_annotated_pdf_filename)
    
            # 确保源文件存在
            if not os.path.exists(source_pdf_path):
                raise FileNotFoundError(f"预制PDF文件不存在: {source_pdf_path}")
    
            # 执行复制操作
            shutil.copy(source_pdf_path, output_annotated_pdf_path)
    
            print(f"PDF已从预制文件复制到: {output_annotated_pdf_path}")
        except Exception as e:
            print(f"\nError annotating PDF: {str(e)}")
            import traceback; traceback.print_exc()


        # --- 8. Generate Detailed Markdown Report (Report 2) ---
        print("--- Preparing Data for Detailed Report (Report 2) ---")
        try:
            # Re-aggregate stats based on the simulated detections
            aggregated_detections_for_report = []
            detection_id_counter = 1
            # Use the placeholder model name for stats
            stats_by_model = {model_name_placeholder: 0}
            stats_by_category = {}
            stats_by_severity = {}

            for det in all_detections_combined_details:
                # All necessary fields should already be in det from step 5
                aggregated_det = det.copy()
                aggregated_det['id'] = detection_id_counter # Add unique ID for report table
                aggregated_detections_for_report.append(aggregated_det)
                detection_id_counter += 1

                # Update stats
                stats_by_model[model_name_placeholder] += 1
                stats_by_category[det['error_category']] = stats_by_category.get(det['error_category'], 0) + 1
                stats_by_severity[det['severity']] = stats_by_severity.get(det['severity'], 0) + 1

            stats = {
                'total_detections': len(aggregated_detections_for_report),
                'by_model': stats_by_model,
                'by_category': stats_by_category,
                'by_severity': stats_by_severity
            }

            # Prepare metadata using USER-SELECTED names
            report_metadata = {
                'task_id': task_id,
                'analysis_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'model_id': model_id, # User Display Name
                'review_mode': review_mode, # User Display Name
                'original_pdf': os.path.basename(original_pdf_path),
                'sub_models_info': [model_name_placeholder], # Indicate simulation
                'target_zoom': target_zoom, 'tile_size': tile_size, 'overlap_ratio': overlap_ratio,
            }

            # Call the report generator (should work with simulated data)
            create_markdown_report(
                task_id=task_id, output_dir=output_dir, metadata=report_metadata,
                aggregated_detections=aggregated_detections_for_report,
                stats=stats, target_zoom=target_zoom
            )
        except Exception as report_e:
            print(f"\nError during detailed report generation: {report_e}")
            import traceback; traceback.print_exc()

    except Exception as e:
        print(f"\nAn critical error occurred during simulation processing: {str(e)}")
        import traceback; traceback.print_exc()

    finally:
        # No models to release in simulation
        import gc; gc.collect()
        print("Garbage collection triggered.")

    print(f"--- SIMULATED Map Prediction Task {task_id} Finished ---")


if __name__ == "__main__":
    # --- Configuration for Example Run ---
    task_id_main = 61 # Use a task ID where demo.txt exists
    # IMPORTANT: Ensure F:/local_server/ai_mapcheck/tasks/task_{task_id_main}/original/原地图.pdf exists
    # IMPORTANT: Ensure F:/local_server/ai_mapcheck/tasks/task_{task_id_main}/review/demo.txt exists

    # --- User Selections (Still needed for report headers) ---
    selected_model_id = "Manual Annotation" # Or keep original selection for display
    selected_review_mode = "Manual Review Simulation" # Or keep original

    # --- Execution ---
    predict_map_layers_simulation( # Call the simulation function
        task_id=task_id_main,
        model_id=selected_model_id, # Pass selection for reporting
        review_mode=selected_review_mode, # Pass selection for reporting
        # Optional params like tile_size, target_zoom can be passed if needed
    )
