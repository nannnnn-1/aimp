# report_generator.py
import os
from datetime import datetime
import json # Or whichever format you use for error_examples
from config import Config
import mysql.connector
# --- Helper Functions ---
def get_db_connection():
    return mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME
    )
def load_error_examples():
    """从数据库加载错误样例数据"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)  # 使用dictionary=True来获取字典格式的结果
        cursor.execute("""
            SELECT error_type, error_category, severity, description, solution, 
                   CONCAT('/local_server/ai_mapcheck/error_examples/', image_before_url) as image_before_url,
                   CONCAT('/local_server/ai_mapcheck/error_examples/', image_after_url) as image_after_url
            FROM error_examples
        """)
        examples = cursor.fetchall()
        examples_map = {item['error_type']: item for item in examples}
        print(f"从数据库加载了 {len(examples_map)} 个错误样例类型。")
        return examples_map
    except mysql.connector.Error as e:
        print(f"数据库错误: {e}")
        return {}
    except Exception as e:
        print(f"加载错误样例时发生错误: {e}")
        return {}
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def format_metadata_md(metadata):
    """格式化元数据为 Markdown"""
    lines = ["## 1. 报告元数据", ""]
    lines.append(f"- **任务 ID:** {metadata.get('task_id', 'N/A')}")
    lines.append(f"- **分析时间:** {metadata.get('analysis_time', 'N/A')}")
    lines.append(f"- **原始地图文件:** `{metadata.get('original_pdf', 'N/A')}`")
    if metadata.get('layer_configs'):
         lines.append("- **分析图层与模型:**")
         for layer_key, config in metadata.get('layer_configs', {}).items():
              lines.append(f"  - **图层:** `{config.get('pdf_path', 'N/A')}`")
              lines.append(f"    - **使用模型:** `{config.get('model_name', config.get('model_path', 'N/A'))}`")
              lines.append(f"    - **置信度阈值:** {config.get('conf_threshold', 'N/A')}")
    lines.append(f"- **瓦片大小/重叠率:** {metadata.get('tile_size', 'N/A')} / {metadata.get('overlap_ratio', 'N/A')}")
    lines.append("")
    return "\n".join(lines)

def format_summary_md(stats):
    """格式化执行摘要为 Markdown"""
    lines = ["## 2. 执行摘要", ""]
    lines.append(f"- 本次分析共检测到 **{stats.get('total_detections', 0)}** 个潜在错误点。")


    category_counts = stats.get('by_category', {})
    if category_counts:
        lines.append("- **主要错误类别分布:**")
        # Sort categories by count, descending
        sorted_categories = sorted(category_counts.items(), key=lambda item: item[1], reverse=True)
        for category, count in sorted_categories:
            lines.append(f"  - {category}: {count} 个")
            
    severity_counts = stats.get('by_severity', {})
    if severity_counts:
        lines.append("- **按严重性分布:**")
        for severity, count in severity_counts.items():
             lines.append(f"  - {severity}: {count} 个")

    # Add key findings and recommendations if available/generated
    # lines.append("- **关键发现:** ...")
    # lines.append("- **建议:** ...")
    lines.append("")
    return "\n".join(lines)

def format_overview_md(task_id,overall_map_relative_path):
    """格式化概览部分为 Markdown"""
    lines = ["## 3. 整体错误分布概览", ""]
    lines.append("下图展示了所有检测到的错误在原始地图上的分布情况：")
    # Assuming the MD file is in the same directory as the image
    original_error_image_path = f"/api/tasks/{task_id}/review/original_error_image/{overall_map_relative_path}"
    lines.append(f"![整体错误分布图]({original_error_image_path})")
    lines.append("")
    # Heatmap mention (optional enhancement)
    # lines.append("*注：未来可考虑增加错误热力图以更直观地展示错误密集区域。*")
    lines.append("")
    return "\n".join(lines)

def format_stats_charts_md(stats):
    """格式化统计图表部分为 Markdown (文本描述)"""
    lines = ["## 4. 统计分析", ""]
    lines.append("以下是本次检测结果的详细统计数据：")

    category_counts = stats.get('by_category', {})
    if category_counts:
        lines.append("\n### 错误类别统计:")
        sorted_categories = sorted(category_counts.items(), key=lambda item: item[1], reverse=True)
        for category, count in sorted_categories:
            lines.append(f"- **{category}:** {count} 个")

    severity_counts = stats.get('by_severity', {})
    if severity_counts:
        lines.append("\n### 严重性统计:")
        for severity, count in severity_counts.items():
            lines.append(f"- **{severity}:** {count} 个")
            
    # model_counts = stats.get('by_model', {})
    # if model_counts:
    #     lines.append("\n### 检测模型统计:")
    #     total = stats.get('total_detections', 1) # Avoid division by zero
    #     for model_name, count in model_counts.items():
    #          percentage = (count / total * 100) if total > 0 else 0
    #          lines.append(f"- **{model_name}:** {count} 个 ({percentage:.1f}%)")

    lines.append("")
    return "\n".join(lines)

def format_details_table_md(task_id,aggregated_detections):
    """格式化详细错误列表为 Markdown 表格"""
    lines = ["## 5. 详细错误列表", ""]
    if not aggregated_detections:
        lines.append("未检测到错误。")
        lines.append("")
        return "\n".join(lines)

    # Table Header
    lines.append("| ID | 错误类型 | 类别 | 严重性 | 置信度 | 位置 (中心点 x, y) | 快照链接 |")
    lines.append("|----|----------|------|--------|----------|----------------------|----------|")

    # Table Rows
    for det in aggregated_detections:
        det_id = det.get('id', 'N/A')
        error_type = det.get('cls_name', 'N/A')
        category = det.get('error_category', 'N/A')
        severity = det.get('severity', 'N/A')
        confidence = f"{det.get('conf', 0):.2f}"

        # Calculate center point from bbox
        x1, y1, x2, y2 = det.get('box_orig_px', (0,0,0,0))
        center_x = int((x1 + x2) / 2)
        center_y = int((y1 + y2) / 2)
        location = f"{center_x}, {center_y}"

        # Link to snapshot (assuming snapshot files exist)
        snapshot_filename = det.get('snapshot_relative_path') # Need to generate this filename
        snapshot_relative_path = f"/api/tasks/{task_id}/review/error_tiles/{snapshot_filename}"
        snapshot_link = f"[查看]({snapshot_relative_path})" if det.get('snapshot_relative_path') else "无"

        lines.append(f"| {det_id} | {error_type} | {category} | {severity} | {confidence}| {location} | {snapshot_link} |")

    lines.append("")
    return "\n".join(lines)

def format_snapshots_md(task_id,aggregated_detections, error_tile_relative_dir):
    """格式化错误点快照部分为 Markdown"""
    lines = ["## 6. 错误点快照详情", ""]
    if not aggregated_detections:
        lines.append("无错误点快照。")
        lines.append("")
        return "\n".join(lines)

    # Limit snapshots shown directly in the report or just link from table?
    # Let's add a section with links and maybe first few images
    lines.append("以下是部分检测到的错误点快照（点击详细列表中的链接查看对应快照）：")
    lines.append("")

    count = 0
    max_snapshots_to_show = 5 # Limit inline display

    for det in aggregated_detections:
         snapshot_path = det.get('snapshot_relative_path')
         snapshot_relative_path = f"/api/tasks/{task_id}/review/error_tiles/{snapshot_path}"
         if snapshot_path:
              if count < max_snapshots_to_show:
                  lines.append(f"### 快照 ID: {det.get('id')}")
                  lines.append(f"- **错误类型:** {det.get('cls_name', 'N/A')} ({det.get('error_category', 'N/A')})")
                  lines.append(f"- **严重性:** {det.get('severity', 'N/A')}")
                  lines.append(f"![快照 {det.get('id')}]({snapshot_relative_path})")
                  lines.append("---") # Separator
                  count += 1
              # Store link info even if not displayed inline
              # (Already done via 'snapshot_relative_path' in aggregated_detections)
         else:
              # Handle cases where snapshot wasn't generated/found
              pass
              
    if len(aggregated_detections) > max_snapshots_to_show:
        lines.append(f"\n*报告中仅展示前 {max_snapshots_to_show} 个快照，请查阅详细列表中的链接获取所有快照。*")

    lines.append("")
    return "\n".join(lines)

# --- Main Function ---

def create_markdown_report(task_id, output_dir, metadata, aggregated_detections, stats, target_zoom):
    """
    生成 Markdown 格式的详细分析报告.

    Args:
        task_id: 任务ID
        output_dir: 报告保存目录
        metadata: 包含任务、模型、参数等信息的字典
        aggregated_detections: 处理过并包含补充信息的检测结果列表
        stats: 统计数据字典
        target_zoom: 目标缩放级别
    """
    print("--- Generating Detailed Markdown Report (Report 2) ---")
    start_time = datetime.now()

    # Define relative paths for resources (images, etc.)
    # Assuming the MD file will be saved in output_dir
    overall_map_relative_path = f"combined_prediction_original_zoom{target_zoom}.jpg"
    error_tile_relative_dir = f"predicted_error_tiles_zoom{target_zoom}"

    # Add snapshot paths to detection details (relative to output_dir)
    for det in aggregated_detections:
         # Construct snapshot filename based on how they are saved in map_prediction.py
         # Example: Assumes they are saved like 'error_tile_rowX_colY.jpg' or similar
         # This logic needs to match the saving logic!
         tile_ref = det.get('tile_ref') # e.g., 'row3_col5' - needs to be added during aggregation
         if tile_ref: # If tile reference is available
            snapshot_filename = f"error_tile_{tile_ref}.jpg" 
            potential_path = os.path.join(error_tile_relative_dir, snapshot_filename)
            # Check if the snapshot file actually exists relative to the output_dir
            if os.path.exists(os.path.join(output_dir, potential_path)):
                 det['snapshot_relative_path'] = snapshot_filename
            else:
                 det['snapshot_relative_path'] = None # Or indicate missing
                 # print(f"Snapshot file not found: {potential_path}")
         else: # Fallback or alternative naming if tile_ref isn't used/available
            # Maybe use det['id']? snapshot_filename = f"error_snapshot_{det['id']}.jpg" 
            # IMPORTANT: Ensure consistency with how snapshots are saved!
             det['snapshot_relative_path'] = None 


    markdown_content = []
    markdown_content.append(f"# 地图质量检测详细分析报告 (Task ID: {task_id})")
    markdown_content.append("")

    # 1. Metadata
    markdown_content.append(format_metadata_md(metadata))

    # 2. Summary
    markdown_content.append(format_summary_md(stats))

    # 3. Overview
    markdown_content.append(format_overview_md(task_id, overall_map_relative_path))

    # 4. Statistics
    markdown_content.append(format_stats_charts_md(stats))

    # 5. Details Table
    markdown_content.append(format_details_table_md(task_id, aggregated_detections))

    # 6. Snapshots
    markdown_content.append(format_snapshots_md(task_id, aggregated_detections, error_tile_relative_dir))


    # --- Save the Report ---
    try:
        report_filename = f"detailed_analysis_report_zoom{target_zoom}.md"
        report_path = os.path.join(output_dir, report_filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(markdown_content))
        
        end_time = datetime.now()
        print(f"Markdown detailed report saved to: {report_path}")
        print(f"Report generation took: {end_time - start_time}")
        return True, report_path

    except Exception as e:
        print(f"Error saving Markdown report: {e}")
        return False, None
