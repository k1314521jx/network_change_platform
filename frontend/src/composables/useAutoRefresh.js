import { onUnmounted } from 'vue'

export function useAutoRefresh(callback, intervalMs = 5000) {
  let timer = null

  function start() {
    stop()
    callback()
    timer = setInterval(() => callback(true), intervalMs)
  }

  function stop() {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  onUnmounted(stop)

  return { start, stop }
}
