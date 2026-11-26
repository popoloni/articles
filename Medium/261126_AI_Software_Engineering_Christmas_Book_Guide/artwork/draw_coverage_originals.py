#!/usr/bin/env python3
"""Editorial coverage diagrams for the three original Non-Deterministic volumes."""
from coverage_canvas import Canvas, BLUE, ORANGE, INK, MUTED


def note(c, x, y, w, h, heading, body, color=BLUE):
    c.box(x, y, w, h)
    c.swatch(x+16, y+15, w-32, 34, color, .16)
    c.text(x+24, y+41, heading, size=28, bold=True, max_width=w-48)
    c.lines(x+24, y+84, body, size=26, leading=35, color=MUTED, max_width=w-48)


def ndse_original():
    c=Canvas('coverage-ndse-original',
        'Coverage of Non-Deterministic Software Engineering, original edition. '
        'A developer and an AI assistant work together within six connected areas: context engineering; '
        'patterns and quality; tools and workflows; team collaboration; security and governance; '
        'and measurement and adoption. Human judgment and ownership remain central.', seed=202611251)
    c.header('ORIGINAL EDITION  /  COLLABORATE WITH AN ASSISTANT',
             ['Non-Deterministic Software Engineering'],
             'Everyday development practices, with human judgment at the centre.')

    for y in [315, 505, 695]:
        c.line(f'M390 {y} Q420 {y} 450 {y}',1.45,BLUE,.65)
        c.line(f'M950 {y} Q980 {y} 1010 {y}',1.45,BLUE,.65)
    c.line('M450 315 Q435 505 450 695 M950 315 Q965 505 950 695',1.3,BLUE,.65)
    c.line('M450 505 L495 505 M905 505 L950 505',1.5,BLUE,.7)

    note(c, 55, 245, 335, 150, 'Context engineering',
         ['Project instructions', 'Live context & sessions'])
    note(c, 55, 435, 335, 150, 'Patterns & quality',
         ['Practices & pitfalls', 'Quality assurance'], ORANGE)
    note(c, 55, 625, 335, 150, 'Tools & workflows',
         ['Tool maturity', 'Single / many agents'])
    note(c, 1010, 245, 335, 150, 'Team collaboration',
         ['Knowledge sharing', 'Team workflows'])
    note(c, 1010, 435, 335, 150, 'Security & governance',
         ['Safe boundaries', 'Compliance'], ORANGE)
    note(c, 1010, 625, 335, 150, 'Measure & adopt',
         ['Observability', '90-day roadmap'])

    c.swatch(482,275,436,42,ORANGE,.14)
    c.text(700,307,'DEVELOPER + ASSISTANT',size=31,anchor='middle',bold=True,max_width=430)
    # A human at the desk and the assistant's work surface.
    c.ellipse(565,402,32,35)
    c.line('M515 492 Q520 447 552 445 L579 445 Q608 453 615 493',2.2)
    c.line('M532 476 L512 503 L557 503 M600 476 L620 503 L578 503',2.2)
    c.box(745,365,145,111)
    c.line('M734 487 L902 487 L893 477 L744 477 Z',2)
    c.swatch(762,389,111,47,BLUE,.15)
    c.text(818,424,'AI',size=35,anchor='middle',bold=True)
    c.line('M494 512 Q700 508 911 512',2.6)
    c.line('M510 513 L510 537 M896 513 L896 537',2)
    c.text(565,557,'Engineer',size=27,anchor='middle',bold=True)
    c.text(818,557,'Assistant',size=27,anchor='middle',bold=True)
    c.arrow('M624 396 Q676 371 727 396',(727,396),direction=(1,.3),color=BLUE)
    c.arrow('M727 448 Q675 473 624 448',(624,448),direction=(-1,-.3),color=ORANGE)
    c.text(700,601,'Read  ·  implement  ·  review',size=27,anchor='middle',max_width=435)
    c.ellipse(700,691,204,62)
    c.lines(700,682,['Human judgment','and ownership'],size=29,leading=37,anchor='middle',bold=True,max_width=395)
    c.footer('Original focus: collaborate with AI while preserving quality, security and control.')
    return c.save()


