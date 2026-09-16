import type { PropsWithChildren } from "react";
import { BarChart3, Bell, BrainCircuit, BriefcaseBusiness, CandlestickChart, ChevronDown, LayoutDashboard, ListOrdered, Menu, Search } from "lucide-react";
import { motion } from "motion/react";
import { NavLink } from "react-router-dom";

const navigation = [
  { to: "/", label: "Overview", icon: LayoutDashboard },
  { to: "/positions", label: "Positions", icon: BriefcaseBusiness },
  { to: "/trades", label: "Trades", icon: ListOrdered },
  { to: "/strategies", label: "Strategies", icon: BarChart3 },
  { to: "/models", label: "Models", icon: BrainCircuit },
  { to: "/market", label: "Market", icon: CandlestickChart },
];

export function AppShell({ children }: PropsWithChildren) {
  return (
    <div className="min-h-screen bg-[#f7f8f6] text-[#18201f]">
      <main className="min-h-screen">
        <header className="sticky top-0 z-10 flex h-[72px] items-center justify-between border-b border-[#e5e9e4]/90 bg-[#f7f8f6]/80 px-5 backdrop-blur-xl lg:h-[86px] lg:px-9">
          <div className="flex items-center gap-3">
            <NavLink to="/" className="flex items-center gap-2.5"><span className="grid h-8 w-8 place-items-center rounded-lg bg-[#101b19] font-display text-base font-bold text-[#eaffdf]">A</span><span className="font-display hidden text-lg font-semibold tracking-[-0.04em] text-[#1c2926] sm:inline">Alyntiq</span></NavLink>
            <button type="button" className="grid h-9 w-9 place-items-center rounded-lg border border-[#e2e7e1] bg-white text-[#50615e] lg:hidden" aria-label="Open navigation"><Menu size={18} /></button>
          </div>
          <nav className="absolute left-1/2 hidden -translate-x-1/2 items-center gap-1 rounded-full border border-white bg-white/75 p-1 shadow-[0_8px_25px_rgba(32,63,50,0.05)] xl:flex" aria-label="Primary navigation">
            {navigation.map(({ to, label, icon: Icon }) => <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) => `relative flex items-center gap-2 rounded-full px-3.5 py-2 text-xs font-medium transition-colors ${isActive ? "text-white" : "text-[#66736f] hover:text-[#1e2c29]"}`}>{({ isActive }) => <>{isActive ? <motion.span layoutId="active-nav" className="absolute inset-0 rounded-full bg-[#111d1b]" transition={{ type: "spring", bounce: 0.15, duration: 0.45 }} /> : null}<Icon className="relative" size={14} /><span className="relative">{label}</span></>}</NavLink>)}
          </nav>
          <div className="flex items-center gap-2">
            <button type="button" className="hidden items-center gap-2 rounded-lg border border-[#e2e7e1] bg-white px-3 py-2 text-xs text-[#778581] md:flex" aria-label="Search dashboard"><Search size={14} />Search <kbd className="rounded border border-[#e5e9e4] px-1.5 py-0.5 text-[10px]">⌘ K</kbd></button>
            <button type="button" className="grid h-9 w-9 place-items-center rounded-lg border border-[#e2e7e1] bg-white text-[#52625f]" aria-label="Notifications"><Bell size={16} /></button>
            <div className="ml-1 flex items-center gap-2 rounded-lg py-1 pl-1 pr-2">
              <span className="grid h-7 w-7 place-items-center rounded-lg bg-[#dff2e4] text-[10px] font-bold text-[#155947]">RA</span>
              <ChevronDown className="hidden text-[#71807c] sm:block" size={14} />
            </div>
          </div>
        </header>
        <div className="mx-auto max-w-[1800px] px-5 py-6 pb-24 lg:px-9 lg:py-8">{children}</div>
      </main>
      <nav className="fixed inset-x-0 bottom-0 z-20 flex border-t border-[#e2e7e1] bg-white/95 px-2 pb-[max(0.45rem,env(safe-area-inset-bottom))] pt-1.5 backdrop-blur lg:hidden" aria-label="Mobile navigation">
        {navigation.map(({ to, label, icon: Icon }) => <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) => `flex min-w-0 flex-1 flex-col items-center gap-1 rounded-lg py-1.5 text-[9px] font-medium ${isActive ? "text-[#15725a]" : "text-[#7e8b87]"}`}><Icon size={16} /><span className="truncate">{label}</span></NavLink>)}
      </nav>
    </div>
  );
}
