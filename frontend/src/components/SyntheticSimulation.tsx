'use client';

import React from 'react';
import { SYNTHETIC_SCENARIOS, SyntheticScenario } from '@/lib/synthetic-scenarios';
import { Radio, Play, Info, Flame, Wind, Activity } from 'lucide-react';

interface SyntheticSimulationProps {
  activeScenarioId: string | null;
  onSelectScenario: (scenario: SyntheticScenario) => void;
  onStopScenario: () => void;
  isSimulating: boolean;
}

export const SyntheticSimulation: React.FC<SyntheticSimulationProps> = ({
  activeScenarioId,
  onSelectScenario,
  onStopScenario,
  isSimulating,
}) => {
  return (
    <div className="p-4 rounded-lg border border-purple-900/50 bg-zinc-950/80 backdrop-blur space-y-3">
      <div className="flex items-center justify-between pb-2 border-b border-zinc-900">
        <div className="flex items-center gap-2">
          <Radio className="w-4 h-4 text-purple-400" />
          <span className="text-xs font-mono font-bold tracking-wider uppercase text-zinc-200">
            Synthetic Hazardous Gas Scenarios (Pure Simulation)
          </span>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-950/60 border border-purple-800 text-purple-300">
          CONTROLLED SYNTHETIC TESTBENCH
        </span>
      </div>

      <div className="p-2.5 rounded bg-purple-950/20 border border-purple-900/40 text-[11px] font-mono text-purple-200 flex items-start gap-2">
        <Info className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
        <span>
          Simulates dynamic leakage profiles without requiring physical chemical exposure or gas canisters. Clearly distinct from hardware measurements.
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2.5">
        {SYNTHETIC_SCENARIOS.map((scenario) => {
          const isActive = isSimulating && activeScenarioId === scenario.id;
          return (
            <div
              key={scenario.id}
              className={`p-3 rounded border transition-all flex flex-col justify-between ${
                isActive
                  ? 'bg-purple-950/40 border-purple-500 shadow-md shadow-purple-950/50'
                  : 'bg-zinc-900/60 border-zinc-800 hover:border-zinc-700'
              }`}
            >
              <div>
                <div className="text-xs font-mono font-bold text-zinc-200 flex items-center justify-between">
                  <span>{scenario.name}</span>
                  {isActive && <span className="w-2 h-2 rounded-full bg-purple-400 animate-ping" />}
                </div>
                <p className="text-[10px] font-mono text-zinc-400 mt-1 line-clamp-2">
                  {scenario.description}
                </p>
              </div>

              <div className="mt-3 pt-2 border-t border-zinc-900/80">
                {isActive ? (
                  <button
                    onClick={onStopScenario}
                    className="w-full py-1 rounded bg-red-950/80 hover:bg-red-900 border border-red-600 text-red-200 font-mono text-xs font-bold"
                  >
                    HALT SCENARIO
                  </button>
                ) : (
                  <button
                    onClick={() => onSelectScenario(scenario)}
                    className="w-full py-1 rounded bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-zinc-200 font-mono text-xs font-bold flex items-center justify-center gap-1.5"
                  >
                    <Play className="w-3 h-3 fill-current text-purple-400" />
                    RUN SCENARIO
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
