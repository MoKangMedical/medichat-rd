import { Button, Slider, Text, Textarea, View } from "@tarojs/components"
import Taro from "@tarojs/taro"
import { useState } from "react"

import { apiRequest } from "@/services/api"
import { ensureSession } from "@/services/auth"

export default function CheckinPage() {
  const [symptomScore, setSymptomScore] = useState(50)
  const [moodScore, setMoodScore] = useState(50)
  const [note, setNote] = useState("")

  async function submit() {
    const token = await ensureSession()
    await apiRequest({
      url: "/followup/checkin",
      method: "POST",
      token,
      data: { symptom_score: symptomScore, mood_score: moodScore, note }
    })
    Taro.showToast({ title: "已记录", icon: "success" })
  }

  return (
    <View className="page-shell">
      <View className="hero-card">
        <Text className="page-title">随访不是表单，是连续的患者轨迹。</Text>
        <Text className="page-subtitle">小程序适合做轻量打卡、提醒、复诊前收集，不适合塞过长的病历编辑器。</Text>
      </View>

      <Text className="section-title">今日打卡</Text>
      <View className="panel-card">
        <Text className="panel-title">症状波动</Text>
        <Slider min={0} max={100} step={5} value={symptomScore} onChange={(e) => setSymptomScore(e.detail.value)} />
        <Text className="panel-desc">当前评分：{symptomScore}</Text>

        <Text className="panel-title" style="margin-top: 18px;">情绪状态</Text>
        <Slider min={0} max={100} step={5} value={moodScore} onChange={(e) => setMoodScore(e.detail.value)} />
        <Text className="panel-desc">当前评分：{moodScore}</Text>

        <Text className="label-muted">补充说明</Text>
        <Textarea
          value={note}
          onInput={(e) => setNote(e.detail.value)}
          maxlength={300}
          placeholder="例如：今天乏力明显，午后吞咽较差，晚上情绪紧张。"
          style="width: 100%; min-height: 160px; margin-top: 12px;"
        />

        <Button className="primary-button" onClick={submit}>
          保存打卡
        </Button>
      </View>
    </View>
  )
}
