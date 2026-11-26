#!/usr/bin/env python3
"""Editorial coverage maps for the two current foundation volumes."""
from coverage_canvas import Canvas, INK, BLUE, ORANGE, MUTED


def note(c,x,y,w,heading,body,color):
    c.swatch(x+3,y,w-8,35,color,.19)
    c.text(x+12,y+27,heading,size=29,bold=True,max_width=w-24)
    c.lines(x+12,y+77,body,size=27,leading=35,color=MUTED,max_width=w-24)
    c.line(f'M{x} {y+48} L{x} {y+125} L{x+18} {y+125}',1.5,color,.85)


def foundation():
    c=Canvas('coverage-ndse2',
        'Coverage of Non-Deterministic Software Engineering, Second Edition. '
        'Trustworthy change connects six editorial groups: intent and contracts; '
        'quality and architecture; security and boundaries; independent checking; '
        'knowledge and learning; teams and economics.',seed=202611251)
    c.header('CURRENT TRILOGY / BOOK 1 / SECOND EDITION',
             ['Non-Deterministic Software Engineering'],
             'Understand the evidence and judgment behind trustworthy software change.')

    # Relationships are plain lines, not a prerequisite sequence.
    for path in [
        'M479 308 C535 308 496 413 535 439',
        'M479 498 Q509 495 535 496',
        'M479 688 C528 688 504 585 535 563',
        'M921 308 C864 308 905 413 865 439',
        'M921 498 Q891 495 865 496',
        'M921 688 C872 688 896 585 865 563',
    ]: c.line(path,2.2,BLUE,.75)

    note(c,56,241,423,'INTENT & CONTRACTS',
         ['Authorised behaviour', 'Examples that make it testable'],BLUE)
    note(c,56,431,423,'QUALITY & ARCHITECTURE',
         ['Design and maintainability', 'The consequences of a change'],ORANGE)
    note(c,56,621,423,'SECURITY & BOUNDARIES',
         ['Generated code and threats', 'Permissions in agent runtimes'],BLUE)
    note(c,921,241,423,'INDEPENDENT CHECKING',
         ['Test oracles and verification', 'Review and accountable verdicts'],ORANGE)
    note(c,921,431,423,'KNOWLEDGE & LEARNING',
         ['Context and persistent memory', 'Human understanding and skills'],BLUE)
    note(c,921,621,423,'TEAMS & ECONOMICS',
         ['Governance and productivity', 'Cost per accepted outcome'],ORANGE)

    # The central open notebook makes the common engineering concern visible.
    c.swatch(550,396,299,194,BLUE,.10)
    c.line('M535 388 Q616 377 700 391 Q783 376 865 388 L865 608 Q781 596 700 609 Q618 595 535 607 Z',2.2)
    c.line('M700 392 Q694 491 700 608',1.2,INK,.55)
    c.line('M542 614 Q621 602 700 616 Q784 602 872 613 L873 394',1.0,INK,.7)
    c.swatch(554,434,292,90,ORANGE,.17)
    c.lines(700,471,['TRUSTWORTHY','CHANGE'],size=35,leading=43,anchor='middle',bold=True)
    c.lines(700,557,['Evidence behind','engineering decisions'],size=25,leading=31,anchor='middle',color=MUTED)
    c.text(700,662,'13 chapters',size=28,anchor='middle',bold=True)
    c.text(700,700,'+ Knowledge Atlas',size=25,anchor='middle',color=MUTED)
    c.footer('Use it to judge which practices deserve trust, and where their limits lie.')
    c.save()


def specification():
    c=Canvas('coverage-ndsdd2',
        'Coverage of Non-Deterministic Spec-Driven Development: Enterprise Edition, '
        'Second Edition. A business need becomes an explicit specification and '
        'implementation evidence. Public frameworks and patterns, enterprise '
        'coordination, templates, playbooks and process economics support the work. '
        'Passing a gate does not replace independent checks and accountable acceptance.',seed=202611252)
    c.header('CURRENT TRILOGY / BOOK 2 / SECOND EDITION',
             ['Non-Deterministic Spec-Driven Development:',
              'Enterprise Edition'],
             'Turn business intent into specifications, coordinated work and evidence.')

    # A simple flow gives the reader a concrete purpose before the coverage groups.
    top=284; w=370; h=181; xs=[62,515,968]
    for x in xs: c.box(x,top,w,h)
    entries=[
        ('BUSINESS NEED',['Clarify scope','Resolve ambiguous cases','Identify the decision owner']),
        ('EXPLICIT SPECIFICATION',['Define behaviour','Link rules to checks','Keep the agreed intent']),
        ('DELIVERY & EVIDENCE',['Plan and coordinate work','Trace rules to results','Use gates and review']),
    ]
    for (x,(heading,body)),color in zip(zip(xs,entries),[BLUE,ORANGE,BLUE]):
        c.swatch(x+14,top+17,w-28,36,color,.19)
        c.text(x+25,top+45,heading,size=28,bold=True,max_width=w-48)
        c.lines(x+25,top+91,body,size=25,leading=32,color=MUTED,max_width=w-48)
    c.arrow('M439 372 Q474 369 506 372',(506,372),color=BLUE)
    c.arrow('M892 372 Q927 369 959 372',(959,372),color=ORANGE)

    c.text(700,520,'METHODS THAT SUPPORT THE FLOW',size=27,anchor='middle',bold=True)
    c.line('M245 466 L245 545 M700 466 L700 491 M1153 466 L1153 545',1.3,BLUE,.65,dash='5 6')
    c.line('M245 545 Q700 540 1153 545',1.3,BLUE,.65,dash='5 6')
    for x in xs: c.box(x,569,w,203)
    lower=[
        ('FRAMEWORK LANDSCAPE',['Public frameworks','Patterns and tradeoffs','Choose a fitting approach']),
        ('TEAM COORDINATION',['Roles and handoffs','Agent cycles and budgets','Traceable decisions']),
        ('WORKING REFERENCE',['Templates and playbooks','Implementation guidance','Process cost and limits']),
    ]
    for (x,(heading,body)),color in zip(zip(xs,lower),[ORANGE,BLUE,ORANGE]):
        c.swatch(x+14,588,w-28,36,color,.18)
        c.text(x+25,616,heading,size=27,bold=True,max_width=w-48)
        c.lines(x+25,664,body,size=25,leading=35,color=MUTED,max_width=w-48)
    c.text(700,817,'From public frameworks to enterprise practice',size=29,anchor='middle',bold=True)
    c.footer('A passed gate is evidence. Acceptance still needs independent checks and an owner.')
    c.save()


if __name__=='__main__':
    foundation()
    specification()
