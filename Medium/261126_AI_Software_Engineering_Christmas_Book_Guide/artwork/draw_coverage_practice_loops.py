#!/usr/bin/env python3
"""Editorial coverage maps for the practical ESA book and its Packt companion."""
from coverage_canvas import Canvas, INK, BLUE, ORANGE, MUTED


def practice():
    c = Canvas('coverage-agentic-ai',
        'Coverage of Engineering Software with Agentic AI. Expect, Delegate, Observe and Decide recur around one accountable change. The book connects needs, specifications, design, context, tools, bounded implementation, independent verification, review, release, history, recovery and learning. Eight missions form two four-mission routes in a workshop service and an existing Treasury router.', 2026112601)
    c.header('CURRENT TRILOGY · BOOK 3 · PRACTICAL ENGINEERING',
             ['Engineering Software with Agentic AI'],
             'Reliable Change with Coding Agents')
    c.text(700,218,'12 CHAPTERS · FROM FIRST REQUEST TO LEARNING AND WHOLE COST',
           size=28,anchor='middle',bold=True,max_width=1270)

    cards = [
        (55,245,'EXPECT',BLUE,['Investigate · specify · design', 'Define authorised behaviour']),
        (830,245,'DELEGATE',ORANGE,['Context · tools · scope', 'Plan work and bound attempts']),
        (830,455,'OBSERVE',BLUE,['Implement · debug · verify', 'Independently check this exact change']),
        (55,455,'DECIDE',ORANGE,['Accept · reject · ask', 'History · release · recovery · learning']),
    ]
    for x,y,title,color,lines in cards:
        c.box(x,y,515,155)
        c.swatch(x+23,y+19,258,37,color,.19)
        c.text(x+32,y+48,title,size=31,bold=True)
        c.lines(x+26,y+94,lines,size=28,leading=37,max_width=460)
    c.arrow('M582 322 Q700 316 818 322',(818,322),(1,0),BLUE)
    c.arrow('M1358 368 Q1383 425 1358 482',(1358,482),(0,1),ORANGE)
    c.arrow('M818 532 Q700 538 582 532',(582,532),(-1,0),BLUE)
    c.arrow('M41 482 Q16 425 41 368',(41,368),(0,-1),ORANGE)
    c.ellipse(700,423,114,66)
    c.swatch(606,386,188,31,BLUE,.1)
    c.text(700,412,'ONE CHANGE',size=28,anchor='middle',bold=True,max_width=199)
    c.text(700,444,'tied to',size=25,anchor='middle',color=MUTED)
    c.text(700,474,'its evidence',size=25,anchor='middle',color=MUTED,max_width=205)

    c.text(700,654,'8 MISSIONS · TWO FOUR-MISSION PRACTICE ROUTES',
           size=28,anchor='middle',bold=True,max_width=1260)
    for x,title,lines,color in [
        (55,'WORKSHOP SERVICE',['Reserve · preserve rules','Cancel · diagnose & cost'],BLUE),
        (715,'TREASURY ROUTER',['Repair · bound provider','Preserve decisions · recover'],ORANGE),
    ]:
        c.box(x,677,630,135)
        c.swatch(x+21,691,585,30,color,.15)
        c.text(x+31,716,title,size=28,bold=True,max_width=568)
        c.lines(x+29,755,lines,size=27,leading=34,max_width=570)
    c.footer('Conduct the change: define it, delegate it, check it, decide.')
    c.save()


def loops():
    c = Canvas('coverage-loop-engineering',
        'Coverage of Loop Engineering for AI Agents, a separately published Packt book. An authorised contract and human owner govern a controller, a probabilistic agent worker and independent checks. The controller manages state, memory, permissions, budgets and stopping. Evidence supports acceptance, correction or escalation, and retry remains bounded. Further coverage includes organization, economics, fresh-context loops, local runtimes and choosing the smallest adequate loop.', 2026112602)
    c.header('SEPARATE PACKT COMPANION · AGENT EXECUTION SYSTEMS',
             ['Loop Engineering for AI Agents'],
             'Design Reliable Agentic AI Systems Beyond the Prompt')

    c.box(55,205,1290,82)
    c.swatch(76,217,1247,27,ORANGE,.16)
    c.text(700,241,'APPROVED CONTRACT + HUMAN OWNER',size=28,anchor='middle',bold=True)
    c.text(700,273,'Authorise behaviour · set policy · decide escalations',size=27,anchor='middle',color=MUTED)

    blocks = [
        (55,325,360,'CONTROLLER',BLUE,['State & memory','Budgets & permissions','Retry · stop · resume']),
        (505,325,315,'AGENT WORKER',ORANGE,['Uses permitted tools','Proposes a candidate','Records its work']),
        (920,325,425,'INDEPENDENT CHECK',BLUE,['Protected expectations','Evidence for this candidate','Reports what passed or failed']),
    ]
    for x,y,w,title,color,lines in blocks:
        c.box(x,y,w,230)
        c.swatch(x+16,y+19,w-32,38,color,.18)
        c.text(x+w/2,y+48,title,size=30,anchor='middle',bold=True,max_width=w-40)
        c.lines(x+22,y+102,lines,size=27,leading=39,max_width=w-42)
    c.arrow('M235 292 L235 314',(235,314),(0,1),ORANGE)
    c.arrow('M1133 292 L1133 314',(1133,314),(0,1),ORANGE)
    c.arrow('M425 449 L495 449',(495,449),(1,0),BLUE)
    c.text(460,431,'work',size=24,anchor='middle',color=MUTED)
    c.arrow('M831 449 L909 449',(909,449),(1,0),BLUE)
    c.text(870,431,'check',size=24,anchor='middle',color=MUTED)

    c.box(920,596,425,86)
    c.text(1132,632,'ACCEPT · CORRECT · ASK',size=27,anchor='middle',bold=True,max_width=385)
    c.text(1132,665,'Owner decision follows evidence',size=24,anchor='middle',color=MUTED,max_width=390)
    c.arrow('M1133 566 L1133 585',(1133,585),(0,1),BLUE)
    c.arrow('M907 641 L235 641 L235 566',(235,566),(0,-1),ORANGE)
    c.text(575,621,'Retry only within budget and authority',size=28,anchor='middle',color=MUTED,max_width=625)

    c.swatch(76,724,1247,34,BLUE,.12)
    c.text(700,751,'ORGANIZATION · ECONOMICS · COST PER ACCEPTED OUTCOME',
           size=28,anchor='middle',bold=True,max_width=1210)
    c.text(700,797,'Fresh-context loops · local runtimes · choosing the smallest adequate loop',
           size=28,anchor='middle',color=MUTED,max_width=1270)
    c.footer('Build the runtime: preserve state, protect checks, bound autonomy.')
    c.save()


if __name__ == '__main__':
    practice()
    loops()
