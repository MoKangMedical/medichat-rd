import Taro from "@tarojs/taro"

const API_BASE =
  process.env.TARO_APP_API_BASE || "https://medichatrd.cloud/api/v1/mp"

export async function apiRequest(options) {
  const response = await Taro.request({
    url: `${API_BASE}${options.url}`,
    method: options.method || "GET",
    data: options.data,
    header: {
      "Content-Type": "application/json",
      ...(options.token ? { Authorization: `Bearer ${options.token}` } : {})
    }
  })

  if (response.statusCode < 200 || response.statusCode >= 300) {
    throw new Error(`API ${options.url} failed with ${response.statusCode}`)
  }

  return response.data
}
