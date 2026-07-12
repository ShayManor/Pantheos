import {
  Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";

export default function AreaSpark({ data, color = "#0F7A4B", height = 120, yWidth = 40, gid = "gspark" }) {
  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 4, right: 4, left: -24, bottom: 0 }}>
          <defs>
            <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.16} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#E4E8ED" vertical={false} />
          <XAxis dataKey="d" tick={{ fontFamily: "var(--mono)", fontSize: 10, fill: "#8E99A4" }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fontFamily: "var(--mono)", fontSize: 10, fill: "#8E99A4" }} axisLine={false} tickLine={false} width={yWidth} />
          <Tooltip contentStyle={{ fontFamily: "var(--mono)", fontSize: 11, borderRadius: 8, border: "1px solid #E4E8ED" }} />
          <Area type="monotone" dataKey="v" stroke={color} strokeWidth={2} fill={`url(#${gid})`} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
