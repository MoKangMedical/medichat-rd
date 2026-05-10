import { Text, View } from "@tarojs/components"
import Taro, { useDidShow } from "@tarojs/taro"
import { useState } from "react"

import { apiRequest } from "@/services/api"
import { ensureSession } from "@/services/auth"

type ProfilePayload = {
  patient_id: string
  linked_runtime: string
  secondme_bound: boolean
  followup_enabled: boolean
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<ProfilePayload | null>(null)

  useDidShow(() => {
    void (async () => {
      const token = await ensureSession()
      const data = await apiRequest<ProfilePayload>({
        url: "/profile",
        token
      })
      setProfile(data)
    })()
  })

  return (
    <View className="page-shell">
      <View className="hero-card">
        <Text className="page-title">账号主体系归你自己，SecondMe 只是增强层。</Text>
        <Text className="page-subtitle">这页明确展示 provider 绑定状态，避免把平台主身份绑定死在外部能力上。</Text>
      </View>

      {profile ? (
        <View className="panel-card">
          <Text className="panel-title">患者编号</Text>
          <Text className="panel-desc">{profile.patient_id}</Text>
          <Text className="panel-title" style="margin-top: 18px;">当前分身运行时</Text>
          <Text className="panel-desc">{profile.linked_runtime}</Text>
          <Text className="panel-title" style="margin-top: 18px;">SecondMe 绑定</Text>
          <Text className="panel-desc">{profile.secondme_bound ? "已绑定" : "未绑定"}</Text>
          <Text className="panel-title" style="margin-top: 18px;">随访服务</Text>
          <Text className="panel-desc">{profile.followup_enabled ? "已开启" : "未开启"}</Text>
        </View>
      ) : null}
    </View>
  )
}
