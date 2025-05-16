import os
import fitz  # PyMuPDF
from PIL import Image
import numpy as np
import math
import json
import re

class MapTiler:
    def __init__(self, pdf_path, output_dir, tile_size=640, overlap_ratio=0.2):
        """
        初始化地图分块器
        
        Args:
            pdf_path: PDF文件路径
            output_dir: 输出目录
            tile_size: 瓦片大小，默认1024x1024像素
            overlap_ratio: 瓦片重叠比例，默认0.2（20%）
        """
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        self.tile_size = tile_size
        self.overlap_ratio = overlap_ratio
        self.overlap_size = int(tile_size * overlap_ratio)
        # 缩放级别对应的 DPI 倍数
        self.zoom_levels = {
            0.5: 72,
            1: 144,
            2: 288,
            4: 576
        }
        
    def process_map(self):
        """处理地图，生成不同缩放级别的瓦片"""
        try:
                
            # 打开PDF文件
            doc = fitz.open(self.pdf_path)
            page = doc[0]  # 假设地图在第一页
            
            # 为每个缩放级别生成瓦片
            for zoom, dpi in self.zoom_levels.items():
                # 根据 DPI 计算缩放矩阵
                matrix = fitz.Matrix(dpi/72.0, dpi/72.0)
                pix = page.get_pixmap(matrix=matrix)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # 生成瓦片
                self._generate_tiles_for_zoom(img, zoom)
                
                # 保存完整图像
                full_image_path = os.path.join(self.output_dir, f"zoom_{zoom}", "full_image.jpg")
                img.save(full_image_path, "JPEG", quality=95)
                
            doc.close()
            return True, "地图分块完成"
            
        except Exception as e:
            return False, f"地图分块失败: {str(e)}"
            
    def _generate_tiles_for_zoom(self, img, zoom):
        """
        为特定缩放级别生成瓦片
        
        Args:
            img: 原始图像（已经是当前缩放级别的高清图像）
            zoom: 缩放级别
        """
        # 创建缩放级别目录
        zoom_dir = os.path.join(self.output_dir, f"zoom_{zoom}")
        os.makedirs(zoom_dir, exist_ok=True)
        
        # 计算有效瓦片大小（考虑重叠）
        effective_tile_size = self.tile_size - self.overlap_size
        
        # 计算行列数
        cols = math.ceil(img.width / effective_tile_size)
        rows = math.ceil(img.height / effective_tile_size)
        
        
        # 生成瓦片
        for row in range(rows):
            for col in range(cols):
                # 计算基础瓦片边界
                left = col * effective_tile_size
                top = row * effective_tile_size
                
                # 添加重叠区域
                if col > 0:  # 不是第一列，左边需要重叠
                    left -= self.overlap_size
                if row > 0:  # 不是第一行，上边需要重叠
                    top -= self.overlap_size
                    
                # 计算右下角坐标（包含重叠）
                right = min(left + self.tile_size, img.width)
                bottom = min(top + self.tile_size, img.height)
                
                # 提取瓦片
                tile = img.crop((left, top, right, bottom))
                
                # 如果瓦片尺寸不完整，填充白色背景
                if tile.size != (self.tile_size, self.tile_size):
                    new_tile = Image.new('RGB', (self.tile_size, self.tile_size), 'white')
                    new_tile.paste(tile, (0, 0))
                    tile = new_tile
                
                # 保存瓦片
                tile_name = f"tile_{row}_{col}"
                tile_path = f"{tile_name}.jpg"
                tile.save(os.path.join(zoom_dir, tile_path), "JPEG", quality=95)

def process_map_tiles(task_id, pdf_path):
    """
    处理地图瓦片的主函数
    
    Args:
        task_id: 任务ID
        pdf_path: PDF文件路径
        
    Returns:
        tuple: (成功标志, 消息, 瓦片信息)
    """
    try:
        # 创建输出目录
        output_dir = os.path.join("/local_server/ai_mapcheck/tasks", f"task_{task_id}", "tiles")
        os.makedirs(output_dir, exist_ok=True)
        
        # 创建分块器并处理地图
        tiler = MapTiler(pdf_path, output_dir)
        tiler.process_map()
        return True, "地图分块成功"
    
    except Exception as e:
        return False, f"处理失败: {str(e)}", None

# 使用示例：
if __name__ == "__main__":
    # 测试代码
    test_pdf = "C:/Users/nan/Desktop/道路房屋.pdf"
    test_task_id = 1
    success, message = process_map_tiles(test_task_id, test_pdf)
    print(f"处理结果: {message}")

