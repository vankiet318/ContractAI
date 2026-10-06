import { BrainCircuit } from "lucide-react";

export function AppLogo() {
  return (
    <div className="flex items-center gap-2">
      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-900 text-white">
        <BrainCircuit className="w-5 h-5" />
      </span>
      <span className="text-base font-semibold text-slate-900">ContractAI</span>
    </div>
  );
}
