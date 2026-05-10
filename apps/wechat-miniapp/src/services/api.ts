import Taro from "@tarojs/taro"

const API_BASE =
  process.env.TARO_APP_API_BASE || "https://medichatrd.cloud/api/v1/mp"

type RequestOptions<T> = {
  url: string
  method?: "GET" | "POST"
  data?: T
  token?: string
}

export async function apiRequest<TResponse, TPayload = Record<string, unknown>>(
  options: RequestOptions<TPayload>
): Promise<TResponse> {
  const response = await Taro.request<TResponse>({
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
