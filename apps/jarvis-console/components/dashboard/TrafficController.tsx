"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'

interface TrafficControllerProps {
    metrics: any
}

const data = [
    { name: 'Local (Lemonade)', value: 400, color: '#10b981' }, // Emerald-500
    { name: 'Cloud (Gemini)', value: 100, color: '#3b82f6' },   // Blue-500
    { name: 'Cloud (Azure)', value: 50, color: '#0ea5e9' },     // Sky-500
];

export function TrafficController({ metrics }: TrafficControllerProps) {
    return (
        <Card className="col-span-1 md:col-span-2">
            <CardHeader>
                <CardTitle>Traffic Controller</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="h-[200px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={data}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={80}
                                paddingAngle={5}
                                dataKey="value"
                            >
                                {data.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Pie>
                            <Tooltip />
                        </PieChart>
                    </ResponsiveContainer>
                </div>
                <div className="mt-4 flex justify-center gap-4 text-sm text-muted-foreground">
                    <div className="flex items-center gap-2">
                        <div className="h-3 w-3 rounded-full bg-emerald-500" />
                        Local
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="h-3 w-3 rounded-full bg-blue-500" />
                        Gemini
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="h-3 w-3 rounded-full bg-sky-500" />
                        Azure
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}
