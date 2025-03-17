import React from 'react'
import workflowImage from '../images/illustrate_multi_agent_workflow.png'
import centralizedImage from '../images/illustrate_centralized_collaboration.png'
import decentralizedImage from '../images/illustrate_decentralized_collaboration.png'
import complexImage from '../images/illustrate_complex_collaboration.png'

function ReferenceCard({ href, src, alt, caption }) {
  return (
    <div className="group relative rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden h-full">
      <div className="absolute -inset-px rounded-xl border-2 border-transparent opacity-0 [background:linear-gradient(var(--quick-links-hover-bg,theme(colors.sky.50)),var(--quick-links-hover-bg,theme(colors.sky.50)))_padding-box,linear-gradient(to_top,theme(colors.indigo.400),theme(colors.cyan.400),theme(colors.sky.500))_border-box] group-hover:opacity-100 dark:[--quick-links-hover-bg:theme(colors.slate.800)]" />
      <div className="relative p-2 flex flex-col h-full">
        <a href={href} className="block no-underline flex flex-col h-full" style={{ boxShadow: 'none' }}>
          <span className="absolute -inset-px rounded-xl" />
          <img src={src} alt={alt} className="rounded-lg mb-auto w-full" />
          <div className="text-sm font-medium text-center text-slate-900 dark:text-white no-underline mt-2">
            {caption}
          </div>
        </a>
      </div>
    </div>
  )
}

export function ReferenceGrid() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 mb-8">
      <ReferenceCard 
        href="/docs/multi-agent-workflow"
        src={workflowImage.src}
        alt="Multi-Agent Workflow Pattern"
        caption="Multi-Agent Workflow"
      />
      <ReferenceCard 
        href="/docs/centralized-collaboration"
        src={centralizedImage.src}
        alt="Centralized Collaboration Pattern"
        caption="Centralized Collaboration"
      />
      <ReferenceCard 
        href="/docs/decentralized-collaboration"
        src={decentralizedImage.src}
        alt="Decentralized Collaboration Pattern"
        caption="Decentralized Collaboration"
      />
      <ReferenceCard 
        href="/docs/complex-collaboration"
        src={complexImage.src}
        alt="Complex Collaboration Pattern"
        caption="Complex Patterns"
      />
    </div>
  )
} 