-- Convert the LaTeX article to ordinary Markdown with images and separate captions.
local alt = {
  ['assets/boundaries.jpg'] = 'Treasury rule BR-001/v1. Reject invalid, nonfinite and nonpositive amounts. Finite positive amounts below EUR 5,000 enter the standard queue. EUR 5,000 and above require human review. The faulty starter routes minus EUR 0.01 to the standard queue because it compares before validating.',
  ['assets/edod.jpg'] = 'Expect, Delegate, Observe, Decide. The rule owner supplies the approved expectation; the engineer delegates a bounded task to the agent; independent checks observe the exact candidate; the accountable reviewer accepts, rejects or asks the responsible owner.',
}
function Figure(fig)
  local img = nil
  fig:walk({Image = function(el) img = el end})
  if not img then return fig end
  assert(alt[img.src], 'Missing alt text for ' .. img.src)
  return {
    pandoc.Para{pandoc.Image({pandoc.Str(alt[img.src])}, img.src)},
    pandoc.Para(pandoc.utils.blocks_to_inlines(fig.caption.long))
  }
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
