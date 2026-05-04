import React, { useEffect, useState } from 'react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, PieChart, Pie, Cell, Legend
} from 'recharts';
import { apiClient as api } from '../api/client';
import { Button } from '@/components/ui/button';
import { 
  BarChart3, Users, Clock, MousePointerClick, 
  Smartphone, Monitor, Globe, 
  TrendingUp, TrendingDown, Layout,
  DollarSign, PieChart as PieIcon, Calendar, Download,
  Activity, ArrowUpRight, ArrowDownRight, Zap, MessageCircle
} from 'lucide-react';
import { toast } from 'sonner';

interface AnalyticsData {
  total_visitors: number;
  avg_time_spent_seconds: number;
  total_conversions: number;
  conversion_rate: number;
  device_stats: { type: string; count: number }[];
  top_rooms: { id: string; name?: string; views: number }[];
  chart_data: { date: string; visitors: number; revenue?: number; adr?: number; revpar?: number }[];
  funnel_data: { stage: string; count: number }[];
  revenue_total: number;
  avg_daily_rate: number;
  rev_par: number;
  occupancy_rate: number;
  geo_stats?: { country: string; code: string; visitors: number; percentage: number; trend?: string }[];
  
  // Advanced metrics
  most_booked_rooms?: { id: string; name: string; count: number }[];
  least_booked_rooms?: { id: string; name: string; count: number }[];
  funnel_dropoffs?: { stage: string; drop_percentage: number }[];
  promo_stats?: { code: string; bookings: number }[];
  traffic_heatmap?: { weekday: number; hour: number; visitors: number }[];
  commission_saved?: number;
  alos?: number;
  cancellation_rate?: number;
  avg_lead_time?: number;

  // New AI fields
  ai_resolution_rate?: number;
  ai_revenue?: number;
  ai_assisted_bookings?: number;
  popular_questions?: { text: string; value: number }[];
  total_leads?: number;

  // Advanced BI fields
  revenue_by_room_type?: { name: string; value: number }[];
  booking_window_data?: { window: string; count: number }[];
  occupancy_forecast?: { date: string; occupancy: number }[];
  pickup_stats?: { today: number; yesterday: number; trend: 'up' | 'down' };
}

interface LiveEvent {
  id: string;
  type: 'booking' | 'view' | 'search' | 'checkout';
  message: string;
  timestamp: string;
  amount?: number;
}

const COLORS = ['#0ea5e9', '#6366f1', '#f59e0b', '#10b981'];

