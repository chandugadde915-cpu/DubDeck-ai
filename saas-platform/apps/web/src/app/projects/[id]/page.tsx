import { Download, FileText, PlayCircle, ShieldCheck } from "lucide-react";

export default function ProjectPage({ params }: { params: { id: string } }) {
  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <section className="mx-auto grid w-full max-w-7xl gap-6 px-6 py-8 lg:grid-cols-[1fr_360px]">
        <div className="space-y-6">
          <header className="rounded-lg border border-white/10 bg-white/[0.04] p-5">
            <p className="text-sm text-slate-400">Project {params.id}</p>
            <h1 className="mt-2 text-3xl font-semibold">Dub review workspace</h1>
            <p className="mt-2 text-slate-300">Preview video, edit transcript/translation, inspect QA, and export the final dubbed MP4.</p>
          </header>

          <section className="aspect-video rounded-lg border border-white/10 bg-black">
            <div className="flex h-full items-center justify-center text-slate-500">
              <PlayCircle className="mr-2 h-6 w-6" />
              Video preview
            </div>
          </section>

          <section className="rounded-lg border border-white/10 bg-white/[0.04] p-5">
            <div className="mb-4 flex items-center gap-2">
              <FileText className="h-5 w-5 text-teal-300" />
              <h2 className="text-xl font-semibold">Transcript editor</h2>
            </div>
            <div className="grid gap-3">
              {[1, 2, 3].map((index) => (
                <div key={index} className="grid gap-3 rounded-md border border-white/10 bg-slate-900/70 p-3 md:grid-cols-[120px_1fr_1fr]">
                  <div className="font-mono text-xs text-slate-400">00:0{index}:12.200</div>
                  <textarea className="min-h-20 rounded-md border border-white/10 bg-slate-950 p-3 text-sm text-slate-200" defaultValue="Original transcript text" />
                  <textarea className="min-h-20 rounded-md border border-white/10 bg-slate-950 p-3 text-sm text-slate-200" defaultValue="Translated speech text" />
                </div>
              ))}
            </div>
          </section>
        </div>

        <aside className="space-y-5">
          <div className="rounded-lg border border-white/10 bg-white/[0.04] p-5">
            <h2 className="text-lg font-semibold">Processing</h2>
            <div className="mt-4 h-2 rounded-full bg-slate-800">
              <div className="h-2 w-[88%] rounded-full bg-teal-400" />
            </div>
            <p className="mt-3 text-sm text-slate-300">QA validation in progress</p>
          </div>

          <div className="rounded-lg border border-white/10 bg-white/[0.04] p-5">
            <div className="mb-3 flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-teal-300" />
              <h2 className="text-lg font-semibold">QA Report</h2>
            </div>
            <ul className="space-y-2 text-sm text-slate-300">
              <li>Timing drift: passing</li>
              <li>Missing segments: none</li>
              <li>Clipped audio: none</li>
              <li>Render validation: pending</li>
            </ul>
          </div>

          <button className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-md bg-teal-500 px-5 font-semibold text-slate-950 hover:bg-teal-400">
            <Download className="h-4 w-4" />
            Download final MP4
          </button>
        </aside>
      </section>
    </main>
  );
}