def ndsdd_original():
    c=Canvas('coverage-ndsdd-original',
        'Coverage of Non-Deterministic Spec-Driven Development, original edition. '
        'A conceptual route moves through specification, plan, tasks and implementation. '
        'The GitHub Spec Kit focus is supported by templates, worked examples and playbooks, '
        'with integration, advanced patterns and professional judgment.', seed=202611252)
    c.header('ORIGINAL EDITION  /  FROM PRINCIPLES TO PRACTICE',
             ['Non-Deterministic Spec-Driven Development'],
             'A practical companion for turning a specification into working software.')
    c.swatch(335,230,730,39,BLUE,.15)
    c.text(700,260,'GITHUB SPEC KIT  /  A CONCEPTUAL WORK ROUTE',size=29,anchor='middle',bold=True,max_width=730)
    xs=[55,390,725,1060]
    cards=[('1  SPECIFICATION',['Define behaviour','Acceptance cases']),
           ('2  PLAN',['Technical approach','Integration choices']),
           ('3  TASKS',['Scoped tasks','Task order']),
           ('4  IMPLEMENT',['Build the change','Check the result'])]
    for i,(x,(head,body)) in enumerate(zip(xs,cards)):
        c.box(x,320,280,176)
        c.swatch(x+15,337,250,34,BLUE if i%2==0 else ORANGE,.17)
        c.text(x+24,365,head,size=28,bold=True,max_width=237)
        c.lines(x+24,416,body,size=27,leading=38,color=MUTED,max_width=237)
        if i<3:
            c.arrow(f'M{x+289} 410 Q{x+312} 406 {xs[i+1]-10} 410',
                    (xs[i+1]-10,410),direction=(1,0),color=ORANGE)
    # The support layer spans the whole route, rather than being another gate.
    c.line('M100 530 L100 545 Q700 542 1300 545 L1300 530',1.4,BLUE,.75)
    c.text(700,582,'PRACTICAL SUPPORT FOR THE WORK',size=29,anchor='middle',bold=True)
    note(c,75,615,590,173,'Templates, examples & playbooks',
         ['Reusable starting points', 'Complete implementation examples', 'Playbook quick reference'],BLUE)
    note(c,735,615,590,173,'Integration & professional judgment',
         ['Connect the toolkit to a project', 'Advanced patterns', 'Limits and trade-offs'],ORANGE)
    c.footer('Original focus: a specification-first workflow you can follow and adapt.')
    return c.save()


def autonomous_agents():
    c=Canvas('coverage-autonomous-agents',
        'Coverage of Non-Deterministic Autonomous Coding Agents. Decompose work into tasks, '
        'let a coding agent implement, use quality gates and backpressure, and hand results or '
        'blocked work to a human. Bounded retries use memory and context. Related subjects include '
        'scheduling, multi-agent orchestration, safety, tooling and troubleshooting.', seed=202611253)
    c.header('EARLIER VOLUME  /  AUTONOMOUS WORK BETWEEN HUMAN REVIEWS',
             ['Non-Deterministic Autonomous Coding Agents'],
             'Task decomposition, persistent context, quality gates and controlled repetition.')

    note(c,65,290,365,145,'Decompose the task',
         ['Machine-sized steps', 'Clear work items'],BLUE)
    note(c,550,290,390,145,'Coding agent',
         ['Implement the task', 'Use development tools'],ORANGE)
    note(c,550,605,390,145,'Quality gates',
         ['Tests & backpressure', 'Expose failures'],BLUE)
    note(c,65,605,365,145,'Human checkpoint',
         ['Review the result', 'Take over blocked work'],ORANGE)
    c.arrow('M442 365 Q490 362 537 365',(537,365),color=BLUE)
    c.arrow('M745 448 Q741 525 745 590',(745,590),direction=(0,1),color=BLUE)
    c.text(780,525,'Check',size=27,color=MUTED)
    c.arrow('M537 677 Q491 674 442 677',(442,677),direction=(-1,0),color=BLUE)
    c.text(490,722,'Handoff',size=26,anchor='middle',color=MUTED)
    # Explicit retry branch sits outside the worker/check pair.
    c.arrow('M951 655 Q995 645 995 520 Q995 380 951 370',
            (951,370),direction=(-1,0),color=ORANGE)
    # Leave a paper label in the retry path so pen strokes never cross the words.
    c.s.append('<rect x="948" y="482" width="96" height="111" fill="white"/>')
    c.text(1000,514,'Retry',size=27,anchor='middle',color=ORANGE)
    c.text(1000,547,'within',size=25,anchor='middle',color=ORANGE)
    c.text(1000,578,'limits',size=25,anchor='middle',color=ORANGE)
    # A memory note accompanies the loop, with a link to the worker.
    c.ellipse(285,516,220,61)
    c.lines(285,506,['Memory & context','Retain useful state'],size=28,leading=37,anchor='middle',bold=True,max_width=420)
    c.arrow('M506 498 Q545 477 566 449',(566,449),direction=(.7,-1),color=BLUE,width=1.8)
    c.text(745,801,'RALPH LOOP PATTERN',size=29,anchor='middle',bold=True)

    note(c,1050,265,295,156,'Schedule agents',
         ['Overnight execution', 'Multiple agents'],BLUE)
    note(c,1050,454,295,156,'Safety & risk',
         ['Working boundaries', 'Stop & escalate'],ORANGE)
    note(c,1050,643,295,156,'Implement & debug',
         ['Tooling', 'Troubleshooting'],BLUE)
    c.footer('Earlier foundations: autonomous coding loops, quality controls and human handoffs.')
    return c.save()


if __name__=='__main__':
    ndse_original()
    ndsdd_original()
    autonomous_agents()
