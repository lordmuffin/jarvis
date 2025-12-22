# Jarvis Console

The **Jarvis Console** is the administrative dashboard for the Jarvis ecosystem. It provides a visual interface for monitoring system health, observing traffic routing, and configuring system behavior.

## Features

- **Hardware HUD**: Real-time visualization of CPU, GPU, VRAM usage, and Server Health.
- **Traffic Controller**: Visualizes the distribution of queries between Local (Lemonade) and Cloud providers.
- **Configuration Panel**: Allows dynamic adjustment of TTFT thresholds and Service URLs.

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Styling**: TailwindCSS
- **Components**: Shadcn/ui (Radix UI) + Lucide React
- **Charting**: Recharts

## Getting Started

1. **Install Dependencies**:
   ```bash
   npm install
   ```

2. **Run Development Server**:
   ```bash
   npm run dev
   ```

   Open [http://localhost:3000](http://localhost:3000) to view the dashboard.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_ROUTER_URL` | URL of the Intelligent Burst Router API |

## Docker

```bash
docker build -t jarvis-console .
docker run -p 3000:3000 jarvis-console
```
