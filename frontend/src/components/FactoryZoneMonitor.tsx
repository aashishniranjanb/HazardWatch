import React from 'react';
import { Factory, AlertTriangle, ShieldCheck, Wrench, Wind } from 'lucide-react';

export interface FactoryZone {
  zone_id: string;
  name: string;
  process_description: string;
  primary_hazards: string[];
  potential_substances: string[];
  installed_sensor_types: string[];
  required_additional_sensors: string[];
  ventilation_equipment: string;
}

interface FactoryZoneMonitorProps {
  selectedZone: string;
  onSelectZone: (zoneId: string) => void;
  activeSeverity: string;
}

export const FACTORY_ZONES: Record<string, FactoryZone> = {
  Z01: {
    zone_id: 'Z01',
    name: 'Gas Storage & Distribution',
    process_description: 'Pressurized cylinders, header manifolds, gas distribution.',
    primary_hazards: ['H01 (Combustible gas)'],
    potential_substances: ['LPG', 'Propane', 'Methane'],
    installed_sensor_types: ['MQ-2', 'DHT11'],
    required_additional_sensors: ['Catalytic LEL Detector', 'O2 Sensor'],
    ventilation_equipment: 'Gravity roof louvers & wall explosion-proof fans',
  },
  Z02: {
    zone_id: 'Z02',
    name: 'Boiler & Furnace Room',
    process_description: 'Steam boilers, fuel burner heads, and flue gas exhaust stacks.',
    primary_hazards: ['H01', 'H03', 'H04 (CO)'],
    potential_substances: ['Carbon Monoxide (CO)', 'Smoke', 'Natural gas'],
    installed_sensor_types: ['MQ-2', 'DHT11'],
    required_additional_sensors: ['Certified Electrochemical CO Monitor'],
    ventilation_equipment: 'Induced draft flue fans & combustion air intake dampers',
  },
  Z03: {
    zone_id: 'Z03',
    name: 'Painting & Coating Section',
    process_description: 'Spray booths, solvent paint application, flash-off curing tunnel.',
    primary_hazards: ['H02 (Solvent vapors)', 'H07 (Extraction failure)'],
    potential_substances: ['Toluene', 'Xylene', 'Acetone', 'VOCs'],
    installed_sensor_types: ['MQ-135', 'DHT11'],
    required_additional_sensors: ['PID Total VOC Detector', 'Airflow DP Sensor'],
    ventilation_equipment: 'Downdraft booth filtration & active carbon scrubber',
  },
  Z04: {
    zone_id: 'Z04',
    name: 'Chemical Storage & Decanting',
    process_description: 'Raw chemical drum storage, solvent dispensing, pump skids.',
    primary_hazards: ['H02', 'H06 (Ammonia)'],
    potential_substances: ['Solvents', 'Acid fumes', 'Ammonia solution'],
    installed_sensor_types: ['MQ-135', 'MQ-2', 'DHT11'],
    required_additional_sensors: ['Dedicated NH3 Detector', 'Corrosive Vapor Sensor'],
    ventilation_equipment: 'Continuous chemical fume extraction hoods',
  },
  Z05: {
    zone_id: 'Z05',
    name: 'Electrical MCC & Switchgear',
    process_description: 'Medium-voltage breakers, motor drives (VFD), distribution buses.',
    primary_hazards: ['H03 (Electrical smoke/pyrolysis)'],
    potential_substances: ['Thermal PVC decomposition smoke'],
    installed_sensor_types: ['MQ-2', 'DHT11'],
    required_additional_sensors: ['Aspirating Smoke Detector (VESDA)'],
    ventilation_equipment: 'Positive-pressure HEPA HVAC (closed circuit)',
  },
  Z06: {
    zone_id: 'Z06',
    name: 'General Production Floor',
    process_description: 'Assembly automation machinery, conveyors, pneumatic stations.',
    primary_hazards: ['H01', 'H02', 'H03'],
    potential_substances: ['Mixed industrial mist', 'Solvent cleaner vapors'],
    installed_sensor_types: ['MQ-2', 'MQ-135', 'DHT11'],
    required_additional_sensors: ['Ambient PM2.5/PM10 Particulate Monitor'],
    ventilation_equipment: 'Central Air Handling Unit (AHU) & HVLS ceiling fans',
  },
  Z07: {
    zone_id: 'Z07',
    name: 'Wastewater & Drainage Sumps',
    process_description: 'Effluent neutralization tanks, below-grade drainage sumps.',
    primary_hazards: ['H05 (H2S)', 'H01 (Methane)', 'H08 (Oxygen deficiency)'],
    potential_substances: ['Hydrogen Sulfide (H2S)', 'Methane', 'Deoxygenated air'],
    installed_sensor_types: ['MQ-135', 'MQ-2'],
    required_additional_sensors: ['Certified Multi-Gas Sump Monitor (H2S, LEL, O2, CO)'],
    ventilation_equipment: 'Continuous sump headspace exhaust ventilator',
  },
  Z08: {
    zone_id: 'Z08',
    name: 'Ventilation & Exhaust Plenums',
    process_description: 'Main rooftop plenums, duct intersections, stack outlets.',
    primary_hazards: ['H07 (Extraction failure/stagnation)'],
    potential_substances: ['Trapped solvent vapors', 'Contaminant buildup'],
    installed_sensor_types: ['MQ-2', 'MQ-135', 'DHT11'],
    required_additional_sensors: ['Exhaust Duct Static Pressure Sensor'],
    ventilation_equipment: 'Industrial centrifugal exhaust blowers',
  },
};

