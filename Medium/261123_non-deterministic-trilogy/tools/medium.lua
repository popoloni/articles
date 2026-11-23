-- Preserve book illustrations as ordinary Markdown images, with independent captions.
local alt = {
  ['assets/esa.jpg'] = 'Two requests both read the machine as free before either writes. Both then commit overlapping reservations.',
  ['assets/ndse.jpg'] = 'The authorized contract leads separately to a candidate implementation and an independent test oracle. Both feed the reviewer’s decision.',
  ['assets/sdd.jpg'] = 'A chain connects project rules and business context to the specification, clarifications, plan, API contract, tests, tasks, source code, release checklist, and security packet.',
  ['assets/esa-overview.jpg'] = 'Book map. Expect, Delegate, Observe, Decide recurs throughout. Chapters 1–3 define the change, 4–6 prepare it, 7–9 implement, verify and release it, and 10–12 cover compatibility, recovery and cost. Part V offers four linked workshop reservation missions or four linked Treasury missions. The appendices contain worked answers, mission solutions and a field card.',
  ['assets/reading-guide.jpg'] = 'Reading guide. Software engineering gives the reviewer a reason to trust or challenge evidence. Spec-driven development yields a behavioral contract with examples and an owner. Engineering with agents yields an observed result and a reason to accept, correct, or stop.',
}
function Figure(fig)
  local img = nil
  fig:walk({Image = function(el) img = el end})
  if not img then return fig end
  assert(alt[img.src], 'Missing alt text for ' .. img.src)
  local caption = pandoc.utils.blocks_to_inlines(fig.caption.long)
  return {
    pandoc.Para{pandoc.Image({pandoc.Str(alt[img.src])}, img.src)},
    pandoc.Para(caption)
  }
end

function Header(header)
  header.level = math.min(header.level + 1, 6)
  return header
end

function Pandoc(doc)
  -- LaTeX readers may emit the abstract as the first paragraph with a custom print layout.
  if not doc.meta.abstract and doc.blocks[1] and doc.blocks[1].t == 'Para' then
    doc.meta.abstract = pandoc.MetaInlines(doc.blocks[1].content)
    doc.blocks:remove(1)
  end
  return doc
end
