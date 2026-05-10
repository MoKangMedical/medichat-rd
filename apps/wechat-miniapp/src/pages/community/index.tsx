import { Button, Text, View } from "@tarojs/components"
import Taro, { useDidShow } from "@tarojs/taro"
import { useState } from "react"

import { apiRequest } from "@/services/api"
import { ensureSession } from "@/services/auth"

type FeedItem = {
  id: string
  author: string
  disease: string
  post_type: string
  summary: string
}

export default function CommunityPage() {
  const [items, setItems] = useState<FeedItem[]>([])

  useDidShow(() => {
    void (async () => {
      const token = await ensureSession()
      const data = await apiRequest<{ feed: FeedItem[] }>({
        url: "/community/feed",
        token
      })
      setItems(data.feed)
    })()
  })

  async function createAvatar() {
    const token = await ensureSession()
    await apiRequest<{ status: string }>({
      url: "/avatar/create",
      method: "POST",
      token
    })
    Taro.showToast({ title: "分身已创建", icon: "success" })
  }

  return (
    <View className="page-shell">
      <View className="hero-card">
        <Text className="page-title">先让患者进入欢迎房，而不是独自面对结果。</Text>
        <Text className="page-subtitle">首版小程序里，社群只保留欢迎房、家长圆桌和试验追踪三个高频入口。</Text>
        <Button className="primary-button" onClick={createAvatar}>
          创建 AI 分身
        </Button>
      </View>

      <Text className="section-title">病友动态</Text>
      <View className="list-stack">
        {items.map((item) => (
          <View key={item.id} className="panel-card">
            <Text className="panel-title">{item.author}</Text>
            <Text className="meta-line">{item.disease} · {item.post_type}</Text>
            <Text className="panel-desc">{item.summary}</Text>
          </View>
        ))}
      </View>
    </View>
  )
}
