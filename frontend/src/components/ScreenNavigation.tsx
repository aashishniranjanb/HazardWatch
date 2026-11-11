'use client';

import React from 'react';
import { 
  Building2, 
  MapPin, 
  Activity, 
  BrainCircuit, 
  AlertTriangle, 
  Fan, 
  BarChart3, 
  FlaskConical, 
  Database, 
  Cpu, 
  Wrench 
} from 'lucide-react';

export type ScreenId = 
  | 'OVERVIEW'
  | 'ZONES'
  | 'LIVE_MONITOR'
  | 'AI_INTELLIGENCE'
  | 'INCIDENTS'
  | 'VENTILATION'
  | 'ANALYTICS'
  | 'SIMULATION_LAB'
  | 'DATASET_EXPLORER'
  | 'MODEL_LAB'
  | 'DIAGNOSTICS';

export interface ScreenNavItem {
  id: ScreenId;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string | number;
}

export const SCREEN_NAV_ITEMS: ScreenNavItem[] = [
  { id: 'OVERVIEW', label: 'Plant Overview', icon: Building2 },
  { id: 'ZONES', label: 'Factory Zones (8)', icon: MapPin },
  { id: 'LIVE_MONITOR', label: 'Live Monitoring', icon: Activity },
  { id: 'AI_INTELLIGENCE', label: 'AI Intelligence', icon: BrainCircuit },
  { id: 'INCIDENTS', label: 'Incident Mgmt', icon: AlertTriangle },
  { id: 'VENTILATION', label: 'Ventilation & Relay', icon: Fan },
  { id: 'ANALYTICS', label: 'Trends & Analytics', icon: BarChart3 },
  { id: 'SIMULATION_LAB', label: 'Simulation Lab', icon: FlaskConical },
  { id: 'DATASET_EXPLORER', label: 'Dataset Explorer', icon: Database },
  { id: 'MODEL_LAB', label: 'Model Laboratory', icon: Cpu },
  { id: 'DIAGNOSTICS', label: 'System Diagnostics', icon: Wrench },
];

export const ScreenNavigation: React.FC<{
  activeScreen: ScreenId;
  onSelectScreen: (id: ScreenId) => void;
  activeIncidentsCount?: number;
}> = ({ activeScreen, onSelectScreen, activeIncidentsCount = 0 }) => {
  return (
    <nav className="flex items-center gap-1.5 overflow-x-auto pb-2 border-b border-zinc-800 scrollbar-thin">
      {SCREEN_NAV_ITEMS.map((item) => {
        const Icon = item.icon;
        const isActive = activeScreen === item.id;
        const hasBadge = item.id === 'INCIDENTS' && activeIncidentsCount > 0;

        return (
          <button
            key={item.id}
            onClick={() => onSelectScreen(item.id)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded text-xs font-mono whitespace-nowrap transition-all ${
              isActive
                ? 'bg-amber-500/20 text-amber-300 font-bold border border-amber-500/50 shadow-sm shadow-amber-500/10'
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/60 border border-transparent'
            }`}
          >
            <Icon className="w-3.5 h-3.5" />
            <span>{item.label}</span>
            {hasBadge && (
              <span className="px-1.5 py-0.2 text-[10px] bg-red-600 text-white font-sans font-bold rounded-full animate-pulse">
                {activeIncidentsCount}
              </span>
            )}
          </button>
        );
      })}
    </nav>
  );
};
