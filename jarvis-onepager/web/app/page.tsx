import SquiggleUnderline from '@/components/SquiggleUnderline';
import BuildJournal from '@/components/BuildJournal';
import StatusTable from '@/components/StatusTable';
import ThemeToggle from '@/components/ThemeToggle';
import FadeIn from '@/components/FadeIn';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Smartphone, Lock, Network, BookOpen, Heart, XCircle } from 'lucide-react';
import ArchDiagram from '@jarvis/shared/architecture';
import {
  meta,
  thesis,
  principles,
  shipsNext,
  whatThisIsNot,
  northStar,
  openDecisions,
  glossary,
  archCaption,
} from '@jarvis/shared/content';
import type { Principle } from '@jarvis/shared/content';
import type { ComponentType } from 'react';

const ICON_MAP: Record<string, ComponentType<{ size?: number; style?: React.CSSProperties }>> = {
  Smartphone,
  Lock,
  Network,
  BookOpen,
  Heart,
};

const CONTAINER = 'mx-auto px-6 w-full' as const;
const MAX_W = { maxWidth: 'min(1120px, 100% - 48px)' } as const;
const SECTION_GAP = 'py-16 border-t' as const;

function PrincipleCard({ p }: { p: Principle }) {
  const Icon = ICON_MAP[p.icon];
  return (
    <Card
      className="principle-card border bg-surface rounded-[12px]"
      style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}
    >
      <CardContent className="p-6">
        {Icon && (
          <Icon size={20} style={{ color: 'var(--fg-muted)', marginBottom: '12px' }} />
        )}
        <h3 className="font-semibold text-base mb-2" style={{ color: 'var(--fg)' }}>
          {p.name}
        </h3>
        <p className="text-sm leading-relaxed mb-3" style={{ color: 'var(--fg-muted)' }}>
          {p.gloss}
        </p>
        <p className="font-mono text-xs" style={{ color: 'var(--fg-subtle)' }}>
          Rules out: {p.rulesOut}
        </p>
      </CardContent>
    </Card>
  );
}

