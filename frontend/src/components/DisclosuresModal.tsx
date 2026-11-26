import { IconShield, IconX } from "./Icons";

export function DisclosuresModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  if (!open) return null;

  const items = [
    {
      code: "D1 · Strutture fittizie",
      title: "Buby Lago (190 cam.) e Buby Montagna (230 cam.)",
      body: "Le due strutture mappano 1:1 i due tipi di hotel del dataset pubblico Kaggle Hotel Booking Demand (2015–2017): Resort Hotel → Buby Lago e City Hotel → Buby Montagna.",
    },
    {
      code: "D2 · Capacità assunta",
      title: "Occupazione e RevPAR non sono misure dirette",
      body: "Le capacità di 190 e 230 camere (420 combinate) sono stimate dai picchi di room-night osservati. Tutti i valori di occupancy e RevPAR vanno letti rispetto a questa capacità assunta.",
    },
    {
      code: "S4 · Zero overlap temporale",
      title: "Recensioni 2012 vs Prenotazioni 2015–2017",
      body: "Il corpus TripAdvisor (1.638 recensioni in inglese, Li et al. 2013) copre solo il 2012; le prenotazioni coprono luglio 2015 – agosto 2017. Il legame è asserito a livello di proprietà e non implica causalità.",
    },
    {
      code: "D20 · Email sintetiche & HITL",
      title: "Nessun invio automatico dalla Inbox",
      body: "Le 800 email degli ospiti sono generate sinteticamente (DA-3). L'assistente propone categoria e bozza; solo un utente con ruolo admin o manager può modificare e approvare l'invio.",
    },
  ];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4 backdrop-blur-xs"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Note metodologiche e disclosure"
    >
      <div
        className="animate-enter w-full max-w-2xl overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
          <div className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-50 text-teal-700">
              <IconShield size={18} />
            </span>
            <div>
              <h2 className="text-base font-bold text-slate-900">
                Trasparenza & Contratto Dati v1.0.0
              </h2>
              <p className="text-xs text-slate-500">
                Regole vincolanti SAL 1 · Buby Travel (Caso 1 Turismo)
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
          >
            <IconX size={18} />
          </button>
        </div>

        <div className="grid gap-3 p-6 sm:grid-cols-2">
          {items.map((item) => (
            <div
              key={item.code}
              className="rounded-xl border border-slate-200/80 bg-slate-50/70 p-4"
            >
              <span className="inline-block rounded-full bg-slate-900 px-2 py-0.5 text-[10px] font-semibold tracking-wide text-white">
                {item.code}
              </span>
              <h3 className="mt-2 text-sm font-semibold text-slate-900">{item.title}</h3>
              <p className="mt-1 text-xs leading-relaxed text-slate-600">{item.body}</p>
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between border-t border-slate-100 bg-slate-50 px-6 py-3">
          <span className="text-xs text-slate-500">
            Contratto congelato OpenAPI 3.0.3 · Ruoli: admin, manager, property_manager
          </span>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg bg-slate-900 px-4 py-1.5 text-xs font-semibold text-white hover:bg-slate-800"
          >
            Ho capito
          </button>
        </div>
      </div>
    </div>
  );
}
