import { Button, Input, Text, Textarea, View } from "@tarojs/components"
import Taro from "@tarojs/taro"
import { useState } from "react"

import { apiRequest } from "@/services/api"
import { ensureSession } from "@/services/auth"

type SubmitResponse = {
  task_id: string
  status: string
  top_diseases: string[]
  suggested_tests: string[]
}

export default function DeepRarePage() {
  const [symptoms, setSymptoms] = useState("")
  const [age, setAge] = useState("")
  const [result, setResult] = useState<SubmitResponse | null>(null)

  async function submit() {
    const token = await ensureSession()
    const data = await apiRequest<SubmitResponse, { symptoms: string; age: string }>(
      {
        url: "/deeprare/submit",
        method: "POST",
        token,
        data: { symptoms, age }
      }
    )
    setResult(data)
  }

  return (
    <View className="page-shell">
      <View className="hero-card">
        <Text className="page-title">把复杂症状先结构化。</Text>
        <Text className="page-subtitle">小程序首版只保留高频输入，不在微信里复刻完整 Web 工作台。</Text>
      </View>

      <Text className="section-title">症状录入</Text>
      <View className="panel-card">
        <Text className="label-muted">年龄</Text>
        <Input value={age} onInput={(e) => setAge(e.detail.value)} placeholder="例如：8岁" />
        <Text className="label-muted">主要症状</Text>
        <Textarea
          value={symptoms}
          onInput={(e) => setSymptoms(e.detail.value)}
          maxlength={500}
          placeholder="例如：反复肌无力、视物重影、步态不稳、吞咽困难"
          style="width: 100%; min-height: 180px; margin-top: 12px;"
        />
        <Button className="primary-button" onClick={submit}>
          提交初筛
        </Button>
      </View>

      {result ? (
        <>
          <Text className="section-title">初筛结果</Text>
          <View className="panel-card">
            <Text className="panel-title">任务 {result.task_id}</Text>
            <Text className="panel-desc">状态：{result.status}</Text>
            <View className="pill-row">
              {result.top_diseases.map((item) => (
                <Text key={item} className="pill">
                  {item}
                </Text>
              ))}
            </View>
            <View className="pill-row">
              {result.suggested_tests.map((item) => (
                <Text key={item} className="pill">
                  {item}
                </Text>
              ))}
            </View>
            <Button
              className="secondary-button"
              onClick={() => Taro.switchTab({ url: "/pages/community/index" })}
            >
              去看病友圈
            </Button>
          </View>
        </>
      ) : null}
    </View>
  )
}