export default function Page() {
  return (
    <main style={{ background: 'var(--bg)', color: 'var(--fg)', minHeight: '100vh' }}>
      <div className={CONTAINER} style={MAX_W}>

        {/* ── Hero ── */}
        <FadeIn>
          <section id="hero" className="pt-24 pb-16 relative">
            <BuildJournal />
            <div className="relative inline-block mb-6">
              <h1
                className="font-mono font-bold lowercase"
                style={{ fontSize: 'clamp(40px, 6vw, 56px)', letterSpacing: '-0.01em', color: 'var(--fg)' }}
              >
                {meta.name}
              </h1>
              <SquiggleUnderline
                className="absolute w-full"
                style={{ bottom: '-6px', left: 0, height: '16px' }}
              />
            </div>
            <div className="flex items-center gap-3 flex-wrap mb-6">
              <Badge
                variant="outline"
                className="font-mono text-xs rounded-full px-3 py-1"
                style={{
                  borderColor: 'var(--border)',
                  background: 'var(--surface)',
                  color: 'var(--fg-muted)',
                }}
              >
                <span
                  className="inline-block w-2 h-2 rounded-full mr-1.5"
                  style={{ background: 'var(--accent)' }}
                />
                {meta.statusPill}
              </Badge>
            </div>
            <p
              className="text-xl md:text-2xl max-w-2xl"
              style={{ color: 'var(--fg-muted)', lineHeight: 1.4 }}
            >
              {thesis.oneLiner}
            </p>
          </section>
        </FadeIn>

        {/* ── Thesis ── */}
        <FadeIn>
          <section id="thesis" className={SECTION_GAP} style={{ borderColor: 'var(--border)' }}>
            <p
              className="font-mono text-xs uppercase tracking-widest mb-4"
              style={{ color: 'var(--accent)' }}
            >
              {thesis.eyebrow}
            </p>
            <div className="max-w-2xl space-y-4">
              {thesis.sentences.map((s, i) => (
                <p key={i} className="text-base leading-relaxed" style={{ color: 'var(--fg)' }}>
                  {s}
                </p>
              ))}
            </div>
          </section>
        </FadeIn>

        {/* ── Five Principles ── */}
        <FadeIn>
          <section id="principles" className={SECTION_GAP} style={{ borderColor: 'var(--border)' }}>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
              {principles.map((p) => (
                <PrincipleCard key={p.id} p={p} />
              ))}
            </div>
          </section>
        </FadeIn>

        {/* ── Architecture Diagram ── */}
        <FadeIn>
          <section id="diagram" className={SECTION_GAP} style={{ borderColor: 'var(--border)' }}>
            <div className="w-full">
              <ArchDiagram mode="dark" />
            </div>
            <p className="mt-3 font-mono text-xs max-w-2xl" style={{ color: 'var(--fg-muted)' }}>
              {archCaption}
            </p>
          </section>
        </FadeIn>

        {/* ── Where We Are ── */}
        <FadeIn>
          <section id="phases" className={SECTION_GAP} style={{ borderColor: 'var(--border)' }}>
            <StatusTable />
          </section>
        </FadeIn>

        {/* ── Ships Next ── */}
        <FadeIn>
          <section id="ships-next" className={SECTION_GAP} style={{ borderColor: 'var(--border)' }}>
            <div
              className="rounded-[12px] p-6 relative overflow-hidden"
              style={{ background: 'var(--surface-2)' }}
            >
              <div
                className="absolute left-0 top-0 bottom-0 w-[3px]"
                style={{ background: 'var(--accent)', borderRadius: '12px 0 0 12px' }}
              />
              <div className="pl-5">
                <h2 className="font-semibold text-xl mb-3" style={{ color: 'var(--fg)' }}>
                  {shipsNext.heading}
                </h2>
                <p className="text-base leading-relaxed mb-3" style={{ color: 'var(--fg-muted)' }}>
                  {shipsNext.body}
                </p>
                <p className="font-mono text-sm" style={{ color: 'var(--warn)' }}>
                  {shipsNext.killCriterion}
                </p>
              </div>
            </div>
          </section>
        </FadeIn>

        {/* ── What This Is Not ── */}
        <FadeIn>
          <section id="not" className={SECTION_GAP} style={{ borderColor: 'var(--border)' }}>
            <ul className="space-y-4">
              {whatThisIsNot.map((item, i) => (
                <li key={i} className="flex items-start gap-3 text-base" style={{ color: 'var(--fg)' }}>
                  <XCircle size={16} className="mt-1 flex-shrink-0" style={{ color: 'var(--fg-subtle)' }} />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </section>
        </FadeIn>

        {/* ── North Star ── */}
        <FadeIn>
          <section id="north-star" className={SECTION_GAP} style={{ borderColor: 'var(--border)' }}>
            <p
              className="font-mono text-xs uppercase tracking-widest mb-4"
              style={{ color: 'var(--accent)' }}
            >
              {northStar.eyebrow}
            </p>
            <div className="flex flex-wrap gap-2 mb-4">
              {northStar.pills.map((pill) => (
                <Badge
                  key={pill.label}
                  className="rounded-full px-3 py-1 font-mono text-xs"
                  style={
                    pill.variant === 'primary'
                      ? { background: 'var(--accent)', color: 'var(--accent-fg)', border: 'none' }
                      : { background: 'var(--surface)', color: 'var(--fg)', borderColor: 'var(--border)' }
                  }
                  variant={pill.variant === 'primary' ? 'default' : 'outline'}
                >
                  {pill.label}
                </Badge>
              ))}
            </div>
            <p className="text-base leading-relaxed max-w-2xl" style={{ color: 'var(--fg-muted)' }}>
              {northStar.body}
            </p>
          </section>
        </FadeIn>

        {/* ── Open Decisions ── */}
        <FadeIn>
          <section id="decisions" className={SECTION_GAP} style={{ borderColor: 'var(--border)' }}>
            <Accordion type="multiple" className="w-full">
              {openDecisions.map((d) => (
                <AccordionItem
                  key={d.id}
                  value={d.id}
                  style={{ borderColor: 'var(--border)' }}
                >
                  <AccordionTrigger
                    className="text-base font-medium py-4 hover:no-underline"
                    style={{ color: 'var(--fg)' }}
                  >
                    <span className="text-left flex-1">{d.name}</span>
                    <span
                      className="font-mono text-xs ml-4 flex-shrink-0 mr-2"
                      style={{ color: 'var(--fg-muted)' }}
                    >
                      Resolve: {d.resolve}
                    </span>
                  </AccordionTrigger>
                  <AccordionContent className="pb-4">
                    <p className="text-sm leading-relaxed" style={{ color: 'var(--fg-muted)' }}>
                      {d.rationale}
                    </p>
                    {d.tbd && (
                      <span
                        className="inline-block mt-2 font-mono text-xs px-2 py-0.5 rounded border"
                        style={{ color: 'var(--fg-subtle)', borderColor: 'var(--border)' }}
                      >
                        [TBD]
                      </span>
                    )}
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </section>
        </FadeIn>

        {/* ── Glossary + Footer ── */}
        <FadeIn>
          <section id="glossary" className={SECTION_GAP} style={{ borderColor: 'var(--border)' }}>
            <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-6">
              {glossary.map((entry) => (
                <div key={entry.term}>
                  <dt className="font-mono font-medium text-sm mb-1" style={{ color: 'var(--fg)' }}>
                    {entry.term}
                  </dt>
                  <dd className="text-sm leading-relaxed" style={{ color: 'var(--fg-muted)' }}>
                    {entry.definition}
                  </dd>
                </div>
              ))}
            </dl>

            <Separator className="my-8" style={{ background: 'var(--border)' }} />

            <div className="flex items-center justify-between">
              <p className="font-mono text-xs" style={{ color: 'var(--fg-subtle)' }}>
                {meta.name} · {meta.date} · g:{meta.buildRef}
              </p>
              <ThemeToggle />
            </div>
          </section>
        </FadeIn>

        {/* bottom breathing room */}
        <div className="h-16" />

      </div>
    </main>
  );
}
