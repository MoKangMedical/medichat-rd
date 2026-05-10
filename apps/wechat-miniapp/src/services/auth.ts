import Taro from "@tarojs/taro"

import { apiRequest } from "./api"

const TOKEN_KEY = "medichat_mp_token"

type LoginResponse = {
  access_token: string
  user_id: string
  patient_id: string
  expires_in: number
}

export async function ensureSession() {
  const cached = Taro.getStorageSync<string>(TOKEN_KEY)
  if (cached) {
    return cached
  }

  const loginResult = await Taro.login()
  if (!loginResult.code) {
    throw new Error("wechat login code missing")
  }

  const data = await apiRequest<LoginResponse, { code: string }>(
    {
      url: "/auth/login",
      method: "POST",
      data: { code: loginResult.code }
    }
  )

  Taro.setStorageSync(TOKEN_KEY, data.access_token)
  return data.access_token
}
