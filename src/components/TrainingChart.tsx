import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function TrainingChart() {
  const [data, setData] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/outputs/history.json')
      .then(res => {
        if (!res.ok) {
          if (res.status === 404) throw new Error('Training history not found');
          throw new Error('Failed to load history');
        }
        const contentType = res.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
          throw new Error('Received invalid response format');
        }
        return res.json();
      })
      .then(data => {
        // Transform data for recharts
        // data is { train_loss: [], train_acc: [], val_acc: [] }
        if (!data.train_loss) throw new Error('Invalid data structure');
        const formatted = data.train_loss.map((loss: number, i: number) => ({
          epoch: i + 1,
          train_loss: loss,
          train_acc: data.train_acc[i],
          val_acc: data.val_acc[i]
        }));
        setData(formatted);
      })
      .catch(err => {
        console.error("Failed to load history:", err);
        setError(err.message);
      });
  }, []);

  if (error) return <p className="text-[var(--secondary-text)] italic">{error}</p>;
  if (data.length === 0) return <p className="text-[var(--secondary-text)] italic">Training in progress or no data...</p>;

  return (
    <div className="h-64 w-full bg-[var(--card-bg)] p-4 rounded-xl border border-[var(--primary-color)]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#444" />
          <XAxis dataKey="epoch" stroke="#888" />
          <YAxis stroke="#888" />
          <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none' }} />
          <Legend />
          <Line type="monotone" dataKey="train_loss" name="Train Loss" stroke="#ef4444" strokeWidth={2} />
          <Line type="monotone" dataKey="train_acc" name="Train Acc %" stroke="#22c55e" strokeWidth={2} />
          <Line type="monotone" dataKey="val_acc" name="Val Acc %" stroke="#3b82f6" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
