"use client"

import { HUD } from "@/components/dashboard/HUD"
import { TrafficController } from "@/components/dashboard/TrafficController"
import { ConfigPanel } from "@/components/dashboard/ConfigPanel"
import { useEffect, useState } from "react"
// import axios from "axios"

export default function Dashboard() {
  const [status, setStatus] = useState<any>({
    is_healthy: true,
    metrics: {},
    system_info: {
      memory_pressure: 45,
      gpu_util: 12,
      vram_util: 68
    }
  })

  // Poll for status
  useEffect(() => {
    const interval = setInterval(() => {
      // fetch("http://localhost:8000/api/v1/dashboard/status")
      //     .then(res => res.json())
      //     .then(data => setStatus(data))
      //     .catch(err => console.error(err))
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Jarvis Console</h2>
      </div>

      <HUD systemInfo={status.system_info} health={status.is_healthy} />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <TrafficController metrics={status.metrics} />
        <ConfigPanel />
      </div>
    </div>
  )
}
