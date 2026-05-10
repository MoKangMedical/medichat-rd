import { Button, Text, View } from "@tarojs/components"
import Taro, { useDidShow } from "@tarojs/taro"
import { useState } from "react"

import { apiRequest } from "@/services/api"
import { ensureSession } from "@/services/auth"

type HomePayload = {
  patient_name: string
  journey_stage: string
  next_actions: string[]
  spotlight_disease: string
  live_rooms: Array<{ title: string; schedule: string; summary: string }>
}

export default function HomePage() {
  const [data, setData] = useState<HomePayload | null>(null)

  useDidShow(() => {
    void (async () => {
      const token = await ensureSession()
      const result = await apiRequest<HomePayload>({
        url: "/home",
        token
      })
      setData(result)
    })()
  })

  return (
    <View className="page-shell">
      <View className="hero-card">
        <Text className="page-title">让患者先被接住，再开始诊断。</Text>
        <Text className="page-subtitle">
          小程序首页先做患者中枢、欢迎房、随访提醒，避免把复杂科研界面直接塞进微信。
        </Text>
        <View className="pill-row">
          <Text className="pill">患者中枢</Text>
          <Text className="pill">欢迎房</Text>
          <Text className="pill">AI 分身</Text>
        </View>
      </View>

      <Text className="section-title">今天先做什么</Text>
      <View className="action-grid">
        <View className="action-card">
          <Text className="action-title">开始 DeepRare 初筛</Text>
          <Text className="action-desc">先采症状，再出风险提示和检查建议。</Text>
          <Button className="primary-button" onClick={() => Taro.switchTab({ url: "/pages/deeprare/index" })}>
            进入初筛
          </Button>
        </View>
        <View className="action-card">
          <Text className="action-title">记录今日随访</Text>
          <Text className="action-desc">把今天的症状、情绪和依从性收进患者轨迹。</Text>
          <Button className="secondary-button" onClick={() => Taro.switchTab({ url: "/pages/checkin/index" })}>
            去打卡
          </Button>
        </View>
      </View>

      {data ? (
        <>
          <Text className="section-title">患者概览</Text>
          <View className="panel-card">
            <Text className="panel-title">{data.patient_name}</Text>
            <Text className="panel-desc">当前阶段：{data.journey_stage}</Text>
            <Text className="panel-desc">聚焦病种：{data.spotlight_disease}</Text>
            <View className="pill-row">
              {data.next_actions.map((item) => (
                <Text key={item} className="pill">
                  {item}
                </Text>
              ))}
            </View>
          </View>

          <Text className="section-title">直播与病友房</Text>
          <View className="list-stack">
            {data.live_rooms.map((room) => (
              <View key={room.title} className="panel-card room-highlight">
                <Text className="panel-title">{room.title}</Text>
                <Text className="meta-line">{room.schedule}</Text>
                <Text className="panel-desc">{room.summary}</Text>
              </View>
            ))}
          </View>
        </>
      ) : null}
    </View>
  )
}