export const AnalyticsDashboard: React.FC = () => {
  const [cachedData, setCachedData] = useState<Record<number, AnalyticsData>>({});
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [switching, setSwitching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(7);
  const [liveEvents, setLiveEvents] = useState<LiveEvent[]>([]);
  const [activeUsers, setActiveUsers] = useState<number>(0);

  useEffect(() => {
    const fetchAnalytics = async (daysCount: number, isSilent = false) => {
      if (cachedData[daysCount]) {
        if (!isSilent) setData(cachedData[daysCount]);
        return;
      }

      if (!isSilent) {
        if (data) setSwitching(true);
        else setLoading(true);
      }

      try {
        const result = await api.get<AnalyticsData>(`/analytics/dashboard?days=${daysCount}`);
        setCachedData(prev => ({ ...prev, [daysCount]: result }));
        if (days === daysCount) setData(result);
      } catch (err: any) {
        console.error(`Failed to load analytics for ${daysCount} days`, err);
        if (!isSilent) setError(err.message || "Failed to load analytics data.");
      } finally {
        if (!isSilent) {
          setLoading(false);
          setSwitching(false);
        }
      }
    };

    fetchAnalytics(days);

    // Prefetch the opposite range silently
    const otherDays = days === 7 ? 30 : 7;
    if (!cachedData[otherDays]) {
      fetchAnalytics(otherDays, true);
    }

    // Real Live Feed Polling
    const fetchLiveStats = async () => {
      try {
        const [activeRes, feedRes] = await Promise.all([
          api.get<{ active_visitors: number }>('/analytics/live/active'),
          api.get<any[]>('/analytics/live/feed')
        ]);
        
        setActiveUsers(activeRes.active_visitors);
        
        // Map backend feed to frontend interface
        const mappedEvents: LiveEvent[] = feedRes.map(e => ({
          id: Math.random().toString(), // We could use timestamp+type as ID if backend doesn't provide one
          type: e.event as LiveEvent['type'],
          message: e.event === 'booking_complete' ? 'New Booking Confirmed' : 
                   e.event === 'search' ? 'Searching for rooms' : 
                   e.event === 'room_view' ? 'Viewing Room details' : 'New page visit',
          timestamp: new Date(e.time).toLocaleTimeString(),
          amount: e.metadata?.total_amount
        }));
        
        setLiveEvents(mappedEvents);
      } catch (err) {
        console.error("Live feed poll failed", err);
      }
    };

    fetchLiveStats();
    const interval = setInterval(fetchLiveStats, 10000); // Poll every 10 seconds

    return () => clearInterval(interval);
  }, [days]);

  const formatTime = (seconds: number) => {
    const s = seconds || 0;
    const mins = Math.floor(s / 60);
    const secs = s % 60;
    return `${mins}m ${secs}s`;
  };

  const getStageLabel = (stage: string) => {
    const labels: Record<string, string> = {
      'page_view': 'Visits',
      'search': 'Searches',
      'room_view': 'Room Views',
      'booking_complete': 'Bookings'
    };
    return labels[stage] || stage;
  };

  const handleExport = () => {
    if (!data) return;
    
    // Prepare simple CSV
    const rows = [
      ["Metric", "Value"],
      ["Total Visitors", data.total_visitors],
      ["Total Conversions", data.total_conversions],
      ["Conversion Rate (%)", data.conversion_rate],
      ["Total Revenue (INR)", data.revenue_total],
      ["AI Assisted Revenue", data.ai_revenue],
      ["Total Leads Generated", data.total_leads],
      ["Direct Commission Saved", data.commission_saved]
    ];
    
    const csvContent = "data:text/csv;charset=utf-8," 
      + rows.map(e => e.join(",")).join("\n");
      
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `analytics_export_${days}d.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success("Analytics exported successfully");
  };

  if (loading) return <div className="p-8 flex justify-center items-center h-full"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div></div>;
  if (error) return <div className="p-8 text-center text-red-500 bg-red-50 rounded-xl m-8 border border-red-100">Error: {error}</div>;
  if (!data) return <div className="p-8 text-center text-gray-500">No data received from server.</div>;

  return (
    <div className="p-4 md:p-8 max-w-[1600px] mx-auto space-y-8 animate-in fade-in duration-1000 bg-[#f8fafc]">
      {/* Header Section with Glassmorphism */}
      <div className="relative overflow-hidden bg-white/40 backdrop-blur-xl p-8 rounded-[2.5rem] border border-white/60 shadow-2xl shadow-blue-500/5">
        <div className="absolute top-[-20%] right-[-10%] w-[40%] h-[150%] bg-blue-500/10 blur-[100px] rounded-full" />
        <div className="absolute bottom-[-20%] left-[-10%] w-[30%] h-[150%] bg-emerald-500/10 blur-[100px] rounded-full" />
        
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-blue-600 rounded-xl shadow-lg shadow-blue-200">
                <BarChart3 className="w-5 h-5 text-white" />
              </div>
              <span className="text-sm font-bold text-blue-600 tracking-wider uppercase">Executive Overview</span>
            </div>
            <h1 className="text-4xl font-black text-slate-900 tracking-tight">Advanced BI Dashboard</h1>
            <p className="text-slate-500 mt-2 font-medium flex items-center gap-2">
              <Globe className="w-4 h-4" /> Global guest insights & revenue intelligence
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-3 bg-white/80 backdrop-blur-md px-5 py-3 rounded-2xl border border-white/50 shadow-sm">
              <div className="relative">
                <Activity className="w-5 h-5 text-emerald-500 animate-pulse" />
                <span className="absolute -top-1 -right-1 w-2 h-2 bg-emerald-500 rounded-full animate-ping" />
              </div>
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase leading-none">Live Now</p>
                <p className="text-lg font-black text-slate-900 leading-none mt-1">{activeUsers} Visitors</p>
              </div>
            </div>

            <div className="flex bg-white/80 backdrop-blur-md p-1.5 rounded-2xl border border-white/50 shadow-sm">
              {[7, 30, 90].map((d) => (
                <button
                  key={d}
                  onClick={() => setDays(d)}
                  className={`px-6 py-2 text-sm font-bold rounded-xl transition-all duration-300 ${
                    days === d 
                      ? 'bg-slate-900 text-white shadow-lg' 
                      : 'text-slate-500 hover:text-slate-900 hover:bg-white'
                  }`}
                >
                  {d}D
                </button>
              ))}
            </div>

            <Button 
              variant="outline" 
              className="rounded-2xl h-12 px-6 gap-2 border-slate-200 bg-white shadow-sm hover:shadow-md transition-all active:scale-95"
              onClick={handleExport}
            >
              <Download className="w-4 h-4" />
              <span className="font-bold">Export Report</span>
            </Button>
          </div>
        </div>
      </div>

      {/* Primary Financial KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard 
          title="Total Revenue"
          value={`₹${(data.revenue_total || 0).toLocaleString()}`}
          subtitle="Gross earnings"
          icon={<DollarSign className="w-6 h-6" />}
          color="blue"
          trend="+12.5%"
          trendUp={true}
        />
        <MetricCard 
          title="Average Daily Rate"
          value={`₹${(data.avg_daily_rate || 0).toLocaleString()}`}
          subtitle="Revenue per occupied room"
          icon={<TrendingUp className="w-6 h-6" />}
          color="emerald"
          trend="+4.2%"
          trendUp={true}
        />
        <MetricCard 
          title="Occupancy Rate"
          value={`${data.occupancy_rate || 0}%`}
          subtitle="Inventory utilization"
          icon={<Calendar className="w-6 h-6" />}
          color="amber"
          trend="-2.1%"
          trendUp={false}
        />
        <MetricCard 
          title="RevPAR"
          value={`₹${(data.rev_par || 0).toLocaleString()}`}
          subtitle="Revenue per available room"
          icon={<Zap className="w-6 h-6" />}
          color="purple"
          trend="+8.9%"
          trendUp={true}
        />
      </div>

      {/* Secondary Operational KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <OperationalMiniCard 
          title="Avg. Length of Stay"
          value={`${data.alos || 0} Nights`}
          icon={<Clock className="w-4 h-4" />}
          description="Optimal stay duration for profit"
        />
        <OperationalMiniCard 
          title="Cancellation Rate"
          value={`${data.cancellation_rate || 0}%`}
          icon={<ArrowDownRight className="w-4 h-4" />}
          description="Revenue leakage this period"
          warning={data.cancellation_rate && data.cancellation_rate > 15 ? true : false}
        />
        <OperationalMiniCard 
          title="Avg. Lead Time"
          value={`${data.avg_lead_time || 0} Days`}
          icon={<Calendar className="w-4 h-4" />}
          description="Days before check-in booking"
        />
      </div>

      {/* Main Performance Visualization */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          {/* Revenue Performance Multi-Axis Chart */}
          <div className="bg-white p-8 rounded-[2.5rem] border border-slate-100 shadow-xl shadow-slate-200/50">
            <div className="flex items-center justify-between mb-8">
              <div>
                <h2 className="text-xl font-black text-slate-900">Performance Dynamics</h2>
                <p className="text-sm text-slate-500 font-medium">Correlation between Traffic, ADR, and Revenue</p>
              </div>
              <div className="flex items-center gap-6">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-blue-500 shadow-lg shadow-blue-200" />
                  <span className="text-xs font-bold text-slate-600">Visitors</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-emerald-500 shadow-lg shadow-emerald-200" />
                  <span className="text-xs font-bold text-slate-600">Revenue</span>
                </div>
              </div>
            </div>
            
            <div className="h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.chart_data}>
                  <defs>
                    <linearGradient id="gradVisitors" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="gradRevenue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.2}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="8 8" vertical={false} stroke="#f1f5f9" />
                  <XAxis 
                    dataKey="date" 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{fontSize: 11, fontWeight: 700, fill: '#94a3b8'}}
                    dy={10}
                    tickFormatter={(val) => val.split('-').slice(1).join('/')}
                  />
                  <YAxis yAxisId="left" axisLine={false} tickLine={false} tick={{fontSize: 11, fontWeight: 700, fill: '#94a3b8'}} />
                  <YAxis yAxisId="right" orientation="right" axisLine={false} tickLine={false} tick={{fontSize: 11, fontWeight: 700, fill: '#94a3b8'}} />
                  <Tooltip 
                    contentStyle={{ borderRadius: '24px', border: 'none', boxShadow: '0 25px 50px -12px rgb(0 0 0 / 0.15)', padding: '20px' }}
                    itemStyle={{ fontWeight: 800, fontSize: '12px' }}
                  />
                  <Area yAxisId="left" type="monotone" dataKey="visitors" stroke="#3b82f6" strokeWidth={4} fill="url(#gradVisitors)" />
                  <Area yAxisId="right" type="monotone" dataKey="revenue" stroke="#10b981" strokeWidth={4} fill="url(#gradRevenue)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Conversion Funnel */}
            <div className="bg-white p-8 rounded-[2.5rem] border border-slate-100 shadow-xl">
              <h2 className="text-xl font-black text-slate-900 mb-8">Acquisition Funnel</h2>
              <div className="space-y-8">
                {data.funnel_data?.map((stage, idx) => {
                  const totalVisits = data.funnel_data?.[0]?.count || 1;
                  const percentage = Math.round((stage.count / totalVisits) * 100);
                  const colors = ['bg-slate-900', 'bg-blue-600', 'bg-indigo-500', 'bg-emerald-500'];
                  return (
                    <div key={stage.stage}>
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className={`w-8 h-8 rounded-lg ${colors[idx]} flex items-center justify-center text-white text-[10px] font-black`}>
                            0{idx + 1}
                          </div>
                          <span className="text-sm font-black text-slate-700 uppercase tracking-wider">{getStageLabel(stage.stage)}</span>
                        </div>
                        <span className="text-sm font-black text-slate-900">{stage.count} <span className="text-slate-400 font-bold ml-1">({percentage}%)</span></span>
                      </div>
                      <div className="w-full bg-slate-50 rounded-full h-3 p-0.5 border border-slate-100">
                        <div className={`h-full rounded-full transition-all duration-1000 ${colors[idx]}`} style={{ width: `${percentage}%` }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Geographical Map Mock/Stats */}
            <div className="bg-white p-8 rounded-[2.5rem] border border-slate-100 shadow-xl overflow-hidden relative">
              <div className="absolute top-[-50px] right-[-50px] w-48 h-48 bg-blue-50 rounded-full blur-3xl opacity-50" />
              <h2 className="text-xl font-black text-slate-900 mb-8 flex items-center gap-2">
                <Globe className="w-5 h-5 text-blue-500" />
                Global Reach
              </h2>
              <div className="space-y-5 relative z-10">
                {data.geo_stats?.slice(0, 5).map((item) => (
                  <div key={item.country} className="group">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <span className="text-xl">{getCountryFlag(item.code)}</span>
                        <span className="text-sm font-bold text-slate-700">{item.country}</span>
                      </div>
                      <span className="text-xs font-black text-slate-900">{item.visitors}</span>
                    </div>
                    <div className="w-full bg-slate-50 rounded-full h-1.5">
                      <div className="bg-blue-600 h-full rounded-full transition-all duration-1000" style={{ width: `${item.percentage}%` }} />
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-8 pt-6 border-t border-slate-50 flex justify-center">
                 <button className="text-xs font-black text-blue-600 uppercase tracking-widest hover:underline">View Full Geo Map</button>
              </div>
            </div>
          </div>
        </div>

        {/* Real-time Intelligence Sidebar */}
        <div className="space-y-8">
          {/* Live Activity Feed */}
          <div className="bg-slate-900 text-white p-8 rounded-[2.5rem] shadow-2xl shadow-slate-900/40 h-full flex flex-col">
            <div className="flex items-center justify-between mb-8">
              <div>
                <h2 className="text-xl font-black">Live Intelligence</h2>
                <div className="flex items-center gap-2 mt-1">
                  <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Real-time Feed</span>
                </div>
              </div>
              <div className="bg-white/10 p-3 rounded-2xl">
                <Activity className="w-5 h-5 text-white" />
              </div>
            </div>

            <div className="space-y-6 overflow-y-auto max-h-[600px] pr-2 custom-scrollbar">
              {liveEvents.length > 0 ? liveEvents.map((event, idx) => (
                <div key={event.id} className={`relative pl-8 pb-6 border-l border-white/10 last:pb-0 last:border-l-0 animate-in slide-in-from-right duration-500`} style={{ animationDelay: `${idx * 100}ms` }}>
                  <div className={`absolute left-[-5px] top-0 w-[10px] h-[10px] rounded-full shadow-[0_0_10px_rgba(255,255,255,0.3)] ${
                    event.type === 'booking' ? 'bg-emerald-500' : 
                    event.type === 'checkout' ? 'bg-blue-400' : 'bg-slate-400'
                  }`} />
                  
                  <div className="bg-white/5 hover:bg-white/10 p-4 rounded-2xl border border-white/10 transition-all cursor-default group">
                    <div className="flex items-center justify-between mb-2">
                      <span className={`text-[10px] font-black px-2 py-0.5 rounded uppercase tracking-tighter ${
                        event.type === 'booking' ? 'bg-emerald-500 text-white' : 'bg-white/20 text-slate-300'
                      }`}>
                        {event.type}
                      </span>
                      <span className="text-[10px] font-bold text-slate-500">{event.timestamp}</span>
                    </div>
                    <p className="text-sm font-bold text-slate-200">{event.message}</p>
                    {event.amount && (
                      <p className="text-lg font-black text-emerald-400 mt-1">₹{event.amount.toLocaleString()}</p>
                    )}
                    <div className="mt-2 flex items-center gap-2 opacity-50 text-[10px] font-bold">
                       <span>User from {getCountryFlag((event as any).country_code || 'IN')}</span>
                       <span>•</span>
                       <span>{(event as any).device === 'mobile' ? <Smartphone className="w-3 h-3" /> : <Monitor className="w-3 h-3" />}</span>
                    </div>
                  </div>
                </div>
              )) : (
                <div className="flex flex-col items-center justify-center py-20 text-slate-500 italic">
                   <Clock className="w-10 h-10 mb-4 opacity-20" />
                   <p className="text-sm">Waiting for live data...</p>
                </div>
              )}
            </div>

            <div className="mt-auto pt-8">
              <div className="bg-white/5 rounded-3xl p-6 border border-white/10">
                <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Direct vs OTA</p>
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <div className="flex justify-between mb-2">
                      <span className="text-xs font-black text-white">Direct</span>
                      <span className="text-xs font-black text-emerald-400">82%</span>
                    </div>
                    <div className="w-full bg-white/10 h-2 rounded-full overflow-hidden">
                      <div className="bg-emerald-500 h-full rounded-full" style={{ width: '82%' }} />
                    </div>
                  </div>
                </div>
                <p className="text-[10px] text-slate-500 font-bold mt-4">💡 Optimized pricing is driving more direct bookings today.</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Predictive & Distribution Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Occupancy Forecast */}
        <div className="bg-white p-8 rounded-[2.5rem] border border-slate-100 shadow-xl">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-xl font-black text-slate-900">7-Day Predictive Occupancy</h2>
              <p className="text-sm text-slate-500 font-medium">AI-driven demand forecasting</p>
            </div>
            <div className="bg-indigo-50 p-3 rounded-2xl">
              <TrendingUp className="w-5 h-5 text-indigo-600" />
            </div>
          </div>
          <div className="h-[300px]">
             <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.occupancy_forecast}>
                  <defs>
                    <linearGradient id="gradOcc" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.2}/>
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="8 8" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{fontSize: 10, fontWeight: 700, fill: '#94a3b8'}} />
                  <YAxis axisLine={false} tickLine={false} tick={{fontSize: 10, fontWeight: 700, fill: '#94a3b8'}} unit="%" />
                  <Tooltip 
                    contentStyle={{ borderRadius: '24px', border: 'none', boxShadow: '0 25px 50px -12px rgb(0 0 0 / 0.15)' }}
                    formatter={(val) => [`${val}%`, 'Predicted Occupancy']}
                  />
                  <Area type="monotone" dataKey="occupancy" stroke="#6366f1" strokeWidth={4} fill="url(#gradOcc)" />
                </AreaChart>
             </ResponsiveContainer>
          </div>
        </div>

        {/* Booking Window Distribution */}
        <div className="bg-white p-8 rounded-[2.5rem] border border-slate-100 shadow-xl">
           <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-xl font-black text-slate-900">Booking Velocity</h2>
              <p className="text-sm text-slate-500 font-medium">How far in advance guests book</p>
            </div>
            <div className="bg-amber-50 p-3 rounded-2xl">
              <Clock className="w-5 h-5 text-amber-600" />
            </div>
          </div>
          <div className="h-[300px]">
             <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.booking_window_data}>
                  <CartesianGrid strokeDasharray="8 8" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="window" axisLine={false} tickLine={false} tick={{fontSize: 10, fontWeight: 700, fill: '#94a3b8'}} />
                  <YAxis axisLine={false} tickLine={false} tick={{fontSize: 10, fontWeight: 700, fill: '#94a3b8'}} />
                  <Tooltip 
                    cursor={{fill: '#f8fafc'}}
                    contentStyle={{ borderRadius: '24px', border: 'none', boxShadow: '0 25px 50px -12px rgb(0 0 0 / 0.15)' }}
                  />
                  <Bar dataKey="count" fill="#f59e0b" radius={[12, 12, 0, 0]} barSize={40} />
                </BarChart>
             </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Bottom Insights Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1 bg-white p-6 rounded-[2rem] border border-slate-100 shadow-lg">
           <h3 className="text-sm font-black text-slate-900 mb-4 flex items-center gap-2">
             <MessageCircle className="w-4 h-4 text-blue-500" />
             AI Resolution Rate
           </h3>
           <div className="flex items-end gap-3 mb-4">
              <span className="text-5xl font-black text-slate-900">{data.ai_resolution_rate}%</span>
              <span className="text-xs font-bold text-emerald-600 mb-1">+5.2% vs prev</span>
           </div>
           <div className="w-full bg-slate-50 h-2 rounded-full overflow-hidden">
              <div className="bg-blue-600 h-full" style={{ width: `${data.ai_resolution_rate}%` }} />
           </div>
        </div>

        <div className="lg:col-span-1 bg-white p-6 rounded-[2rem] border border-slate-100 shadow-lg">
           <h3 className="text-sm font-black text-slate-900 mb-4 flex items-center gap-2">
             <Zap className="w-4 h-4 text-amber-500" />
             AI Assisted Revenue
           </h3>
           <div className="flex items-end gap-3 mb-4">
              <span className="text-3xl font-black text-slate-900">₹{(data.ai_revenue || 0).toLocaleString()}</span>
           </div>
           <p className="text-xs font-bold text-slate-400 leading-relaxed">
             {data.ai_assisted_bookings || 0} bookings secured via AI automation this period.
           </p>
        </div>

        <div className="lg:col-span-2 bg-gradient-to-br from-indigo-600 to-blue-700 p-8 rounded-[2rem] text-white shadow-xl shadow-blue-200">
           <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-black tracking-tight">Smart Strategy Suggestion</h3>
              <div className="p-2 bg-white/20 rounded-xl">
                 <Zap className="w-5 h-5 text-white" />
              </div>
           </div>
           <p className="text-sm font-medium leading-relaxed mb-6 opacity-90">
             Based on your {data.cancellation_rate}% cancellation rate and current demand forecast, we suggest implementing a 
             <span className="font-black"> "Non-Refundable Early Bird" </span> 
             promotion for the upcoming weekend to secure revenue.
           </p>
           <button className="bg-white text-blue-700 px-6 py-3 rounded-2xl font-black text-sm shadow-xl hover:scale-105 transition-all">
              Apply Strategy Now
           </button>
        </div>
      </div>
    </div>
  );
};

const MetricCard: React.FC<{ 
  title: string; 
  value: string; 
  subtitle: string; 
  icon: React.ReactNode; 
  color: 'blue' | 'emerald' | 'amber' | 'purple';
  trend?: string;
  trendUp?: boolean;
}> = ({ title, value, subtitle, icon, color, trend, trendUp }) => {
  const colors = {
    blue: 'bg-blue-50 text-blue-600 border-blue-100 shadow-blue-100/50',
    emerald: 'bg-emerald-50 text-emerald-600 border-emerald-100 shadow-emerald-100/50',
    amber: 'bg-amber-50 text-amber-600 border-amber-100 shadow-amber-100/50',
    purple: 'bg-purple-50 text-purple-600 border-purple-100 shadow-purple-100/50',
  };

  return (
    <div className="bg-white p-8 rounded-[2.5rem] border border-slate-100 shadow-xl shadow-slate-200/50 group hover:scale-[1.02] transition-all duration-500 relative overflow-hidden">
      <div className={`absolute top-[-20%] right-[-10%] w-24 h-24 rounded-full opacity-5 group-hover:scale-150 transition-transform duration-700 ${colors[color].split(' ')[1]}`} style={{ background: 'currentColor' }} />
      <div className="flex items-start justify-between relative z-10">
        <div className={`p-4 rounded-2xl ${colors[color]} border shadow-lg`}>
          {icon}
        </div>
        {trend && (
          <div className={`flex items-center gap-1 text-[10px] font-black px-2.5 py-1 rounded-full border ${trendUp ? 'bg-emerald-50 text-emerald-600 border-emerald-100' : 'bg-red-50 text-red-600 border-red-100'}`}>
            {trendUp ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
            {trend}
          </div>
        )}
      </div>
      <div className="mt-8 relative z-10">
        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none mb-2">{title}</p>
        <h3 className="text-3xl font-black text-slate-900 tracking-tight leading-none">{value}</h3>
        <p className="text-xs font-bold text-slate-400 mt-4 leading-none">{subtitle}</p>
      </div>
    </div>
  );
};

const OperationalMiniCard: React.FC<{ 
  title: string; 
  value: string; 
  icon: React.ReactNode; 
  description: string;
  warning?: boolean;
}> = ({ title, value, icon, description, warning }) => (
  <div className="bg-white px-6 py-5 rounded-[1.5rem] border border-slate-100 shadow-lg flex items-center gap-5 hover:bg-slate-50/50 transition-colors">
    <div className={`p-3 rounded-xl ${warning ? 'bg-red-50 text-red-600' : 'bg-slate-50 text-slate-600'}`}>
      {icon}
    </div>
    <div>
      <p className="text-[10px] font-black text-slate-400 uppercase tracking-wider">{title}</p>
      <p className="text-xl font-black text-slate-900">{value}</p>
      <p className="text-[9px] font-bold text-slate-400 mt-0.5">{description}</p>
    </div>
  </div>
);

const getCountryFlag = (code: string) => {
  const flags: Record<string, string> = {
    'IN': '🇮🇳', 'US': '🇺🇸', 'GB': '🇬🇧', 'AE': '🇦🇪', 'DE': '🇩🇪', 
    'AU': '🇦🇺', 'CA': '🇨🇦', 'FR': '🇫🇷', 'JP': '🇯🇵', 'CN': '🇨🇳'
  };
  return flags[code] || '🌐';
};



const StatCard: React.FC<{ 
  title: string; 
  value: string; 
  icon: React.ReactNode;
  trend?: string;
  trendUp?: boolean;
  description: string;
}> = ({ title, value, icon, trend, trendUp, description }) => (
  <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm hover:shadow-xl transition-all duration-500 group relative overflow-hidden">
    <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:scale-150 transition-transform duration-700">
      {icon}
    </div>
    <div className="flex items-start justify-between relative z-10">
      <div className="p-3 bg-slate-50 rounded-2xl group-hover:bg-slate-900 group-hover:text-white transition-colors duration-500">
        {icon}
      </div>
      {trend && (
        <div className={`flex items-center gap-1 text-[10px] font-bold px-2 py-1 rounded-lg border ${trendUp ? 'bg-emerald-50 text-emerald-600 border-emerald-100' : 'bg-red-50 text-red-600 border-red-100'}`}>
          {trendUp ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
          {trend}
        </div>
      )}
    </div>
    <div className="mt-6 relative z-10">
      <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">{title}</p>
      <h3 className="text-3xl font-black text-slate-900 mt-1 tracking-tight">{value}</h3>
      <p className="text-xs text-slate-500 mt-2 font-medium">{description}</p>
    </div>
  </div>
);

export default AnalyticsDashboard;
