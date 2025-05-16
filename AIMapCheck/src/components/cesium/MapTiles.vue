<template>
  <div class="map-container" ref="mapContainer"></div>
</template>

<script setup lang="ts">
import { onMounted, ref, onBeforeUnmount } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = defineProps<{
  taskId: number;
  fileUrl: string;
}>()



const mapContainer = ref<HTMLElement | null>(null)
let map: L.Map | null = null



// 加载地图瓦片
const loadMapTiles = async () => {
  
  try {
    const imageBounds = [[30.533333, 114.350000], [30.547222 , 114.372222]];
    // 创建自定义图层
    const imageOverlay = L.imageOverlay(
      props.fileUrl,
      imageBounds,
      {
        opacity: 1,
        zIndex: 20,
        interactive: true
      }
    )
    
    if (map) {
      // 添加图层
      imageOverlay.addTo(map)
      
      // 缩放到图层范围
      map.fitBounds(imageBounds)

    }
  } catch (error) {
    console.error('加载地图瓦片失败:', error)
  }
}

// 初始化地图
onMounted(() => {
  if (mapContainer.value) {
    // 创建地图实例
    map = L.map(mapContainer.value, {
      center: [0, 0],
      zoom: 2,
      crs: L.CRS.EPSG3857, // 使用Web墨卡托投影
      preferCanvas: true
    })
    
    // 添加OpenStreetMap底图（可选）
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(map)
    
    // 加载地图瓦片
    loadMapTiles()
  }
})

// 清理资源
onBeforeUnmount(() => {
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<style>
.map-container {
  width: 100%;
  height: 100%;
  position: relative;
}
</style>
