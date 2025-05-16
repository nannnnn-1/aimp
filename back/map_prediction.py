import os
import fitz  # PyMuPDF
from PIL import Image
import numpy as np
import math
import cv2
from ultralytics import YOLO
import re
import shutil # For directory cleanup
from report_generator import create_markdown_report, load_error_examples # Assuming report_generator.py is in the same directory or PYTHONPATH
from datetime import datetime
TASK_FOLDER = 'F:/local_server/ai_mapcheck/tasks'
class MapTiler:
    def __init__(self, pdf_path, output_dir_base, tile_size=640, overlap_ratio=0.2, target_zoom=4, map_type="original"):
        """
        初始化地图分块器
        Args:
            pdf_path: PDF文件路径
            output_dir_base: 任务根输出目录 (e.g., task_XXX)
            tile_size: 瓦片大小
            overlap_ratio: 瓦片重叠比例
            target_zoom: 指定处理的目标缩放级别
            map_type: 'original', 'layer1', or 'layer2' to organize output
        """
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
            4: 576
        }
        if target_zoom not in self.zoom_levels:
            raise ValueError(f"Unsupported zoom level: {target_zoom}. Available levels: {list(self.zoom_levels.keys())}")

        # Create specific output directory for this map type and zoom level
        self.output_dir = os.path.join(output_dir_base, f"tiles_{map_type}_zoom{target_zoom}")
        os.makedirs(self.output_dir, exist_ok=True)
        self.full_image_path = os.path.join(self.output_dir, f"{map_type}_full_image.jpg")
        self.tiles_info = {} # Store tile paths and dimensions

    def process_map_for_target_zoom(self):
        """仅处理目标缩放级别的地图"""
        try:
            print(f"Processing {self.map_type} PDF: {self.pdf_path} for zoom {self.target_zoom}...")
            doc = fitz.open(self.pdf_path)
            page = doc[0]

            dpi = self.zoom_levels[self.target_zoom]
            matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
            pix = page.get_pixmap(matrix=matrix)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            print(f"  - Rendered {self.map_type} image dimensions: {img.width}x{img.height}")


            # 保存完整图像
            img.save(self.full_image_path, "JPEG", quality=95)
            print(f"  - Full image for {self.map_type} zoom {self.target_zoom} saved to {self.full_image_path}")

            # 生成瓦片
            self._generate_tiles(img)
            print(f"  - Generated {len(self.tiles_info.get('tiles', []))} tiles for {self.map_type}.")


            doc.close()
            # Return dimensions along with other info
            dims = {'width': img.width, 'height': img.height}
            return True, f"Map tiling for {self.map_type} zoom {self.target_zoom} completed.", self.full_image_path, self.tiles_info, dims

        except Exception as e:
            return False, f"Map tiling failed for {self.map_type}: {str(e)}", None, None, None

    def _generate_tiles(self, img):
        """为目标缩放级别生成瓦片"""
        effective_tile_size = self.tile_size - self.overlap_size
        cols = math.ceil(img.width / effective_tile_size)
        rows = math.ceil(img.height / effective_tile_size)

        self.tiles_info['dimensions'] = {'width': img.width, 'height': img.height, 'rows': rows, 'cols': cols}
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

    # Add a method to get the matrix used for rendering
    def get_rendering_matrix(self):
        dpi = self.zoom_levels[self.target_zoom]
        return fitz.Matrix(dpi / 72.0, dpi / 72.0)


# --- Fixed Backend Execution Configuration ---
# Defines the *actual* models and layers processed, regardless of user selection
FIXED_EXECUTION_PLAN = {
    # Which PDF layers are *always* required for the fixed process?
    'required_layer_keys': ['original', 'roads', 'roads_with_buildings'], # Example: always need these 3 layers
    # Define the fixed paths for these layers relative to the task base dir
    'layer_pdf_paths': {
        'original': 'original/原地图.pdf',
        'roads': 'analysis/roads_layer.pdf',
        'roads_with_buildings': 'analysis/roads_with_buildings_layer.pdf' 
    },
    # Define the fixed sub-models, their paths, conf, and which layer they process
    'sub_models': [
        {
            'internal_key': 'road_detector', # Unique internal identifier
            'path': 'F:/vue/ai-mapCheck/back/models/sample1.pt', # Fixed path to the model
            'name': '道路检测器', # Fixed internal name for stats/logs/image labels
            'conf': 0.9, # Fixed confidence threshold
            'processes_layer': 'roads' # Which tiled layer this model runs on (must be in required_layer_keys)
        },
        {
            'internal_key': 'building_detector',
            'path': 'F:/vue/ai-mapCheck/back/models/sample2.pt',
            'name': '建筑检测器',
            'conf': 0.80,
            'processes_layer': 'roads_with_buildings' # Runs on the 'buildings' layer tiles
        }
        # Add other fixed sub-models if part of the standard process
    ]
}

