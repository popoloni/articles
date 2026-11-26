-- Preserve the article, its accessible figure description and its caption in GFM.
local alt = {
  ['assets/banners/01_ndse2_christmas_guide.jpg'] = 'English Christmas Book Guide square banner for ndse2: official English cover and hand-drawn coverage map showing the engineering foundation with six concerns around trustworthy change.',
  ['assets/banners/02_ndsdd2_christmas_guide.jpg'] = 'English Christmas Book Guide square banner for ndsdd2: official English cover and hand-drawn coverage map showing business intent through specification and governed delivery.',
  ['assets/banners/03_agentic_ai_christmas_guide.jpg'] = 'English Christmas Book Guide square banner for agentic ai: official English cover and hand-drawn coverage map showing Expect, Delegate, Observe, Decide and two four-mission practice routes.',
  ['assets/banners/04_loop_engineering_christmas_guide.jpg'] = 'English Christmas Book Guide square banner for loop engineering: official English cover and hand-drawn coverage map showing the human owner, controller, agent worker, independent checker, state and retry budget.',
  ['assets/banners/05_ndse_original_christmas_guide.jpg'] = 'English Christmas Book Guide square banner for ndse original: official English cover and hand-drawn coverage map showing the engineer and AI assistant supported by context, patterns, quality, security and teams.',
  ['assets/banners/06_ndsdd_original_christmas_guide.jpg'] = 'English Christmas Book Guide square banner for ndsdd original: official English cover and hand-drawn coverage map showing the original specification, plan, task and implementation workflow.',
  ['assets/banners/07_autonomous_agents_christmas_guide.jpg'] = 'English Christmas Book Guide square banner for autonomous agents: official English cover and hand-drawn coverage map showing task breakdown, guarded coding attempts, retained memory and human handoff.',
  ['assets/covers/cover-ndse2.jpg'] = 'Official English front cover of Non-Deterministic Software Engineering, Second Edition, by Enrico Papalini.',
  ['assets/covers/cover-ndsdd2.jpg'] = 'Official English front cover of Non-Deterministic Spec-Driven Development: Enterprise Edition, Second Edition, by Enrico Papalini.',
  ['assets/covers/cover-agentic-ai.jpg'] = 'Official English front cover of Engineering Software with Agentic AI: Reliable Change with Coding Agents, by Enrico Papalini.',
  ['assets/covers/cover-loop-engineering.jpg'] = 'Official English front cover of the Packt edition of Loop Engineering for AI Agents, by Enrico Papalini.',
  ['assets/covers/cover-ndse-original.jpg'] = 'Official English front cover of Non-Deterministic Software Engineering, original edition, by Enrico Papalini.',
  ['assets/covers/cover-ndsdd-original.jpg'] = 'Official English front cover of Non-Deterministic Spec-Driven Development, original edition, by Enrico Papalini.',
  ['assets/covers/cover-autonomous-agents.jpg'] = 'Official English front cover of Non-Deterministic Autonomous Coding Agents, by Enrico Papalini.',
  ['assets/reading-map.jpg'] = 'A pen-and-crayon reading map. The current trilogy is: 1, Non-Deterministic Software Engineering, Second Edition, for understanding which practices deserve trust; 2, Non-Deterministic Spec-Driven Development: Enterprise Edition, Second Edition, for specifying what a change must do; 3, Engineering Software with Agentic AI, for directing and judging a change. The separately published Packt book Loop Engineering for AI Agents covers the execution runtime. All four connect to the reader\'s next engineering question; each stands alone.',
  ['assets/coverage-ndse2.jpg'] = 'Coverage of Non-Deterministic Software Engineering, Second Edition. Trustworthy change connects intent and contracts, quality and architecture, code and runtime security, independent verification and review, system knowledge and human learning, and teams, productivity and economics.',
  ['assets/coverage-ndsdd2.jpg'] = 'Coverage of Non-Deterministic Spec-Driven Development: Enterprise Edition, Second Edition. Business intent becomes explicit behaviour and a verifiable specification, supported by framework choices, traceability, gates and evidence, roles and bounded autonomous work, templates, playbooks and process-cost judgment.',
  ['assets/coverage-agentic-ai.jpg'] = 'Coverage of Engineering Software with Agentic AI. Expect, Delegate, Observe and Decide organise responsibilities from investigation and specification to implementation, independent checks, release, recovery and learning. The book has twelve chapters and eight missions: four in a workshop reservation service and four in a Treasury router.',
  ['assets/coverage-loop-engineering.jpg'] = 'Coverage of Loop Engineering for AI Agents, the separate Packt companion. A controller coordinates a worker and independent checking, with protected state, budgets, stopping conditions and human authority. Further topics include organisation, outcome economics, fresh-context loops, a local runtime and selecting an adequate loop.',
  ['assets/coverage-ndse-original.jpg'] = 'Coverage of the original Non-Deterministic Software Engineering. The engineer collaborates with an AI assistant, supported by context engineering, patterns and antipatterns, development and quality practices, team collaboration, security and governance, and measurement and adoption.',
  ['assets/coverage-ndsdd-original.jpg'] = 'Coverage of the original Non-Deterministic Spec-Driven Development. The practical route runs from specification to planning, task breakdown and implementation. GitHub Spec Kit, integration practices, advanced patterns, templates, worked examples, playbooks and professional judgment support the work.',
  ['assets/coverage-autonomous-agents.jpg'] = 'Coverage of Non-Deterministic Autonomous Coding Agents. Bounded coding attempts connect task decomposition, the Ralph loop, memory and context, quality gates and backpressure, scheduling and multi-agent orchestration, safety, troubleshooting and handoff for human review.',
}
local cover_links = {
  ['assets/banners/01_ndse2_christmas_guide.jpg'] = 'https://www.amazon.com/dp/B0HN9J7VZG',
  ['assets/banners/02_ndsdd2_christmas_guide.jpg'] = 'https://www.amazon.com/dp/B0GZZDFMYF',
  ['assets/banners/03_agentic_ai_christmas_guide.jpg'] = 'https://www.amazon.com/dp/B0HSPH86CG',
  ['assets/banners/04_loop_engineering_christmas_guide.jpg'] = 'https://www.amazon.com/dp/1808766415',
  ['assets/banners/05_ndse_original_christmas_guide.jpg'] = 'https://www.amazon.com/dp/B0G7LPJBTH',
  ['assets/banners/06_ndsdd_original_christmas_guide.jpg'] = 'https://www.amazon.com/dp/B0GHFBNC5Z',
  ['assets/banners/07_autonomous_agents_christmas_guide.jpg'] = 'https://www.amazon.com/dp/B0GMCFLH2C',
  ['assets/covers/cover-ndse2.jpg'] = 'https://www.amazon.com/dp/B0HN9J7VZG',
  ['assets/covers/cover-ndsdd2.jpg'] = 'https://www.amazon.com/dp/B0GZZDFMYF',
  ['assets/covers/cover-agentic-ai.jpg'] = 'https://www.amazon.com/dp/B0HSPH86CG',
  ['assets/covers/cover-loop-engineering.jpg'] = 'https://www.amazon.com/dp/1808766415',
  ['assets/covers/cover-ndse-original.jpg'] = 'https://www.amazon.com/dp/B0G7LPJBTH',
  ['assets/covers/cover-ndsdd-original.jpg'] = 'https://www.amazon.com/dp/B0GHFBNC5Z',
  ['assets/covers/cover-autonomous-agents.jpg'] = 'https://www.amazon.com/dp/B0GMCFLH2C',
}
function Figure(fig)
  local img = nil
  fig:walk({Image = function(el) img = el end})
  if not img then return fig end
  assert(alt[img.src], 'Missing alt text for ' .. img.src)
  local picture = pandoc.Image({pandoc.Str(alt[img.src])}, img.src)
  if cover_links[img.src] then picture = pandoc.Link({picture}, cover_links[img.src]) end
  return {
    pandoc.Para{picture},
    pandoc.Para(pandoc.utils.blocks_to_inlines(fig.caption.long))
  }
end
function Div(div)
  if div.classes:includes('samepage') then return div.content end
  return div
end
function Header(header)
  header.level = math.min(header.level + 1, 6)
  return header
end
function Pandoc(doc)
  if not doc.meta.abstract and doc.blocks[1] and doc.blocks[1].t == 'Para' then
    doc.meta.abstract = pandoc.MetaInlines(doc.blocks[1].content)
    doc.blocks:remove(1)
  end
  return doc
end
