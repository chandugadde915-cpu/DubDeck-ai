import { Activity, CloudUpload, FileVideo, Languages, ShieldCheck } from "lucide-react";

const stats = [
  ["Active projects", "18"],
  ["Queued jobs", "7"],
  ["Avg sync score", "94%"],
  ["Languages", "50+"]
];

const pipeline = [
  "Upload Video",
  "Extract Audio",
  "Generate Transcript",
  "Translate",
  "Duration Fit",
  "Rewrite Long Segments",
  "Generate TTS",
  "Sync Audio",
  "QA Validation",
  "Export MP4"
];

export default function DashboardPage() {
  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <section className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-6 py-8">
        <header className="flex flex-col gap-3 border-b border-white/10 pb-6">
          <p className="text-sm font-semibold uppercase tracking-wide text-teal-300">DubDeck AI SaaS</p>
          <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
            <div>
              <h1 className="text-4xl font-semibold tracking-normal">AI Video Dubbing Studio</h1>
              <p className="mt-2 max-w-2xl text-slate-300">
                Upload long-form videos, translate into 50+ languages, sync generated speech to original timing, validate QA, and export professional MP4s.
              </p>
            </div>
            <button className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-teal-500 px-5 font-semibold text-slate-950 hover:bg-teal-400">
              <CloudUpload className="h-4 w-4" />
              Upload video
            </button>
          </div>
        </header>

        <section className="grid gap-4 md:grid-cols-4">
          {stats.map(([label, value]) => (
            <div key={label} className="rounded-lg border border-white/10 bg-white/[0.04] p-5">
              <p className="text-sm text-slate-400">{label}</p>
              <p className="mt-2 text-3xl font-semibold">{value}</p>
            </div>
          ))}
        </section>

        <section className="grid gap-5 lg:grid-cols-[1.2fr_.8fr]">
          <div className="rounded-lg border border-white/10 bg-white/[0.04] p-5">
            <div className="mb-4 flex items-center gap-2">
              <Activity className="h-5 w-5 text-teal-300" />
              <h2 className="text-xl font-semibold">Processing pipeline</h2>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              {pipeline.map((step, index) => (
                <div key={step} className="flex items-center gap-3 rounded-md border border-white/10 bg-slate-900/70 p-3">
                  <span className="flex h-7 w-7 items-center justify-center rounded-full bg-teal-400/15 text-sm text-teal-200">{index + 1}</span>
                  <span className="text-sm text-slate-200">{step}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="grid gap-5">
            <div className="rounded-lg border border-white/10 bg-white/[0.04] p-5">
              <div className="mb-4 flex items-center gap-2">
                <FileVideo className="h-5 w-5 text-teal-300" />
                <h2 className="text-xl font-semibold">Current project</h2>
              </div>
              <p className="text-sm text-slate-400">Safety Training Module 03</p>
              <div className="mt-4 h-2 rounded-full bg-slate-800">
                <div className="h-2 w-[68%] rounded-full bg-teal-400" />
              </div>
              <p className="mt-3 text-sm text-slate-300">Generating TTS audio, 34/50 segments completed</p>
            </div>

            <div className="rounded-lg border border-white/10 bg-white/[0.04] p-5">
              <div className="mb-4 flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-teal-300" />
                <h2 className="text-xl font-semibold">QA checks</h2>
              </div>
              <ul className="space-y-2 text-sm text-slate-300">
                <li>Timing drift threshold: 250ms</li>
                <li>Missing segments: blocked</li>
                <li>Placeholder text: blocked</li>
                <li>Final render validation: required</li>
              </ul>
            </div>

            <div className="rounded-lg border border-white/10 bg-white/[0.04] p-5">
              <div className="mb-4 flex items-center gap-2">
                <Languages className="h-5 w-5 text-teal-300" />
                <h2 className="text-xl font-semibold">Languages</h2>
              </div>
              <p className="text-sm text-slate-300">Hindi, Spanish, Arabic, Filipino, French, German, Japanese, Korean, Tamil, Telugu, and more.</p>
            </div>
          </div>
        </section>
      </section>
    </main>
  );
}