def get_reporting_names(model_id, review_mode):
    """Retrieves the display names for the report based on user selection."""
    names = {"display_model_name":model_id,"display_review_mode":review_mode}
    return names

# --- Refactored Main Function ---

def predict_map_layers(
    task_id, 
    model_id,         # User selected Model ID (for reporting)
    review_mode,      # User selected Review Mode (for reporting)
    # --- Optional common parameters ---
    tile_size=640, 
    overlap_ratio=0.2, 
    target_zoom=4,
    # --- Path to error examples ---
    ):
    """
    Processes map layers using a FIXED backend pipeline, performs predictions, 
    and generates results including a detailed Markdown report with user-specified names.
    
    Args:
        task_id: Unique ID for the task.
        model_id: Identifier for the main model selected by the user (used for report display).
        review_mode: Name of the review mode selected by the user (used for report display).
        output_dir_base: Base path for all task outputs.
        tile_size: Size of prediction tiles.
        overlap_ratio: Overlap ratio for tiles.
        target_zoom: Target zoom level for PDF rendering and analysis.
        error_examples_path: Path to the file/resource containing error example details.
    """
    print(f"--- Starting Fixed Map Prediction Task {task_id} ---")
    reporting_names = get_reporting_names(model_id, review_mode)
    print(f"User Selection (for reporting): Model='{reporting_names['display_model_name']}', Mode='{reporting_names['display_review_mode']}'")
    
    # --- Use FIXED execution plan ---
    required_layer_keys = FIXED_EXECUTION_PLAN.get('required_layer_keys', [])
    layer_pdf_rel_paths = FIXED_EXECUTION_PLAN.get('layer_pdf_paths', {})
    fixed_sub_models_config = FIXED_EXECUTION_PLAN.get('sub_models', [])

    if not required_layer_keys or not layer_pdf_rel_paths or not fixed_sub_models_config:
        print("Error: FIXED_EXECUTION_PLAN is incomplete or missing.")
        return

    # --- 1. Setup Paths ---
    output_dir = os.path.join(TASK_FOLDER, f'task_{task_id}', "review") 
    os.makedirs(output_dir, exist_ok=True)
    
    pdf_paths = {}
    try:
        for layer_key in required_layer_keys:
            if layer_key not in layer_pdf_rel_paths:
                 raise ValueError(f"Missing PDF path definition for required layer '{layer_key}' in FIXED_EXECUTION_PLAN")
            relative_path = layer_pdf_rel_paths[layer_key]
            full_path = os.path.join(TASK_FOLDER, f'task_{task_id}', relative_path)
            if not os.path.exists(full_path):
                raise FileNotFoundError(f"Required PDF file for layer '{layer_key}' not found at {full_path}")
            pdf_paths[layer_key] = full_path
    except (FileNotFoundError, ValueError) as e:
         print(f"Error setting up PDF paths: {e}")
         return
         
    print(f"Output Directory: {output_dir}")

    try:
        # --- 2. Tiling Phase (Tile all required layers) ---
        print("--- Starting Tiling Phase ---")
        tilers = {}
        tile_infos = {}
        full_image_paths = {}
        dimensions = {}
        print(required_layer_keys)
        for layer_key in required_layer_keys:
            pdf_path = pdf_paths[layer_key]
            print(f"Tiling layer: {layer_key} from {pdf_path}")
            tiler = MapTiler(pdf_path, output_dir, tile_size, overlap_ratio, target_zoom, layer_key)
            success, msg, fp, ti, dim = tiler.process_map_for_target_zoom()
            
            if not success:
                print(f"Error tiling layer '{layer_key}': {msg}")
            return

            tilers[layer_key] = tiler
            tile_infos[layer_key] = ti
            full_image_paths[layer_key] = fp
            dimensions[layer_key] = dim
            
            # Check consistency vs Original
            if layer_key != 'original':
                if not dimensions.get('original') or not tile_infos.get('original'):
                    print("Error: Original layer failed or wasn't tiled first.")
                    return
                if not (dimensions['original'] == dim and len(tile_infos['original']['tiles']) == len(ti['tiles'])):
                    print(f"Error: Dim/tile count mismatch between '{layer_key}' and 'original'. Check PDF alignment.")
            return

        print("--- Tiling Phase Completed ---")
        img_w = dimensions['original']['width'] 
        img_h = dimensions['original']['height']
        num_tiles = len(tile_infos['original']['tiles']) 

        # --- 3. Load Fixed Sub-Models ---
        print("--- Loading Fixed Sub-Models ---")
        loaded_sub_models = {} # Key: internal_key, Value: {'model': obj, 'name': str, 'conf': float, 'processes_layer': str}
        for sm_config in fixed_sub_models_config:
            model_path = sm_config['path']
            internal_key = sm_config['internal_key']
            model_name = sm_config['name'] # The fixed internal name
            if os.path.exists(model_path):
                try:
                    loaded_sub_models[internal_key] = {
                        'model': YOLO(model_path), 
                        'name': model_name, 
                        'conf': sm_config['conf'],
                        'processes_layer': sm_config['processes_layer']
                    }
                    print(f"Loaded fixed sub-model '{model_name}' ({internal_key})")
                except Exception as e:
                    print(f"Error loading fixed sub-model {internal_key} from {model_path}: {e}")
                    return 
            else:
                print(f"Error: Fixed sub-model path does not exist: {model_path}")
                return 
        
        if not loaded_sub_models:
             print("Error: No fixed sub-models were successfully loaded.")
             return
        print("Fixed sub-models loaded.")

        # --- 4. Prepare Colors and Output Images ---
        print("--- Preparing Output Images ---")
        class_color_map = { "road": (255, 0, 0), "highway": (255, 100, 0), "building": (0, 0, 255), "house": (0, 100, 255), 'default': (128, 128, 128) }
        full_image_orig_bgr = cv2.imread(full_image_paths['original'])
        if full_image_orig_bgr is None: return print("Error: Could not load original full image.")
        output_img_combined = full_image_orig_bgr.copy() 
        error_tile_dir = os.path.join(output_dir, f"predicted_error_tiles_zoom{target_zoom}")
        os.makedirs(error_tile_dir, exist_ok=True)
        print(f"Saving error tiles to: {error_tile_dir}")

        # --- 5. Predict on Tiles using Fixed Models ---
        print("--- Starting Prediction Phase ---")
        all_detections_combined_details = [] 

        for i in range(num_tiles):
            # Get original tile data
            tile_data_orig = tile_infos['original']['tiles'][i]
            tile_path_orig = tile_data_orig['path'] 
            tile_row = tile_data_orig['row'] 
            tile_col = tile_data_orig['col']
            tile_orig_x, tile_orig_y, _, _ = tile_data_orig['orig_coords']
            eff_x, eff_y, eff_x2, eff_y2 = tile_data_orig['effective_coords']

            print(f"Processing tile {i+1}/{num_tiles} (Row: {tile_row}, Col: {tile_col})", end='\r')

            output_error_tile_img = None 
            tile_contains_detection = False
            tile_image_orig_bgr = cv2.imread(tile_path_orig)
            if tile_image_orig_bgr is not None: output_error_tile_img = tile_image_orig_bgr.copy()
            
            # --- Iterate through the LOADED FIXED SUB-MODELS ---
            for internal_key, sub_model_data in loaded_sub_models.items():
                layer_to_process = sub_model_data['processes_layer']
                
                # Check if the required layer was tiled successfully
                if layer_to_process not in tile_infos: 
                    print(f"Warning: Layer '{layer_to_process}' needed by model '{sub_model_data['name']}' was not tiled. Skipping.")
                    continue         

                tile_data_layer = tile_infos[layer_to_process]['tiles'][i]
                tile_path_layer = tile_data_layer['path']
                
                tile_image_layer_bgr = cv2.imread(tile_path_layer)
                if tile_image_layer_bgr is None: continue

                # Perform prediction
                model_obj = sub_model_data['model']
                conf_thresh = sub_model_data['conf']
                fixed_model_name = sub_model_data['name'] # Use the fixed internal name

                results = model_obj(tile_image_layer_bgr, conf=conf_thresh, verbose=False)

                for result in results:
                    # Process results (same logic)
                    boxes = result.boxes.xyxy.cpu().numpy()
                    classes = result.boxes.cls.cpu().numpy().astype(int)
                    confs = result.boxes.conf.cpu().numpy()
                    names = result.names
                    for box, cls_idx, conf in zip(boxes, classes, confs):
                        x1_tile, y1_tile, x2_tile, y2_tile = map(int, box)
                        center_x_tile = (x1_tile + x2_tile) / 2
                        center_y_tile = (y1_tile + y2_tile) / 2
                        center_x_orig = center_x_tile + tile_orig_x
                        center_y_orig = center_y_tile + tile_orig_y

                        if eff_x <= center_x_orig < eff_x2 and eff_y <= center_y_orig < eff_y2:
                            x1_orig = x1_tile + tile_orig_x
                            y1_orig = y1_tile + tile_orig_y
                            x2_orig = x2_tile + tile_orig_x
                            y2_orig = y2_tile + tile_orig_y

                            cls_name = names[cls_idx]
                            color = class_color_map.get(cls_name, class_color_map['default'])
                            # Label uses the FIXED internal model name
                            label = f"{fixed_model_name}:{cls_name} {conf:.2f}" 

                            tile_contains_detection = True
                            # Draw on Combined image & error tile snapshot
                            cv2.rectangle(output_img_combined, (x1_orig, y1_orig), (x2_orig, y2_orig), color, 2)
                            cv2.putText(output_img_combined, label, (x1_orig, y1_orig - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                            if output_error_tile_img is not None:
                                cv2.rectangle(output_error_tile_img, (x1_tile, y1_tile), (x2_tile, y2_tile), color, 2)
                                cv2.putText(output_error_tile_img, label, (x1_tile, y1_tile - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                            # Store details, including the FIXED internal model name
                            all_detections_combined_details.append({
                                'box_orig_px': (x1_orig, y1_orig, x2_orig, y2_orig), 'conf': conf, 'cls_idx': cls_idx, 'cls_name': cls_name,
                                'model_name': fixed_model_name, # Store FIXED internal name
                                'color': color, 'tile_ref': f"row{tile_row}_col{tile_col}" 
                            })

            # --- Save Error Tile Snapshot ---
            if tile_contains_detection and output_error_tile_img is not None:
                error_tile_filename = f"error_tile_row{tile_row}_col{tile_col}.jpg"
                error_tile_path = os.path.join(error_tile_dir, error_tile_filename)
                try: cv2.imwrite(error_tile_path, output_error_tile_img)
                except Exception as write_e: print(f"\nError saving error tile {error_tile_path}: {write_e}")

        print("\n--- Prediction Phase Finished ---")

        # --- 6. Save Combined Result Image ---
        print("--- Saving Combined Output Image ---")
        output_image_combined_filename = f"combined_prediction_original_zoom{target_zoom}.jpg"
        output_image_combined_path = os.path.join(output_dir, output_image_combined_filename)
        cv2.imwrite(output_image_combined_path, output_img_combined)
        print(f"Combined prediction image saved to: {output_image_combined_path}")

        # --- 7. Annotate Original PDF (Report 1) ---
        print("--- Annotating Original PDF (Report 1) --- ")
        try:
            if 'original' not in tilers: raise RuntimeError("Original tiler not available for PDF annotation matrix.")
            matrix_orig = tilers['original'].get_rendering_matrix()
            inv_matrix = ~matrix_orig 
            pdf_doc_path_orig = pdf_paths.get('original')
            pdf_doc = fitz.open(pdf_doc_path_orig)
            if not pdf_doc: raise RuntimeError("Could not open original PDF for annotation.")
            
            page = pdf_doc[0]
            annot_count = 0
            for det in all_detections_combined_details:
                x1_px, y1_px, x2_px, y2_px = det['box_orig_px']
                bgr_color = det['color']
                rgb_float_color = (bgr_color[2]/255.0, bgr_color[1]/255.0, bgr_color[0]/255.0)
                p1 = fitz.Point(x1_px, y1_px) * inv_matrix
                p2 = fitz.Point(x2_px, y2_px) * inv_matrix
                pdf_rect = fitz.Rect(p1.x, p1.y, p2.x, p2.y); pdf_rect.normalize() 
                annot = page.add_rect_annot(pdf_rect)
                annot.set_colors(stroke=rgb_float_color); annot.set_border(width=1.5)
                # Use FIXED internal model name in the annotation popup
                label_text = f"{det['model_name']}:{det['cls_name']} {det['conf']:.2f}"
                annot.set_info(content=label_text); annot.update()
                annot_count += 1
                
            output_annotated_pdf_filename = f"combined_prediction_annotated_zoom{target_zoom}.pdf"
            output_annotated_pdf_path = os.path.join(output_dir, output_annotated_pdf_filename)
            pdf_doc.save(output_annotated_pdf_path, garbage=4, deflate=True); pdf_doc.close()
            print(f"Annotated PDF saved to: {output_annotated_pdf_path} ({annot_count} annotations added)")
        except Exception as e:
            print(f"\nError annotating PDF: {str(e)}")
            import traceback; traceback.print_exc()

        # --- 8. Generate Detailed Markdown Report (Report 2) ---
        print("--- Preparing Data for Detailed Report (Report 2) ---")
        try:
            error_examples_map = load_error_examples() 
            aggregated_detections_for_report = []
            detection_id_counter = 1
            stats_by_internal_model = {} # Stats keyed by FIXED internal name
            stats_by_category = {}
            stats_by_severity = {}

            for det in all_detections_combined_details:
                error_type = det['cls_name']
                example_info = error_examples_map.get(error_type, {})
                aggregated_det = det.copy() 
                aggregated_det['id'] = detection_id_counter
                aggregated_det['error_category'] = example_info.get('error_category', '未知类别')
                aggregated_det['severity'] = example_info.get('severity', '未知') 
                aggregated_det['description'] = example_info.get('description', '-')
                aggregated_det['solution'] = example_info.get('solution', '-')
                aggregated_detections_for_report.append(aggregated_det)
                detection_id_counter += 1

                # Update stats using the FIXED internal model name
                internal_model_name = det['model_name'] 
                category = aggregated_det['error_category']
                severity = aggregated_det['severity']
                stats_by_internal_model[internal_model_name] = stats_by_internal_model.get(internal_model_name, 0) + 1
                stats_by_category[category] = stats_by_category.get(category, 0) + 1
                stats_by_severity[severity] = stats_by_severity.get(severity, 0) + 1

            stats = {
                'total_detections': len(aggregated_detections_for_report),
                'by_model': stats_by_internal_model, # Use internal model stats
                'by_category': stats_by_category,
                'by_severity': stats_by_severity
            }

            # Prepare metadata using USER-SELECTED names from reporting_names
            report_metadata = {
                'task_id': task_id,
                'analysis_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'model_id': reporting_names['display_model_name'], # User Display Name
                'review_mode': reporting_names['display_review_mode'], # User Display Name
                'original_pdf': os.path.basename(pdf_paths.get('original', 'N/A')),
                # Optional: List FIXED internal sub-models used in this run
                'sub_models_info': [f"{sm['name']} (Conf: {sm['conf']})" for sm in fixed_sub_models_config],
                'target_zoom': target_zoom, 'tile_size': tile_size, 'overlap_ratio': overlap_ratio,
            }

            # Call the report generator
            create_markdown_report(
                task_id=task_id, output_dir=output_dir, metadata=report_metadata, 
                aggregated_detections=aggregated_detections_for_report, 
                stats=stats, target_zoom=target_zoom
            )
        except Exception as report_e:
            print(f"\nError during detailed report generation: {report_e}")
            import traceback; traceback.print_exc()

    except Exception as e:
        print(f"\nAn critical error occurred: {str(e)}")
        import traceback; traceback.print_exc()
        
    finally:
        # Release model resources
        if 'loaded_sub_models' in locals():
             for key in loaded_sub_models: del loaded_sub_models[key]['model'] 
        del loaded_sub_models
        import gc; gc.collect() 

    print(f"--- Map Prediction Task {task_id} Finished ---")


if __name__ == "__main__":
    # --- Configuration for Example Run ---
    task_id_main = 49
    # IMPORTANT: This base dir must contain the required PDFs in subdirs 
    # as defined in FIXED_EXECUTION_PLAN['layer_pdf_paths'] before running.
    base_task_dir_main = f"F:/local_server/ai_mapcheck/tasks/task_{task_id_main}" 
    os.makedirs(base_task_dir_main, exist_ok=True) 
    # Example: Ensure F:/local_server/ai_mapcheck/tasks/task_44/original/原地图.pdf exists
    # Example: Ensure F:/local_server/ai_mapcheck/tasks/task_44/analysis/roads_layer.pdf exists
    # Example: Ensure F:/local_server/ai_mapcheck/tasks/task_44/analysis/roads_with_buildings_layer.pdf exists
    
    # --- User Selections (Passed from Frontend/API) ---
    selected_model_id = "generic-map-v1" # Matches key in REPORTING_NAMES_CONFIG
    selected_review_mode = "通用地图分析V1" # Matches key in REPORTING_NAMES_CONFIG
    


    # --- Execution ---
    predict_map_layers(
        task_id=task_id_main,
        model_id=selected_model_id, # Pass user selection for reporting
        review_mode=selected_review_mode, # Pass user selection for reporting
        # Optional params like tile_size, target_zoom can be passed if needed
    )