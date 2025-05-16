from PIL import Image

# 打开图片
image_path = "C:/Users/nan/Downloads/生成 AI 地图智能审查 logo (1).png"  # 替换为你的图片路径
image = Image.open(image_path).convert("RGBA")  # 确保图片是 RGBA 模式（支持透明度）

# 将黑色部分替换为透明
pixels = image.load()
for x in range(image.width):
    for y in range(image.height):
        r, g, b, a = pixels[x, y]
        # 如果颜色接近黑色（可以根据需要调整阈值）
        if r < 50 and g < 50 and b < 50:
            pixels[x, y] = (0, 0, 0, 0)  # 设置为透明

# 保存修改后的图片
output_path = "output_logo.png"
image.save(output_path)
print(f"处理后的图片已保存到 {output_path}")