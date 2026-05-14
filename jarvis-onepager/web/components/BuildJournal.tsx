'use client';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { meta } from '@jarvis/shared/content';

export default function BuildJournal() {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div
            className="hidden md:block absolute top-0 right-0 text-right font-mono text-xs leading-relaxed cursor-default select-none"
            style={{ color: 'var(--fg-subtle)' }}
          >
            <div>g:{meta.buildRef}</div>
            <div>{meta.buildDate} {meta.buildTime}</div>
            <div>{meta.buildDiff}</div>
          </div>
        </TooltipTrigger>
        <TooltipContent side="left" className="font-mono text-xs">
          <p>feat(onepager): initial build</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