export const FactoryZoneMonitor: React.FC<FactoryZoneMonitorProps> = ({
  selectedZone,
  onSelectZone,
  activeSeverity,
}) => {
  const current = FACTORY_ZONES[selectedZone] || FACTORY_ZONES['Z03'];

  return (
    <div className="p-4 rounded-lg border border-zinc-800 bg-zinc-950/80 backdrop-blur space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-zinc-900">
        <div className="flex items-center gap-2">
          <Factory className="w-4 h-4 text-amber-500" />
          <span className="text-xs font-mono font-bold tracking-wider uppercase text-zinc-200">
            Factory Zone Context & Industrial Atmospheric Boundaries
          </span>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-400">
          ENVIRONMENT: GENERAL MANUFACTURING FACILITY
        </span>
      </div>

      {/* Zone Grid Selector */}
      <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-8 gap-1.5">
        {Object.values(FACTORY_ZONES).map((z) => {
          const isSelected = selectedZone === z.zone_id;
          return (
            <button
              key={z.zone_id}
              onClick={() => onSelectZone(z.zone_id)}
              className={`p-2 rounded text-left border transition-all ${
                isSelected
                  ? 'bg-amber-950/60 border-amber-500 text-amber-200 shadow-md shadow-amber-950/40'
                  : 'bg-zinc-900/60 border-zinc-800 hover:border-zinc-700 text-zinc-400'
              }`}
            >
              <div className="text-[10px] font-mono font-bold uppercase">{z.zone_id}</div>
              <div className="text-[11px] font-mono font-medium truncate mt-0.5 text-zinc-200">
                {z.name.split(' ')[0]}
              </div>
            </button>
          );
        })}
      </div>

      {/* Selected Zone Deep Dive Card */}
      <div className="p-3.5 rounded bg-zinc-900/80 border border-zinc-800 grid grid-cols-1 md:grid-cols-3 gap-3 text-xs font-mono">
        <div>
          <span className="text-[10px] text-zinc-500 uppercase font-semibold block">Configured Zone Area</span>
          <div className="text-sm font-bold text-zinc-100 mt-0.5">{current.zone_id} — {current.name}</div>
          <p className="text-[11px] text-zinc-400 mt-1">{current.process_description}</p>
          <div className="mt-2 text-[10px] text-amber-400 font-semibold">
            Potential Hazards: {current.primary_hazards.join(', ')}
          </div>
        </div>

        <div>
          <span className="text-[10px] text-zinc-500 uppercase font-semibold block">Sensors & Extraction Equipment</span>
          <div className="text-[11px] text-zinc-300 mt-1">
            <span className="text-zinc-500">Hardware Available:</span> {current.installed_sensor_types.join(', ')}
          </div>
          <div className="text-[11px] text-zinc-400 mt-1">
            <span className="text-amber-500">Required Certified Sensors:</span> {current.required_additional_sensors.join(', ')}
          </div>
          <div className="text-[11px] text-zinc-400 mt-1">
            <span className="text-cyan-400">Ventilation System:</span> {current.ventilation_equipment}
          </div>
        </div>

        <div className="p-2.5 rounded bg-zinc-950/60 border border-zinc-800/80 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-1.5 text-[10px] font-bold text-zinc-400 uppercase">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              Safety Verification Policy
            </div>
            <p className="text-[10px] text-zinc-400 mt-1">
              *Contextual intelligence only. Never declare a specific chemical detected without dedicated calibrated gas instrumentation.
            </p>
          </div>
          <div className="text-[10px] text-zinc-500 mt-2">
            Status: <span className="text-zinc-300 font-bold">{activeSeverity}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
